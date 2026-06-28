# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5703935108265198`
- Iteration incumbent primary score: `-0.532053269893688`
- Iteration delta: `-0.03834024093283184`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5219023378614627` from cached leaderboard artifact
- Validation delta: not applicable

## Rationale

The candidate passed fast and iteration diagnostics with zero reported issues, but it failed the fixed iteration promotion gate. The required iteration delta is at least `+0.002`; this candidate produced `-0.03834024093283184`.

It also failed an RMSE guardrail: early day 1-5 `2m_temperature` mean RMSE regressed by `+2.265840139901215%`, above the `2%` threshold. The largest variable+lead regression was `10m_u_component_of_wind` at 360 hours with `+4.732425514257608%`, below the `10%` threshold. Validation was not run because iteration did not promote.

The incumbent was not rerun. The scorer reused the valid leaderboard cache after confirming model, commit, artifact readability, finite scores, complete records, and compatible evaluation fingerprint.

## Lessons Learned

- Applying weak Held-Suarez relaxation only to the zonal-mean thermal tendency removes a local correction that the incumbent appears to need.
- The degradation is visible in early `2m_temperature`, so future weak-HS proposals should avoid weakening the local lower-atmosphere thermal correction unless they add a compensating physical mechanism.
- Cache reuse worked as intended: the comparison used accepted incumbent artifacts and did not spend compute rerunning the baseline.

## Cleanup Completed

- Candidate code retained or reverted: reverted after this decision.
- Research state updated: selected ready proposal removed from `.logbook/research/ready`.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the loop by selecting or generating the next ready proposal.
