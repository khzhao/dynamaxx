# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.4270112877010464
- Iteration incumbent primary score: -0.42701187536092744
- Iteration delta: +0.0000005876598810350409
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.417391902036791
- Validation delta: not applicable

## Rationale

The candidate completed the fixed fast and iteration gates with clean diagnostics, but it did not meet the iteration promotion threshold. The required iteration delta is +0.002; the observed delta was only +0.0000005876598810350409 against the cached leaderboard incumbent.

Validation was not run because the protocol allows validation only after the iteration promotion gate passes. The Scorer reused the incumbent iteration metrics from `outputs/eval/iteration_ocean_bulk_sensible_heat_flux.json`; no incumbent rerun was performed.

The RMSE guardrails were clean. Early day 1-5 mean RMSE regressions were all below the 2% limit, and the worst variable+lead RMSE regression was 0.0011088825235142125% for `10m_u_component_of_wind` at 240h, below the 10% limit. The candidate still fails because the primary-score gain is effectively zero.

## Lessons Learned

- A conservative land soil/snow thermal-reservoir tendency is numerically stable but does not materially improve the global fixed iteration score.
- The accepted ocean-bulk incumbent appears hard to beat with weak, local lower-boundary thermal additions unless they change aggregate primary score by more than numerical noise.
- Future proposals should prioritize mechanisms with broader dynamical leverage or a clearer path to primary-score improvement, not another narrow lower-layer thermal reservoir variant.

## Cleanup Completed

- Candidate code retained or reverted: reverted with the saved `candidate.diff`.
- Research state updated: selected ready proposal removed from `.logbook/research/ready`; immutable copy preserved as `proposal.md`.
- Leaderboard updated: no, rejected candidates do not update the incumbent.
- Git status checked: clean after rollback.

## Next Action

Continue the optimization loop with the accepted ocean-bulk sensible heat flux incumbent and generate or triage the next ready idea after cleanup.
