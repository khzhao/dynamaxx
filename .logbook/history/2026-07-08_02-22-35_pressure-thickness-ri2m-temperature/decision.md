# Decision Record

## Decision

`accepted`.

## Score Summary

- Iteration candidate primary score: `-0.1177416449326221`
- Iteration incumbent primary score: `-0.12618112079830215`
- Iteration delta: `+0.008439475865680057`
- Validation candidate primary score: `-0.11891349527750807`
- Validation incumbent primary score: `-0.12682079599872897`
- Validation delta: `+0.007907300721220908`

## Rationale

The candidate passed the fixed fast, iteration, and validation gates with clean
diagnostics. The iteration primary delta exceeded the `+0.002` promotion
threshold, and the validation primary delta exceeded the `+0.001` acceptance
threshold. Early lead day-1-to-5 RMSE guardrails passed for all target
variables on both iteration and validation, and the worst variable-lead RMSE
regression was `0.420056%`, below the fixed `10%` guardrail.

The incumbent iteration and validation scores were reused from the valid
leaderboard cache. The Scorer verified matching incumbent identity, compatible
evaluation fingerprint, readable finite artifacts, unchanged fixed evaluation
files, and non-colliding candidate output paths. No incumbent rerun and no
golden evaluation were performed.

## Lessons Learned

- Pressure-thickness weighted lower-column references materially improved the
  2 m temperature diagnostic while keeping wind, MSLP, and 500 hPa geopotential
  essentially neutral under fixed RMSE guardrails.
- Future guardrail helpers must filter evaluator CSV rows by `model_name`
  because the files also contain persistence rows used for skill calculation.
- The accepted mechanism is a side-by-side Dinosaur variant, so future
  experiments should use
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m` as the
  incumbent instead of mutating the prior terrain-work model.

## Cleanup Completed

- Candidate code retained or reverted: retained as accepted source commit
  `d0c364cf1973e5f926c7795d266afc6789638fc7`.
- Research state updated: ready proposal
  `.logbook/research/ready/pressure-thickness-ri2m-temperature.md` removed
  after history record creation.
- Leaderboard updated: yes, to
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m`.
- Git status checked: source/test tree was clean after the accepted source
  commit except the pre-existing untracked `gifs/` directory.

## Next Action

Continue the open-ended optimization loop by starting the next
Researcher/Evaluator iteration from the new incumbent.
