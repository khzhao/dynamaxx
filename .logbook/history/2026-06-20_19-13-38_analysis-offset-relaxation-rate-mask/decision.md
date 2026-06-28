# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5313755627331137`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `-0.016312861142089408`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: not applicable

## Rationale

The candidate passed full tests and produced finite fast and iteration outputs,
but it failed the iteration promotion gate. The primary-score delta was
negative and far below the required `+0.002` threshold.

The guardrails also failed. Day-1-through-day-5 mean RMSE regressed by
`57.31598628733586%` for `2m_temperature` and by `3.232225060994042%` for
`mean_sea_level_pressure`, exceeding the `2%` early-lead limit. The
variable-lead `10%` RMSE guardrail had `48` violations; the worst was
`2m_temperature` at lead hour `240`, with `171.11436565406353%` regression.

Validation was skipped because iteration did not promote. The incumbent was
compared from the valid leaderboard cache; no incumbent evaluation was rerun,
and golden was not run.

## Lessons Learned

- Weakening the weak-HS thermal relaxation rate where the accepted analysis
  offset is large removes too much stabilizing thermal damping.
- The accepted analysis-offset equilibrium should not be interpreted as
  evidence that the local weak-HS rate can be reduced; the equilibrium offset
  improved skill, while the rate mask strongly degraded 2 m temperature and
  pressure-field guardrails.
- Future weak-HS ideas should preserve or add stabilizing tendencies unless
  they have a narrower physical target than offset magnitude alone.
- The scoring cache policy worked as intended: the incumbent iteration artifact
  was reused, validation cache was checked valid but not needed, and no
  incumbent rerun occurred.

## Cleanup Completed

- Candidate code retained or reverted: reverted all source and test changes for
  this experiment.
- Research state updated: removed the consumed ready proposal after copying it
  into this history directory.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop by generating or triaging the next proposal.
