---
schema_version: 1
slug: ocean-bulk-sensible-heat-flux
title: Ocean-Weighted Bulk Sensible Heat Flux Forcing
status: ready
created_at: 2026-06-22T05:21:08Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/held_suarez.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Ocean-Weighted Bulk Sensible Heat Flux Forcing

## Hypothesis

The accepted incumbent recovered a large score gain by making the `2m_temperature`
residual memory land-sea aware, which is evidence that the remaining near-surface
thermal error has a lower-boundary component. The current rollout still has no
explicit surface sensible heat exchange; its thermodynamic lower-boundary effect
is the weak Held-Suarez Newtonian relaxation toward an analytic equilibrium,
optionally offset from the analysis. Over ocean, the lower boundary temperature
changes slowly over 1-15 day lead times, so a weak flow-dependent bulk heat flux
toward an initial ocean surface-air anchor may improve the lowest prognostic
thermal layer before the output residual correction is applied.

This is narrower than the staged `bulk-surface-sensible-heat-flux` idea: it is
ocean-weighted only, uses one conservative fixed transfer scale, acts only on the
lowest sigma layer, and leaves land points on the incumbent trajectory. It is not
a forecast-output blend because the tendency enters the prognostic temperature
state during rollout and can affect later pressure-level interpolation through
the normal dycore path.

## Mechanism

Register a side-by-side candidate extending the incumbent with an
`_ocean_bulk_shf` suffix. Preserve the incumbent DFI, weak-HS analysis
equilibrium offset, Strang Coriolis split, theta tendency, theta mean recentering,
semi-implicit off-centering, scale-separated residuals, accepted land-sea
`2m_temperature` residual, output variables, and fixed evaluation protocols.

Add an opt-in explicit forcing composed with the primitive-equation tendency:

- load the existing land-sea fraction through the same static-mask path already
  used by the accepted land-sea residual correction;
- construct an ocean weight `1 - land_fraction`, smoothed only by the existing
  grid alignment path and falling back to zero if the mask is missing or invalid;
- derive a fixed initial ocean thermal anchor from the lead-zero `2m_temperature`
  channel when present, otherwise from the initialized lowest-layer full
  temperature;
- each tendency call, diagnose the current lowest-layer wind speed and lowest
  full temperature, then add `dT/dt = w_ocean * C_h * |V| * (T_anchor - T_1) / H`
  to the lowest-layer temperature tendency only;
- bound the equivalent e-folding time to a weak range, for example no faster
  than 5-7 days at strong wind, and cap the single-step temperature increment;
- leave vorticity, divergence, `log_surface_pressure`, tracers, diagnostics, and
  residual-correction code unchanged;
- use the incumbent tendency if the mask, anchor, wind, or flux diagnostics are
  nonfinite.

The first implementation should not add stability-dependent coefficients,
multi-layer diffusion, drag heating, or land fluxes. Those would be separate
experiments if this ocean-only lower-boundary signal promotes.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for dataclass flags, anchor
    capture, mask threading, forcing composition, and the side-by-side factory.
  - `src/dynamaxx/dycore/models/dinosaur/held_suarez.py` only if the Implementer
    chooses to express the term as a reusable forcing object beside the current
    weak-HS forcing.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` and
    `src/dynamaxx/dycore/registry.py` for export and model registration.
  - Focused tests under `tests/dycore/models/dinosaur/` plus
    `tests/dycore/test_registry.py`.
- Registry changes:
  - Add one side-by-side model named
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf`.
- API changes:
  - None. The anchor is derived from existing initial-state variables and the
    candidate returns the same forecast variables for the same lead requests.
- Tests to update:
  - Verify zero ocean weight is exactly incumbent behavior.
  - Verify the flux drives the lowest-layer temperature toward the anchor and is
    zero when the current temperature equals the anchor.
  - Verify wind-speed scaling, increment cap, and finite fallback.
  - Verify only temperature tendency changes; wind, mass, tracers, and output
    variable lists remain unchanged by the forcing object.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2-15, especially oceanic and coastal points after
    the accepted residual memory begins to decay.
  - Secondary small improvements in `geopotential_500` are possible if the
    lower-column thermal structure becomes less biased without exciting mass
    noise.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be nearly neutral because no momentum
    tendency or wind diagnostic is changed.
  - `mean_sea_level_pressure` should be close to neutral under the weak cap and
    ocean-only weighting.
- Possible regressions:
  - Ocean surface-air temperature is not true SST; using the initial screen or
    lowest-layer value as an anchor can over-nudge air masses under strong
    advection.
  - Thermal changes can indirectly affect MSLP through hydrostatic coupling if
    the cap is too loose.

## Risks

- Numerical stability:
  - Moderate. A wind-dependent heat exchange can become stiff in storms, so the
    first implementation must bound the e-folding time and single-step thermal
    increment and must finite-fallback to the incumbent.
- Compute cost:
  - Low. The forcing adds local arithmetic and one mask/anchor field; no new
    resolution, lead, worker, or output volume is required.
- Data leakage:
  - Low. The anchor uses only lead-zero forecast inputs and a static land-sea
    mask already used by the accepted incumbent, never future target fields.
- Physical plausibility:
  - Moderate to high. Bulk aerodynamic sensible heat exchange is standard, but
    this stripped implementation lacks an explicit ocean skin temperature and
    full surface energy balance.
- Rollback complexity:
  - Low. Remove one flag, one forcing helper, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed early-lead or variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, especially with neutral
    `2m_temperature`, would show that the accepted land-sea residual already
    captures the available lower-boundary thermal signal or that an initial
    surface-air anchor is too crude.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
    hardcodes `orography = 0`, composes weak-HS forcing, and applies land-sea
    structure only in output residual correction rather than as a prognostic
    lower-boundary heat flux.
  - Dynamaxx history:
    `.logbook/history/2026-06-21_23-32-41_land-sea-contrast-surface-temperature/decision.md`
    accepted a large `2m_temperature` gain from land-sea-aware residual memory;
    this proposal tests a prognostic, ocean-only physical route to the same
    remaining error family.
  - Dynamaxx history:
    `.logbook/history/2026-06-22_03-19-03_exponential-integrator-newtonian-relaxation/decision.md`
    found exact integration of the existing weak-HS relaxation neutral, so this
    proposal changes the lower-boundary process rather than only its time
    integration.
  - Louis, J. F. 1979. "A parametric model of vertical eddy fluxes in the
    atmosphere." Boundary-Layer Meteorology, 17, 187-202.
    https://doi.org/10.1007/BF00117978
  - Monin, A. S. and Obukhov, A. M. 1954. "Basic laws of turbulent mixing in the
    surface layer of the atmosphere." Tr. Akad. Nauk SSSR Geophiz. Inst.,
    24(151), 163-187.
    https://www2.mmm.ucar.edu/wrf/users/physics/phys_refs/SURFACE_LAYER/eta_part1.pdf
  - Beljaars, A. C. M. and Holtslag, A. A. M. 1991. "Flux parameterization over
    land surfaces for atmospheric models." Journal of Applied Meteorology.
    https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2

## Researcher Notes

This is a refined physical subset of staged `bulk-surface-sensible-heat-flux`,
not a duplicate. The staged version allowed land fluxes, stability factors, and
one- or two-layer choices; this proposal pins the first test to an ocean-weighted
lowest-layer flux with one weak coefficient family and no diagnostic output
changes. It also differs from the accepted `land-sea-contrast-surface-temperature`
mechanism because it does not alter residual decay or blend forecast outputs.
It leaves the fixed forecast contract and evaluation protocols unchanged.

## Evaluator Notes

### 2026-06-22T05:25:51Z

Decision: move to `ready`; ranked 1 of 2 fresh proposals and recommended as
the next implementation candidate.

The physical premise is supported, but the implementation should stay as narrow
as written. Peer-reviewed air-sea flux literature describes turbulent heat fluxes
as a major lower-boundary exchange and says bulk formulas estimate those fluxes
from surface atmospheric variables, including wind and air temperature, through
bulk transfer coefficients. Louis 1979 also supports stability-dependent eddy
fluxes of heat, momentum, and water vapor in forecast models. That literature
supports the direction of the mechanism, while also underscoring the main
simplification here: the candidate uses a lead-zero screen or lowest-layer air
anchor, not a true prognostic skin or sea-surface temperature.

Promote this narrower ocean-only version because the recent loop evidence now
favors a physical lower-boundary thermal process. The incumbent's large accepted
gain came from land-sea-aware `2m_temperature` residual memory, while the later
exact-integration weak-HS experiment was clean but score-negative. The broader
staged `bulk-surface-sensible-heat-flux` note said to revisit after that
integration-only test failed; this proposal answers that by limiting the first
test to ocean weight, one weak bounded coefficient family, the lowest sigma
layer, and no land flux, momentum tendency, forecast-contract change, or
leaderboard/cache change.

Implementation concerns for the Orchestrator: require a conservative e-folding
floor and single-step temperature-increment cap, require exact incumbent behavior
when ocean weight is zero or diagnostics are nonfinite, and watch MSLP/Z500
guardrails because even a weak lowest-layer thermal tendency couples through
hydrostatic thickness. Do not rerun the incumbent solely because this candidate
would edit shared dycore source; the leaderboard cache remains authoritative
unless concretely invalid.
