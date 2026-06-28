# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: not_run
- Iteration incumbent primary score: -1.2218408656785489
- Iteration delta: not_run
- Validation candidate primary score: not_run
- Validation incumbent primary score: -1.2103467803549615
- Validation delta: not_run

## Rationale

The candidate failed the fixed fast gate. The fast evaluation command exited 0,
but diagnostics reported `nonfinite_forecast` and `nonfinite_metric`, and the
raw primary score was `-Infinity`. Iteration, validation, and golden were not
run.

The first nonfinite metric records occurred at lead hour 264 for all four target
variables: 2 m temperature, mean sea level pressure, 500 hPa geopotential, and
10 m zonal wind. The result falsifies the bounded ablation before iteration
scoring and confirms that explicit vertical advection is required for stability
in this incumbent configuration.

## Lessons Learned

- Disabling explicit vertical advection destabilizes the current weak-Held-
  Suarez incumbent at long fast leads.
- Future vertical-transport proposals should not simply remove the term; they
  need a separate stabilizing mechanism and should be reviewed as a distinct
  idea before any scoring.
- The current sequence has now rejected conservation-only, time-step,
  damping-style, and vertical-transport ablation candidates after the accepted
  weak-Held-Suarez incumbent.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the tracked worktree
- Research state updated: ready proposal removed after rejection
- Leaderboard updated: no, rejected candidates do not update the leaderboard
- Git status checked: tracked status clean after rollback

## Next Action

Start the next optimization iteration from
`dinosaur_dfi_surface_residual_weak_hs` as the incumbent and request new
Researcher proposals. If no researchable ideas remain after documented search,
record the protocol stop condition.
