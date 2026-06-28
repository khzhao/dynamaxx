# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: -1.2826846667797114
- Fast diagnostics: passed, issue count 0
- Iteration candidate primary score: -1.3205664654977811
- Iteration incumbent primary score: -1.3208025947740873
- Iteration delta: +0.00023612927630622949
- Validation candidate primary score: not run
- Validation incumbent primary score: -1.308334010223954
- Validation delta: not run

## Rationale

The candidate passed tests and the fast diagnostic gate, and the iteration artifact had clean diagnostics. However, the iteration primary-score delta was only `+0.00023612927630622949`, below the protocol's required `+0.002` promotion threshold. Validation was therefore not run.

RMSE guardrails did not fail: early-lead mean RMSE regressions and per-variable/lead RMSE regressions were only roundoff-scale for the fixed target variables. That makes the result a clean scientific rejection rather than a numerical-stability failure. The standard-atmosphere reference split is plausible but did not move the fixed evaluation enough to justify retaining the candidate.

## Lessons Learned

- Changing the semi-implicit reference-temperature profile is numerically safe in this adapter, but the fixed scores are essentially unchanged relative to the accepted `dinosaur_dfi` incumbent.
- DFI's accepted gain should not be interpreted as broad evidence that all balance-partition changes will improve WeatherBench2 metrics.
- Future proposals should target mechanisms with larger expected surface in the fixed metrics, such as mass-coordinate/orography handling or missing physical tendencies, while still protecting the sensitive low-level wind gate.

## Cleanup Completed

- Candidate code retained or reverted: reverted; no candidate code retained in tracked source/test files.
- Research state updated: removed from `.logbook/research/ready`; immutable copy retained in this history directory.
- Leaderboard updated: no; incumbent remains `dinosaur_dfi`.
- Git status checked: clean tracked worktree after rollback.

## Next Action

Continue the loop by re-triaging staged ideas against the accepted `dinosaur_dfi` incumbent. Do not run `golden`.
