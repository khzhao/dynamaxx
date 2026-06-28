---
schema_version: 1
slug: low-mode-thermal-wind-relaxation
title: Relax Low-Mode Extratropical Wind Shear Toward Thermal-Wind Balance
status: scrap
created_at: 2026-06-20T19:03:48Z
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

# Relax Low-Mode Extratropical Wind Shear Toward Thermal-Wind Balance

## Hypothesis

The incumbent now has strong output handling for 10 m wind and several accepted
thermal-balance improvements, but it still evolves a dry primitive-equation
state with coarse vertical resolution and a simple weak-HS thermal closure. A
remaining error source may be slow drift between extratropical baroclinic
temperature gradients and large-scale vertical shear. Instead of changing 10 m
wind diagnostics after the harmful gradient-wind output failure, a safer test
is a low-wavenumber, extratropical, above-boundary-layer tendency that nudges
only broad vertical shear toward thermal-wind balance while leaving the
accepted Richardson 10 m diagnostic and near-surface residuals untouched.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_thermal_wind_relax`.
Preserve all accepted incumbent initialization, DFI, weak-HS analysis-offset
equilibrium, Coriolis Strang split, theta tendency, theta mean recentering,
off-centering, scale-separated surface residuals, and output diagnostics.

Add a positive-time-only step filter after the dynamical step and before output
packing:

- diagnose nodal temperature and pressure on sigma layers from the forecast
  state;
- compute an extratropical thermal-wind shear target from meridional
  temperature gradients with a bounded Coriolis denominator and a zero tendency
  in the deep tropics;
- project the shear residual onto low horizontal modes only, for example total
  wavenumber `<= 8`, and exclude the lowest sigma layer so the accepted 10 m
  wind diagnostic is not directly overwritten;
- apply a weak relaxation tendency to the vertical shear of zonal wind, with a
  long fixed timescale such as 10 days and a small per-step wind-increment cap;
- preserve each column's barotropic zonal wind and leave meridional wind,
  temperature, log surface pressure, tracers, and near-surface residual
  helpers unchanged except through the balanced low-mode wind update;
- transform the updated wind pair back to modal vorticity/divergence with
  finite fallback to the incumbent state if any diagnostic is invalid;
- do not apply this filter inside the time-reversed DFI initializer.

This is not a broad 10 m wind diagnostic and not a gradient-wind surface
correction. It acts on resolved large-scale extratropical vertical shear, avoids
day-1 output-only activation, and intentionally leaves the lowest layer and
accepted Richardson diagnostic alone.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py` only if a small
    reusable low-mode mask helper is needed
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate with suffix `_thermal_wind_relax`.
- API changes:
  - None. Forecast contract, variables, target metrics, splits, and lead times
    remain fixed.
- Tests to update:
  - Unit-test the tropical mask, low-mode mask, lowest-layer exclusion, and
    per-step wind-increment cap.
  - Verify a barotropic wind profile receives no vertical-shear correction when
    the thermal-wind residual is zero.
  - Verify non-wind state leaves are unchanged by the filter.
  - Verify finite fallback for invalid temperature, pressure, latitude, or wind
    diagnostics.
  - Verify the candidate factory preserves every incumbent option except the new
    thermal-wind relaxation selector.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and MSLP at medium and long leads if low-mode
    wind-temperature imbalance is feeding large-scale phase error.
  - `10m_u_component_of_wind` may improve indirectly at longer leads through a
    better-balanced column, not through output post-processing.
- Expected neutral metrics:
  - Early day-1 `10m_u_component_of_wind` should be protected by the lowest-layer
    exclusion and long relaxation timescale.
  - `2m_temperature` should remain near incumbent because the thermal state,
    weak-HS forcing, and surface residual correction are unchanged.
- Possible regressions:
  - Thermal-wind balance is not valid in the tropics, boundary layer, or strong
    ageostrophic flow; an overly broad mask could damage mass fields or wind
    skill.
  - Updating vorticity/divergence from an adjusted wind field can perturb the
    accepted off-centered balance.

## Risks

- Numerical stability:
  - Moderate. The update is bounded and low-mode, but it changes prognostic
    wind variables during rollout.
- Compute cost:
  - Low to moderate. It adds wind reconstruction, gradients, low-mode filtering,
    and wind-to-vorticity/divergence conversion once per inner step.
- Data leakage:
  - None. The filter uses only the current forecast state and fixed physical
    constants.
- Physical plausibility:
  - Moderate. Thermal-wind balance is a large-scale extratropical constraint,
    but the proposal must mask regions and layers where the approximation is
    invalid.
- Rollback complexity:
  - Low. Remove one filter/flag, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_thermal_wind_relax`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_thermal_wind_relax --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_thermal_wind_relax --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show large-scale
    thermal-wind shear imbalance is not a material remaining score source. Any
    early `10m_u_component_of_wind`, MSLP, or Z500 guardrail failure would show
    that even the low-mode masked wind update spends too much balance margin.

## Citations

- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press. https://doi.org/10.1016/C2009-0-63394-8
- Vallis, G. K. 2017. Atmospheric and Oceanic Fluid Dynamics, second edition.
  Cambridge University Press. https://doi.org/10.1017/9781107588417
- Jablonowski, C. and Williamson, D. L. 2006. A baroclinic instability test
  case for atmospheric model dynamical cores. Quarterly Journal of the Royal
  Meteorological Society, 132, 2943-2975. https://doi.org/10.1256/qj.06.12
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: A review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This proposal explicitly accounts for the harmful
`.logbook/history/2026-06-20_17-12-34_gradient-wind-surface-diagnostic` result:
that candidate applied a broad same-direction 10 m output diagnostic and failed
the early 10 m wind guardrail. The new mechanism does not alter output 10 m wind
formulas, excludes the lowest sigma layer, uses a long positive-time
relaxation, and targets low-mode extratropical shear rather than day-1 surface
curvature.

It is not a duplicate of scrapped `thermal-wind-zonal-shear-init`, which edited
the initialized zonal-mean wind before DFI and was deprioritized as another
pre-DFI wind edit. This proposal is a rollout tendency on low horizontal modes,
preserves barotropic wind, leaves eddies outside the low-mode mask unchanged,
and tests whether slow baroclinic balance maintenance is different from
overwriting the initial analyzed shear. It should still be treated as risky
because it changes prognostic wind state; the proposal is included only because
it is mechanistically distinct from the rejected output wind family.

## Evaluator Notes

### 2026-06-20T19:12:40Z

Decision: move to `scrap`; ranked 3 of 3 triaged proposals.

The mechanism is scientifically recognizable, but the local evidence makes this
a poor model-selection candidate now. The recent `gradient-wind-surface-
diagnostic` candidate changed only an output diagnostic, completed cleanly, and
still regressed iteration by `-0.007979044425046156` with a day-1-through-day-5
`10m_u_component_of_wind` guardrail failure. Older balance-projected wind
families are also negative: `thermal-wind-zonal-shear-init` was already scrapped
as a tunable thermal-wind wind edit, `low-mode-geostrophic-wind-init` was
scrapped as another balance-projected prognostic wind initialization edit, and
broad Helmholtz/vorticity-preserving wind initialization records show mass-field
and wind guardrail sensitivity.

This proposal avoids the exact surface-output failure by excluding the lowest
layer and acting slowly during rollout, but it is still a prognostic wind-state
correction requiring tunable latitude masks, low-mode cutoffs, Coriolis
denominator bounds, shear caps, and wind-to-vorticity/divergence conversion.
Thermal-wind balance is invalid in the tropics, boundary layer, and ageostrophic
flow, so the implementation risk falls directly on fixed MSLP, Z500, and early
wind guardrails. Do not spend a fixed model-selection run on this family without
prior read-only diagnostics demonstrating a persistent low-mode extratropical
thermal-wind shear imbalance in the accepted incumbent trajectories.
