# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.8018895586779444`
- Iteration incumbent primary score: `-0.532053269893688`
- Iteration delta: `-0.2698362887842565`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5219023378614627` from cached leaderboard artifact
- Validation delta: not applicable

## Rationale

The candidate passed fast and iteration diagnostics with zero reported issues, and RMSE guardrails did not fail. However, the fixed primary iteration score was much worse than the cached incumbent score. The required promotion threshold is `+0.002`; this candidate produced `-0.2698362887842565`, so validation was not allowed.

The incumbent was not rerun. The leaderboard cache was valid: the requested incumbent matched `.logbook/leaderboard.json`, the metric artifacts existed and were readable, scores were finite, records were complete, and the evaluation fingerprint was compatible.

## Lessons Learned

- CN-RK3 positive-time rollout without the accepted offcentered SIL3 damping is not a useful successor to the current incumbent.
- Solver-family experiments should preserve the stabilizing offcentered mechanism unless the proposal is explicitly testing an equivalent damping or phase-control replacement.
- The primary score can move sharply even when the existing RMSE guardrail summaries are nearly unchanged, so future scorer notes should keep reporting both.

## Cleanup Completed

- Candidate code retained or reverted: reverted after scoring decision.
- Research state updated: selected ready proposal removed from `.logbook/research/ready`.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the loop by selecting or generating the next ready proposal.
