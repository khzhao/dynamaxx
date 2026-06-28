---
schema_version: 1
slug: polar-metric-nonlinear-regularization
title: Regularize Polar Metric Amplification in Nonlinear Tendencies
status: staging
created_at: 2026-06-20T04:32:18Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
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

# Regularize Polar Metric Amplification in Nonlinear Tendencies

## Hypothesis

The incumbent uses spherical-harmonic transforms, but several explicit
primitive-equation products are evaluated in nodal space with metric factors
such as `sec2_lat`. Near the poles, those metric factors can strongly amplify
small transform or nonlinear-product noise. Prior polar wind initialization
tapering was too weak to matter, and a broad polar vorticity guard is already
scrapped, but neither tested the actual runtime source of polar amplification:
the nonlinear metric products inside vorticity/divergence and scalar advection
tendencies.

A fixed, smooth cap on only the metric factors used inside explicit nonlinear
tendency products should reduce polar noise without changing the spherical
harmonic basis, the exact Coriolis split, initialization, residual memory, or
the fixed forecast contract.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_polar_metric`.
Preserve the full incumbent except for an opt-in nonlinear metric regularizer
inside `PrimitiveEquationsSigma`.

For this candidate only:

- add a fixed helper that returns a regularized `sec2_lat` for nonlinear
  products, equal to the incumbent `sec2_lat` through most latitudes and smoothly
  capped poleward of a fixed threshold such as `|lat| >= 85 deg`;
- use the regularized metric only in explicit nodal nonlinear products where
  `sec2_lat` multiplies velocity, vorticity, pressure-gradient, or scalar
  advection terms;
- leave spectral derivative operators, spherical-harmonic transforms,
  quadrature weights, exact Coriolis rotation, implicit gravity-wave operator,
  horizontal diffusion, pressure initialization, and output interpolation
  unchanged;
- keep the same regularizer in DFI and positive-time rollout because it is an
  equation-discretization selector, not an output filter;
- verify with tests that the regularizer is smooth, finite, monotone toward the
  cap, and identity outside the polar band.

This proposal is not a polar wind taper and not a vorticity guard. It changes
the nonlinear metric amplification that can create polar tendencies before they
project back to global spectral modes.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. Forecast input/output variables, lead schedule, metrics, and fixed
    protocols remain unchanged.
- Tests to update:
  - Unit-test regularized metric shape, finiteness, identity outside the polar
    band, and bounded polar maximum.
  - Verify the default equation path is bitwise unchanged.
  - Verify the candidate uses the regularized metric in nonlinear terms while
    leaving implicit terms and derivative operators unchanged.
  - Verify a resting state remains a resting state within transform tolerance.
  - Verify the candidate factory preserves every incumbent option except the
    polar metric selector and model name.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium-to-long leads if
    polar nonlinear noise aliases into global balanced mass fields.
  - `10m_u_component_of_wind` may improve at later leads if polar noise affects
    large-scale wave phase.
- Expected neutral metrics:
  - `2m_temperature` should remain close to incumbent because surface residual
    memory and lower-column diagnostics are unchanged.
  - Lead-zero output should be unchanged except through DFI if the same equation
    selector is used there.
- Possible regressions:
  - Capping metric factors can understate real polar dynamics and slightly
    degrade high-latitude pressure or wind evolution.
  - The effect may be clean but subthreshold if the accepted off-centering and
    diffusion already control the relevant polar noise.

## Risks

- Numerical stability:
  - Moderate. The cap is stabilizing and finite, but it changes core nonlinear
    tendencies in polar regions.
- Compute cost:
  - Low. It adds one precomputed metric array and no extra transforms or
    rollout steps.
- Data leakage:
  - None. It uses only fixed grid geometry.
- Physical plausibility:
  - Moderate. Polar filtering and grid-metric regularization are established
    numerical controls, but applying a cap in a spherical-harmonic dycore must
    remain narrow to avoid distorting legitimate polar flow.
- Rollback complexity:
  - Moderate. Remove one equation option, one helper, one factory/export, one
    registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_polar_metric`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_polar_metric --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_polar_metric --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show polar metric
    amplification is not a material remaining error source. Any early MSLP,
    Z500, or 10 m wind guardrail failure would show the cap distorts balanced
    flow more than it suppresses noise.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  uses `coords.horizontal.sec2_lat` in explicit nonlinear vorticity,
  divergence, pressure-gradient, and scalar-advection products.
- Dynamaxx history:
  `.logbook/history/2026-06-17_14-44-29_polar-vector-wind-initialization-taper/decision.md`
  found a one-time polar wind taper clean but numerical-noise scale, motivating
  a runtime nonlinear-source mechanism rather than another initialization taper.
- Dynamaxx research:
  `.logbook/research/scrap/polar-absolute-vorticity-guard.md` targets local
  polar vorticity outliers. This proposal instead regularizes the metric
  multiplier that can create polar nonlinear tendencies.
- Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
  Atmospheric Models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241
- Lauritzen, P. H., Nair, R. D., and Ullrich, P. A. 2012. A standard test case
  suite for two-dimensional linear transport on the sphere. Geoscientific Model
  Development. https://doi.org/10.5194/gmd-5-887-2012
- Takacs, L. L., Suarez, M. J., and Todling, R. 2001. Maintaining Atmospheric
  Mass and Water Vapor in Reanalyses. NASA/GMAO technical report context
  discusses high-latitude filtering controls for global models.
  https://gmao.gsfc.nasa.gov/pubs/docs/Takacs112.pdf
- Jablonowski, C. 2004. Adaptive Grids in Weather and Climate Modeling. Ph.D.
  dissertation, University of Michigan. The associated diffusion/filtering
  lecture notes summarize polar filtering practice in atmospheric models.
  https://public.websites.umich.edu/~cjablono/Jablonowski-Diffusion-Filters-Damping.pdf

## Researcher Notes

This is not a duplicate of rejected `polar-vector-wind-initialization-taper`:
that candidate changed only the initialized wind near the poles and moved the
score by numerical noise. This proposal changes the runtime explicit nonlinear
metric factor that can regenerate polar noise every step.

It is not a duplicate of scrapped `polar-absolute-vorticity-guard` or
`pv-gradient-aware-vorticity-filter`; it does not inspect vorticity outliers or
add a flow-dependent vorticity filter. It is also distinct from staged broad
diffusion and tendency-dealiasing ideas because it is geographically confined,
fixed by grid geometry, and leaves modal truncation unchanged.

## Evaluator Notes

### 2026-06-20T04:40:42Z

Decision: move to `staging`; not ready.

The mechanism is real and source-local enough to preserve. In
`PrimitiveEquationsSigma.curl_and_div_tendencies`, `sec2_lat` multiplies the
absolute-vorticity flux and the vertical/pressure-gradient vector terms before
they are transformed back to modal curl/divergence tendencies. A fixed
geometry-only regularizer is therefore materially different from the rejected
exact-pole wind initialization taper and from the scrapped polar
absolute-vorticity guard.

Do not promote it to `ready` yet. Capping a coordinate metric inside the core
primitive-equation products is a broader equation-discretization change than
the proposal's narrow wording suggests: it affects DFI and positive-time
rollout, vorticity and divergence tendencies, and legitimate polar pressure-
gradient or vortex dynamics. The threshold/cap choice is also a fixed modeling
constant with no loop-local diagnostic evidence that polar metric amplification
is currently driving the global WeatherBench2 score.

Keep it staged as a later polar/nonlinear-noise candidate only after cheaper or
more targeted anti-aliasing options are exhausted. Active staged ideas such as
`pressure-gradient-product-dealiasing` and `two-thirds-explicit-tendency-
dealiasing` test nonlinear-product noise with less geographic metric
distortion, while prior polar evidence has been weak: exact-pole wind tapering
was numerical-noise scale, and the broader polar vorticity guard was scrapped
for balance and evidence risks. If selected later, the Orchestrator should
require tests proving identity outside the polar band, smooth finite caps, and
unchanged derivative/implicit operators.
