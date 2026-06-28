---
schema_version: 1
slug: six-hundred-second-inner-step
title: Use a Shorter Inner Time Step for the Accepted Physics
status: ready
created_at: 2026-06-16T17:39:18Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs
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

# Use a Shorter Inner Time Step for the Accepted Physics

## Hypothesis

The incumbent combines the IMEX SIL3 primitive-equation stepper with DFI,
near-surface residual diagnostics, and weak thermal Held-Suarez relaxation.
After the accepted forcing reduced broad thermal drift, remaining Z500 and
long-lead 10 m wind errors may include time-discretization phase and amplitude
error from the `900 s` inner step. A single smaller, predeclared `600 s` inner
step should improve integration accuracy for advective and gravity-wave
coupling without adding more damping or changing the forecast contract.

## Mechanism

Create a side-by-side candidate that preserves the accepted physics and sets
`inner_step_seconds=600.0`. This increases the number of inner IMEX SIL3 steps
by 50 percent over each fixed evaluation forecast interval. The horizontal
diffusion filter already scales by physical `dt / tau`, so the continuous-time
diffusion strength should remain close to the incumbent rather than becoming a
new hyperdiffusion experiment. The candidate should keep the DFI time span and
cutoff period in seconds unchanged, so initialization filters the same physical
window with finer internal stepping.

The proposed model name should be
`dinosaur_dfi_surface_residual_weak_hs_600s`.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add a side-by-side factory for
    `dinosaur_dfi_surface_residual_weak_hs_600s`.
- API changes:
  - None. The candidate still returns one deterministic trajectory over the
    existing `WeatherState` channels.
- Tests to update:
  - Add a factory test confirming `inner_step_seconds == 600.0` and all accepted
    incumbent flags remain enabled.
  - Add or extend an inner-step divisibility test confirming common fixed
    forecast step lengths divide cleanly by `600.0`.
  - Add registry and dependency smoke tests for the new model name.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `10m_u_component_of_wind` at medium and long leads if
    the incumbent's remaining error includes numerical phase or amplitude error.
  - Small broad primary-score improvement if the finer step improves multiple
    variables without changing their physical tendencies.
- Expected neutral metrics:
  - `2m_temperature` and `mean_sea_level_pressure` should retain most accepted
    weak-Held-Suarez and near-surface residual gains because those mechanisms
    remain unchanged.
- Possible regressions:
  - The finer step could expose a different balance between the IMEX solver and
    filter applications, producing neutral or slightly worse MSLP/Z500 skill.
  - If the current `900 s` error accidentally damps long-lead wind error, the
    candidate may worsen `10m_u_component_of_wind`.

## Risks

- Numerical stability:
  - Low to moderate. A smaller inner step should not be less stable, but the
    altered interaction with DFI and explicit thermal relaxation must pass the
    fixed fast diagnostics.
- Compute cost:
  - Moderate. Iteration and validation should take roughly 1.5 times the
    incumbent wall-clock for candidate runs. The reported resources and 4-worker
    budget are sufficient, but the Scorer should still supervise runtime.
- Data leakage:
  - Low. The time step is fixed before evaluation and uses no target statistics,
    validation feedback, or golden results.
- Physical plausibility:
  - Moderate. This is a numerical convergence experiment, not new physics. It is
    justified only as one predeclared discretization candidate, not a sweep over
    time-step values.
- Rollback complexity:
  - Low. The implementation is a side-by-side factory and registry entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_600s`.
  - Require finite outputs, `diagnostics.failed=false`, and zero diagnostic
    issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_600s --workers 4`.
  - Support for the hypothesis is a primary-score gain of at least `+0.002`
    versus `dinosaur_dfi_surface_residual_weak_hs` with all fixed RMSE
    guardrails passing.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_600s --workers 4`
    only after iteration promotion.
  - Validation should show at least `+0.001` primary-score gain with clean
    diagnostics and guardrails.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with sub-threshold score movement or any
    early 10 m wind guardrail failure would show that time-step error is not a
    useful remaining lever for this incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  uses `DEFAULT_INNER_STEP_SECONDS = 900.0` and constructs
  `time_integration.imex_rk_sil3` with the nondimensionalized inner step.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements the IMEX SIL3 stepper and applies horizontal diffusion filters with
  a physical `dt / tau` scale.
- Ascher, U. M., Ruuth, S. J., and Spiteri, R. J. 1997. Implicit-explicit
  Runge-Kutta methods for time-dependent partial differential equations.
  Applied Numerical Mathematics, 25, 151-167.
  https://doi.org/10.1016/S0168-9274(97)00056-1
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to
  Geophysics, 2nd ed. Springer, Texts in Applied Mathematics.
  https://doi.org/10.1007/978-1-4419-6412-0
- Courant, R., Friedrichs, K., and Lewy, H. 1928. Uber die partiellen
  Differenzengleichungen der mathematischen Physik. Mathematische Annalen, 100,
  32-74. English translation: IBM Journal of Research and Development, 1967.

## Researcher Notes

This is not a duplicate of `scale-selective-hyperdiffusion`: it does not
increase modal damping or alter the diffusion order, and it explicitly avoids
spending more low-level wind guardrail margin through added drag. It is not a
Held-Suarez variant because the weak thermal forcing coefficients are unchanged.

This proposal is also distinct from DFI, pressure-grid, standard-atmosphere, and
mass-residual experiments. It changes only temporal discretization for the
already accepted model. Because it is a numerical convergence experiment, the
Evaluator should reject any follow-on attempt to sweep multiple time steps inside
the same model-selection round; the proposed `600 s` value is a single bounded
candidate selected for clean divisibility and a conservative 50 percent cost
increase under the current 4-worker resource budget.

## Evaluator Notes

2026-06-16T17:42:01Z - Move to `staging` for Iteration 11 triage against
`dinosaur_dfi_surface_residual_weak_hs` at
`4756cc9a4b69c41eec60e2177fb03a73974f0e2d`.

Ranked recommendation: 2 of 2, plausible follow-up but not the best immediate
candidate.

The proposal is technically implementable and does not change the forecast
contract, target variables, metrics, splits, or deterministic evaluation gates.
The requested `600 s` inner step is a single predeclared convergence candidate,
not a sweep, and the adapter already exposes `inner_step_seconds` with
divisibility checks. The expected source changes would be small and reversible.

Keep staged rather than ready now. The accepted weak-Held-Suarez incumbent
already improved primary scores strongly, but its largest validation guardrail
cost is long-lead `10m_u_component_of_wind` with relative regression
`0.08252957396916741`, leaving limited margin below the 10 percent cap. A
shorter time step changes the whole rollout and filter cadence, so it could
improve numerical phase error but also alter wind amplitude enough to consume
that remaining margin. It also costs roughly 50 percent more scoring time than
the incumbent and has less direct evidence tying the remaining fixed-metric gap
to time-discretization error.

This remains a useful follow-up if the pressure-anchor candidate fails or if
additional read-only diagnostics show coherent phase/amplitude error at medium
and long leads. Any future implementation should keep the value fixed at
`600.0`, preserve DFI, near-surface residual correction, and weak thermal
Held-Suarez relaxation, and avoid turning this into a multi-value time-step
selection experiment.

2026-06-16T18:40:51Z - Move to `ready` for Iteration 12 re-triage against
`dinosaur_dfi_surface_residual_weak_hs` at
`4756cc9a4b69c41eec60e2177fb03a73974f0e2d`.

Ranked recommendation: 1 of 1, selected as the only ready/researchable
proposal after the pressure-anchor candidate was rejected.

The pressure-anchor result changes the ranking in favor of this proposal. That
candidate passed fast diagnostics and all iteration guardrails but moved the
primary score by only `-9.44240674982666e-7`, which is floating-point-scale
evidence that a one-mode mass constraint is too weak for the current incumbent.
It did not expose instability, a protocol issue, or a new dependency that would
block a separate numerical-discretization experiment.

Promote this proposal now because it is side-by-side, forecast-contract
preserving, fixed before evaluation, and implementable with a small adapter,
export, registry, and test surface. The `600.0 s` value remains a single
bounded convergence candidate rather than a sweep, and the current resource
budget is adequate for the expected roughly 50 percent higher scoring cost at
4 workers.

Keep the caveats explicit for the Orchestrator, Implementer, and Scorer. The
accepted weak-Held-Suarez incumbent still has limited long-lead
`10m_u_component_of_wind` guardrail margin, so this candidate must preserve DFI,
near-surface residual correction, and weak thermal Held-Suarez relaxation
unchanged, and it must be rejected before validation if iteration primary
movement is sub-threshold or if any fixed RMSE guardrail fails. No evaluation
protocol, split, metric, or golden gate should be changed for this experiment.
