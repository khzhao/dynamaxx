# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1286185780501627`
- Iteration incumbent primary score: `-1.1241936221835356`
- Iteration delta: `-0.004424955866627167`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1127999773519712`
- Validation delta: not available

## Rationale

The candidate did not meet the fixed iteration promotion gate. Its iteration
primary-score delta was negative, below the required `+0.002` threshold.
Diagnostics were clean with zero issues, and the early day 1-5 mean RMSE
guardrail passed with only `+0.012352086364009196%` relative change. However,
the per-variable+lead guardrail failed: `10m_u_component_of_wind` day 1 RMSE
regressed by `+12.310765318969419%`, exceeding the allowed `+10%` limit.

Validation was skipped according to protocol because the candidate did not
promote from iteration.

## Lessons Learned

- Rotating the accepted near-surface zonal-wind residual by local inertial
  phase worsened early `10m_u_component_of_wind`, especially day 1.
- The accepted fixed-component residual appears more consistent with a
  stationary zonal bias correction than an inertially rotating ageostrophic
  residual under the fixed WeatherBench2 target.
- The output-only implementation did not materially disturb mass-field metrics,
  so future output-diagnostic proposals can remain viable if they avoid
  degrading early wind leads.

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
