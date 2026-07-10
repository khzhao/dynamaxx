# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate primary `-0.11041836504747159`;
  diagnostics `failed=false`, issues `0`; 120 records contained 60 candidate
  rows and 60 persistence rows.
- Iteration promotion gate: passed. Candidate primary
  `-0.1102658536572533` versus cached incumbent `-0.1177416449326221`
  gives delta `+0.007475791275368793`, above the `+0.002` threshold.
  Diagnostics and both fixed RMSE guardrails passed.
- Validation acceptance gate: passed. Candidate primary
  `-0.11137528326510353` versus cached incumbent
  `-0.11891349527750807` gives delta `+0.007538212012404538`, above the
  `+0.001` threshold. Diagnostics, finite checks, early RMSE guardrails, and
  physical plausibility review passed.

## Commands And Artifacts

- `uv run pytest`: exit `0`; 318 passed and 2 skipped.
- `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin --workers 4`:
  exit `0`; raw JSON/CSV under `outputs/eval/fast_*_lateskin.*`.
- `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin --workers 4`:
  exit `0`; 229 chunks merged; raw JSON/CSV under
  `outputs/eval/iteration_*_lateskin.*`.
- `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin --workers 4`:
  exit `0`; 46 chunks merged; raw JSON/CSV under
  `outputs/eval/validation_*_lateskin.*`.
- No golden evaluation was run.

## Cache Reuse

- Reused the leaderboard incumbent metrics for iteration and validation; the
  incumbent was not rerun.
- Verified incumbent model identity, data path, protocols, target variables,
  lead range, readable finite JSON/CSV artifacts, clean diagnostics, and 60
  model plus 60 persistence records per protocol.
- Candidate output paths did not collide with incumbent paths. Candidate
  dycore source changes did not invalidate the accepted incumbent cache under
  the repository policy.

## Iteration Guardrails

- Primary delta: `+0.007475791275368793`.
- Days 1-5 mean RMSE regressions: U10 `-0.000002180%`, T2m
  `+0.000002806%`, Z500 `+0.000105907%`, MSLP `+0.000001960%`; all below
  the fixed `2%` limit.
- Worst variable/lead RMSE regression: U10 at 264 h,
  `+0.032491988%`; no violation of the fixed `10%` limit.

## Validation Guardrails

- Primary delta: `+0.007538212012404538`.
- Days 1-5 mean RMSE regressions: U10 `-0.000010649%`, T2m
  `+0.000017053%`, Z500 `-0.000039144%`, MSLP `-0.000002367%`; all below
  the fixed `2%` limit.
- Worst variable/lead RMSE regression: U10 at 312 h,
  `+0.026310056%`; no violation of the `10%` diagnostic limit.
- Candidate diagnostics contained no issues, all metric records were finite,
  and the bounded late-ramped exchange produced no obvious unstable or
  nonphysical score signature.

## Measurement Lessons

- Delaying surface-reservoir coupling through 120 h preserved incumbent-like
  early RMSE while recovering a threshold-sized late T2m improvement from the
  previously rejected always-active force-restore family.
- The fixed constants and single ramp were sufficient; no candidate tuning or
  validation-driven revision was performed.
- Model-row filtering remained mandatory because each metrics artifact also
  contains persistence rows.

## Anomalies

- Cache reuse: valid incumbent artifacts reused; no incumbent recomputation.
- Resource limits: none hit. Iteration and validation used four effective GPU
  workers.
- Failed or restarted commands: none. Ruff initially found import ordering
  during implementation; the import-only repair passed before scoring.
- Nonfinite or unstable outputs: none.

## Recommendation To Orchestrator

All measured gates pass without caveat. Scorer recommends acceptance; final
decision authority remains with the Orchestrator.
