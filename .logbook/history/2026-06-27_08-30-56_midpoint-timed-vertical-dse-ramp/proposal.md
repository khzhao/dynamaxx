---
schema_version: 1
slug: midpoint-timed-vertical-dse-ramp
title: Midpoint-Timed Vertical-DSE Ramp
status: ready
created_at: 2026-06-27T05:18:39Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Midpoint-Timed Vertical-DSE Ramp

## Hypothesis

The incumbent's pressure-ramped vertical-DSE increment evaluates the smooth ramp
at the beginning of each inner step via `state.sim_time`. During the 24-72 hour
activation window, that is a first-order time lag relative to the tendency it
weights. Evaluating the ramp at the step midpoint should better match the
time-centered transport already used by the accepted midpoint HSL departure
without exposing the vertical-DSE increment earlier than the accepted ramp
schedule.

## Mechanism

Add a side-by-side candidate
`dino_hsl2_mass_dse_wtg_vdse_ramp_midtime`. For this candidate only, compute
the pressure-ramped vertical-DSE increment weight from
`state.sim_time + 0.5 * horizontal_semilagrangian_theta_transport_step` instead
of `state.sim_time`.

The candidate must preserve the incumbent ramp constants, vertical-DSE
increment formula, low-mode pressure guard, per-step temperature cap, WTG
relaxation filter, spectral filters, DFI exclusion, output contract, and fixed
evaluation protocols.

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
  - Register only the side-by-side candidate model name.
- API changes:
  - Add an opt-in boolean selector for midpoint ramp timing. The incumbent
    remains byte-for-byte behaviorally unchanged when the selector is false.
- Tests to update:
  - Unit-test start-time and midpoint-time ramp weights on synthetic `sim_time`.
  - Verify incumbent factory keeps start-of-step timing.
  - Verify candidate factory enables midpoint timing and remains finite in a
    non-JIT smoke forecast.
  - Verify registry and dependency exports include the candidate only once.

## Expected Metric Movement

- Expected improvements:
  - Small improvement in 24-72 hour thermal and pressure fields during the
    ramp-on transition, especially `2m_temperature`, `geopotential_500`, and
    `mean_sea_level_pressure`.
- Expected neutral metrics:
  - Late leads should be nearly neutral because the ramp is fully active after
    the activation window.
  - Wind diagnostics should be nearly neutral because momentum equations are
    unchanged.
- Possible regressions:
  - Slight early-lead degradation if the midpoint ramp applies the vertical-DSE
    increment too aggressively near the ramp onset.

## Risks

- Numerical stability:
  - Low. The same increment, cap, and finite-diagnostic fallback are preserved.
- Compute cost:
  - Negligible. The candidate adds one scalar time offset and no new transforms.
- Data leakage:
  - None. The change depends only on forecast model time and fixed step size.
- Physical plausibility:
  - Moderate to high. Time-centered forcing weights are standard for improving
    phase accuracy in split or staged tendencies.
- Rollback complexity:
  - Low. The selector can be removed cleanly if rejected.

## Evaluation Plan

- Fast gate:
  - Run focused unit tests, full `uv run pytest`, and
    `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_midtime`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_midtime --workers 4`.
  - Compare against the cached leaderboard incumbent metrics for
    `dino_hsl2_mass_dse_wtg_vdse_ramp`.
- Validation gate:
  - Run validation only if iteration clears the acceptance threshold and
    guardrails.
- Outcome that would falsify the hypothesis:
  - Any diagnostic failure, an iteration primary score not at least `0.002`
    above the cached incumbent, or early day-1 to day-5 guardrail regressions.

## Citations

- Strang, G. 1968. On the construction and comparison of difference schemes.
  SIAM Journal on Numerical Analysis.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.

## Researcher Notes

This is not another vertical-DSE amplitude, cap, pressure-work, or WTG-relaxation
variant. Recent rejected candidates changed WTG timing, WTG gating, filter
ordering, low-mode treatment, or hydrostatic-work coupling. This proposal
changes only the scalar time at which the already accepted vertical-DSE ramp is
sampled, preserving the accepted physics and fixed evaluation gates.

## Evaluator Notes

2026-06-27T05:18:39Z main-loop Evaluator simulation: ready. This is the best
next experiment because it changes one scalar timing choice in the accepted
vertical-DSE ramp, preserves all fixed gates and the forecast contract, and has
lower tuning risk than another WTG support adjustment. Implementation must keep
the incumbent start-of-step ramp behavior unchanged and add only a side-by-side
candidate model.
