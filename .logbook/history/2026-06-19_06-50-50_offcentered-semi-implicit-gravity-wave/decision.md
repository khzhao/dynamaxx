# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.5719873627530224`
- Iteration incumbent primary score: `-0.8309027246148776`
- Iteration delta: `+0.25891536186185515`
- Validation candidate primary score: `-0.562579968224105`
- Validation incumbent primary score: `-0.8148384940015672`
- Validation delta: `+0.2522585257774621`

## Rationale

The candidate passed the fixed protocol gates. Iteration improved by
`+0.25891536186185515`, above the required `+0.002`, with clean diagnostics and
no RMSE guardrail violations. Validation improved by `+0.2522585257774621`,
above the required `+0.001`, also with clean diagnostics and no RMSE guardrail
violations.

Early day-1-through-day-5 mean RMSE improved on both scored protocols. The
largest positive variable-by-lead RMSE regression was late `2m_temperature`:
`+3.789818%` at day 15 on iteration and `+3.583942%` at day 15 on validation,
both below the `+10%` guardrail. The largest improvements were in late mass
fields, especially `mean_sea_level_pressure` near day 15.

The Scorer rejected leaderboard incumbent cache reuse because this candidate
modified shared `time_integration.py`, which the incumbent also imports. The
incumbent iteration and validation comparisons were recomputed with `--restart`
and `cached=0`, so the accepted deltas are direct comparisons under the same
current source state.

Accepted source/test changes were committed as
`54375ce2994827fcc2dfe09ce0df3924cbaa6c75`.

## Lessons Learned

- Off-centering the SIL3 implicit treatment is a high-signal improvement for
  this incumbent, consistent with the hypothesis that fast-mode/mass-field
  imbalance was a major remaining error source.
- Shared-source experiments must force incumbent reruns with `--restart`; a
  non-restart command may report all chunks cached and is not sufficient for
  cache validity.
- Future proposals can build on this accepted time-discretization baseline, but
  should avoid changing fixed evaluation protocols or treating the fast gate as
  a selection metric.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed in
  `54375ce2994827fcc2dfe09ce0df3924cbaa6c75`.
- Research state updated: selected proposal frozen in this history directory
  with implementation and scoring records.
- Leaderboard updated: yes, new incumbent is the off-centered SIL3 candidate.
- Git status checked: tracked worktree clean after commit and leaderboard
  update.

## Next Action

Start the next continuous-loop iteration with a fresh Researcher proposal set.
