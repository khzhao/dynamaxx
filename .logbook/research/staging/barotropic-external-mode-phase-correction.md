---
schema_version: 1
slug: barotropic-external-mode-phase-correction
title: Correct Barotropic External-Mode Phase Drift
status: staging
created_at: 2026-06-22T12:02:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Correct Barotropic External-Mode Phase Drift

## Hypothesis

The accepted off-centered SIL3 scheme strongly improved mass-field skill by
damping fast gravity-wave noise, but it may also introduce phase or amplitude
error in the lowest vertical normal mode that controls broad surface pressure
and Z500 evolution. A bounded barotropic external-mode phase correction can
adjust only the vertically averaged divergence/log-surface-pressure pair after
each accepted step, leaving baroclinic structure, theta physics, residual
diagnostics, and lower-boundary heat-flux sources unchanged.

## Mechanism

Add one side-by-side candidate with short alias `dino_ext_phase`. After the
incumbent step, apply a guarded low-wavenumber correction to the external
gravity-wave subspace:

- compute mass-weighted vertical-mean divergence and log-surface-pressure modal
  anomalies from `next_state - prev_state`;
- restrict the operation to broad horizontal modes, for example total
  wavenumber `1..8`, excluding the global mass mode;
- apply a fixed small phase rotation or leapfrog-style time-centering blend to
  the divergence/log-pressure pair, using the existing semi-implicit reference
  temperature and sigma layer thicknesses to scale the two variables;
- cap the per-step correction relative to the raw increment and require finite
  fallback to the incumbent next state;
- leave vorticity, baroclinic divergence, temperature/theta, tracers, Coriolis
  splitting, weak-HS/ocean forcing, diffusion, residual correction, and output
  interpolation unchanged.

This is not another divergence damping filter or vertical-normal-mode sponge.
It is a conservative phase-control split for the lowest mass mode, intended to
preserve useful amplitude while reducing external-mode timing error.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one registered side-by-side model, preferably using evaluation
    alias `dino_ext_phase`.
- API changes:
  - None.
- Tests to update:
  - Verify the correction preserves the global mean log-surface-pressure mode.
  - Verify high-wavenumber, vorticity, temperature, and tracer components are
    unchanged.
  - Verify nonfinite or over-cap diagnostics fall back to the incumbent state.
  - Add a non-JIT finite forecast smoke test and registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 2 to 10 if broad
    mass-field phase error remains after accepted off-centering.
  - Secondary `2m_temperature` improvement if lower-column pressure/thickness
    evolution stays better aligned with the thermal state.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because rotational wind,
    the Richardson diagnostic, and near-surface residual memory are unchanged.
- Possible regressions:
  - Any external-mode phase correction can damage balanced cyclogenesis if the
    selected low modes contain useful forecast signal.
  - MSLP/Z500 early guardrails are the primary risk.

## Risks

- Numerical stability:
  - Moderate. The correction touches prognostic divergence and mass fields every
    inner step, so caps and finite fallbacks are required.
- Compute cost:
  - Low. Uses modal masks and vertical reductions without changing grid size,
    trajectory length, or worker policy.
- Data leakage:
  - None. Uses only current and previous model states.
- Physical plausibility:
  - Moderate. Split treatment of fast external modes is common, but this is a
    pragmatic low-mode phase corrector rather than a full normal-mode solver.
- Rollback complexity:
  - Low. Remove one post-step filter, selector, factory/export, registry entry,
    and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ext_phase`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ext_phase --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failures, and
    iteration primary delta at least `+0.002` against cached incumbent artifacts.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ext_phase --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would indicate accepted
    off-centered SIL3 already controls the relevant external mode. Any early
    MSLP/Z500 guardrail failure would show the phase correction disrupts
    balanced mass evolution.

## Citations

- Simmons, A. J., Hoskins, B. J., and Burridge, D. M. 1978. Stability of the
  semi-implicit method of time integration. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1978)106%3C0405:SOTSMO%3E2.0.CO;2
- Skamarock, W. C. and Klemp, J. B. 2008. A time-split nonhydrostatic
  atmospheric model for weather research and forecasting applications. Journal
  of Computational Physics. https://doi.org/10.1016/j.jcp.2007.01.037

## Researcher Notes

This is not a duplicate of the accepted off-centered SIL3 experiment because it
does not change the tableau or damping strength. It is not the scrapped
vertical-normal-mode gravity-wave filter because it does not add a sponge or
select the fastest vertical eigenmode; it applies a capped phase correction to
only broad barotropic mass/divergence modes. It is also unrelated to the recent
near-zero SST/soil/snow/ocean-anchor lower-boundary thermal variants.

## Evaluator Notes

### 2026-06-22T12:06:03Z

Decision: move to `staging`; ranked 2 of 2 fresh proposals.

The mechanism is plausible enough to preserve, but it is not the next
implementation target. The literature check supports the broad premise:
Simmons, Hoskins, and Burridge 1978 justify semi-implicit treatment for
primitive-equation fast modes, and Skamarock and Klemp 2008 discuss time-split
treatment of fast external/acoustic-gravity modes. Those sources do not,
however, justify the proposal's specific fixed low-wavenumber post-step phase
rotation of vertically averaged divergence and log-surface-pressure.

Repository evidence raises the main concern. Source inspection shows
`implicit_terms` already leaves vorticity zero and couples the fast mass
subsystem through divergence, temperature variation, and log surface pressure.
A post-step correction to only vertically averaged divergence/log pressure is
therefore not a clean external-mode solve unless the scaling, oscillator phase,
and projection are specified more rigorously. The current proposal offers
alternatives ("fixed small phase rotation or leapfrog-style time-centering
blend") rather than one auditable numerical operator.

History also argues against promoting it now. Uniform SIL3 off-centering was a
large accepted win (`+0.25891536186185515` iteration), so external-mode control
is important, but follow-up low-mode or mass/divergence edits have been weak or
risky: the vertical-normal-mode gravity-wave filter was scrapped for
complexity and weak local testability; divergence-selective off-centering is
staged because a literal implementation looked close to a no-op or a broader
solver rewrite; low-mode mass-divergence IAU was scrapped; and time-centered
log-pressure continuity remains staged after several prognostic mass-equation
changes regressed or landed near zero.

Keep this staged as a later diagnostic-driven fast-mode follow-up. Before
promotion, it needs one precise linearized external-mode derivation, a clear
modal scaling between divergence and log pressure, a proof that global mass and
high modes are untouched, and a small offline or unit demonstration that the
operator is not equivalent to the accepted off-centering or to a disguised
divergence damping filter.
