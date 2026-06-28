# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.5149908273392567
- Iteration incumbent primary score: -0.5150627015910243
- Iteration delta: 7.187425176757856e-05
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5044433981077879 cached, verified
- Validation delta: not computed

## Rationale

The candidate passed fast and iteration diagnostics with zero issues, and the
fixed RMSE guardrails were clean. It improved early `10 m zonal wind` mean RMSE
from `4.761812121930365` to `4.75835582429845`, but the primary iteration score
gain was only `+7.187425176757856e-05`, below the fixed `+0.002` promotion
threshold. Validation was therefore correctly skipped.

Incumbent iteration and validation metrics were reused from the valid
leaderboard cache. No incumbent evaluation command was run, and candidate
source edits were not treated as cache invalidation.

## Lessons Learned

- A one-channel coherence gate can improve early wind RMSE slightly without
  destabilizing mass or thermal fields, but the primary-score effect is too
  small for promotion.
- Future residual-memory ideas need more primary-score leverage than a bounded
  u10-only damping gate.
- The cache reuse policy again avoided unnecessary incumbent scoring while
  preserving a valid comparison.

## Cleanup Completed

- Candidate code retained or reverted: reverted after preserving
  `candidate.diff`.
- Research state updated: selected ready proposal removed from
  `.logbook/research/ready`.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Start the next continuous-loop iteration with a fresh resource, git, logbook,
and incumbent-cache check.
