---
schema_version: 1
slug: orographic-wave-drag-split
title: Add a Bounded Orographic Gravity-Wave Drag Split
status: staging
created_at: 2026-06-20T12:51:32Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a Bounded Orographic Gravity-Wave Drag Split

## Hypothesis

The incumbent still rolls out on a flat lower boundary (`orography = 0`) even
though real WeatherBench2 flow contains terrain-forced stationary waves and
mountain drag. Prior terrain proposals that changed surface pressure or the
prognostic lower-boundary geopotential were risky because they perturbed mass
and pressure-gradient balance directly. A narrower, momentum-only orographic
gravity-wave drag split can represent terrain-induced momentum deposition while
leaving surface pressure, hydrostatic initialization, weak-HS equilibrium,
residual memory, and output remapping unchanged.

This should mainly help `10m_u_component_of_wind`, late `mean_sea_level_pressure`,
and `geopotential_500` if part of the remaining error is excessive free-slip
flow over effective terrain.

## Mechanism

Add an opt-in positive-time step filter after the accepted non-Coriolis dynamics
and before the symmetric Coriolis half-step. The filter:

- estimates a smooth effective orographic height from the initial analysis using
  the existing pressure-level geopotential, temperature, and surface pressure
  channels, with a finite zero fallback when the required channels are absent;
- keeps only large-scale terrain slopes through a low-order spectral taper, so it
  does not reintroduce the failed prognostic-orography pressure-gradient path;
- diagnoses low-level wind and lower-column static stability from the current
  Dinosaur state;
- applies a bounded deceleration parallel to the local low-level wind where flow
  crosses strong terrain gradients and stability supports vertically propagating
  waves;
- writes the momentum increment back through `uv_nodal_to_vor_div_modal`, leaving
  temperature, log surface pressure, tracers, DFI, weak-HS forcing, theta
  recentering, scale-separated surface residuals, and diagnostics unchanged.

The first implementation should use conservative caps: no more than a few
percent of local low-level wind speed per 900 s inner step and no direct thermal
or pressure tendency.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for dataclass flags, an
    effective-orography helper, and the bounded momentum filter.
  - `src/dynamaxx/dycore/registry.py` for a side-by-side candidate factory.
  - `tests/dycore/test_registry.py` and focused adapter tests for registration,
    finite fallback, zero-terrain no-op behavior, and cap enforcement.
- Registry changes:
  - Add a model named
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_orog_wave_drag`.
- API changes:
  - None. The model continues to return one `WeatherState` trajectory for the
    requested leads. The terrain proxy must come from existing initial-state
    channels, not from new eval inputs.
- Tests to update:
  - Registry/dependency tests for the new factory.
  - Unit tests that the filter is exactly no-op for flat effective terrain and
    finite for missing or nonfinite terrain-proxy channels.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at days 2-15 if free-slip low-level flow remains
    too strong over mountainous wave-source regions.
  - `mean_sea_level_pressure` and `geopotential_500` at medium and late leads if
    the missing mountain torque currently feeds synoptic phase and amplitude
    errors.
- Expected neutral metrics:
  - `2m_temperature` should be close to neutral because no screen-temperature
    residual or thermal forcing is changed.
  - Lead-zero and day-1 fields should move little under the per-step cap.
- Possible regressions:
  - Excess drag can under-speed jets and worsen `10m_u_component_of_wind`.
  - Momentum damping can shift storm tracks and indirectly worsen MSLP/Z500.
  - Effective terrain inferred from coarse pressure levels may be noisy over
    high mountains or polar columns.

## Risks

- Numerical stability:
  - Low to moderate if the momentum tendency is capped and finite-guarded. The
    filter must not operate on nonfinite terrain or wind diagnostics.
- Compute cost:
  - Low. One or two spectral transforms plus wind conversion per inner step are
    small relative to the existing primitive-equation rollout on 4 workers.
- Data leakage:
  - Low if the terrain proxy uses only forecast initialization channels and fixed
    constants, never truth at valid leads or validation statistics.
- Physical plausibility:
  - Moderate. It is a simplified resolved-grid surrogate for subgrid orographic
    wave drag and blocked-flow drag, not a full parameterization.
- Rollback complexity:
  - Low. Keep the feature behind a default-false flag and a side-by-side registry
    entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_orog_wave_drag`.
  - Require finite diagnostics and no issue count increase.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_orog_wave_drag --workers 4`.
  - Support requires primary-score delta at least `+0.002` with clean guardrails,
    with special inspection of `10m_u_component_of_wind` and MSLP over days 5-15.
- Validation gate:
  - Run validation with `--workers 4` only after iteration promotion; require
    primary-score delta at least `+0.001` and no fixed guardrail failures.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, or an early wind/MSLP
    regression, would show that the flat-boundary incumbent is not materially
    limited by missing terrain drag under this simplified formulation.

## Citations

- McFarlane, N. A. 1987. "The effect of orographically excited gravity wave drag
  on the general circulation of the lower stratosphere and troposphere." Journal
  of the Atmospheric Sciences. https://doi.org/10.1175/1520-0469(1987)044%3C1775:TEOOEG%3E2.0.CO;2
- Lott, F. and Miller, M. J. 1997. "A new subgrid-scale orographic drag
  parametrization: Its formulation and testing." Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1002/qj.49712353704
- ECMWF IFS Documentation CY49R1, Part IV: Physical Processes, chapters on
  subgrid-scale orographic drag and non-orographic gravity-wave drag.
  https://www.ecmwf.int/en/elibrary/81626-ifs-documentation-cy49r1-part-iv-physical-processes

## Researcher Notes

This is not a repeat of `terrain-aware-surface-pressure-orography` or
`terrain-reduced-pressure-cycle`: it does not alter surface pressure, sea-level
pressure reduction, or the primitive-equation pressure-gradient lower boundary.
It is also distinct from staged Rayleigh or boundary-layer drag proposals because
the drag is terrain-slope and stability gated rather than a generic low-level
friction timescale. The recent accepted analysis-offset HS equilibrium remains
unchanged.

## Evaluator Notes

### 2026-06-20T12:56:24Z

Decision: move to `staging`.

This is scientifically plausible and decorrelated from the accepted thermal and
near-surface residual changes. Orographic gravity-wave drag is a real missing
momentum process, and the proposed momentum-only split is much narrower than
the rejected full terrain/orography candidate because it avoids feeding terrain
height into pressure-gradient, surface-pressure, MSLP, or geopotential
diagnostic paths.

Do not promote it over the theta-variance guard in this pass. Source inspection
shows the current trajectory still hardcodes modal `orography = 0`, while
surface pressure is optional and MSLP is used as a fallback when surface
pressure is absent. That makes the proposed effective-terrain proxy dependent
on dynamic pressure-level analysis channels and dataset-specific availability,
not on a clean static surface geopotential input. The recent terrain history is
also cautionary: the full terrain/orography experiment had a large aggregate
primary gain but catastrophic early Z500 and MSLP guardrail failures, and the
narrower terrain pressure-cycle idea was scrapped because static constants are
not exposed cleanly through the model API.

Keep staged as a later, bounded wind/mass experiment if diagnostics point to
excess free-slip flow over mountain-wave source regions. If selected later, the
Implementer should first prove zero-terrain and missing-channel no-op behavior,
predeclare a very smooth terrain proxy and wind-speed cap, keep the split out
of pressure/geopotential diagnostics, and avoid any evaluation-plumbing or
static-data API change.
