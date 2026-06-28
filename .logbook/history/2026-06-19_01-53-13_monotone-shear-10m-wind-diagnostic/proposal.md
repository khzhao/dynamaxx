---
schema_version: 1
slug: monotone-shear-10m-wind-diagnostic
title: Add a Monotone Shear Limit to the 10 m Wind Diagnostic
status: ready
created_at: 2026-06-19T01:47:32Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
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

# Add a Monotone Shear Limit to the 10 m Wind Diagnostic

## Hypothesis

The accepted theta layer-mean recentering improved both iteration and validation
scores, but its limiting regression moved to late `10m_u_component_of_wind`:
day 15 regressed by `+8.010338959282189%` on iteration and
`+7.039021793195873%` on validation. The current 10 m diagnostic already uses
bulk Richardson stability information, but it can still emit a near-surface
wind vector whose speed is slightly amplified above the lowest sigma-layer wind
under unstable mixing. A surface-layer monotonicity guard that keeps 10 m wind
speed within a conservative lower-column shear envelope should reduce late
wind overshoot without touching the accepted thermal trajectory or theta
recentering gains.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_monotone_10m_wind`.
Preserve the incumbent initialization, DFI, weak Held-Suarez forcing,
theta-form thermodynamic tendency, theta layer-mean recentering, symmetric
exact Coriolis split, horizontal diffusion, stability-aware residual decay,
output variables, WeatherBench2 splits, lead times, metrics, and deterministic
evaluation gates.

For the candidate only, replace the existing Richardson 10 m wind output helper
with a stricter vector-speed diagnostic:

- compute the incumbent Richardson wind factor exactly as today;
- diagnose lowest and second-lowest sigma-layer wind vectors, their speeds, the
  same dry hypsometric layer heights, and the same bulk Richardson number;
- apply the incumbent Richardson factor to the lowest-layer wind vector;
- bound the resulting 10 m wind speed by a monotone lower-column envelope:
  under stable or neutral flow, the 10 m speed should not exceed the lowest
  model-level speed; under unstable flow, allow only a small fixed overshoot,
  for example `1.02 * lowest_speed`, to represent downward momentum mixing;
- prevent artificial direction flips by preserving the candidate vector
  direction and applying only a scalar speed limiter;
- keep the current finite fallback to the raw lowest-layer wind when
  temperature, pressure, shear, height, or the limiter is nonfinite;
- leave `2m_temperature`, pressure-level fields, `surface_pressure`, MSLP,
  `geopotential_500`, the prognostic Dinosaur state, and residual-correction
  decay fields unchanged.

This is not a new residual-decay law, persistence blend, validation-tuned wind
scale, or thermal rollback. It narrows the accepted physical surface-layer
diagnostic to respect the expected monotone wind-speed relation between 10 m
and the lowest model level.

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
  - None. `DycoreModel.forecast`, input channels, output channels, target
    variables, lead times, splits, metrics, and deterministic gates stay fixed.
- Tests to update:
  - Unit-test stable, neutral, and unstable synthetic lower columns.
  - Verify the monotone limiter never increases speed above the configured
    stable/neutral envelope and applies only a scalar vector-speed correction.
  - Verify nonfinite diagnostics fall back to the incumbent raw lowest-layer
    wind path.
  - Verify the candidate factory preserves every incumbent option except the new
    10 m wind diagnostic selector.
  - Verify all non-wind output channels and the trajectory remain identical to
    the incumbent before near-surface residual correction.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at days 10 to 15 if theta recentering's remaining
    wind cost is caused by late near-surface speed overshoot.
  - Primary score may improve without reducing the accepted `2m_temperature`
    gains because the thermal state and theta recentering filter are unchanged.
- Expected neutral metrics:
  - `2m_temperature`, `geopotential_500`, and `mean_sea_level_pressure` should
    be unchanged except for metric bookkeeping noise because the candidate is
    an isolated 10 m output diagnostic.
  - Day-1 through day-5 aggregate RMSE should remain protected by the accepted
    residual correction and current Richardson structure.
- Possible regressions:
  - Some unstable boundary layers can physically mix higher momentum downward,
    so too strict a cap may remove useful 10 m wind amplitude.
  - If the late regression is directional or synoptic-phase error rather than
    speed overshoot, this limiter may be clean but subthreshold.

## Risks

- Numerical stability:
  - Very low. The change is output-diagnostic only and cannot feed back into the
    rollout.
- Compute cost:
  - Low. It reuses the existing surface-layer algebra and adds only local speed
    bounds.
- Data leakage:
  - None. It uses only forecast state, fixed constants, and same-lead diagnostic
    fields. It does not inspect future truth, validation scores, or golden
    artifacts.
- Physical plausibility:
  - Moderate to high. Log-layer and Monin-Obukhov surface-layer theory support
    diagnosing 10 m wind from model-level wind with stability corrections, and
    a monotone speed envelope is a conservative safeguard.
- Rollback complexity:
  - Low. Remove one diagnostic option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_monotone_10m_wind`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_monotone_10m_wind --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_monotone_10m_wind --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that late 10 m wind
    regression is not primarily a surface-layer speed-envelope issue. Any early
    10 m wind guardrail failure would show that the accepted Richardson
    diagnostic should not be tightened this way.

## Citations

- Citation or source:
  - Dynamaxx source:
    `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
    `_surface_layer_richardson_10m_wind`, including the current bounded
    Richardson factor and finite fallback.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/decision.md`
    accepted the current Richardson 10 m wind diagnostic with large wind gains
    and nearly neutral non-wind fields.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_00-02-28_theta-zero-mode-thermal-recentering/scoring_notes.md`
    records the accepted theta recentering result and identifies late day-15
    `10m_u_component_of_wind` as the largest remaining regression.
  - American Meteorological Society Glossary of Meteorology, Monin-Obukhov
    similarity theory.
    https://glossary.ametsoc.org/wiki/monin-obukhov-similarity-theory/
  - ECMWF IFS Documentation Part IV: Physical Processes describes surface-layer
    diagnostics and stability-dependent transfer.
    https://www.ecmwf.int/sites/default/files/elibrary/2016/17117-part-iv-physical-processes.pdf
  - Beljaars, A. C. M. and Holtslag, A. A. M. 1991. Flux Parameterization over
    Land Surfaces for Atmospheric Models. Journal of Applied Meteorology.
    https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of accepted `surface-layer-richardson-wind-diagnostic`;
it keeps that diagnostic's bulk Richardson structure and tests only a
physically motivated vector-speed monotonicity guard. It is also not a repeat
of rejected `surface-layer-diagnostic-extrapolation`, which linearly
extrapolated both 2 m temperature and 10 m wind and failed near-surface
guardrails. This proposal changes only the 10 m wind channel, preserves vector
direction, and is motivated by the new post-theta-recentering evidence that the
remaining wind problem is late and below the guardrail rather than an early
surface-layer failure.

## Evaluator Notes

### 2026-06-19T01:51:18Z

Decision: move to `ready`; ranked 1 of 3 new proposals.

This is the strongest next candidate because it is narrowly targeted at the
only sizable remaining regression after the accepted theta recentering: late
`10m_u_component_of_wind` day 15, `+8.010338959282189%` on iteration and
`+7.039021793195873%` on validation, still below the `+10%` guardrail but close
enough to limit follow-up thermal proposals. The accepted Richardson diagnostic
is strong precedent for a physically justified 10 m diagnostic, and the source
currently isolates that behavior behind
`use_surface_layer_richardson_10m_wind_diagnostic`, so the implementation and
rollback surface are small.

This is output-diagnostic work on a scored channel, so it should be constrained
carefully. The proposed limiter remains acceptable because it is a conservative
surface-layer speed-envelope check, uses only forecast-state lower-column
fields, preserves the vector direction by applying a scalar speed factor, and
does not inspect future truth or alter the forecast contract. It is not a
generic validation-tuned wind scale and should not change residual decay,
thermal trajectory, pressure fields, target variables, splits, metrics, or
fixed evaluation gates.

Orchestrator enforcement if selected: implement exactly one candidate factory
with a predeclared monotone cap, keep non-wind outputs and the prognostic
trajectory identical to the incumbent before near-surface residual correction,
add finite fallback tests, and do not tune the cap after seeing fast,
iteration, or validation results.
