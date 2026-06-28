# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.5510108000467965
- Iteration incumbent primary score: -0.532053269893688
- Iteration delta: -0.018957530153108526
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5219023378614627
- Validation delta: not applicable

## Rationale

The candidate passed tests, fast diagnostics, and iteration diagnostics, but it
failed the fixed iteration promotion gates. The primary-score delta was
`-0.018957530153108526`, below the required `+0.002`. The early day-1-through-
day-5 `2m_temperature` mean RMSE regressed by `4.093025532202365%`, exceeding
the `2%` guardrail. The variable-lead guardrail passed, with maximum
`2m_temperature` regression of `4.3973055184362115%` at 48 hours.

Validation was correctly not run. The incumbent iteration and validation
artifacts were reused from the valid leaderboard cache; no incumbent rerun was
performed.

## Lessons Learned

- Seasonal/static-stability modulation of the accepted low-mode `2m_temperature` residual decay worsened the main channel it was intended to improve.
- The incumbent's current scale-separated residual decay is a sensitive part of the accepted solution; extending or shortening it by coarse seasonal/stability gates can degrade early T2m without helping other fixed targets.
- Future near-surface residual proposals should avoid changing the low-mode T2m lifetime unless they include stronger, directly testable safeguards for early day-1-through-day-5 RMSE.

## Cleanup Completed

- Candidate code retained or reverted: reverted after decision.
- Research state updated: selected proposal copied into history and removed from `ready`.
- Leaderboard updated: no; rejected candidates do not update `.logbook/leaderboard.json`.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop by selecting another ready/staged idea or asking
Researcher for fresh proposals if no ready idea remains.
