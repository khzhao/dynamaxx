# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -1.2220957940878374
- Iteration incumbent primary score: -1.2218408656785489
- Iteration delta: -0.0002549284092885351
- Validation candidate primary score: not_run
- Validation incumbent primary score: -1.2103467803549615
- Validation delta: not_run

## Rationale

The candidate passed the fast gate and produced clean iteration diagnostics, but
the fixed iteration primary-score delta was negative and below the required
`+0.002` promotion threshold. Validation was therefore not run.

All fixed iteration guardrails passed. The largest early day 1-5 mean RMSE
regression was `0.0002082206502015146` for 10 m zonal wind, and the largest
variable+lead RMSE regression was `0.0005529361348106701` for 500 hPa
geopotential at 72 hours. The rejection is therefore due to primary-score
degradation, not instability or a guardrail breach.

## Lessons Learned

- The fixed `600.0 s` inner step is stable but slightly worse than the `900.0 s`
  incumbent under the iteration split.
- Remaining error in the current incumbent is unlikely to be improved by a
  simple one-value finer time-step convergence candidate.
- Future time-discretization work should not sweep time steps inside this
  model-selection loop without a separate, reviewed protocol proposal.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the tracked worktree
- Research state updated: ready proposal removed after rejection
- Leaderboard updated: no, rejected candidates do not update the leaderboard
- Git status checked: tracked status clean after rollback

## Next Action

Start the next optimization iteration from
`dinosaur_dfi_surface_residual_weak_hs` as the incumbent and request new
Researcher proposals because the active ready/staging queues are exhausted.
