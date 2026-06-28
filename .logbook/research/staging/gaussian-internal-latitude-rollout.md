---
schema_version: 1
slug: gaussian-internal-latitude-rollout
title: Roll Out on an Internal Gaussian Latitude Grid
status: staging
created_at: 2026-06-21T10:18:55Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Roll Out on an Internal Gaussian Latitude Grid

## Hypothesis

The current incumbent runs directly on the WeatherBench2
`equiangular_with_poles` grid and then guards polar metric singularities by
replacing zero polar cosines with the smallest interior cosine. That finite
guard prevents NaNs, but the primitive-equation spectral transforms and
nonlinear metric products still operate on endpoint polar nodes that are not
ideal quadrature nodes for spherical harmonics.

An internal Gaussian latitude grid should reduce polar metric and transform
quadrature noise without adding another damping, timestep, pressure-gradient,
or residual-memory variant. This may improve late `mean_sea_level_pressure`,
`geopotential_500`, and `10m_u_component_of_wind` if part of the remaining
error is horizontal discretization noise rather than physical forcing.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gaussian_grid`.
Preserve the incumbent DFI, 900 s inner step, weak-HS analysis-offset
equilibrium, hydrostatic/log-pressure initialization, exact Coriolis Strang
split, theta tendency, theta mean recentering, off-centered SIL3, scale-separated
near-surface residual correction, Richardson 10 m wind diagnostic, output
variables, and evaluation protocols.

For the candidate only:

- build two horizontal grids with the same longitude count and comparable T80
  modal truncation: the input/output equiangular-with-poles grid and an internal
  Gaussian latitude grid with no endpoint poles;
- regrid each initialized pressure-level field from the input grid to the
  Gaussian grid using existing conservative or bilinear horizontal regridders
  before `weather_state_to_dinosaur_state`;
- run the full Dinosaur trajectory on the Gaussian grid with the incumbent
  vertical sigma grid and all incumbent physics flags;
- convert trajectory outputs back to the original WeatherBench2 grid before
  applying the existing surface residual correction and before returning
  `WeatherState`;
- use finite fallbacks that return the incumbent direct-grid path if a regridder
  is shape-incompatible or emits nonfinite values;
- keep lead schedule, target variables, data source, and metric computation
  unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/coordinates.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. `DycoreModel.forecast` receives and returns the same `ForecastInput`
    and `WeatherState` contract.
- Tests to update:
  - Verify Gaussian-grid construction preserves longitude count and uses
    `latitude_spacing="gauss"`.
  - Verify horizontal regridding round-trips a constant field exactly and a
    smooth field within tolerance.
  - Verify a zero-motion non-JIT smoke forecast is finite and returns values on
    the original input latitude axis.
  - Verify the candidate factory preserves every incumbent option except the
    internal-grid selector.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium to late leads if
    polar endpoint noise feeds spurious mass adjustment.
  - `10m_u_component_of_wind` at late leads if spherical-harmonic wind transforms
    are cleaner on Gaussian quadrature nodes.
- Expected neutral metrics:
  - `2m_temperature` should remain near incumbent because weak-HS forcing,
    residual correction, and thermal variables are unchanged.
- Possible regressions:
  - Horizontal remapping can smooth useful small-scale initial structure.
  - The input and output grid are still equiangular with poles, so interpolation
    error may offset any internal quadrature gain.

## Risks

- Numerical stability:
  - Moderate. The rollout equations are unchanged, but every initial and output
    field passes through horizontal regridding.
- Compute cost:
  - Moderate. Extra regridding work occurs per forecast initialization and output
    time, but no extra inner steps or model-selection evaluations are added.
- Data leakage:
  - None. The regridding uses only same-time forecast inputs and fixed grid
    geometry.
- Physical plausibility:
  - High for spectral transform models; Gaussian latitudes are standard
    spherical-harmonic quadrature nodes.
- Rollback complexity:
  - Moderate. Remove the internal-grid branch, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gaussian_grid`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gaussian_grid --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gaussian_grid --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that direct
    equiangular-with-poles rollout is not a material remaining error source. An
    early MSLP or Z500 guardrail failure would show that horizontal regridding
    perturbs balanced mass fields too much.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/coordinates.py` currently
  chooses the input latitude spacing and uses `_with_safe_polar_cosine` for
  endpoint pole safety.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/horizontal_interpolation.py`
  already contains bilinear, nearest-neighbor, and conservative horizontal
  regridders that can support an internal-grid branch.
- History: `.logbook/history/2026-06-21_08-11-13_startup-subcycled-first-day-rollout/decision.md`
  rejected smaller startup steps, so this proposal does not change timestep or
  subcycling.
- Active staging comparison:
  `.logbook/research/staging/polar-metric-nonlinear-regularization.md` targets
  polar nonlinear metric products in-place; this proposal changes the internal
  quadrature grid instead of adding a tendency regularizer.
- Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
  Atmospheric Models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not another startup-step or subcycling proposal; the 900 s inner step
and accepted off-centering remain unchanged in light of the rejected
`startup-subcycled-first-day-rollout` result. It is also not a pressure-gradient
product, diffusion, vertical-advection, residual-memory, drag, or diagnostic
variant already present in active staging. The distinct mechanism is horizontal
quadrature and pole treatment through an internal Gaussian grid while preserving
the external WeatherBench2 forecast contract.

## Evaluator Notes

### 2026-06-21T10:25:51Z

Decision: move to `staging`; do not make it the next ready model-selection
candidate.

The scientific premise is credible. Williamson's dycore review explicitly
frames polar grid geometry as a hard problem for global atmospheric models, and
Gaussian latitudes are standard quadrature points for spectral-transform
methods. Source inspection also confirms that the repository already recognizes
`latitude_spacing="gauss"` and has reusable horizontal interpolation utilities,
so the proposal is technically feasible without changing the external forecast
contract.

The risk/cost tradeoff is still too broad for the next experiment. This would
change the initialized grid, the rollout grid, and every pressure-level output
through bidirectional horizontal remapping. That makes it a higher-blast-radius
test than `polar-metric-nonlinear-regularization` or
`pressure-gradient-product-dealiasing`, and it can smooth balanced initial mass
and wind structures before any possible quadrature benefit appears. Local
evidence for polar endpoint noise as the remaining score limiter is weak: the
exact-pole wind taper was numerical-noise scale, and the active polar-metric
proposal is still staged for lack of direct diagnostics.

Keep this as a later candidate or as infrastructure-enabling work if the loop
first adds read-only polar/noise diagnostics. It is not a duplicate of the
polar metric cap because it changes quadrature/remapping rather than nonlinear
metric factors, but it should be treated as a broad grid-architecture
experiment, not a cheap next model-selection run.
