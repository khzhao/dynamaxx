# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.2673741387223367`
- Iteration incumbent primary score: `-0.26737373217433574`
- Iteration delta: `-0.00000040654800093076204`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.2654819769882763`
- Validation delta: not run

## Rationale

The candidate passed fast diagnostics and completed iteration with clean
diagnostics, but it did not meet the fixed `+0.002` iteration promotion
threshold. The measured primary-score delta was slightly negative at
`-4.0654800093076204e-07`, so validation was not run.

The fixed RMSE guardrails were clean and did not drive the rejection. The worst
day-1-to-5 mean RMSE regression was `mean_sea_level_pressure` at
`0.000008742268421735428%`, far below the 2% limit. The worst variable+lead
RMSE regression was `2m_temperature` at 336 hours with `0.00018122650088975333%`,
far below the 10% limit.

Incumbent iteration metrics were reused from the accepted leaderboard cache at
`outputs/eval/iteration_dino_hsl2_theta_dse_hsl.json` and `.csv`. The incumbent
was not rerun. Candidate source edits did not invalidate the accepted cache.

## Lessons Learned

- Adding humidity through guarded MSE transport was stable but effectively
  neutral relative to the accepted dry-static-energy HSL transport.
- The accepted DSE-HSL gain appears to come from hydrostatic thermal transport
  consistency rather than from latent-energy information in passive humidity.
- Future humidity proposals should probably change a more complete moist
  process or tracer coupling, not just the horizontally transported thermal
  invariant.

## Cleanup Completed

- Candidate code retained or reverted: reverted after decision using the saved
  candidate diff.
- Research state updated: selected ready proposal removed after scoring.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: pending rollback verification.

## Next Action

Start the next continuous-loop iteration immediately after rollback is verified.
