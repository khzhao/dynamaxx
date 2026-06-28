# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5191155612061304`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `-0.0040528596151061524`
- Validation candidate primary score: not run
- Validation incumbent primary score: not used
- Validation delta: not run

## Rationale

The candidate completed full tests, fast, and iteration with clean diagnostics, but the iteration primary score regressed by `-0.0040528596151061524` against the cached incumbent. This fails the `+0.002` iteration promotion threshold, so validation was intentionally skipped.

Fixed guardrails did not fail. The largest day 1-5 mean RMSE increase was `0.12843851494942854%`, and the largest variable-lead RMSE increase was `0.7481300673656195%`, both below protocol limits. The decision is therefore driven by primary-score regression rather than instability.

## Lessons Learned

- The accepted analysis-offset Held-Suarez equilibrium benefits from using local evolving surface pressure in the weak thermal target.
- Future Held-Suarez variants should avoid removing that local pressure coupling unless new diagnostics show a specific mass-error feedback.

## Cleanup Completed

- Candidate code retained or reverted: reverted.
- Research state updated: ready proposal removed after decision.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: clean after rollback.

## Next Action

Continue the optimization loop with a new Researcher/Evaluator iteration.
