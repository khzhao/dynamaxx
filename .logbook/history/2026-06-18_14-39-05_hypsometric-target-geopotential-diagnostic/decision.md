# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.124209610114461`
- Iteration incumbent primary score: `-1.1241936221835356`
- Iteration delta: `-0.00001598793092548894`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1127999773519712`
- Validation delta: not evaluated

## Rationale

The candidate passed registration, tests, fast evaluation, diagnostics, and the
formal RMSE guardrails, but it failed the fixed iteration promotion threshold.
The candidate-minus-incumbent iteration primary delta was
`-0.00001598793092548894`, below the required `+0.002`, so validation was not
run.

The measurement also showed that the output-only geopotential diagnostic moved
the target channel in the wrong direction at early lead. The largest day 1-5
mean RMSE regression was `geopotential_500` at `0.9813979668901341%`, below the
`2%` guardrail but unfavorable. The largest single variable+lead regression was
`geopotential_500` at 24 hours with `7.385768302790055%`, below the `10%`
guardrail but close enough to count as negative evidence for this mechanism.

## Lessons Learned

- Hypsometric target-level geopotential output is not better than the incumbent
  finite sigma-to-pressure interpolation under the fixed iteration protocol.
- Geopotential-only output diagnostics remain fragile; future Z500 proposals
  should avoid changing only the scored output path unless they specifically
  address the 24 h Z500 degradation mode.
- The accepted hydrostatic initialization is still useful, but downstream
  output-only hydrostatic refinements do not automatically preserve the metric
  improvements.

## Cleanup Completed

- Candidate code retained or reverted: reverted from
  `src/dynamaxx/dycore/models/dinosaur/__init__.py`,
  `src/dynamaxx/dycore/models/dinosaur/adapter.py`,
  `src/dynamaxx/dycore/registry.py`,
  `tests/dycore/models/dinosaur/test_dependency.py`,
  `tests/dycore/models/dinosaur/test_primitive_equations.py`, and
  `tests/dycore/test_registry.py`.
- Research state updated: proposal moved to immutable history at
  `.logbook/history/2026-06-18_14-39-05_hypsometric-target-geopotential-diagnostic/`.
- Leaderboard updated: no, rejected candidates do not update the incumbent.
- Git status checked: pending final rollback verification.

## Next Action

Start the next iteration immediately. The user explicitly removed idea-exhaustion
as a stop condition, so the Researcher must continue producing new ideas.
