# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.4270088457239165
- Iteration incumbent primary score: -0.42701187536092744
- Iteration delta: +0.0000030296370109317294
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.417391902036791
- Validation delta: not applicable

## Rationale

The candidate completed the fixed fast and iteration gates with clean diagnostics, but it did not meet the iteration promotion threshold. The required iteration delta is +0.002; the observed delta was only +0.0000030296370109317294 against the cached leaderboard incumbent.

Validation was not run because the protocol allows validation only after the iteration promotion gate passes. The Scorer reused the incumbent iteration metrics from `outputs/eval/iteration_ocean_bulk_sensible_heat_flux.json` and did not rerun the incumbent.

The RMSE guardrails were clean: the early day 1-5 mean RMSE regression was 1.5843645488412374e-07, and the worst variable+lead RMSE regression was 7.396900136200324e-06 for `10m_u_component_of_wind` at 192h. These guardrails were not enough to promote the candidate because the primary-score gate failed.

## Lessons Learned

- Replacing the ocean bulk heat-flux anchor with SST and sea-ice weighting produced a nearly neutral score movement rather than a meaningful improvement.
- Future near-surface flux proposals should avoid adding boundary-condition complexity unless the mechanism has a stronger expected primary-score effect than this nearly zero delta.
- Short candidate registry aliases prevented the prior long-filename metric-write anomaly; `dino_obulk_sstice` wrote standard candidate metrics successfully.

## Cleanup Completed

- Candidate code retained or reverted: reverted with the saved `candidate.diff`.
- Research state updated: selected ready proposal removed from `.logbook/research/ready`; immutable copy preserved as `proposal.md`.
- Leaderboard updated: no, rejected candidates do not update the incumbent.
- Git status checked: clean after rollback.

## Next Action

Continue the optimization loop with the accepted ocean-bulk sensible heat flux incumbent and select the next ready idea after cleanup.
