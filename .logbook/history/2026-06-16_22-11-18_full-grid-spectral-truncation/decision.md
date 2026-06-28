# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: not_run
- Iteration incumbent primary score: -1.2218408656785489
- Iteration delta: not_run
- Validation candidate primary score: not_run
- Validation incumbent primary score: -1.2103467803549615
- Validation delta: not_run

## Rationale

The candidate failed the fixed fast gate. The fast evaluation command exited 0,
but diagnostics reported `nonfinite_forecast` and `nonfinite_metric`, and the
raw primary score was `-Infinity`. Iteration, validation, and golden were not
run.

Every exact-filtered candidate metric row contained nonfinite fields, beginning
at the first scored lead of 24 hours for all four target variables. This shows
that fixed T120 truncation is unstable when combined with the incumbent time
step, filters, and forcing setup. A bounded revision would require a separate
stabilizing idea rather than the selected resolution-only experiment.

## Lessons Learned

- Raising truncation to T120 without changing stability controls fails the fast
  gate immediately.
- Future resolution proposals need an explicit stability mechanism and should
  be reviewed as new proposals before evaluation.
- The active research queues are exhausted after this rejection.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the tracked worktree
- Research state updated: ready proposal removed after rejection
- Leaderboard updated: no, rejected candidates do not update the leaderboard
- Git status checked: tracked status clean after rollback

## Next Action

Start the next optimization iteration from
`dinosaur_dfi_surface_residual_weak_hs` as the incumbent and request a new
Researcher pass. If no defensible ideas remain after documented search, record
the no-researchable-ideas stop condition.
