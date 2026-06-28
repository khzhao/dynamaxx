# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-Infinity`
- Iteration incumbent primary score: `-0.8308832822743712`
- Iteration delta: `-Infinity`
- Validation candidate primary score: not run
- Validation incumbent primary score: not run
- Validation delta: not applicable

## Rationale

The candidate passed unit tests and the fast sanity gate, but failed the fixed
iteration gate. The iteration command exited `0`, while the metrics reported
`failed=True`, six diagnostic issues, and a nonfinite primary score. The issues
were five `nonfinite_forecast` errors and one `nonfinite_metric` error.

The acceptance gates failed on every material criterion after fast:

- Primary-score delta was `-Infinity`, below the required `+0.002`.
- Early day-1-through-day-5 mean RMSE guardrail failed with regressions of
  `+8.6718%` for `10m_u_component_of_wind`, `+7.8460%` for
  `geopotential_500`, and `+2.2718%` for `mean_sea_level_pressure`.
- Variable-by-lead RMSE guardrail failed with finite violations at
  `10m_u_component_of_wind` day 4 (`+10.6240%`), `geopotential_500` day 5
  (`+14.0274%`), and `10m_u_component_of_wind` day 5 (`+14.6491%`).
- Forty candidate model metric rows were nonfinite for all four target
  variables from lead days 6 through 15.

Validation was not run because the iteration promotion gate failed. Golden was
not run.

The Scorer reused incumbent iteration metrics from `.logbook/leaderboard.json`
after verifying the incumbent model, evaluation fingerprint, readable finite
artifact, and side-by-side candidate registration. The incumbent was still
compared against the candidate; only the incumbent rerun was skipped under the
cache-reuse rule.

## Lessons Learned

- Fast is not sufficient for stronger recentering filters in this family; this
  candidate passed fast but became nonfinite during iteration.
- Latitude-by-latitude zonal theta preservation is too aggressive for the
  current incumbent, destabilizing wind, geopotential, and pressure despite an
  early `2m_temperature` improvement.
- Future theta-followup ideas should avoid exact zonal-mean preservation and
  prefer weaker, globally constrained or energy-aware mechanisms.

## Cleanup Completed

- Candidate code retained or reverted: reverted after scoring.
- Research state updated: selected proposal remains frozen in this history
  directory with implementation and scoring records.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration with a fresh Researcher proposal set.
