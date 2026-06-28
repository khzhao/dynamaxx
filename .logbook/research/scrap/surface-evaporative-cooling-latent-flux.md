---
schema_version: 1
slug: surface-evaporative-cooling-latent-flux
title: Wind- and Stability-Dependent Surface Evaporative (Latent) Cooling Flux
status: scrap
created_at: 2026-06-23T03:05:00Z
author_role: Researcher
target_model: dino_hsl2_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Wind- and Stability-Dependent Surface Evaporative (Latent) Cooling Flux

## Hypothesis

The incumbent's only surface thermal process is the accepted ocean *sensible*
heat flux plus the analytic Held-Suarez relaxation. There is **no latent / moist
process anywhere**: surface evaporation, which over moist surfaces removes
comparable or larger energy than the sensible flux (Bowen ratio < 1 over ocean
and wet land), is entirely absent. Because evaporation cools the near-surface
air and the moist surface skin, its omission biases the lowest-layer temperature
*warm* relative to the energy-balanced state -- and `2m_temperature` is by far
the worst-skilled variable (~ -1.01). A bounded surface **evaporative cooling**
tendency on the lowest layer -- a latent heat sink whose magnitude follows the
standard bulk transfer law (wind- and stability-dependent), scaled by a static
surface moisture-availability factor `beta(x)` -- adds the missing latent term
and should reduce the dominant warm near-surface temperature error through the
prognostic state, not an output diagnostic.

## Mechanism

This is a **latent** lower-boundary flux, mechanistically distinct from the
accepted **sensible** flux: the accepted flux relaxes the lowest-layer
temperature *toward a persisted air-temperature anchor* (it can warm or cool
toward analysis); this term is a one-signed **cooling** sink set by the
saturation deficit at the surface, not by an anchor.

- Add an opt-in `_SurfaceEvaporativeCoolingForcingSigma`
  (`time_integration.ExplicitODE`), composed in `adapter.py` via a new
  `_compose_*` helper gated by `apply_surface_evaporative_cooling`,
  structurally mirroring `_OceanBulkSensibleHeatFluxForcingSigma` (same
  guards, per-step cap, minimum e-folding clamp, modal round-trip, finite
  fallback).
- Build a static moisture-availability field `beta(x)` in [0,1] once per
  forecast from the available constants via the existing `read_constants`
  loader: `beta = beta_ocean` over ocean (`land_sea_mask -> 0`, treat ocean as
  saturated, `beta ~ 1`), and over land a soil-class-dependent value derived
  from `soil_type` (coarse/sandy classes drier, fine/loam classes moister),
  bounded well away from extremes. No SST, vegetation, or soil-moisture field is
  required.
- The lowest-layer cooling tendency:
  `dT/dt = -(L_v / c_p) * (Cd * |U_1| / H_bl) * beta(x) * max(q_sat(T_1, p_s) - q_1, 0)`,
  where `q_sat` uses the Tetens/Clausius-Clapeyron form already implied by the
  existing saturation-adjustment helpers, `q_1` is the lowest-layer specific
  humidity if the dry incumbent is run with humidity carried, **or** a fixed
  climatological near-surface relative-humidity closure (`q_1 = RH0 * q_sat`,
  `RH0 ~ 0.7-0.8`) so the term remains well-defined in the dry configuration.
  The `max(..., 0)` makes it a pure sink (no spurious heating). Apply the same
  `_OCEAN_BULK_SHF_*`-style cap and clamp constants (e.g.
  `max_step_increment ~ 0.05 K`, `min_efolding`), reusing the accepted bounds.

## Implementation Scope

- `adapter.py`: new forcing class + `_compose_*` helper + `_build_beta_field`
  (reuses `_load_land_sea_fraction_for_grid` pattern, adds `soil_type` read),
  new boolean dataclass field, one registered factory; reuse `q_sat`/Tetens
  helper, unit factors, `_to_dinosaur_latitude_order`.
- `__init__.py`, `registry.py`: one new short-named candidate (e.g.
  `dino_evap_cool`).
- Tests: registry presence, finite forecast, unit test that the term is a
  non-positive temperature tendency and is zero when the mask/soil constants are
  unavailable.

## Expected Metric Movement

- `2m_temperature`: primary target; expect a reduction of the warm near-surface
  bias and the dominant standing error after the residual decays, strongest at
  mid-to-late leads where the analytic relaxation otherwise dominates.
- `mean_sea_level_pressure` / `geopotential_500`: small/neutral via column
  thickness; must stay within the 2% early-lead guardrail.
- `10m_u_component_of_wind`: neutral (no momentum term).

## Risks

- Wrong sign / over-cooling if `beta` or `RH0` is mis-set, producing a cold bias
  that flips the error -> mitigate with conservative `beta`, the per-step cap,
  and a small `RH0` deficit; bound `beta` away from 1 over land.
- Dependence on a climatological RH closure in the dry config is the weakest
  assumption; if humidity is available it should be used instead, but the closure
  keeps the term defined and bounded.
- Saturation-deficit nonlinearity could interact with the lowest-layer thermal
  budget; the `max(.,0)` sink and finite guards prevent runaway, falling back to
  the exact incumbent on any nonfinite.

## Evaluation Plan

- `uv run pytest`, then `fast`, then `iteration`. Promote to `validation` only
  if iteration delta >= +0.002 with clean diagnostics and no early-lead RMSE
  guardrail breach. Success signal: positive primary-score delta concentrated in
  `2m_temperature` with neutral MSLP/Z500/wind.

## Why Novel vs Prior Slugs

- vs accepted `ocean-bulk-sensible-heat-flux`: that is a *sensible* flux relaxing
  toward a persisted *temperature anchor*; this is a *latent* evaporative
  *cooling sink* set by the surface saturation deficit, active over land too,
  with a soil/ocean moisture-availability weighting. Different energy term,
  different sign behavior, different spatial mask.
- vs rejected `snow-soil-land-thermal-reservoir` and
  `sst-sea-ice-ocean-flux-anchor`: those are *energy-storage reservoirs* / new
  *boundary temperature data*; this adds no reservoir and no new boundary
  temperature -- it is a flux computed from the prognostic state and a static
  moisture mask, so it respects the land-surface-energy negative evidence.
- vs scrapped `near-surface-stability-heat-mixing` and
  `humidity-weighted-radiative-temperature-relaxation`: the former is *vertical
  heat diffusion* between layers; the latter is a *radiative* relaxation keyed to
  humidity as a longwave emitter. This is a *surface evaporative latent flux* --
  a turbulent boundary-condition term, not interior mixing and not radiation.
- vs scrapped `moist-convective-adjustment`: that relaxes interior columns toward
  a moist adiabat (convective heating); this is a surface evaporative *cooling*
  boundary flux on the lowest layer only.

## Honest Success Probability

Low-medium. The physics is sound and targets the worst variable, but the dry-run
RH closure is a real weakness, and prior near-surface thermal additions (snow/
soil reservoir, SST anchor) repeatedly produced near-zero global deltas, which is
meaningful negative evidence that aggregate score is hard to move with bounded
lowest-layer thermal terms. Offered as the better-targeted of the two ideas if
only one slot is available, but the momentum-roughness idea is the more defensible
primary bet.

## Citations

- Held, I. M., and M. J. Suarez, 1994: A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bull. Amer. Meteor.
  Soc., 75, 1825-1830.
  https://doi.org/10.1175/1520-0477(1994)075<1825:APFTIO>2.0.CO;2
- Manabe, S., 1969: Climate and the ocean circulation: I. The atmospheric
  circulation and the hydrology of the earth's surface. Mon. Wea. Rev., 97,
  739-774. https://doi.org/10.1175/1520-0493(1969)097<0739:CATOC>2.3.CO;2
  (bucket evaporation / moisture-availability beta closure).
- Fairall, C. W., E. F. Bradley, J. E. Hare, A. A. Grachev, and J. B. Edson,
  2003: Bulk parameterization of air-sea fluxes: Updates and verification for the
  COARE algorithm. J. Climate, 16, 571-591.
  https://doi.org/10.1175/1520-0442(2003)016<0571:BPOASF>2.0.CO;2

## Evaluator Notes

### 2026-06-23T03:03:08Z

Decision: move to `scrap`; ranked 4 of 4 current proposals.

The missing latent-flux physics is real, but this proposal is not a good
model-selection target under the fixed gates. It relies on a dry-run relative
humidity closure and a static soil/ocean moisture-availability map, while the
current dycore does not carry a robust prognostic moist surface state. That
makes the one-signed cooling sink closer to a tuned lower-layer thermal bias
correction than a constrained latent heat flux. If soil or moisture constants
are not already exposed in the model path, the proposal also drifts toward new
static-data/infrastructure support, which is out of scope for a ready dycore
experiment.

Recent surface evidence is strongly negative for spending another run here.
The accepted ocean sensible heat flux was high leverage, but the SST/sea-ice
anchor and snow/soil land thermal reservoir follow-ups were clean and
effectively zero. Existing staging already contains lower-boundary sensible
heat and exact ocean-flux variants, while this proposal adds a weaker dry RH
assumption and a risk of broad cold bias in the worst-scored variable. Scrap
this file rather than keep another near-surface thermal variant in staging.
