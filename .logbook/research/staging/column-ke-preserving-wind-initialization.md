---
schema_version: 1
slug: column-ke-preserving-wind-initialization
title: Preserve Column Kinetic Energy During Wind Initialization
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

# Preserve Column Kinetic Energy During Wind Initialization

## Hypothesis

The current adapter interpolates analyzed pressure-level wind components to
sigma layer centers, then projects the nodal vector wind to modal vorticity and
divergence. Prior broad wind-balance initialization changes were harmful or
scrapped, but the incumbent still has negative late `10m_u_component_of_wind`
skill and modest low-level wind bias. A very narrow initialization correction
that preserves column-integrated horizontal kinetic energy can reduce wind-speed
drift introduced by pressure-to-sigma remapping while preserving wind direction,
vertical shear shape, DFI, Coriolis splitting, mass fields, and thermal state.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_ke_wind_init`.
Preserve all incumbent rollout, forcing, residual, recentering, off-centering,
and output behavior.

For the candidate only, add an opt-in wind initialization step after the accepted
log-pressure and hydrostatic temperature remap has produced sigma-level nodal
`u_wind` and `v_wind`, but before `uv_nodal_to_vor_div_modal`:

- diagnose a column pressure-thickness proxy from the source pressure levels and
  from target sigma layers using same-time surface pressure;
- compute source column kinetic energy from the analyzed pressure-level winds
  and target column kinetic energy from the sigma-remapped winds;
- form one bounded multiplicative wind-speed factor per horizontal column,
  `sqrt(source_ke / target_ke)`, clipped for example to `[0.9, 1.1]`;
- apply the factor equally to sigma-level `u_wind` and `v_wind`, preserving wind
  direction, vertical shear ratios, vorticity/divergence phase, and zero-wind
  columns;
- use an area-mean finite fallback factor of `1.0` wherever source or target
  diagnostics are nonfinite or the target kinetic energy is too small;
- do not alter temperature, humidity, `log_surface_pressure`, pressure-level
  output interpolation, residual corrections, DFI timing, or positive-time
  timestep.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, output variables, lead times, and evaluation metrics
    remain unchanged.
- Tests to update:
  - Unit-test the kinetic-energy factor on simple wind columns, including
    zero-wind and nonfinite fallback cases.
  - Verify clipping limits are applied and direction is preserved.
  - Verify the selector changes only initialized winds before modal projection.
  - Verify the candidate factory preserves every incumbent option except the
    kinetic-energy wind initialization selector.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at days 3-15 if wind-speed loss or gain during
    pressure-to-sigma initialization contributes to the incumbent late wind
    degradation.
  - `mean_sea_level_pressure` and `geopotential_500` may improve slightly if
    better initialized wind amplitude reduces geostrophic adjustment.
- Expected neutral metrics:
  - `2m_temperature` should remain close to incumbent because thermal
    initialization, weak-HS forcing, and surface residual correction are
    unchanged.
- Possible regressions:
  - Column kinetic-energy preservation can amplify noisy low-level winds in
    shallow or high-terrain columns.
  - Even a bounded wind rescale can perturb early mass adjustment and spend
    day-1 MSLP guardrail margin.

## Risks

- Numerical stability:
  - Low to moderate. The change is initialization-only and bounded, but it
    changes both vorticity and divergence initial states.
- Compute cost:
  - Low. It adds column reductions before rollout, with no new inner steps.
- Data leakage:
  - None. It uses only same-time initial wind and pressure information already
    consumed by the incumbent.
- Physical plausibility:
  - Moderate. Column kinetic energy is not exactly conserved under vertical
    remapping, but preserving bulk wind amplitude while leaving direction and
    shear shape intact is a conservative alternative to broad balance
    projections.
- Rollback complexity:
  - Low. Remove one adapter helper/flag, one factory/export, one registry entry,
    and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_ke_wind_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_ke_wind_init --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_ke_wind_init --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show pressure-to-sigma
    wind kinetic-energy drift is not a material remaining error source. Any
    early wind or MSLP guardrail failure would show the rescale disrupts the
    accepted initialization balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` remaps
  pressure-level `u_component_of_wind` and `v_component_of_wind` to sigma
  levels before `uv_nodal_to_vor_div_modal`.
- History: `.logbook/history/2026-06-17_08-03-52_conservative-pressure-thickness-init-remap/decision.md`
  rejected broad finite-layer remapping of all fields; this proposal changes
  only a bounded wind-amplitude moment after the accepted center remap.
- History: `.logbook/history/2026-06-17_03-22-44_helmholtz-wind-initialization/decision.md`
  rejected broad wind-control initialization, motivating a scalar amplitude
  correction that preserves direction and shear shape.
- History: `.logbook/history/2026-06-21_06-24-25_mass-weighted-theta-recentering/decision.md`
  showed mass-weighting the accepted theta recentering was slightly negative;
  this proposal avoids thermal recentering and targets wind initialization only.
- Lorenz, E. N. 1955. Available potential energy and the maintenance of the
  general circulation. Tellus.
  https://doi.org/10.1111/j.2153-3490.1955.tb01148.x
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not another conservative pressure-thickness remap: the accepted
pointwise log-pressure interpolation remains in place, and only a bounded scalar
wind-amplitude moment is restored afterward. It is not a geostrophic,
thermal-wind, Helmholtz, angular-momentum, drag, or 10 m diagnostic proposal.
It also avoids the recent failed theta-family recentering refinements and the
startup-step/subcycling family.

## Evaluator Notes

### 2026-06-21T10:25:51Z

Decision: move to `staging`; preserve as a lower-cost backup, but not `ready`.

The proposal has a clear, source-local hook: after log-pressure pressure-to-
sigma interpolation in `weather_state_to_dinosaur_state`, winds are still nodal
and have not yet been projected through `uv_nodal_to_vor_div_modal`. A bounded
column scalar rescale is much narrower than the rejected Helmholtz wind-control
initialization, and it avoids changing temperature, surface pressure, DFI,
rollout, or diagnostics. Implementation cost should be low if the factor is
finite-guarded and default-off.

The local evidence is unfavorable enough to hold it out of ready. Broad
Helmholtz wind initialization caused a very large negative iteration delta and
early mass/geopotential guardrail failures, conservative pressure-thickness
remapping of initialized fields was negative, and the recent vector-wind PCHIP
initialization was clean but effectively neutral. The Lorenz citation supports
energy-conversion context, but it does not directly justify conserving
column-integrated wind kinetic energy under pressure-to-sigma remapping as a
forecast-skill mechanism. Even a clipped wind-speed rescale can disturb early
MSLP through ageostrophic adjustment.

Keep staged only as a narrow wind-initialization backup after stronger mass and
thermal candidates. It is distinct from existing geostrophic, diagnostic, and
Helmholtz wind ideas, but the expected effect size is likely small and the
failure mode overlaps the recent early-MSLP sensitivity.
