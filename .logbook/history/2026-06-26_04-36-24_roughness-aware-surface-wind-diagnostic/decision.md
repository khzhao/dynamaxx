# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.21994736458089423
- Iteration incumbent primary score: -0.2197104515448394
- Iteration delta: -0.00023691303605483105
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.21940899263836755
- Validation delta: not run

## Rationale

The roughness-aware 10 m wind diagnostic did not promote from iteration. The
candidate had clean diagnostics and passed both fixed RMSE guardrails, but its
primary score was below the cached incumbent by `-0.00023691303605483105`,
failing the required `+0.002` iteration promotion threshold. Validation was
therefore skipped by protocol.

The incumbent comparison reused the valid leaderboard cache for
`dino_hsl2_mass_dse_wtg_vdse_ramp`; no incumbent evaluation and no golden
evaluation were run. The worst early day 1-5 mean RMSE relative regression was
`0.0007022380855321846` for `10 m zonal wind`, and the worst variable+lead RMSE
relative regression was `0.001214642543237071` for `10 m zonal wind` at 264 h,
both comfortably below their guardrail thresholds. The failure mode was not
instability; it was insufficient and slightly negative aggregate score movement.

## Lessons Learned

- Land-sea roughness adjustment of the 10 m wind output is too narrow and
  slightly harmful against this incumbent under the fixed iteration metric.
- Output-only wind diagnostics can pass safety guardrails while still failing
  to move the aggregate primary score enough for validation.
- Future wind-output proposals need a stronger mechanism than a static
  land-sea roughness proxy, or should be staged behind broader evidence that
  the fixed metric is sensitive enough to the wind channel to justify the cost.

## Cleanup Completed

- Candidate code retained or reverted: reverted via reverse application of
  `candidate.diff`.
- Research state updated: selected ready proposal removed after being copied to
  this immutable history directory.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean; pre-existing untracked `gifs/`
  directory preserved.

## Next Action

Continue the open-ended loop by starting the next Researcher/Evaluator cycle
after confirming the tracked worktree is clean except unrelated pre-existing
untracked files.
