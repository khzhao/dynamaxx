# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5155611533781376`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `-0.0004984517871132743`
- Validation candidate primary score: not run
- Validation incumbent primary score: not used
- Validation delta: not run

## Rationale

The candidate passed the full test suite, fast gate, and iteration diagnostics,
but it failed the iteration promotion threshold. The primary score regressed by
`-0.0004984517871132743` against the cached incumbent, below the required
`+0.002` iteration delta. Validation was intentionally skipped.

Fixed guardrails did not fail. The largest day-1-through-day-5 mean RMSE
increase was `0.023261464893778377%`, and the largest variable-lead RMSE
increase was `0.14231331515548704%`, both below protocol limits. The decision
is therefore driven by primary-score regression rather than instability.

## Lessons Learned

- The accepted area-weighted theta recentering is empirically better than this
  mass-weighted replacement under the current incumbent stack.
- Mass weighting slightly worsened late 10 m zonal wind RMSE, so future thermal
  zero-mode refinements should avoid assuming pressure-weighted layer moments
  will automatically improve balanced surface and wind diagnostics.
- The incumbent cache was sufficient for comparison; no incumbent rerun was
  needed.

## Cleanup Completed

- Candidate code retained or reverted: reverted after this decision record was written.
- Research state updated: ready proposal removed after preserving it in this history directory.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: completed after rollback.

## Next Action

Continue the optimization loop with a new Researcher/Evaluator iteration.
