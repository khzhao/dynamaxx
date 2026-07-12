# Decision Record

## Decision

`accepted`

## Score Summary

- Fast candidate primary score: `-0.07487637059903021`
- Iteration candidate primary score: `-0.07495718284454471`
- Iteration cached incumbent primary score: `-0.07908852007250675`
- Iteration delta: `+0.004131337227962037`
- Iteration margin above the `+0.002` promotion threshold: `+0.002131337227962037`
- Validation candidate primary score: `-0.07524184185018803`
- Validation cached incumbent primary score: `-0.07929026517101266`
- Validation delta: `+0.004048423320824626`
- Validation margin above the `+0.001` acceptance threshold: `+0.003048423320824626`

## Rationale

All fixed gates pass. The full source-behavior test suite passed with 390 tests and 2 skips; the related suite passed 324 tests; the final dedicated APVM suite passed 10 tests; Ruff, compilation, diff checks, and the frozen-patch audit passed. Fast, iteration, and the single permitted validation run completed with finite metrics, clean diagnostics, zero issues, and zero retries.

All 120 variable/lead comparisons pass the fixed per-lead guardrail. Both splits have zero day-1-to-5 mean RMSE violations over 2% and zero target/lead violations over 10%. The worst single regression is validation MSLP at 48 hours, `+2.2841440448927584%`, which is well inside the 10% limit. The day-6-to-15 mean RMSE improves for every target on both splits, led by validation Z500 at `-1.4025038373487668%` and validation T2m at `-0.7837964826996746%`. No score or diagnostic indicates instability, nonfinite output, or an obvious nonphysical mode.

The incumbent was always compared. Its authoritative iteration and validation artifacts passed identity, fingerprint, data-path, protocol, target, lead-range, evaluation-code, hash, record-count, finite-value, diagnostics, and guardrail checks. They were reused without an incumbent command. Candidate commands: 3. Incumbent commands: 0. Golden commands: 0. Scorer pytest commands: 0.

## Lessons Learned

- A work-neutral anticipated layer-PV flux can improve aggregate skill through medium/late-lead Z500 and T2m gains even while allowing small early MSLP, Z500, and U10 regressions.
- The benefit is consistent across iteration and validation, so it is not an iteration-only split fluctuation.
- Added modal/nodal work at every explicit stage increased iteration runtime to 13,837 seconds; future proposals should account for this accepted cost baseline.
- The implemented closure remains a sigma-layer shallow-water PV proxy. Future research must not reinterpret this result as full Ertel-PV or exact full-model energy conservation.

## Cleanup Completed

- Candidate code retained in source commit `7174848c3641a43299fc5c2682bef2fc75f2ff89`.
- The selected proposal was removed from `.logbook/research/ready`; its immutable copy is this history record.
- The leaderboard was updated to the accepted candidate and its candidate-only iteration/validation artifacts.
- The accepted history and leaderboard are committed separately from source/tests.
- Protected pre-existing `gifs/` remains untouched.
- No rejected candidate artifact or implementation is included in either commit.

## Next Action

Start the next Researcher/Evaluator iteration immediately. Treat `dino_rskin_apv` and source commit `7174848c3641a43299fc5c2682bef2fc75f2ff89` as the incumbent, and reuse the newly recorded compatible iteration and validation artifacts without rerunning it.
