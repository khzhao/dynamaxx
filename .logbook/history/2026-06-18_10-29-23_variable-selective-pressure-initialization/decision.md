# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1293266929843402`
- Iteration incumbent primary score: `-1.1241936221835356`
- Iteration delta: `-0.005133070800804607`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1127999773519712`
- Validation delta: not available

## Rationale

The candidate passed fixed pytest and fast sanity checks with clean diagnostics,
then failed the fixed iteration promotion gate. Its primary-score delta was
`-0.005133070800804607`, below the required `+0.002` threshold.

Diagnostics were clean with zero issues. RMSE guardrails also passed: the
overall early day 1-5 mean RMSE regression was `+0.28756168845514457%`, the
worst early per-variable mean regression was `geopotential_500` at
`+0.3729611246919541%`, and no variable+lead RMSE regression exceeded `+10%`.
The worst variable+lead regression was `geopotential_500` day 1 at
`+1.2101187234468025%`.

Validation was skipped according to protocol because the candidate did not
promote from iteration.

## Lessons Learned

- Pressure-linear scalar initialization was worse than the accepted all-log-p
  initialization for this Strang incumbent.
- The result broadly degraded target RMSE in iteration; no target variable and
  lead improved over the incumbent.
- Future initialization proposals should preserve the accepted all-log-pressure
  remap unless they introduce a stronger balance mechanism than variable family
  grouping.

## Cleanup Completed

- Candidate code retained or reverted: reverted the six source/test files
  changed by this experiment.
- Research state updated: selected proposal is preserved in this immutable
  history directory.
- Leaderboard updated: no; rejected candidates do not update the incumbent.
- Git status checked: yes; `git status --short` was empty after rollback.

## Next Action

Report the rejected iteration and start the next continuous-loop
research/evaluation pass.
