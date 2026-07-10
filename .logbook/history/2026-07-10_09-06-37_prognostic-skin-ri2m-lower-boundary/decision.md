# Decision Record

## Decision

`accepted`.

## Score Summary

- Iteration candidate primary score: `-0.10655439732760863`
- Iteration incumbent primary score: `-0.1102658536572533`
- Iteration delta: `+0.0037114563296446745`
- Validation candidate primary score: `-0.10736873851248371`
- Validation incumbent primary score: `-0.11137528326510353`
- Validation delta: `+0.0040065447526198145`

## Rationale

The candidate passed focused tests, Ruff, full pytest, fast, iteration, and
validation with clean diagnostics. Its iteration delta exceeded the fixed
`+0.002` promotion threshold, and its validation delta exceeded the fixed
`+0.001` acceptance threshold. No days 1-5 target-variable mean RMSE
regression exceeded `2%`; no iteration variable/lead regression exceeded
`10%`. The worst validation variable/lead regression was only
`+0.0003637308964243857%` for Z500 at 24 h.

The measured improvement matches the proposal: mean T2m RMSE over days 6-15
improved by `0.07982718618523776 K` on iteration and
`0.08479064331858588 K` on validation, while non-T2m movement remained at
numerical scale. Physical review found no instability, nonfinite values,
trajectory change, auxiliary output, or forecast-contract expansion. The
observer is causal, land-only, bounded by the existing RI2m cap, and inactive
through the accepted 120-hour window.

The incumbent iteration and validation artifacts passed identity,
fingerprint, readability, finite-value, diagnostics, record-count, and
guardrail-key checks. They were reused without an incumbent rerun. Validation
ran exactly once, and golden was not run.

## Lessons Learned

- The accepted prognostic skin contains useful late screen-temperature
  information beyond its indirect lowest-layer heat exchange.
- A physically standard skin-to-lowest-model-level observer produced a larger
  and more reproducible gain than recent atmospheric-only RI2m reference-state
  refinements.
- Exact temporal isolation protected early guardrails while allowing a
  T2m-only output experiment to be attributed cleanly.
- Future follow-ups should target independent dynamics or variables rather
  than retuning this observer against validation.

## Cleanup Completed

- Candidate code retained or reverted: retained as accepted source commit
  `3fb32ff048b00b779d7e16a2c72e728866a4f4ba`.
- Research state updated: selected ready proposal removed after accepted
  history completion.
- Leaderboard updated: yes, to
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri`.
- Git status checked: accepted source/test changes were committed separately;
  only accepted history/leaderboard changes remained for the artifact commit,
  plus protected pre-existing `gifs/`.

## Next Action

Continue the open-ended optimization loop with a fresh Researcher/Evaluator
cycle using the accepted skin-aware RI2m model and its cached metrics as the
incumbent.
