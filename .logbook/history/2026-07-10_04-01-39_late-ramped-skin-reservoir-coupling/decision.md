# Decision Record

## Decision

`accepted`.

## Score Summary

- Iteration candidate primary score: `-0.1102658536572533`
- Iteration incumbent primary score: `-0.1177416449326221`
- Iteration delta: `+0.007475791275368793`
- Validation candidate primary score: `-0.11137528326510353`
- Validation incumbent primary score: `-0.11891349527750807`
- Validation delta: `+0.007538212012404538`

## Rationale

The candidate passed focused tests, Ruff, full pytest, fast, iteration, and
validation with clean diagnostics. The iteration delta exceeded the fixed
`+0.002` promotion threshold, and the validation delta exceeded the fixed
`+0.001` acceptance threshold. No days 1-5 target-variable mean RMSE
regression exceeded `2%`; no variable/lead regression exceeded `10%`. The
worst validation regression was only `+0.026310056%` for U10 at 312 h.

Physical plausibility review found no nonfinite values, instability, severe
oversmoothing signature, or contract change. The auxiliary reservoir remains
causal, bounded, energy-neutral for its air/skin exchange, excluded from DFI
and outputs, and exactly inactive through the early guardrail window.

The incumbent scores came from the valid leaderboard cache after identity,
fingerprint, artifact, finite-value, and record-count checks. No incumbent
rerun and no golden evaluation were performed.

## Lessons Learned

- The large gain from the rejected always-active reservoir represented useful
  late surface-memory signal, but immediate coupling caused its early T2m
  failure. Temporal isolation recovered the signal without those regressions.
- Exact incumbent behavior through 120 h was an effective risk control: early
  target RMSE remained neutral to numerical precision on both fixed splits.
- Future lower-boundary memory proposals should preserve the accepted ramp and
  test distinct mechanisms rather than retuning its constants against these
  validation results.

## Cleanup Completed

- Candidate code retained or reverted: retained as accepted source commit
  `b92c07d2f054bd34cb90d36592501c5ff74c5991`.
- Research state updated: the selected ready proposal was removed after this
  history record was completed.
- Leaderboard updated: yes, to
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin`.
- Git status checked: accepted source/test changes were committed separately;
  only the accepted artifact update remained for the second commit, plus the
  pre-existing user-owned untracked `gifs/` directory.

## Next Action

Continue the open-ended optimization loop with a new Researcher/Evaluator
iteration using the accepted late-skin model and its cached metrics as the
incumbent.
