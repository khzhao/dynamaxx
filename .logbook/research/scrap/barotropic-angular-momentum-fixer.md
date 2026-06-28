---
schema_version: 1
slug: barotropic-angular-momentum-fixer
title: Preserve Barotropic Axial Angular Momentum During Rollout
status: scrap
created_at: 2026-06-17T13:30:43Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Preserve Barotropic Axial Angular Momentum During Rollout

## Hypothesis

The incumbent keeps the accepted DFI, near-surface residual, weak thermal
Held-Suarez relaxation, log-pressure sigma initialization, hydrostatic
thickness initialization, and layer-mean hydrostatic temperature
initialization. It still develops a persistent negative `10m_u_component_of_wind`
bias and strongly negative wind skill versus persistence, especially at medium
and long leads.

In the current flat, wind-sparing dry rollout there is no orographic torque and
the accepted weak Held-Suarez forcing has no Rayleigh drag. The total axial
angular momentum of the resolved flow should therefore be much more nearly
conserved than an unconstrained spectral rollout may achieve after repeated
transforms, filters, and pressure-coordinate projection. A narrow barotropic
angular-momentum fixer should reduce domain-wide zonal-wind drift without
adding damping, changing thermal fields, or modifying the fixed forecast
contract.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_aam_fixer`.
Preserve every incumbent initialization, forcing, output, residual, grid,
truncation, diffusion, DFI span, timestep, metric, split, and target variable.

Add one positive-time step filter after the existing IMEX step and horizontal
diffusion filter, but do not pass this new filter into the time-reversed DFI
initializer. The filter should:

- convert previous and candidate next states from modal vorticity/divergence to
  nodal winds with the existing spherical-harmonic helpers;
- compute a single sigma-thickness-weighted, area-weighted barotropic axial
  angular-momentum proxy from zonal wind, for example an integral proportional
  to `u * cos(latitude)` using the local quadrature weights;
- add the smallest global solid-body zonal-wind increment to the next state
  needed to match the previous state's barotropic proxy;
- transform only the corrected wind pair back to modal vorticity/divergence;
- leave temperature variation, log surface pressure, passive tracers, `sim_time`,
  output interpolation, and near-surface residual correction unchanged.

The first implementation should use one deterministic global correction, not a
latitude-width sweep, not lead-dependent tuning, and not target-variable
feedback. It should preserve total barotropic axial angular momentum
step-to-step rather than forcing the flow toward an analyzed or validation-set
wind climatology.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_aam_fixer`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState`, emitted variables, lead
    times, target variables, metrics, and deterministic gates remain unchanged.
- Tests to update:
  - Unit-test the angular-momentum proxy on simple zonal-wind fields and both
    latitude orderings if helper inputs expose latitude orientation.
  - Unit-test the step filter: it corrects the barotropic proxy of the next
    state to the previous-state value, changes vorticity consistently, and
    leaves divergence changes limited to transform roundoff.
  - Verify temperature variation, log surface pressure, tracers, and `sim_time`
    are unchanged by the filter.
  - Verify the candidate factory preserves all incumbent flags and keeps the AAM
    filter out of the DFI initializer.
  - Add registry coverage and a non-JIT finite smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and long leads if part of the current
    negative zonal-wind bias comes from slow global angular-momentum drift.
  - `mean_sea_level_pressure` and `geopotential_500` may improve slightly if a
    less biased barotropic wind reduces downstream balanced mass-field errors.
- Expected neutral metrics:
  - `2m_temperature` should be close to neutral because temperature,
    hydrostatic initialization, weak thermal relaxation, and surface residuals
    are unchanged.
  - Day-1 fields should be close to the incumbent if angular-momentum drift is a
    cumulative numerical error rather than an initialization offset.
- Possible regressions:
  - If the wind error is regional or baroclinic rather than barotropic, a global
    solid-body increment may improve mean bias while worsening RMSE.
  - The correction may perturb geostrophic balance through Coriolis coupling,
    producing `geopotential_500` or `mean_sea_level_pressure` regressions even
    though temperature and pressure are not directly edited.
  - If existing horizontal diffusion or DFI already preserves the relevant
    angular-momentum mode, score movement may be near zero.

## Risks

- Numerical stability:
  - Low to moderate. The filter is a bounded global wind correction, but it
    changes prognostic vorticity every forward inner step and must pass the
    fixed fast diagnostics before iteration.
- Compute cost:
  - Low. It adds a small number of existing wind transforms and reductions per
    inner step; it does not change resolution, lead count, output volume, or the
    configured `--workers 4` evaluation budget.
- Data leakage:
  - Low. The correction uses only the previous and next forecast states plus
    fixed grid geometry. It uses no truth fields, future targets, validation
    scores, learned climatology, or golden data.
- Physical plausibility:
  - Moderate to high. Angular-momentum conservation is a standard dynamical-core
    concern, and this dycore configuration lacks the main external torques that
    would justify large total axial angular-momentum drift.
- Rollback complexity:
  - Low. The mechanism can be isolated behind one adapter flag, one step filter,
    one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_aam_fixer`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_aam_fixer --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, no early day 1-5 RMSE guardrail failure, and no
    variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_aam_fixer --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that barotropic
    angular-momentum drift is not a material remaining error source. Any early
    `10m_u_component_of_wind`, `geopotential_500`, or `mean_sea_level_pressure`
    guardrail failure would show the global wind correction is too disruptive
    for this benchmark.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` constructs
  the incumbent with zero orography, wind-sparing weak Held-Suarez forcing, and
  step filters through `time_integration.step_with_filters`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py`
  provides `vor_div_to_uv_nodal`, `uv_nodal_to_vor_div_modal`, and quadrature
  weights needed for a local angular-momentum proxy.
- History: `.logbook/history/2026-06-17_03-22-44_helmholtz-wind-initialization/decision.md`
  rejected a broad wind-control-variable initialization change, motivating a
  rollout-only global conservation fixer instead of another wind remap.
- History: `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected broad damping after wind guardrail degradation; this proposal is not
  a damping or diffusion change.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is not a duplicate of `helmholtz-wind-initialization`: that candidate
changed the initial full wind projection and strongly damaged mass-field
balance, while this proposal preserves the accepted initialization and applies
only a global barotropic conservation correction during the forward rollout.

It is also distinct from hyperdiffusion, divergence damping, timestep changes,
T120 truncation, vertical-transport changes, polar-row wind regularization,
thermal recentering, humidity proposals, pressure remaps, terrain/orography,
surface diagnostics, and residual extensions. The mechanism targets a single
conservation property of the wind field under the already accepted flat,
wind-sparing dycore configuration.

## Evaluator Notes

2026-06-17T13:33:51Z - Move to `scrap`; do not promote under current evidence.

Angular-momentum conservation is a credible dycore design concern, and the
cited conservation literature supports the general principle. The proposed
implementation is nevertheless a broad forward-rollout wind correction: it
adds modal-nodal wind transforms and a global solid-body zonal increment after
every positive inner step, then rewrites prognostic vorticity/divergence. That
blast radius is much closer to rejected broad wind and numerics changes than to
the low-risk diagnostic and initialization candidates still available.

Recent evidence argues against spending an iteration here. Broad wind control
or damping changes have repeatedly failed fixed gates: Helmholtz wind
initialization regressed primary score by `-0.34423230670441374` with large
mass-field guardrail failures, scale-selective hyperdiffusion failed the early
`10m_u_component_of_wind` guardrail, and timestep, divergence-damping, T120,
and vertical-transport variants were rejected or unstable. A global
barotropic-wind correction could reduce mean zonal bias while worsening RMSE or
geostrophic balance, especially in `geopotential_500` and
`mean_sea_level_pressure`.

If revisited later, require a separate diagnostic proposal first showing that
resolved axial angular-momentum drift is large, monotonic, and causally linked
to the scored `10m_u_component_of_wind` error. Without that evidence this is an
unfavorable cost-risk tradeoff for the current incumbent.
