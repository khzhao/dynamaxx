# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.6992577344425344
- Iteration incumbent primary score: -0.532053269893688
- Iteration delta: -0.1672044645488464
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5219023378614627
- Validation delta: not applicable

## Rationale

The candidate passed tests and completed fast and iteration with clean
diagnostics, but it failed the fixed iteration gate by a wide margin. The
primary-score delta was `-0.1672044645488464`, below the required `+0.002`.
It also failed guardrails: day-1-through-day-5 mean `2m_temperature` RMSE
regressed by `62.79058980554264%`, and the largest variable-lead regression was
`2m_temperature` at 24 hours with `113.24920750881391%` higher RMSE than the
incumbent.

Validation was correctly not run. The incumbent iteration comparison reused the
valid leaderboard cache; no incumbent rerun was performed.

## Lessons Learned

- The accepted low-mode near-surface residual appears to be geographically anchored or otherwise unsafe to advect with the simple forecast-flow proxy.
- Flow-following low-mode residual phase produced immediate, severe 2 m temperature error despite finite diagnostics.
- Future residual-memory ideas should avoid moving the accepted 2 m temperature low-mode residual spatially without a much stronger land/air-mass separation mechanism.

## Cleanup Completed

- Candidate code retained or reverted: reverted after decision.
- Research state updated: selected proposal copied into history and removed from `ready`.
- Leaderboard updated: no; rejected candidates do not update `.logbook/leaderboard.json`.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop by selecting another ready/staged idea or asking
Researcher for fresh proposals if no ready idea remains.
