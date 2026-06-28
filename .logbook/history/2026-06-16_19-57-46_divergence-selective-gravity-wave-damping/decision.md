# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -1.2220454761111341
- Iteration incumbent primary score: -1.2218408656785489
- Iteration delta: -0.00020461043258523937
- Validation candidate primary score: not_run
- Validation incumbent primary score: -1.2103467803549615
- Validation delta: not_run

## Rationale

The candidate passed the fast gate and produced clean iteration diagnostics, but
the fixed iteration primary-score delta was negative and below the required
`+0.002` promotion threshold. Validation was therefore not run.

All fixed iteration guardrails passed. The largest early day 1-5 mean RMSE
regression was `0.00017500547750159967` for 2 m temperature, and the largest
variable+lead RMSE regression was `0.00038858055968793437` for 2 m temperature
at 336 hours. The rejection is due to primary-score degradation, not numerical
instability or a guardrail breach.

## Lessons Learned

- Weak divergence-selective damping is too small or misdirected for the current
  weak-Held-Suarez incumbent under the fixed iteration split.
- The candidate slightly improved early mean 10 m zonal wind RMSE but worsened
  aggregate primary enough to fail promotion.
- Further damping-style proposals should be treated skeptically unless they
  introduce a genuinely different, well-supported mechanism.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the tracked worktree
- Research state updated: ready proposal removed after rejection; staged
  vertical-advection proposal retained
- Leaderboard updated: no, rejected candidates do not update the leaderboard
- Git status checked: tracked status clean after rollback

## Next Action

Start the next optimization iteration from
`dinosaur_dfi_surface_residual_weak_hs` as the incumbent and re-triage the
staged `vertical-advection-suppression` proposal before implementation.
