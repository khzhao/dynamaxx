# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.2857361476786912`
- Iteration incumbent primary score: `-0.2616483974683927`
- Iteration delta: `-0.02408775021029852`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.2600180396322455`
- Validation delta: not applicable

## Rationale

The candidate passed the fast sanity gate and full repository tests, and the
iteration diagnostics were clean. It failed the fixed iteration promotion gate:
the primary score delta was `-0.02408775021029852`, below the required `+0.002`
improvement threshold.

The fixed RMSE guardrails also failed. Early days 1-5 mean RMSE regressed by
`8.481852632772549%` for `mean_sea_level_pressure` and
`12.830770258222913%` for `geopotential_500`. The worst individual
variable/lead regressions were `10.0117132850309%` for
`mean_sea_level_pressure` at day 3 and `16.94183102106469%` for
`geopotential_500` at day 1.

Validation was not run because iteration did not promote. Golden was not run.
The incumbent iteration metrics were reused from the leaderboard cache after
the Scorer validated compatibility; no incumbent rerun occurred.

## Lessons Learned

- A direct migrating surface-pressure tide was numerically clean but damaged
  early mass and height fields enough to fail both skill and guardrail gates.
- Fast diagnostics did not expose the iteration degradation, so fast should
  remain a sanity check only.
- Future pressure-related ideas should avoid directly perturbing surface mass
  unless paired with a balanced dynamical response that is evaluated as its own
  ready proposal.

## Cleanup Completed

- Candidate code retained or reverted: reverted via saved `candidate.diff`.
- Research state updated: selected ready proposal removed after terminal
  rejection.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean; unrelated untracked `gifs/`
  directory preserved.

## Next Action

Continue the optimization loop with the next Researcher/Evaluator cycle.
