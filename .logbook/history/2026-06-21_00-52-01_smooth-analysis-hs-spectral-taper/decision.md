# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5146503692452032`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `+0.0004123323458210537`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: not applicable

## Rationale

The candidate passed the full test suite, `fast`, and `iteration` with clean
diagnostics, but it did not clear the fixed iteration promotion threshold. The
primary-score delta was positive but only `+0.0004123323458210537`, below the
required `+0.002`, so validation was correctly skipped.

The fixed RMSE guardrails were clean. No day-1-through-day-5 mean RMSE
regression exceeded `2%`, and no variable-lead RMSE regression exceeded `10%`.
The worst variable-lead RMSE change was still a slight improvement:
`2 m temperature` at lead hour `336`, with `-0.001352936492160675%`
relative RMSE change.

The incumbent comparison reused the valid leaderboard cache. No incumbent
evaluation was rerun, and `golden` was not run.

## Lessons Learned

- Smoothing the accepted analysis-HS horizontal spectral mask is numerically
  safe and produces broad but very small RMSE improvements.
- The hard cutoff in the accepted analysis-HS equilibrium is probably not a
  large remaining error source under the fixed iteration protocol.
- Future analysis-HS follow-ups should require a larger physical difference
  than smoothing the mask edge, because several small variants are now clean
  but subthreshold.

## Cleanup Completed

- Candidate code retained or reverted: reverted source and test changes after this decision.
- Research state updated: consumed ready proposal removed after copying into history.
- Leaderboard updated: no; rejected candidates do not update `.logbook/leaderboard.json`.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop by selecting a staged model-selection idea or
asking Researcher for fresh proposals if no ready model-selection idea remains.
