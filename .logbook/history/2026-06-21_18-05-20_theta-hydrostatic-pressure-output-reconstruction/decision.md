# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.5291823004046923
- Iteration incumbent primary score: -0.5150627015910243
- Iteration delta: -0.014119598813667977
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5044433981077879
- Validation delta: not applicable

## Rationale

The candidate completed fast and iteration scoring with clean diagnostics, but
it failed the primary iteration promotion gate. The required
candidate-minus-incumbent iteration delta is at least `+0.002`; the measured
delta was `-0.014119598813667977` against the accepted incumbent cache.

RMSE guardrails were clean. The early day 1-5 mean RMSE regressions were far
below the `2%` threshold for all target variables, and the worst variable-lead
RMSE regression was `2 m temperature` at 96 hours with a `3.0959957598042456e-07%`
increase, far below the `10%` guardrail. Validation was skipped because the
candidate did not promote from iteration.

The incumbent iteration metrics were reused from the valid leaderboard cache.
No incumbent evaluation was rerun.

## Lessons Learned

- Coupled theta-based pressure-level temperature output reconstruction is stable
  but harms the fixed iteration primary score for the current incumbent.
- The output-level consistency gap targeted by this proposal is not a useful
  remaining score source under the fixed WeatherBench2 iteration gate.
- Future pressure-level output reconstruction proposals should be treated as
  exhausted unless they provide stronger read-only evidence or a distinct
  mechanism beyond theta/hydrostatic resampling.

## Cleanup Completed

- Candidate code retained or reverted: reverted after preserving `candidate.diff`.
- Research state updated: selected ready proposal removed from `.logbook/research/ready` after archival in history.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes; tracked source/test worktree was clean after rollback.

## Next Action

Continue the open-ended optimization loop with a fresh resource and git-state
check, then generate or select the next proposal.
