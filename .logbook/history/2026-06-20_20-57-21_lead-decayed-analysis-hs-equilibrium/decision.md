# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.514816113028215`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `+0.0002465885628093467`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: not applicable

## Rationale

The candidate was numerically clean and slightly better than the incumbent on
iteration, but the improvement did not meet the fixed promotion threshold. The
iteration delta was `+0.0002465885628093467`, below the required `+0.002`.

Diagnostics were clean and both RMSE guardrails passed. No day-1-through-day-5
mean RMSE regression exceeded `2%`, and no variable-lead RMSE regression
exceeded `10%`. The largest relative RMSE regression was
`10m_u_component_of_wind` at day `15`, `+2.9583314085064374%`.

Validation was skipped because the iteration gate did not promote. The
incumbent comparison reused the valid leaderboard iteration artifact; no
incumbent evaluation was rerun, and golden was not run.

## Lessons Learned

- Decaying the accepted analysis-HS equilibrium offset is much safer than
  weakening the weak-HS relaxation rate, but the measured gain is too small for
  promotion.
- The constant accepted analysis-HS offset remains close to optimal under the
  fixed iteration protocol; future follow-ups should need a stronger physical
  change than a simple 10-day offset taper.
- Clean subthreshold candidates should be rejected without validation to avoid
  validation-driven tuning.
- Incumbent cache reuse worked as intended: iteration comparison used the
  leaderboard artifact, and validation cache was checked but not used.

## Cleanup Completed

- Candidate code retained or reverted: reverted all source and test changes for
  this experiment.
- Research state updated: removed the consumed ready proposal after copying it
  into this history directory.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop with a fresh Researcher or Evaluator pass.
