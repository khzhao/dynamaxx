# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: `-0.650884383009584`
- Iteration candidate primary score: `-0.6751099222964386`
- Iteration incumbent primary score: `-0.5719887262109961`
- Iteration delta: `-0.10312119608544257`
- Validation candidate primary score: not run
- Validation incumbent primary score: not run
- Validation delta: not run

## Rationale

The candidate passed the fast gate and produced finite iteration metrics with
zero diagnostic issues, but it failed the iteration promotion gate by a wide
margin. The required primary-score delta is `+0.002`; the measured iteration
delta was `-0.10312119608544257`.

The fixed RMSE guardrails also failed. Early day 1-5 mean RMSE regressed by
`+11.168302602462047%` for `mean_sea_level_pressure` and
`+4.042683689707392%` for `10m_u_component_of_wind`, both above the `2%`
limit. Fourteen variable+lead RMSE regressions exceeded the `10%` limit, led
by `mean_sea_level_pressure` day 14 at `+16.29340937522116%`.

Validation was not run because iteration did not promote. Golden was not run.
The Scorer correctly rejected incumbent cache reuse because the implementation
modified shared incumbent source in `primitive_equations.py` and `adapter.py`
and had an uncommitted registry change. The accepted incumbent iteration
artifacts were snapshotted before rerun and are restored after rejection.

## Lessons Learned

- The theta-form implicit gravity operator remained finite but substantially
  degraded pressure/gravity coupling under the fixed iteration split.
- The harmful signal concentrated in MSLP from days 3 through 15, with an
  additional 10 m zonal wind guardrail violation, so this was not merely a
  harmless thermal-variable relabeling.
- Future theta/implicit followups should be staged only after offline operator
  diagnostics or a narrower matrix change; the current form is too damaging for
  model selection.
- Shared primitive-equation and adapter edits must continue to invalidate
  incumbent metric cache reuse unless immutable pre-change artifacts are
  supplied.

## Cleanup Completed

- Candidate code retained or reverted: reverted.
- Research state updated: implemented proposal retained in immutable history.
- Leaderboard updated: no.
- Incumbent leaderboard artifacts restored: yes, from `cache_snapshots`.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop with a fresh Researcher pass.
