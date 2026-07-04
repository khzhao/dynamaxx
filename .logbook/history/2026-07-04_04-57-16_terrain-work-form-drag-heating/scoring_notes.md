# Scoring Notes

## Gate Status

- Fast gate: passed from Orchestrator-provided run; Scorer verified `outputs/eval/fast_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.json` and `outputs/eval/fast_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.csv` are readable, finite, model/case matched, contain 120 rows, and diagnostics report `failed=false`, issues `0`.
- Iteration promotion gate: passed. Candidate primary `-0.12618112079830215` vs incumbent `-0.1285119843716688` gives delta `0.0023308635733666483` with threshold `+0.002`; diagnostics are clean; all early-lead and per-lead RMSE guardrails pass.
- Validation acceptance gate: passed as a measurement. Candidate primary `-0.12682079599872897` vs incumbent `-0.12911217353049617` gives delta `0.002291377531767197` with threshold `+0.001`; diagnostics are clean; all early-lead and per-lead RMSE guardrails pass.

## Commands And Artifacts

- Scorer ran `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag --workers 4`: exit status `0`; raw metrics `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.json` and `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.csv`.
- Scorer ran `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag --workers 4`: exit status `0`; raw metrics `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.json` and `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.csv`.
- Incumbent iteration reused: `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind.json` and `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind.csv`.
- Incumbent validation reused: `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind.json` and `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind.csv`.
- Existing pytest/fast records were not rerun: focused pytest `237 passed in 291.48s`, full pytest `303 passed, 2 skipped in 301.34s`, fast primary `-0.12743232368039709`, diagnostics clean.

## Cache Reuse

- Reused incumbent metrics for both iteration and validation; no incumbent evaluation was recomputed.
- Checks performed: requested incumbent matched `.logbook/leaderboard.json`; leaderboard fingerprint had matching data path, targets, lead range, and included both protocols; `git diff --name-only db2387935aa0937eb8669de20843dc3caaccb115 -- src/dynamaxx/eval roles tests/eval` and `git diff --name-only -- src/dynamaxx/eval roles tests/eval` printed no files; incumbent JSON/CSV files existed, were readable, finite, model/case matched, and each contained 60 incumbent model rows plus 60 persistence rows.
- Candidate output paths did not collide with incumbent paths, so no snapshot/restore was needed.

## Iteration Guardrails

Primary delta: `0.0023308635733666483`.

Early lead 1-5 mean RMSE regressions:
- `10m_u_component_of_wind`: candidate 3.8618509309, incumbent 3.86906938438, regression -0.186568% (pass).
- `2m_temperature`: candidate 4.62813354194, incumbent 4.63222041268, regression -0.088227% (pass).
- `geopotential_500`: candidate 560.628252177, incumbent 562.059116114, regression -0.254575% (pass).
- `mean_sea_level_pressure`: candidate 651.856360852, incumbent 654.631300843, regression -0.423894% (pass).

Worst per-lead RMSE regression: `2m_temperature` day `1.0` had `-0.0052867%`, threshold `10%`, pass `true`. Full per-lead table is in `scores.json`.

## Validation Guardrails

Primary delta: `0.002291377531767197`.

Early lead 1-5 mean RMSE regressions:
- `10m_u_component_of_wind`: candidate 3.82641947865, incumbent 3.83296682902, regression -0.170817% (pass).
- `2m_temperature`: candidate 4.62263235897, incumbent 4.62662501495, regression -0.0862974% (pass).
- `geopotential_500`: candidate 553.317378616, incumbent 554.619963953, regression -0.234861% (pass).
- `mean_sea_level_pressure`: candidate 639.777006833, incumbent 642.246245792, regression -0.384469% (pass).

Worst per-lead RMSE regression: `2m_temperature` day `1.0` had `-0.00486587%`, threshold `10%`, pass `true`. Full per-lead table is in `scores.json`.

## Measurement Lessons

- The candidate improved primary score on both iteration and validation while every candidate-model RMSE guardrail comparison was non-regressing relative to the cached incumbent.
- Future scoring helpers should filter metric rows to `record.model_name == result.model_name`; evaluator artifacts also include persistence rows, which are necessary for skill but should not be compared as candidate model RMSE rows.
- Future proposal generation can treat this terrain-work drag/heating mechanism as promising measured signal, while keeping conservative caps and side-by-side model registration for clean comparisons.

## Anomalies

- Cache reuse: incumbent metrics reused for iteration and validation; no recomputation.
- Resource limits: none hit. Iteration used 4 requested/effective GPU workers for 229 chunks; validation used 4 requested/effective GPU workers for 46 chunks.
- Failed or restarted commands: no evaluation command failed or restarted. One local comparison helper exited `1` before artifact writing because it used `channel_name, lead_hours` as a unique key and encountered persistence rows; corrected by filtering candidate model rows.
- Nonfinite or unstable outputs: none observed in candidate or incumbent metrics.

## Recommendation To Orchestrator

Measured gates are recorded above. Scorer does not accept or reject the candidate.
