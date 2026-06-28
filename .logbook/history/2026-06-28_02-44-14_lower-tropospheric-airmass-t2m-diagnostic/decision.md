# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.2527670042476971
- Iteration incumbent primary score: -0.21299732605547173
- Iteration delta: -0.03976967819222538
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.21274255459898536
- Validation delta: not run

## Rationale

The candidate passed implementation tests, full pytest, fast evaluation, and
iteration diagnostics, but it failed the fixed iteration promotion gate. The
primary-score delta was negative by -0.03976967819222538, far below the
required positive promotion threshold.

The regression was scientifically targeted but harmful: T2m mean skill moved by
-0.07953923723642987 and early lead T2m RMSE increased by 0.16351594393167757 K
on average. The largest T2m RMSE regression was 0.6870379845394492 K at 144 h.
Non-T2m fields remained effectively unchanged, so the rejection is attributable
to the selected T2m air-mass adjustment rather than unrelated channel drift.

Validation was not run because the iteration gate did not promote. The
leaderboard remains unchanged.

## Lessons Learned

- The forecast lower-tropospheric temperature anomaly is not a useful simple final-output screen-temperature correction on top of the accepted RI2m and residual-memory paths.
- Final-output T2m blends are now low-priority unless a future proposal first demonstrates a stronger read-only diagnostic or introduces actual lower-boundary physics.
- The implementation strategy successfully isolated non-T2m channels, which makes the failed hypothesis easy to interpret.

## Cleanup Completed

- Candidate code retained or reverted: reverted after history creation.
- Research state updated: ready proposal moved into this history directory.
- Leaderboard updated: no; rejected candidates do not update leaderboard.
- Git status checked: yes; only the pre-existing untracked gifs/ directory remains.

## Next Action

Start the next continuous-loop iteration after rollback leaves only the
pre-existing untracked gifs/ directory.
