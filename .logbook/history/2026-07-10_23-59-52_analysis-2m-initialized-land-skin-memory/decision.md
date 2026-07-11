# Decision Record

## Decision

`accepted`.

## Score Summary

- Iteration candidate primary score: `-0.08966691030501653`
- Iteration incumbent primary score: `-0.10655439732760863`
- Iteration delta: `+0.0168874870225921`
- Validation candidate primary score: `-0.09015390068642175`
- Validation incumbent primary score: `-0.10736873851248371`
- Validation delta: `+0.017214837826061966`

## Rationale

The candidate passed focused tests, Ruff, full pytest, fast, iteration, and
validation with clean diagnostics. Its iteration delta exceeded the fixed
`+0.002` promotion threshold by `+0.0148874870225921`, and its validation
delta exceeded the fixed `+0.001` acceptance threshold by
`+0.016214837826061966`. All numeric metrics were finite and both evaluated
protocols contained the expected 120 records.

No days 1-5 target-variable mean RMSE regression exceeded `2%`, and no
variable/lead regression exceeded `10%`. The largest early-mean regression
was only `+0.000048151711%` on iteration and `+0.000024651341%` on
validation. This confirms the intended exact isolation through the accepted
120-hour ramp boundary.

Over days 6-15, mean T2m RMSE improved by `0.3489504894295097 K`
(`4.950179763248361%`) on iteration and `0.3492895696561842 K`
(`4.975655152171936%`) on validation. Late MSLP, Z500, and U10 mean RMSE also
improved on both splits. The large primary gain reproduces closely across the
independent iteration and validation protocols.

Physical review found no instability, nonfinite field, severe oversmoothing
signal, or forecast-contract expansion. The initializer is causal and
land-only, uses only lead-zero analyzed T2m, introduces no initial hidden
skin/deep gradient, preserves exact incumbent fallback cells, and leaves every
accepted exchange, cap, observer, and activation constant unchanged.

The incumbent iteration and validation artifacts passed identity, fingerprint,
readability, finite-value, diagnostics, record-count, and guardrail-key checks.
They were reused without an incumbent rerun. Validation ran exactly once, and
golden was not run.

## Lessons Learned

- Lead-zero analyzed T2m is a materially better late land-memory endpoint than
  the post-DFI lowest atmospheric layer for this reduced reservoir.
- Delaying the analyzed memory until after day 5 preserves early behavior while
  retaining a reproducible late T2m improvement across splits.
- Setting skin and deep to the same analyzed value was sufficient; no blend,
  smoothing, land-class tuning, or invented subsurface gradient was needed.
- Future work should seek independent dynamics or variables instead of tuning
  this accepted initializer against validation.

## Cleanup Completed

- Candidate code retained or reverted: retained as accepted source commit
  `603f44a9b052557bd3bf3a16a9dcd9c05f343449`.
- Research state updated: selected ready proposal removed after accepted
  history completion.
- Leaderboard updated: yes, to
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si`.
- Git status checked: accepted source/test changes were committed separately;
  only accepted history/leaderboard changes remain for the artifact commit,
  plus protected pre-existing `gifs/`.

## Next Action

Continue the open-ended optimization loop with a fresh Researcher/Evaluator
cycle using the accepted analysis-initialized land-skin model and its cached
iteration and validation metrics as the incumbent.
