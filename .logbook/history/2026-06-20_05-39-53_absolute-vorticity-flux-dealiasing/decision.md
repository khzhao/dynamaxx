# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5318825727690968`
- Iteration incumbent primary score: `-0.532053269893688`
- Iteration delta: `+0.00017069712459116815`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5219023378614627`
- Validation delta: not applicable

## Rationale

The candidate passed pytest, fast diagnostics, iteration diagnostics, and all fixed RMSE guardrails. The incumbent iteration and validation metrics were reused from `.logbook/leaderboard.json` after cache checks passed; the incumbent was not rerun.

The iteration promotion gate failed because the primary-score delta was only `+0.00017069712459116815`, below the required `+0.002`. Validation was therefore not run. Under the fixed protocol, this candidate cannot replace the incumbent.

## Lessons Learned

- Narrow absolute-vorticity flux product dealiasing is numerically stable but effectively neutral at the accepted incumbent state.
- The clean guardrails indicate the idea is low risk, but the remaining WeatherBench2 error is not materially reduced by this near-truncation product filter.
- Future dealiasing proposals should justify a stronger or more targeted mechanism than this very local vorticity-flux taper, or pivot to a different source of error.

## Cleanup Completed

- Candidate code retained or reverted: reverted after this decision record.
- Research state updated: selected proposal copied to this history directory and removed from `.logbook/research/ready`.
- Leaderboard updated: no.
- Git status checked: yes, after rollback.

## Next Action

Start the next continuous-loop iteration by checking resources/git state and generating or triaging the next ready proposal. The loop remains active.
