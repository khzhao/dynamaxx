# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.2616352238490598`
- Iteration incumbent primary score: `-0.2616483974683927`
- Iteration delta: `+0.000013173619332895736`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.2600180396322455` available from cache, not used
- Validation delta: not applicable

## Rationale

The candidate passed focused checks, full repository tests, fast diagnostics,
and the iteration diagnostic and RMSE guardrails. The fixed iteration primary
gate did not pass: the signed primary-score delta was only
`+0.000013173619332895736`, below the required `+0.002` promotion threshold.

Validation was not run because iteration did not promote. Golden was not run.
The incumbent iteration metrics were reused from the leaderboard cache after
the Scorer validated compatibility; no incumbent rerun occurred.

## Lessons Learned

- DSE-consistent horizontal diffusion was stable and essentially neutral, but
  its effect size was far below the fixed promotion threshold.
- Clean guardrails indicate the idea did not create localized RMSE damage; it
  simply did not improve enough.
- The candidate substantially increased iteration wall time due to added DSE
  diagnostics and transforms, so future diffusion ideas should either be
  cheaper or have a stronger expected mechanism.

## Cleanup Completed

- Candidate code retained or reverted: reverted via saved `candidate.diff`.
- Research state updated: selected ready proposal removed after terminal
  rejection.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean; unrelated untracked `gifs/`
  directory preserved.

## Next Action

Continue the optimization loop with the next Researcher/Evaluator cycle.
