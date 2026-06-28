# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -1.2218418099192239
- Iteration incumbent primary score: -1.2218408656785489
- Iteration delta: -0.000000944240674982666
- Validation candidate primary score: not_run
- Validation incumbent primary score: -1.2103467803549615
- Validation delta: not_run

## Rationale

The candidate passed the fast gate and produced clean iteration diagnostics, but
the fixed iteration primary-score delta was negative and far below the required
`+0.002` promotion threshold. Validation was therefore not run under the
protocol.

All fixed iteration guardrails passed. Early day 1-5 mean RMSE regressions were
near zero for all evaluated variables, and the largest variable+lead RMSE
regression was `0.000003262918195273341` for 500 hPa geopotential at 360 hours.
This indicates the implementation was stable and benign, but the mechanism was
too weak to improve the incumbent.

## Lessons Learned

- Anchoring only the zero-wavenumber `log_surface_pressure` coefficient has
  negligible WeatherBench2 effect for the current weak-Held-Suarez incumbent.
- Future pressure or mass-conservation ideas need a stronger mechanism than one
  global pressure mode, while avoiding spatial pressure-gradient imbalance and
  output-time residual tuning.
- The staged 600 s inner-step proposal remains a plausible follow-up, but it
  should be evaluated as a single fixed candidate because validation-guided
  time-step sweeps would violate the protocol.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the tracked worktree
- Research state updated: ready proposal removed; staged proposal retained
- Leaderboard updated: no, rejected candidates do not update the leaderboard
- Git status checked: tracked status clean after rollback

## Next Action

Start the next optimization iteration from
`dinosaur_dfi_surface_residual_weak_hs` as the incumbent.
