---
schema_version: 1
slug: theta-omega-spinup
title: Add a Theta-Only Short Omega Spinup
status: staging
created_at: 2026-06-19T01:47:32Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/channels.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a Theta-Only Short Omega Spinup

## Hypothesis

The current adapter ignores analyzed pressure-coordinate vertical velocity even
when `vertical_velocity_*` channels are present in the initial WeatherBench2
state. Recent accepted changes improved horizontal wind phase, thermodynamic
variable choice, and layer-mean theta drift, so a smaller remaining source of
mass and thickness error may be early vertical-motion spinup. A short,
theta-only incremental analysis update based on same-time analyzed omega may
reduce early `geopotential_500`, MSLP, and lower-column temperature errors
without modifying vorticity, divergence, log surface pressure, output
diagnostics, or the accepted theta recentering filter.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_theta_omega_spinup`.
Preserve the incumbent initialization, DFI, weak Held-Suarez forcing, theta
tendency, theta layer-mean recentering, symmetric exact Coriolis split,
horizontal diffusion, stability-aware residual correction, Richardson 10 m wind
diagnostic, output variables, WeatherBench2 splits, lead times, metrics, and
deterministic gates.

For the candidate only, add a bounded positive-time omega spinup source:

- add `vertical_velocity` channel support for reading pressure-level analysis
  inputs only, not for output;
- during `weather_state_to_dinosaur_state`, interpolate initial
  `vertical_velocity_*` from pressure levels to sigma centers when all required
  channels are present;
- convert pressure velocity omega to a small sigma-dot anomaly proxy using the
  local initial surface pressure, with top and bottom tapering so the increment
  is column-boundary compatible;
- remove the column mass-weighted mean sigma-dot anomaly so it does not act as
  a net column mass source;
- store the fixed anomaly in a private rollout wrapper, not in emitted
  `WeatherState` variables;
- during positive-time rollout only, add a decaying theta-advection tendency
  proportional to this omega anomaly for the first 12 forecast hours, with a
  bounded amplitude and smooth taper to zero;
- apply the source to the theta/temperature tendency only, not to vorticity,
  divergence, `log_surface_pressure`, passive humidity, Coriolis rotation,
  residual correction, or output packing;
- leave DFI on the incumbent equation and incumbent filters so the update is
  not time reversed or merged into the initialization filter;
- fall back to the incumbent rollout if omega inputs are absent or if any
  pressure, sigma-dot, theta, or converted tendency is nonfinite.

This revisits the staged omega-spinup family for the current theta-recentered
incumbent, but narrows the mechanism to theta-only, column-mass-neutral,
positive-time IAU rather than broad vertical-transport or divergence
initialization changes.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/channels.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, emitted variables, target variables, lead
    times, splits, metrics, and deterministic gates remain unchanged.
- Tests to update:
  - Unit-test pressure-level omega stacking and pressure-to-sigma interpolation
    with absent-channel and nonfinite fallback.
  - Unit-test top/bottom tapering and zero column-mean sigma-dot anomaly.
  - Verify the IAU window integrates to the configured bounded increment and
    decays to exactly zero after the fixed window.
  - Verify vorticity, divergence, `log_surface_pressure`, tracers, Coriolis
    options, theta recentering, output variables, and DFI filter selection are
    unchanged.
  - Verify the candidate factory preserves every incumbent option except the
    omega-spinup selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 1 to 5 if missing
    analyzed ascent/descent contributes to early balanced mass-field spinup.
  - `2m_temperature` at days 2 to 7 if lower-column thermal evolution benefits
    from a short analyzed vertical-motion correction.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be less exposed than in wind
    initialization experiments because horizontal wind state, Coriolis split,
    and 10 m diagnostic are unchanged.
  - Long leads should approach the incumbent trajectory as the omega IAU source
    decays to zero.
- Possible regressions:
  - ERA5 pressure-level omega may be noisy or inconsistent with the model's
    sigma-coordinate continuity relation at this resolution.
  - Even theta-only vertical-motion nudging can perturb hydrostatic thickness
    and indirectly affect pressure-gradient and wind phase.

## Risks

- Numerical stability:
  - Moderate. The source is bounded, tapered, and time-limited, but it changes
    positive-time thermodynamic tendencies during the spinup window.
- Compute cost:
  - Low to moderate. It adds one input interpolation and local tendency algebra;
    no resolution, lead count, output volume, or worker count changes.
- Data leakage:
  - Low. It uses only same-time initial analysis channels already present in the
    forecast input. It must not use future target states, validation artifacts,
    or golden data.
- Physical plausibility:
  - Moderate. Omega is the hydrostatic pressure-coordinate vertical velocity,
    and IAU is a standard gradual-increment strategy. The approximation is that
    a short theta-only omega tendency can reduce spinup without full balanced
    data assimilation.
- Rollback complexity:
  - Low to moderate. Remove one input-channel constant, one interpolation path,
    one rollout wrapper or equation option, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_theta_omega_spinup`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_theta_omega_spinup --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_theta_omega_spinup --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that analyzed omega
    is not a material remaining spinup source for the current incumbent. Any
    early MSLP, Z500, or 10 m wind guardrail failure would show that the omega
    increment disrupts balance more than it helps.

## Citations

- Citation or source:
  - Dynamaxx source:
    `src/dynamaxx/dycore/models/dinosaur/adapter.py` initializes temperature,
    winds, pressure, and humidity but does not read pressure-level
    `vertical_velocity_*` channels.
  - Dynamaxx source:
    `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` diagnoses
    sigma vertical motion internally and uses it in thermodynamic tendencies.
  - Dynamaxx research:
    `.logbook/research/staging/analysis-omega-vertical-motion-spinup.md`
    records the earlier omega-spinup idea for a pre-theta-recentering
    incumbent; this proposal narrows it to theta-only and column-neutral under
    the current incumbent.
  - Dynamaxx history:
    `.logbook/history/2026-06-17_22-19-32_continuity-balanced-divergence-init/decision.md`
    rejected direct divergence correction, so this proposal avoids editing
    horizontal wind control variables.
  - Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
    Assimilation Using Incremental Analysis Updates. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
  - Polavarapu, S., Ren, S., Clayton, A. M., Sankey, D., and Rochon, Y. 2004.
    On the Relationship between Incremental Analysis Updating and Incremental
    Digital Filtering. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(2004)132%3C2495:OTRBIA%3E2.0.CO;2
  - ECMWF IFS Documentation CY41R2, Part III: Dynamics and Numerical
    Procedures, describes pressure-coordinate vertical motion and hydrostatic
    primitive-equation dynamics.
    https://www.ecmwf.int/sites/default/files/elibrary/2016/79696-ifs-documentation-cy41r2-part-iii-dynamics-and-numerical-procedures_1.pdf
  - Copernicus Climate Data Store ERA5 pressure-level reanalysis documentation.
    https://cds.climate.copernicus.eu/datasets/reanalysis-era5-pressure-levels

## Researcher Notes

This proposal deliberately revisits a staged mechanism because the evidence has
changed. The accepted theta tendency and theta recentering make a theta-only
vertical-motion spinup more coherent than the older temperature/tracer omega
idea, while the accepted Richardson wind diagnostic reduces the risk that a
small thermodynamic spinup immediately fails the wind channel. It remains
distinct from staged `upwind-vertical-advection-rollout`, which changes the
vertical-advection discretization for the whole forecast, and from rejected
`continuity-balanced-divergence-init`, which edited horizontal divergence. This
candidate is time-limited, same-time-input-only, and should be rejected if mass
or wind guardrails show that analyzed omega is inconsistent with the model's
free sigma-coordinate balance.

## Evaluator Notes

### 2026-06-19T01:51:18Z

Decision: move to `staging`; ranked 3 of 3 new proposals.

This is a useful current-incumbent refinement of the existing staged
`analysis-omega-vertical-motion-spinup` idea: it narrows the mechanism to a
theta-only, column-neutral, positive-time IAU source and avoids direct wind,
divergence, pressure, or output edits. The physical basis is reasonable in the
limited sense that same-time analysis omega can describe vertical-motion
spinup, and IAU is a standard gradual-increment strategy.

It is not ready for the next implementation. The proposal has the broadest
surface of the three new ideas, touching channel support, pressure-to-sigma
input interpolation, primitive-equation or rollout wrapping, and candidate
state handling. It also depends on optional `vertical_velocity_*` input
availability and consistency with the free sigma-coordinate continuity balance.
Prior direct balance/init changes are cautionary, and the current incumbent's
best immediate diagnostic is a late 10 m wind regression rather than an early
omega-specific mass-field failure.

Orchestrator enforcement if selected later: verify the fixed local
WeatherBench2 source actually provides the required `vertical_velocity_*`
channels for all evaluated splits before implementation; use only same-time
initial analysis fields; require absent-channel and nonfinite fallback to the
incumbent; keep DFI on the incumbent path; and do not change output variables,
forecast contract, metrics, splits, or deterministic gates.
