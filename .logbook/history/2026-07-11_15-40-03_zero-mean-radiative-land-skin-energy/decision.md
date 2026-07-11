# Decision Record

## Decision

`accepted`.

## Score Summary

- Iteration candidate primary score: `-0.07908852007250675`
- Iteration incumbent primary score: `-0.08429962366251152`
- Iteration delta: `+0.005211103590004776`
- Validation candidate primary score: `-0.07929026517101266`
- Validation incumbent primary score: `-0.08458916260281377`
- Validation delta: `+0.005298897431801106`

## Rationale

The candidate passed Ruff, focused tests, full pytest, fast, iteration, and
validation with clean diagnostics. Its iteration delta exceeded the fixed
`+0.002` promotion threshold by `+0.003211103590004776`, and its validation
delta exceeded the fixed `+0.001` acceptance threshold by
`+0.004298897431801106`. Validation ran exactly once after every promotion
condition passed. Golden was not run.

All eight early day-1-to-5 target-variable mean RMSE comparisons passed the
`2%` guardrail, and none of the 120 variable/lead comparisons across iteration
and validation exceeded the `10%` guardrail. The largest single regression was
only `+0.000234092543%`, for validation Z500 at 24 hours. Early-window changes
stayed at numerical-trajectory scale, consistent with the unchanged 120-hour
inactive window.

Over days 6-15, T2m mean RMSE improved by `0.1066571376578409 K`
(`1.619674451793882%`) on iteration and `0.10677348139614384 K`
(`1.6293062831949578%`) on validation. Mean MSLP, Z500, and U10 RMSE also
improved on both fixed splits. The primary gains reproduced closely across the
two independent splits.

Physical review found no instability, nonfinite field, severe oversmoothing,
or forecast-contract change. The candidate computes existing solar forcing at
each sample's own initial-time phase, centers shortwave and longwave energy
separately over active land, applies one common cap scale, and changes only the
private land-skin state. The active-land weighted mean is zero by construction,
so the mechanism redistributes radiative skin energy without adding a net
global land-energy source.

The incumbent iteration and validation artifacts passed model identity,
fingerprint, artifact-hash, readability, finite-value, diagnostics,
record-count, and guardrail-key checks. They were reused without an incumbent
rerun. The candidate commands ran exactly once each with no retry or restart.

## Lessons Learned

- A late-ramped, energy-neutral land-skin radiative redistribution recovers a
  split-consistent T2m gain without spending early guardrail margin.
- The improvement in all four late-window target means indicates that the
  private lower-boundary state affects the coupled trajectory, not only the
  T2m observer.
- Per-sample solar phase and exact invalid-anchor fallback are important for
  preserving batch correctness and the incumbent path.
- Future work should add distinct physical information rather than retuning
  this candidate's ramp, cap, albedo, emissivity, or thermal inertia.

## Cleanup Completed

- Candidate code retained or reverted: retained as accepted source commit
  `8d8b2cba4399bf9f35689c4e55855e2436d367a6`.
- Research state updated: selected ready proposal removed after accepted
  history completion.
- Leaderboard updated: yes, to
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin`.
- Git status checked: accepted source/test changes were committed separately;
  only accepted history/leaderboard changes remain for the artifact commit,
  plus protected pre-existing `gifs/`.

## Next Action

Continue the open-ended optimization loop with a fresh Researcher/Evaluator
cycle using the accepted zero-mean radiative land-skin model and its cached
iteration and validation metrics as the incumbent.
