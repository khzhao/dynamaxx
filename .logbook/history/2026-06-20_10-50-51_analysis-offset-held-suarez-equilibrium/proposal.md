---
schema_version: 1
slug: analysis-offset-held-suarez-equilibrium
title: Offset Weak Held-Suarez Equilibrium Toward the Initial Thermal State
status: ready
created_at: 2026-06-20T10:45:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
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

# Offset Weak Held-Suarez Equilibrium Toward the Initial Thermal State

## Hypothesis

The current incumbent keeps the accepted weak Held-Suarez thermal relaxation,
but the fixed analytic Held-Suarez equilibrium is an idealized dry climate, not
the initialized WeatherBench2 atmosphere. The current iteration cache shows a
growing cold bias in `2m_temperature`, while the recent
`zonal-mean-weak-hs-relaxation` rejection shows that weakening the local weak-HS
anomaly correction is harmful without compensation.

A safer alternative is to keep the accepted local relaxation rates unchanged,
but shift the weak-HS equilibrium by a same-time, low-order initial thermal
offset. The forcing then damps toward an equilibrium closer to the initialized
seasonal and vertical structure while still applying the accepted local
Newtonian relaxation strength.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq`.
Preserve the accepted DFI, log-pressure and hydrostatic initialization, exact
Coriolis Strang split, Richardson 10 m wind diagnostic, theta tendency,
theta-mean recentering, off-centered SIL3, and scale-separated near-surface
residual memory.

Add an opt-in weak-HS forcing variant that computes an initial thermal offset
for each forecast start:

- after the accepted pressure-to-sigma initialization, compute nodal absolute
  sigma-layer temperature from the initial Dinosaur state;
- compute the standard Held-Suarez equilibrium temperature on the same sigma
  grid and surface-pressure field;
- form `initial_temperature - held_suarez_equilibrium`;
- retain only a broad, low-order component, for example the layerwise
  area-weighted mean plus zonal wavenumbers 0 through 3, with a fixed amplitude
  cap such as 20 K and finite fallback to zero offset;
- add this offset to the weak-HS equilibrium temperature inside the forcing;
- keep `kt`, `ka`, `ks`, the no-Rayleigh-drag setting, and all rollout and DFI
  timing unchanged.

The implementer should avoid recompiling per initial time by passing the offset
as a dynamic JAX argument to the trajectory function, or by using a small
factory wrapper that is demonstrably not the runtime bottleneck under the
standard `--workers 4` setting.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, output variables, lead times, target variables,
    metrics, and protocols remain unchanged.
- Tests to update:
  - Unit-test offset construction, finite fallback, and amplitude clipping.
  - Verify that a zero offset reproduces the incumbent weak-HS forcing.
  - Verify that the offset changes only the weak-HS equilibrium, not relaxation
    coefficients, DFI settings, off-centering, or residual-correction flags.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` from days 3 to 15 if the current cold drift is partly from
    relaxing toward an overly idealized thermal equilibrium.
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if improved
    thermal thickness reduces hydrostatic mass-field drift.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to neutral because the proposal
    keeps the accepted wind diagnostic, Coriolis split, and no-Rayleigh weak-HS
    configuration.
- Possible regressions:
  - If the fixed idealized equilibrium is acting as useful regularization, the
    offset may preserve analysis-scale thermal structure too long.
  - If the retained low modes include weather-dependent increments rather than
    stationary seasonal structure, MSLP or Z500 can regress at early leads.

## Risks

- Numerical stability:
  - Moderate. This changes a rollout forcing, but the offset is bounded and the
    accepted weak-HS rates are unchanged.
- Compute cost:
  - Low to moderate. Offset construction is cheap; the main risk is accidental
    JIT recompilation per initial state.
- Data leakage:
  - Low if the offset uses only the same forecast initial analysis and fixed
    constants. Do not use future truth, validation statistics, or golden data.
- Physical plausibility:
  - Moderate to high. Newtonian relaxation toward a seasonally representative
    thermal state is physically more plausible than relaxing all cases toward a
    single idealized dry equilibrium, provided the correction is low-order and
    bounded.
- Rollback complexity:
  - Low. Remove one forcing option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or sub-threshold iteration delta would show that the
    accepted idealized weak-HS equilibrium is not a remaining material error
    source. Any early `2m_temperature` guardrail failure would show the offset is
    preserving incompatible thermal increments.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` composes the
  accepted primitive equation with `_TracerSafeHeldSuarezForcingSigma` while
  keeping `weak_held_suarez_kf_per_day` at zero.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
  implements the analytic Held-Suarez equilibrium temperature and relaxation
  rates used by the adapter.
- History: `.logbook/history/2026-06-16_16-27-03_wind-sparing-held-suarez-relaxation/decision.md`
  accepted weak thermal Held-Suarez relaxation with a large positive iteration
  delta.
- History: `.logbook/history/2026-06-20_09-03-16_zonal-mean-weak-hs-relaxation/decision.md`
  rejected weakening local weak-HS anomaly correction, so this proposal keeps
  the accepted local relaxation rate and changes only the low-order equilibrium.
- History: `.logbook/history/2026-06-16_23-51-06_calendar-aware-solar-relaxation/decision.md`
  rejected a broad calendar-aware thermal forcing after `2m_temperature`
  guardrail failures; this proposal is narrower and bounded.
- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of staged `weak-hs-positive-time-ramp`,
`column-neutral-weak-hs-heating-split`, `tropopause-capped-thermal-relaxation`,
or `solar-weighted-thermal-tendency`. Those proposals change the timing,
vertical compensation, tropopause mask, or radiative spatial weighting of the
thermal tendency. This proposal keeps the accepted weak-HS tendency strength and
instead changes the low-order equilibrium around which the same tendency acts.

It is also not a revival of rejected `zonal-mean-weak-hs-relaxation`: that
experiment weakened local anomaly correction and failed `2m_temperature`
guardrails. Here the local damping coefficient is unchanged, with a bounded
equilibrium offset as the compensating mechanism required by recent history.

## Evaluator Notes

### 2026-06-20T10:48:47Z

Decision: move to `ready`; ranked 1 of 3 in this triage pass.

This is the strongest current proposal because it changes a real remaining
weak-HS issue while preserving the accepted local relaxation rate. The recent
`zonal-mean-weak-hs-relaxation` rejection is important negative evidence: that
candidate weakened local thermal correction and regressed iteration by
`-0.03834024093283184`, including a day-1-through-day-5 `2m_temperature`
guardrail failure. This proposal does not weaken that local rate; it only
changes the low-order equilibrium target with a finite, bounded offset derived
from the same forecast initial analysis.

It also has a narrower and more testable implementation surface than the
pressure limiter or vorticity-Jacobian proposal. Source inspection confirms the
thermal-only weak-HS wrapper computes absolute nodal temperature and the analytic
equilibrium in one isolated forcing path, so an opt-in equilibrium offset can be
tested without touching vorticity, divergence, `log_surface_pressure`, residual
memory, the accepted off-centered SIL3 damping, or output diagnostics.

The risk is real. Calendar-aware equilibrium displacement previously regressed
`2m_temperature`, and any analysis-derived offset can preserve incompatible
initial thermal structure too strongly. Keep ready small by promoting only this
idea, and require the implementation to retain only broad low modes, use a fixed
temperature cap, fall back to the incumbent equilibrium on nonfinite diagnostics,
avoid validation- or truth-derived statistics, and prove that a zero offset is
incumbent-equivalent.
