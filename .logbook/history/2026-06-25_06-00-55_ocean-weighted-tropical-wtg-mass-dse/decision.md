# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: `-0.26067780143152963`
- Iteration candidate primary score: `-0.2593525084992675`
- Iteration incumbent primary score: `-0.25851235493825614`
- Iteration delta: `-0.0008401535610113586`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.25704033104116597` available from
  cache, not used
- Validation delta: not applicable

## Rationale

The candidate passed the full repository test gate, fast sanity gate, and
iteration diagnostics. Fast and iteration both reported `failed=False` and
`issues=0`.

The candidate failed the fixed iteration promotion gate. Its iteration primary
score was `-0.2593525084992675`, below the cached incumbent score
`-0.25851235493825614`, for a signed delta of
`-0.0008401535610113586`. This is below the required `+0.002` promotion
threshold, so validation was correctly skipped. Golden was not run.

The fixed RMSE guardrails passed. The worst early day-1-to-5 mean RMSE
regression was `+0.122777%` for `10m_u_component_of_wind`, below the `2%`
limit. The worst single variable-and-lead RMSE regression was
`10m_u_component_of_wind` at `360` hours with `+0.435032%`, below the `10%`
limit.

The Scorer reused cached incumbent iteration metrics from
`.logbook/leaderboard.json` after validating cache compatibility. No incumbent
rerun occurred. The cached validation artifact was also checked as available and
valid, but it was not used because validation was skipped.

## Lessons Learned

- Restricting the accepted WTG relaxation to ocean-weighted tropical columns
  weakened the accepted incumbent rather than improving it.
- Early RMSE changes were small and guardrail-clean, so this was not a
  numerical stability failure. The signal is that the accepted WTG gain likely
  depends on tropical land and Maritime Continent columns as well as ocean
  columns.
- Future WTG follow-ups should avoid simply narrowing the spatial support of
  the accepted operator unless they add a stronger compensating mechanism.

## Cleanup Completed

- Candidate code retained or reverted: reverted using the saved
  `candidate.diff`.
- Research state updated: selected ready proposal removed after terminal
  rejection.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: pending final cleanup check.

## Next Action

Clean the tracked worktree, then continue the optimization loop with the next
Researcher/Evaluator cycle.
