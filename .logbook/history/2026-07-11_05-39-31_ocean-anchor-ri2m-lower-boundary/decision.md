# Decision Record

## Decision

`accepted`.

## Score Summary

- Iteration candidate primary score: `-0.08429962366251152`
- Iteration incumbent primary score: `-0.08966691030501653`
- Iteration delta: `+0.005367286642505006`
- Validation candidate primary score: `-0.08458916260281377`
- Validation incumbent primary score: `-0.09015390068642175`
- Validation delta: `+0.005564738083607981`

## Rationale

The candidate passed focused tests, Ruff, full pytest, fast, iteration, and
validation with clean diagnostics. Its iteration delta exceeded the fixed
`+0.002` promotion threshold by `+0.003367286642505006`, and its
validation delta exceeded the fixed `+0.001` acceptance threshold by
`+0.004564738083607981`. All metrics were finite, both scored protocols had
the expected 120 records, and validation ran exactly once.

No days 1-5 target-variable mean RMSE regression exceeded `2%`, and no
variable/lead regression exceeded `10%`. The largest early-mean regression
was only `+0.000005914831%` on iteration and `+0.000041713234%` on
validation, confirming the intended exact isolation through 120 hours.

Over days 6-15, T2m mean RMSE improved by `0.11520110615581736 K`
(`1.7193429331983945%`) on iteration and `0.11737247615155333 K`
(`1.7595274183232266%`) on validation. Non-T2m differences remained at
numerical scale, matching the output-only mechanism. The primary gains
reproduced closely across the two fixed splits.

Physical review found no instability, nonfinite field, severe oversmoothing
signal, trajectory change, or forecast-contract expansion. The observer uses
the causal ocean anchor already accepted for the bulk sensible heat flux,
reuses the bounded skin-aware Richardson operator, applies complementary
land/ocean weights, retains exact invalid-cell fallback, and leaves every
accepted forcing and trajectory state unchanged.

The incumbent iteration and validation artifacts passed identity, fingerprint,
artifact-hash, readability, finite-value, diagnostics, record-count, and
guardrail-key checks. They were reused without an incumbent rerun. Golden was
not run.

## Lessons Learned

- The accepted lead-zero ocean thermal anchor contains useful late marine
  screen-temperature information beyond its weak prognostic heat-flux effect.
- Reusing the accepted bounded Richardson observation operator over the
  complementary ocean domain produced a split-consistent gain without spending
  early or non-T2m guardrail margin.
- The result supports physical endpoint observers over additive high-mode
  ocean residual memory, which previously regressed iteration.
- Future observer work should target remaining distinct surface information
  rather than tuning this anchor, cap, ramp, or Richardson formula.

## Cleanup Completed

- Candidate code retained or reverted: retained as accepted source commit
  `ea124f2d1b43e8e9e54efcbe0abf05e80f6b8001`.
- Research state updated: selected ready proposal removed after accepted
  history completion.
- Leaderboard updated: yes, to
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori`.
- Git status checked: accepted source/test changes were committed separately;
  only accepted history/leaderboard changes remain for the artifact commit,
  plus protected pre-existing `gifs/`.

## Next Action

Continue the open-ended optimization loop with a fresh Researcher/Evaluator
cycle using the accepted ocean-anchor RI2m model and its cached iteration and
validation metrics as the incumbent.
