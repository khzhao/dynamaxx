# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5230417460160705`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `-0.007979044425046156`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: not applicable

## Rationale

The candidate failed the fixed iteration promotion gate. Fast and iteration completed with clean diagnostics, but the primary score regressed by `-0.007979044425046156` and the early day-1-through-day-5 mean RMSE guardrail failed for `10m_u_component_of_wind` with a `3.152849%` regression. The max variable-lead RMSE regression was `3.787733%`, below the `10%` guardrail, but the primary-score and early-wind guardrail failures are sufficient for rejection.

The incumbent comparison reused the valid leaderboard cache. No incumbent evaluation and no `golden` run were performed. Validation was correctly skipped because the iteration gate did not pass.

## Lessons Learned

- A same-direction curvature-aware 10 m wind diagnostic was not conservative enough at early leads and worsened the target variable it aimed to improve.
- Future 10 m wind diagnostics should avoid broad day-1 activation and need stronger no-op gating around the accepted Richardson diagnostic.
- Output-only wind ideas remain easy to test and roll back, but they can still fail fixed guardrails even with clean numerical diagnostics.

## Cleanup Completed

- Candidate code retained or reverted: reverted from tracked source and test files.
- Research state updated: consumed ready proposal removed after copying into this history directory.
- Leaderboard updated: no, incumbent unchanged.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration immediately.
