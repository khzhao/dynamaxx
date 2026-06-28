---
schema_version: 1
slug: startup-subcycled-first-day-rollout
title: Subcycle Only the First Positive Forecast Day
status: ready
created_at: 2026-06-21T08:05:17Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Subcycle Only the First Positive Forecast Day

## Hypothesis

The accepted incumbent uses DFI and off-centered SIL3, but the first positive
forecast day still has the largest adjustment from pressure-level analysis data
to the sigma-coordinate dycore. A prior full-rollout `600 s` inner-step
candidate was clean but slightly negative, so uniformly shrinking the timestep
is not useful. A bounded startup-only subcycle can instead target spinup
imbalance while preserving the accepted `900 s` cadence, damping, and compute
profile for days 2 through 15.

## Mechanism

Register one side-by-side candidate that preserves every incumbent option and
changes only the positive-time rollout schedule. For the first saved 24 hour
forecast interval, use two `450 s` inner steps wherever the incumbent uses one
`900 s` inner step. After the day-1 state is saved, continue with the incumbent
`900 s` inner-step trajectory for all later saved leads. Keep DFI on the
incumbent stepper and timestep so this is not a DFI routing experiment.

The candidate should not change the forecast contract, target variables, lead
times, metrics, or WeatherBench2 splits. If the startup-subcycled state is
nonfinite, the implementation must fall back to the incumbent 900 s first-day
step before returning diagnostics.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` if a two-phase
    trajectory helper is cleaner than adapter-local scan logic
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model with a `_startup_subcycle` suffix.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, and lead
    indexing stay unchanged.
- Tests to update:
  - Verify the candidate preserves all incumbent flags except startup
    subcycling.
  - Verify lead count and lead indexing match the incumbent for arbitrary
    `lead_steps`.
  - Verify DFI still uses the incumbent 900 s stepper.
  - Verify a finite non-JIT smoke forecast and registry construction.

## Expected Metric Movement

- Expected improvements:
  - Days 1 to 5 `mean_sea_level_pressure` and `geopotential_500` if early
    sigma-coordinate adjustment is still timestep-sensitive.
  - `2m_temperature` if lower-column thickness adjustment becomes smoother
    before the accepted residual correction is applied.
- Expected neutral metrics:
  - Days 6 to 15 should stay close to incumbent because the long rollout uses
    the accepted 900 s schedule.
  - `10m_u_component_of_wind` should be mostly neutral because wind diagnostics
    and Coriolis splitting are unchanged.
- Possible regressions:
  - The first-day trajectory may move off the empirically favorable incumbent
    path before the residual and weak-HS terms can correct it.

## Risks

- Numerical stability:
  - Low to moderate. The step is smaller during startup, but it changes the
    positive-time spinup trajectory.
- Compute cost:
  - Low to moderate. Only day 1 is twice as expensive; days 2 through 15 retain
    incumbent cost.
- Data leakage:
  - None. The schedule is fixed and uses no verification data.
- Physical plausibility:
  - Moderate. Shorter startup steps are a standard way to limit initial
    adjustment error, but this is a pragmatic spinup schedule rather than a new
    physical process.
- Rollback complexity:
  - Low if implemented as one candidate-only trajectory selector.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Compare against the cached leaderboard incumbent artifacts when valid.
  - Require primary-score delta at least `+0.002`, clean diagnostics, and the
    fixed RMSE guardrails.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4` only
    after iteration promotion, again reusing valid incumbent cache.
  - Require validation primary-score delta at least `+0.001` and the same
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show the first-day
    adjustment is not improved by local timestep refinement. Any early MSLP,
    Z500, or T2m guardrail breach would show the startup path is worse than the
    accepted 900 s balance.

## Citations

- Wicker, L. J. and Skamarock, W. C. 2002. Time-splitting methods for elastic
  models using forward time schemes. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2002)130%3C2088:TSMFEM%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Dynamaxx history:
  `.logbook/history/2026-06-16_18-41-23_six-hundred-second-inner-step/decision.md`
  rejected a full-rollout `600 s` timestep, so this proposal intentionally
  limits the smaller step to the first positive forecast day.

## Researcher Notes

This is distinct from `split-explicit-nonlinear-advection-subcycle`, which
changes nonlinear tendency sampling throughout the rollout, and from
`fourth-order-imex-rk-rollout`, which changes the time integrator everywhere.
It tests a narrow spinup-schedule hypothesis while keeping the accepted
long-lead numerical behavior.

## Evaluator Notes

### 2026-06-21T08:09:05Z

Decision: move to `ready`; ranked first and should be the only active ready
candidate.

This is the strongest next experiment after reviewing the new proposals, active
staging, current empty `ready/`, and recent decisions. The mechanism is narrow:
it preserves the incumbent DFI path, off-centered SIL3 scheme, exact Coriolis
split, analysis-offset weak-HS equilibrium, residual correction, output
contract, target variables, and fixed evaluation protocols, while changing only
the first positive saved forecast day. That makes it materially lower blast
radius than the staged `split-explicit-nonlinear-advection-subcycle`, which
changes nonlinear tendency sampling through the whole positive-time rollout and
adds DFI symmetry complexity.

The negative full-rollout `600 s` timestep history is important but not fatal:
`.logbook/history/2026-06-16_18-41-23_six-hundred-second-inner-step/decision.md`
was clean and only slightly negative, so it argues against timestep sweeps or a
global smaller step, not against this fixed startup-only spinup schedule. The
implementation risk is moderate because the current adapter builds one fixed
`inner_steps` trajectory for every saved outer step, so this needs a
candidate-only two-phase trajectory wrapper rather than simply changing
`inner_step_seconds`. The Orchestrator should instruct the Scorer to reuse the
valid cached incumbent metrics from `.logbook/leaderboard.json` and not run
`golden`.
