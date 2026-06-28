# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.5312654903142987
- Iteration incumbent primary score: -0.532053269893688
- Iteration delta: +0.0007877795793892473
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5219023378614627
- Validation delta: not applicable

## Rationale

The candidate passed unit tests, fast diagnostics, and iteration diagnostics,
and it violated no fixed RMSE guardrails. However, the iteration primary-score
delta was only `+0.0007877795793892473`, below the required `+0.002`
promotion threshold. Validation was therefore correctly gated off.

The incumbent comparison reused the valid leaderboard cache for iteration. The
incumbent was not rerun.

## Lessons Learned

- Low-mode mass diagnostic residual memory is numerically clean and slightly positive, but too weak to justify promotion over the current scale-separated surface-residual incumbent.
- The mass-field improvements were not large enough to offset the fixed aggregate threshold, even though early mass RMSE moved in the intended direction.
- Future mass-diagnostic proposals need a stronger mechanism than output-only low-mode lead-zero residual carryover, or should target a different remaining error source.

## Cleanup Completed

- Candidate code retained or reverted: reverted after decision.
- Research state updated: selected proposal copied into history and removed from `ready`.
- Leaderboard updated: no; rejected candidates do not update `.logbook/leaderboard.json`.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop by selecting another ready/staged idea or asking
Researcher for fresh proposals if no ready idea remains.
