# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5150758260293438`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `-0.000013124438319467302`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: not run

## Rationale

The candidate passed compile, focused tests, full tests, fast evaluation, and
iteration diagnostics, but did not pass the fixed iteration promotion gate. The
candidate-minus-incumbent iteration delta was slightly negative and below the
required `+0.002` threshold.

Guardrails passed: the day 1-5 mean RMSE relative change was
`-2.0282424776122887e-07`, and the worst variable+lead RMSE regression was
`3.3883458252312426e-05` for `mean_sea_level_pressure` at day 12, far below the
`10%` threshold. Validation was skipped because the iteration score gate did
not promote the candidate.

Incumbent iteration metrics were reused from the valid leaderboard cache; no
incumbent evaluation and no `golden` protocol were run.

## Lessons Learned

- A weak, one-time high-wavenumber divergence increment filter is effectively
  neutral under fixed iteration metrics and does not beat the accepted
  incumbent.
- The remaining error is unlikely to be improved by extremely local divergence
  cleanup alone after accepted DFI and off-centered SIL3.
- Future divergence-family proposals should require stronger evidence or a
  distinct mechanism before promotion.

## Cleanup Completed

- Candidate code retained or reverted: rejected source/test changes reverted
  from the tracked worktree after saving `candidate.diff`.
- Research state updated: selected ready proposal removed; immutable history
  directory retained.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked status clean after rollback.

## Next Action

Continue the optimization loop by inspecting resources and research state, then
request or triage the next single ready proposal. Continue using valid cached
leaderboard incumbent metrics for candidate comparisons.
