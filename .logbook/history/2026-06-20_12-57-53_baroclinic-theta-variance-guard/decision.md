# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5150640253022584`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `-0.0000013237112340691581`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: not applicable

## Rationale

The candidate failed the fixed iteration promotion gate. Diagnostics were clean, the optional fast gate was clean, and RMSE guardrails showed no early day-1-through-day-5 mean regression over `2%` and no variable-lead regression over `10%`. The primary-score delta was slightly negative and far below the required `+0.002` iteration improvement, so validation was correctly skipped.

The incumbent comparison reused the valid leaderboard cache. No incumbent evaluation and no `golden` run were performed.

## Lessons Learned

- A bounded theta-anomaly variance guard was numerically stable but did not materially change the fixed iteration metrics.
- The current accepted theta mean recentering plus analysis-offset weak-HS equilibrium does not appear limited by abrupt layerwise theta variance loss under this guard formulation.
- Future theta-family proposals need a stronger physical tendency mechanism than post-step variance preservation, or should focus on variables/leads where accepted candidates still show measurable structure.

## Cleanup Completed

- Candidate code retained or reverted: reverted from tracked source and test files.
- Research state updated: consumed ready proposal removed after copying into this history directory.
- Leaderboard updated: no, incumbent unchanged.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration immediately.
