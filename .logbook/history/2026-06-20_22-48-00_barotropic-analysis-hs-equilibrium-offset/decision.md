# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5151407484276682`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `-0.00007804683664391909`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: not applicable

## Rationale

The candidate passed full tests, fast, diagnostics, and both iteration RMSE
guardrails, but it did not improve the incumbent. The iteration delta was
negative and below the required `+0.002` promotion threshold.

No day-1-through-day-5 mean RMSE regression exceeded `2%`, and no
variable-lead RMSE regression exceeded `10%`. The largest relative RMSE
regression was `10m_u_component_of_wind` at day `15`,
`+3.657273076145462%`. Validation was skipped because iteration did not
promote.

The incumbent comparison reused the valid leaderboard iteration artifact; no
incumbent evaluation was rerun, and golden was not run.

## Lessons Learned

- The full vertical structure of the accepted analysis-HS offset remains
  preferable to the tested barotropic projection.
- The immediate analysis-HS projection branch has produced one severe failure
  from rate masking, one clean subthreshold result from lead decay, and one
  clean slightly negative result from barotropic projection. Future analysis-HS
  follow-ups should require a materially stronger mechanism before promotion to
  ready.
- The projection modestly improved early mean MSLP while slightly hurting the
  primary score, so isolated mass-field gains are not enough without broader
  score movement.
- Cached incumbent reuse remained valid and avoided unnecessary baseline
  computation.

## Cleanup Completed

- Candidate code retained or reverted: reverted all source and test changes for
  this experiment.
- Research state updated: removed the consumed ready proposal after copying it
  into this history directory.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop with a fresh Researcher or Evaluator pass.
