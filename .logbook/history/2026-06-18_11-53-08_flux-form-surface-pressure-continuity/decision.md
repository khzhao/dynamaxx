# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.139320455742976`
- Iteration incumbent primary score: `-1.1241936221835356`
- Iteration delta: `-0.015126833559440334`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1127999773519712`
- Validation delta: not run

## Rationale

The candidate passed the fast sanity gate and produced finite, diagnostically
clean iteration metrics, but it failed the fixed iteration promotion threshold.
The protocol requires the candidate iteration primary score to improve over the
incumbent by at least `+0.002`; this candidate regressed by
`-0.015126833559440334`.

Validation was not run because the iteration gate failed. The raw metric
comparisons were filtered by evaluated `model_name` to exclude persistence rows.
No early day-1-through-day-5 mean RMSE regression exceeded the `2%` guardrail,
and no variable-by-lead RMSE regression exceeded the `10%` guardrail. The
scientific failure was broad primary-score degradation rather than a localized
diagnostic instability or guardrail spike.

The result suggests that forcing the incumbent semi-implicit sigma-coordinate
surface-pressure evolution toward this local flux-form product-rule correction
does not improve the accepted Strang-Coriolis model's balanced rollout. The
clean diagnostics indicate the implementation was numerically stable, but the
mass-continuity correction worsened the fixed WeatherBench2 iteration score.

## Lessons Learned

- A local flux-form log-surface-pressure continuity correction is not a useful
  next step for this incumbent despite being physically plausible and
  diagnostically clean.
- Future pressure/mass-continuity proposals should avoid simply replacing the
  rollout product-rule balance unless they also address the pressure-gradient
  and semi-implicit balance that the current incumbent appears to rely on.
- Clean guardrails are not sufficient for promotion; primary-score movement
  remained clearly negative across the fixed iteration split.

## Cleanup Completed

- Candidate code retained or reverted: reverted all source and test changes from
  this experiment.
- Research state updated: selected proposal remains archived in this history
  directory with implementation, scores, scoring notes, and decision records.
- Leaderboard updated: no.
- Git status checked: yes, `git status --short` was empty after rollback.

## Next Action

Start the next iteration immediately. The user explicitly requested continuous
idea generation without an idea-exhaustion stop condition.
