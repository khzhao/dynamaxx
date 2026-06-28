# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5150755275557011`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `-0.00001282596467677699`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: not applicable

## Rationale

The candidate failed the fixed iteration promotion gate. Fast and iteration both completed with clean diagnostics, and the RMSE guardrails passed comfortably. The worst variable-lead RMSE regression was only `2.2378814357182364e-7%`, but the primary score moved slightly negative instead of clearing the required `+0.002` iteration threshold. Validation was therefore skipped.

The incumbent comparison reused the valid leaderboard iteration cache. No incumbent evaluation and no `golden` run were performed.

## Lessons Learned

- Computing the accepted analysis-offset Held-Suarez equilibrium from the DFI-balanced state is numerically stable but does not improve fixed iteration metrics.
- The accepted raw-state analysis-HS anchor appears at least as good as the DFI-balanced anchor under this implementation.
- Future weak-HS follow-ups should introduce a larger physical difference than reordering the same low-mode offset around DFI.

## Cleanup Completed

- Candidate code retained or reverted: reverted from tracked source and test files.
- Research state updated: consumed ready proposal removed after copying into this history directory.
- Leaderboard updated: no, incumbent unchanged.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration immediately.
