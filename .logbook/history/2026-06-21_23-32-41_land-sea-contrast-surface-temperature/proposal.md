---
schema_version: 1
slug: land-sea-contrast-surface-temperature
title: Land-Sea-Contrast-Aware Near-Surface Temperature Correction
status: ready
created_at: 2026-06-21T21:38:57Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
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

# Land-Sea-Contrast-Aware Near-Surface Temperature Correction

## Hypothesis

`2m_temperature` remains by far the dominant error (area-weighted skill near
`-1.47`, worse than persistence at every lead), while the mass and wind fields
are near or above persistence at short lead. Every accepted near-surface
mechanism so far -- the analysis-offset Held-Suarez equilibrium, the
stability-aware surface residual decay, the scale-separated residual memory --
is **spatially uniform**: it applies the same correction strength and memory
over land and ocean. But the `2m_temperature` error is not spatially uniform.
Over **land**, screen temperature has large diurnal and seasonal amplitude and
strong surface-type sensitivity that a single global correction cannot match;
over **ocean**, screen temperature closely tracks the slowly varying sea-surface
state and is therefore nearly persistent over a 1-15 day forecast, so a
correction tuned to land dynamics actively degrades it. Splitting the
near-surface correction by land fraction should reduce `2m_temperature` error
where it is largest (land) while letting ocean points stay close to their
near-persistent initial state.

## Mechanism

Register a side-by-side candidate named
`..._analysis_hs_eq_landsea_surface`. Preserve every incumbent setting --
initialization, DFI, weak-HS forcing, Coriolis split, theta tendency/recentering,
off-centering, scale-separated residual, analysis-offset HS equilibrium, output
variables, splits, lead times, metrics, and gates.

For the candidate only, make the accepted near-surface `2m_temperature`
correction land-fraction aware:

- read the static `land_sea_mask` constant for the WeatherBench2 grid through
  the existing `WeatherBench2Source.read_constants` API (the same static-field
  path the accepted terrain-aware orography work uses), and cache it grid-aligned;
- form a bounded land fraction in `[0, 1]`;
- over land, retain the incumbent analysis-anchored correction and residual
  decay at full strength;
- over ocean, lengthen the residual memory toward persistence (weaker decay of
  the lead-zero residual), since ocean screen temperature is well-approximated by
  its slowly varying initial state;
- blend the two regimes continuously with the land fraction so coastlines are
  smooth, using fixed bounded coefficients;
- apply only to the `2m_temperature` diagnostic; leave `10m` winds,
  `mean_sea_level_pressure`, `geopotential_500`, prognostic dynamics, and mass
  diagnostics unchanged;
- use the identical correction in DFI and positive-time rollout (it is a
  diagnostic mapping, not a spinup);
- fall back to the incumbent uniform correction if the mask is unavailable or
  nonfinite.

This is distinct from all prior near-surface work, which is uniform in space:
`analysis-offset-held-suarez-equilibrium`, `stability-aware-surface-residual-decay`,
`scale-separated-surface-residual-memory`, `bulk-richardson-2m-temperature-diagnostic`,
and `seasonal-stability-surface-residual-decay` none use a land-sea mask. No
prior idea in history, staging, or scrap references land or sea surface type.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` (land-fraction blend in the
    near-surface temperature correction; static-constant loading)
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes: add only the side-by-side candidate named above.
- API changes: none.
- Tests to update:
  - pure-land and pure-ocean columns reduce to the two intended regimes;
  - a coastline fraction blends continuously between them;
  - non-`2m_temperature` outputs are byte-for-byte unchanged versus the incumbent;
  - missing-mask fallback reproduces the incumbent;
  - registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements: `2m_temperature` at days 1-10, concentrated over land
  (less uniform mis-correction) and over ocean (less spurious decay away from a
  near-persistent state).
- Expected neutral metrics: `mean_sea_level_pressure`, `geopotential_500`,
  `10m_u_component_of_wind` -- only the `2m_temperature` diagnostic changes.
- Possible regressions: if the global correction was already near the land/ocean
  average optimum, the split is neutral; an overly persistent ocean regime could
  regress ocean `2m_temperature` if real ocean screen temperature drifts.

## Risks

- Numerical stability: negligible; this is a bounded diagnostic blend, no
  prognostic tendency.
- Compute cost: negligible; one cached static field and an elementwise blend.
- Data leakage: none; uses a static land-sea mask and the model's own forecast
  state, no verification-time information.
- Physical plausibility: high; land-ocean contrast in near-surface temperature
  behavior is a first-order feature of the climate system.
- Rollback complexity: low; remove one blend and constant load, one
  factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate: `uv run pytest`; `uv run dynamaxx-eval fast --model ..._landsea_surface`;
  require finite forecasts and zero diagnostic issues.
- Iteration gate: `uv run dynamaxx-eval iteration --model ..._landsea_surface --workers 4`;
  support is primary-score delta at least `+0.002` with clean diagnostics and no
  early-lead or variable-by-lead RMSE guardrail failure. Because `2m_temperature`
  carries the largest deficit, a moderate per-variable gain there can clear the gate.
- Validation gate: `uv run dynamaxx-eval validation --model ..._landsea_surface --workers 4`
  only after iteration promotion; require validation delta at least `+0.001`.
- Falsification: a clean near-zero or negative iteration delta would show the
  uniform correction already sits at the land/ocean optimum and that surface-type
  structure is not a recoverable error source under fixed HS forcing.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/data/weatherbench2.py` `read_constants`
    exposes static grid fields; `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography`
    confirms static constants are loadable and usable by the dycore.
  - Dynamaxx history:
    `.logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium`
    improved `2m_temperature` with a spatially uniform analysis offset; this
    proposal adds the missing land-sea structure to that gain.
  - Betts, A. K. 2004. Understanding hydrometeorology using global models.
    Bulletin of the American Meteorological Society (land-atmosphere coupling vs
    ocean-atmosphere coupling of near-surface temperature).
    https://doi.org/10.1175/BAMS-85-11-1673
  - Trenberth, K. E. et al. 2009. Earth's global energy budget. BAMS
    (contrasting land vs ocean surface energy balance and temperature response).
    https://doi.org/10.1175/2008BAMS2634.1

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-21 to help the
loop out of a ~33 hour plateau (no accept since 2026-06-20 12:47). It targets the
dominant remaining error, `2m_temperature`, through spatial structure that no
prior idea has used: a land-sea mask. It is intentionally a low-implementation-surface
diagnostic blend -- the kind of bounded near-surface mechanism the Evaluator has
favored over higher-risk prognostic schemes -- so it is more likely to be picked
than scrapped. The larger-swing untried alternatives remain the staged dynamics
ideas `divergence-selective-offcentering` and `leith-nonlinear-eddy-viscosity`.

## Evaluator Notes

### 2026-06-21T23:30:36Z

Decision: move to `ready`; ranked 1 of 3 current proposals.

This is the strongest next implementable candidate in the batch. It targets the
dominant remaining `2m_temperature` deficit while keeping the forecast
trajectory, mass fields, wind diagnostics, pressure-level outputs, splits,
metrics, and fixed gates unchanged. The land/ocean contrast mechanism is
physically clear and materially different from the recent subthreshold
analysis-HS, residual-gate, and hydrostatic reconstruction variants.

The main caveat is implementation hygiene: this proposal requires a static
WeatherBench2 constant at forecast time. That is acceptable only if the
Implementer reuses the existing `WeatherBench2Source.read_constants` path with
strict grid/shape/finite checks, keeps the public forecast contract unchanged,
uses no validation-derived constants, and falls back exactly to the incumbent
uniform correction whenever the mask cannot be read or aligned. Prefer this
over the orographic lapse proposal because a bounded land-sea blend changes one
diagnostic channel without invoking terrain height differences, which have
strong negative mass-field history in this repository.
