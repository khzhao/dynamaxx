# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1325393662110732`
- Iteration incumbent primary score: `-1.1241936221835356`
- Iteration delta: `-0.008345744027537627`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1127999773519712`
- Validation delta: not applicable

## Rationale

The candidate passed the fast sanity gate with clean diagnostics, but failed
the fixed iteration promotion gate. Its iteration primary-score delta was
`-0.008345744027537627`, below the required `+0.002` threshold, so validation
was not run.

Diagnostics and guardrails were clean. No early day 1-5 mean RMSE regression
exceeded `2%`, and no variable+lead RMSE regression exceeded `10%`. Scoring
reported the largest early mean RMSE increase as `2m_temperature` at
`+1.0896092728062252%`, and the largest single variable+lead RMSE increase as
day-1 `geopotential_500` at `+1.1587809049258489%`.

The result indicates that moving the accepted hydrostatic initialization from
pressure-level thicknesses to sigma-native thicknesses disrupted aggregate
skill under the current Strang incumbent despite remaining numerically stable.

## Lessons Learned

- The accepted pressure-level layer-mean hydrostatic initialization remains
  preferable to the sigma-native variant under the fixed iteration gate.
- Hydrostatic initialization refinements can be stable while still degrading the
  primary score; future initialization ideas need a stronger balance argument
  than simply matching the model sigma layers more locally.
- Short-lead `2m_temperature` and day-1 `geopotential_500` are useful warning
  channels for future thermal-initialization proposals.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the six source/test files.
- Research state updated: selected proposal moved from `ready` into this
  history directory; implementation, scores, and scoring notes written locally.
- Leaderboard updated: no, rejected candidate.
- Git status checked: clean tracked worktree after rollback.

## Next Action

Continue the optimization loop with a new Researcher proposal pass and
Evaluator triage against the unchanged incumbent
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang`.
