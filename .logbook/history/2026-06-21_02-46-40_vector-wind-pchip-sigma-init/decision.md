# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5150613366089396`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `+0.0000013649820846950433`
- Validation candidate primary score: not run
- Validation incumbent primary score: not used
- Validation delta: not run

## Rationale

The candidate passed the fast gate and completed the iteration gate with clean diagnostics, but it did not meet the iteration promotion threshold. The measured delta was only `+0.0000013649820846950433`, below the required `+0.002`.

Guardrails were clean. The largest day 1-5 mean RMSE regression by variable was `0.000016140874521350618%`, and the largest variable-lead RMSE regression was `0.001303832769859698%`, both far inside the protocol limits. Because the score threshold failed, validation was intentionally skipped.

## Lessons Learned

- Shape-preserving vector-wind remapping during initialization is stable, but the current formulation is not a meaningful score improvement over the incumbent.
- Initialization-only changes that are nearly identical after DFI need stronger targeting toward known forecast-error modes before they justify another candidate.

## Cleanup Completed

- Candidate code retained or reverted: reverted.
- Research state updated: ready proposal removed after decision.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: clean after rollback.

## Next Action

Continue the optimization loop with a new Researcher/Evaluator iteration.
