---
schema_version: 1
slug: low-mode-nonlinear-balance-pressure-tendency
title: Add a Weak Low-Mode Nonlinear-Balance Pressure Tendency
status: scrap
created_at: 2026-06-21T16:04:00Z
author_role: Researcher
target_model: dinosaur
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

# Add a Weak Low-Mode Nonlinear-Balance Pressure Tendency

## Hypothesis

The incumbent has strong initialization and near-surface output handling, but
medium-lead MSLP and Z500 errors can still grow when the low-order mass field
drifts out of balance with the resolved rotational flow. Direct pressure
anchors, surface-pressure residuals, and startup divergence filters have been
neutral or harmful. A weaker alternative is a prognostic tendency that acts only
on very low horizontal modes of log surface pressure and nudges them toward a
nonlinear-balance pressure implied by the current wind and thickness fields,
without using analysis targets after initialization.

## Mechanism

Add an opt-in explicit pressure tendency during positive-time rollout. Diagnose
large-scale wind, vorticity, divergence, temperature, and hydrostatic thickness
from the current state; solve a low-mode spherical balance relation for the
mass-field increment implied by rotational flow and thermal thickness; retain
only broad modes such as total wavenumber `<= 6`; remove the global mean; cap the
increment per inner step; and add it as a weak relaxation tendency to
`log_surface_pressure`.

The first implementation should keep DFI unchanged, avoid startup-only behavior,
avoid any output diagnostic correction, and use a long relaxation timescale such
as 5 to 10 days. If any balance diagnostic is nonfinite, if the elliptic solve
has unsupported modes, or if the increment exceeds the cap, the candidate should
fall back to the incumbent pressure tendency for that step.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side incumbent-derived model with suffix `_low_mode_balance_pressure`.
- API changes:
  - None. The forecast contract, target variables, splits, metrics, and fixed protocols remain unchanged.
- Tests to update:
  - Unit-test low-mode mask construction, zero-global-mean enforcement, and cap enforcement.
  - Verify a zero-wind horizontally uniform state receives no pressure increment.
  - Verify nonfinite balance diagnostics fall back to the incumbent tendency.
  - Verify the candidate factory preserves all incumbent options except the new balance-pressure selector.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 3 to 15 if low-mode mass-balance drift remains a leading error source.
  - `10m_u_component_of_wind` may improve indirectly if balanced pressure gradients reduce slowly growing wind phase errors.
- Expected neutral metrics:
  - `2m_temperature` should be mostly neutral because no thermal forcing, screen-temperature nudge, or surface residual change is introduced.
- Possible regressions:
  - Even low-mode pressure changes can disrupt the carefully tuned semi-implicit pressure-gradient balance and worsen early MSLP/Z500 guardrails.
  - Balance relations are approximate in the tropics and in divergent flow.

## Risks

- Numerical stability:
  - Moderate. The tendency is capped and low-mode, but pressure feeds back strongly into the primitive equations.
- Compute cost:
  - Low to moderate. It adds modal masking and a small elliptic/balance diagnostic, but no extra rollout steps.
- Data leakage:
  - None if the tendency uses only the current forecast state and fixed operators. Do not use future analyses, validation statistics, or leaderboard residuals.
- Physical plausibility:
  - Moderate. Nonlinear balance is a recognized large-scale atmospheric constraint, but this is a simplified sigma-coordinate relaxation.
- Rollback complexity:
  - Low. Remove one option/helper, one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics, and no early day-1-through-day-5 or variable-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with fixed guardrails passing.
- Outcome that would falsify the hypothesis:
  - A clean neutral/negative iteration delta would show low-mode nonlinear-balance pressure drift is not material. Any early MSLP/Z500 guardrail failure would show the pressure tendency is too invasive despite low-mode capping.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` computes explicit and implicit `log_surface_pressure` tendencies and exposes spherical harmonic gradient, divergence, and inverse-Laplacian operators needed for a low-mode balance diagnostic.
  - History: `.logbook/history/2026-06-21_10-27-50_first-step-divergence-balance-filter/decision.md` rejected a startup-only divergence cleanup as neutral-negative, so this proposal acts continuously and on pressure balance rather than only first-step divergence.
  - History: `.logbook/history/2026-06-19_23-29-46_low-mode-mass-diagnostic-residual-memory/decision.md` and pressure-anchor records are negative evidence against analysis-residual output corrections; this proposal uses no target residuals after initialization.
  - Charney, J. G. 1955. The use of the primitive equations of motion in numerical prediction. Tellus. https://doi.org/10.1111/j.2153-3490.1955.tb01138.x
  - Daley, R. 1991. Atmospheric Data Analysis. Cambridge University Press. https://doi.org/10.1017/CBO9780511802270
  - Lynch, P. 2006. The Emergence of Numerical Weather Prediction. Cambridge University Press. https://doi.org/10.1017/CBO9780511606823

## Researcher Notes

This is not a direct pressure anchor, not a surface diagnostic, not a screen
temperature nudge, and not a startup-only fix. It is also distinct from scrapped
`low-mode-mass-divergence-iau`: that idea inserted analysis increments during
initial adjustment, while this proposal computes a current-state balance
tendency during rollout and removes the global mean to avoid mass anchoring. It
should still be treated as high risk because pressure tendencies can easily
damage early MSLP and Z500 guardrails.

## Evaluator Notes

### 2026-06-21T16:04:40Z

Decision: move to `scrap`; ranked 3 of 3 current proposals.

The proposal is scientifically recognizable but a poor next search point under
the current loop evidence. Nonlinear balance and low-mode mass-wind consistency
are legitimate concepts, but the implementation described here would add a new
prognostic `log_surface_pressure` tendency every positive-time step using an
approximate spherical balance diagnostic. That is a high-leverage pressure-path
change in the same area where recent candidates have repeatedly failed to clear
the fixed gates.

Recent history is strong negative evidence. The first-step divergence balance
filter was essentially neutral-negative after accepted DFI and offcentering.
Startup subcycling produced a large negative iteration delta and failed the
early MSLP guardrail. Low-mode mass diagnostic residual memory was clean but
subthreshold, and the scrapped `low-mode-mass-divergence-iau` already concluded
that making low-mode mass residuals more prognostic is too invasive relative
to the measured signal. Other active pressure-path ideas are already staged in
narrower forms, including surface-pressure zero-mode tendency projection,
DFI-only mass restoration, log-pressure increment limiting, and an Exner
pressure-gradient split.

This proposal is not an exact duplicate because it uses a current-state balance
tendency rather than analysis residuals or startup-only divergence increments.
It is still dominated by safer staged pressure experiments and by the current
ready momentum-filter candidate. Scrap it unless future diagnostics show a
specific persistent low-mode nonlinear-balance pressure error that cannot be
addressed by the narrower staged pressure mechanisms.
