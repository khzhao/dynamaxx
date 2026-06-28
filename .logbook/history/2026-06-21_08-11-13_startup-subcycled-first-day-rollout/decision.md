# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5271979435795002`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `-0.012135241988475931`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: not run

## Rationale

The candidate passed full tests, the fast evaluation, and the iteration command
with clean diagnostics, but it failed the fixed iteration promotion gate by a
large margin. The primary-score delta was negative and below the required
`+0.002` threshold.

The fixed early-lead guardrail also failed: day 1-5 mean RMSE for
`mean_sea_level_pressure` regressed by `2.3077781360493983%`, above the `2%`
limit. The worst variable+lead RMSE regression was `mean_sea_level_pressure` at
day 1 with `3.5537493303567578%`, which stayed below the `10%` guardrail, and
diagnostics reported no issues. Validation was skipped because iteration did
not promote.

Incumbent iteration metrics were reused from the valid leaderboard cache; no
incumbent evaluation and no `golden` protocol were run.

## Lessons Learned

- Startup-only subcycling worsened the same early MSLP behavior it was expected
  to improve, so the accepted 900 s first-day balance appears preferable under
  the fixed iteration split.
- The earlier negative full-rollout timestep result was relevant negative
  evidence: localizing the smaller step to day 1 did not recover skill.
- Future time-discretization proposals should need a more specific mechanism
  than reducing early positive-time step size.

## Cleanup Completed

- Candidate code retained or reverted: rejected source/test changes reverted
  from the tracked worktree after saving `candidate.diff`.
- Research state updated: selected ready proposal removed; immutable history
  directory retained.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked status clean after rollback.

## Next Action

Continue the optimization loop by inspecting resources and research state,
then request or triage the next single ready proposal. Keep using valid cached
leaderboard incumbent metrics for candidate comparisons.
