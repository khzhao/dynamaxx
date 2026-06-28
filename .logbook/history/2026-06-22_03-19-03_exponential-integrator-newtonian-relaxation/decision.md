# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.49861953482554927`
- Iteration incumbent primary score: `-0.49843977504709575`
- Iteration delta: `-0.00017975977845352542`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.48771725322193726`
- Validation delta: not run

## Rationale

The candidate failed the fixed iteration promotion gate. The required iteration
primary-score delta is at least `+0.002`; this candidate scored
`-0.00017975977845352542` below the cached incumbent. Candidate iteration
completed with clean diagnostics and passed the fixed RMSE guardrails, but the
primary-score gate did not promote it to validation.

Incumbent iteration metrics were reused from `.logbook/leaderboard.json`; no
incumbent evaluation command was run. Candidate validation and `golden` were
not run.

## Lessons Learned

- Exact exponential integration of the weak-HS thermal relaxation was
  numerically clean but did not improve the fixed iteration primary score.
- The RMSE guardrail movement was near numerical noise, suggesting the current
  explicit treatment is already sufficiently resolved for this accepted
  incumbent configuration.
- Future relaxation-forcing proposals should change the physical target or
  coupling mechanism, not only the local integration of the existing weak-HS
  term.

## Cleanup Completed

- Candidate code retained or reverted: reverted with the saved candidate diff.
- Research state updated: consumed ready proposal removed after copying into
  this history directory.
- Leaderboard updated: unchanged because the candidate was rejected.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration immediately.
