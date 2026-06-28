# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1242117369530207`
- Iteration incumbent primary score: `-1.1241936221835356`
- Iteration delta: `-0.000018114769485100268`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1127999773519712`
- Validation delta: not evaluated

## Rationale

The candidate passed registration, full tests, fast evaluation, diagnostics, and
RMSE guardrails, but failed the required iteration promotion threshold. The
candidate-minus-incumbent iteration primary delta was
`-0.000018114769485100268`, below the required `+0.002`, so validation was not
run under the fixed protocol.

Guardrail checks were clean. The largest early day 1-5 mean RMSE regression was
`10m_u_component_of_wind` at `0.02377748010882197%`, below the `2%` guardrail.
The largest single variable+lead RMSE regression was also
`10m_u_component_of_wind` at 48 hours with `0.02827308327868483%`, below the
`10%` guardrail.

## Lessons Learned

- Splitting the existing rollout horizontal diffusion into symmetric half steps
  produced only numerical-scale movement and a slight primary-score regression.
- Future diffusion-ordering proposals need a larger physical or numerical
  behavioral change than pure half-step placement around the same dynamics.
- Scoring utilities should filter raw CSV rows by exact `model_name`; evaluation
  CSVs also include persistence baseline rows.

## Cleanup Completed

- Candidate code retained or reverted: reverted from
  `src/dynamaxx/dycore/models/dinosaur/__init__.py`,
  `src/dynamaxx/dycore/models/dinosaur/adapter.py`,
  `src/dynamaxx/dycore/registry.py`,
  `tests/dycore/models/dinosaur/test_dependency.py`,
  `tests/dycore/models/dinosaur/test_primitive_equations.py`, and
  `tests/dycore/test_registry.py`.
- Research state updated: proposal moved to immutable history at
  `.logbook/history/2026-06-18_13-26-11_symmetric-horizontal-diffusion-split/`.
- Leaderboard updated: no, rejected candidates do not update the incumbent.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next iteration immediately. The user explicitly removed idea-exhaustion
as a stop condition, so the Researcher must continue producing new ideas.
