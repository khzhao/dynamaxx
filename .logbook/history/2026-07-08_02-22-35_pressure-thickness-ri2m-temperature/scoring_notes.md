# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast primary `-0.11783133421907396`; diagnostics `failed=false`, issues `0`; artifact rows `120` with `60` candidate model rows and `60` persistence rows.
- Iteration promotion gate: passed as a measurement. Candidate primary `-0.1177416449326221` vs cached incumbent `-0.12618112079830215` gives delta `0.008439475865680057` with threshold `+0.002`; diagnostics are clean; early-lead mean and variable-lead RMSE guardrails pass.
- Validation acceptance gate: passed as a measurement. Candidate primary `-0.11891349527750807` vs cached incumbent `-0.12682079599872897` gives delta `0.007907300721220908` with threshold `+0.001`; diagnostics are clean; early-lead mean and variable-lead RMSE guardrails pass.

## Commands And Artifacts

- Ran `uv run pytest`: exit status `0`; `310 passed, 2 skipped in 304.85s`.
- Ran `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m`: exit status `0`; raw metrics `outputs/eval/fast_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m.json` and `outputs/eval/fast_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m.csv`.
- Ran `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m --workers 4`: exit status `0`; raw metrics `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m.json` and `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m.csv`.
- Ran `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m --workers 4`: exit status `0`; raw metrics `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m.json` and `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m.csv`.
- Incumbent iteration reused: `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.json` and `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.csv`.
- Incumbent validation reused: `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.json` and `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag.csv`.

## Cache Reuse

- Reused incumbent metrics for both iteration and validation; no incumbent evaluation was recomputed.
- Checks performed: requested incumbent matched `.logbook/leaderboard.json`; leaderboard fingerprint matched the fixed data path, targets, and lead range; leaderboard protocols included iteration and validation; cached incumbent JSON/CSV artifacts existed, were readable, finite, model/case matched, and each contained `60` incumbent model rows plus `60` persistence rows.
- Fixed-evaluation compatibility checks printed no files for both `git diff --name-only 8f0b4f529d29d372341e136bd11cbe2f21542bc2 -- pyproject.toml uv.lock src/dynamaxx/eval src/dynamaxx/data/weatherbench2.py src/dynamaxx/cli.py tests/eval roles/PROTOCOL.md roles/SCORER.md roles/templates/scores.json roles/templates/scoring_notes.md` and the same working-tree diff without the commit.
- Candidate output paths did not collide with incumbent paths, so no snapshot/restore was needed.

## Iteration Guardrails

Primary delta: `0.008439475865680057`.

Early lead 1-5 mean RMSE regressions:
- `10m_u_component_of_wind`: candidate 3.86185058122, incumbent 3.8618509309, regression -9.05488e-06% (pass `true`).
- `2m_temperature`: candidate 4.46210416555, incumbent 4.62813354194, regression -3.58739% (pass `true`).
- `geopotential_500`: candidate 560.627756459, incumbent 560.628252177, regression -8.84219e-05% (pass `true`).
- `mean_sea_level_pressure`: candidate 651.856326759, incumbent 651.856360852, regression -5.23014e-06% (pass `true`).

Worst per-lead RMSE regression: `2m_temperature` day `15` had `0.319991%`, threshold `10%`, pass `true`. Full per-lead table is in `scores.json`.

## Validation Guardrails

Primary delta: `0.007907300721220908`.

Early lead 1-5 mean RMSE regressions:
- `10m_u_component_of_wind`: candidate 3.82642009965, incumbent 3.82641947865, regression 1.62293e-05% (pass `true`).
- `2m_temperature`: candidate 4.45878374548, incumbent 4.62263235897, regression -3.54449% (pass `true`).
- `geopotential_500`: candidate 553.317806333, incumbent 553.317378616, regression 7.73004e-05% (pass `true`).
- `mean_sea_level_pressure`: candidate 639.777053578, incumbent 639.777006833, regression 7.30651e-06% (pass `true`).

Worst per-lead RMSE regression: `2m_temperature` day `15` had `0.420056%`, threshold `10%`, pass `true`. Full per-lead table is in `scores.json`.

## Measurement Lessons

- The pressure-thickness RI2m candidate improved primary score on both iteration and validation, with the largest measured per-lead RMSE regression below `0.43%` and therefore well under the fixed `10%` guardrail.
- Guardrail scripts must filter evaluator CSV rows by `model_name`; the CSV also contains persistence rows used for skill calculation. A preliminary helper missed that filter, then was corrected before artifact writes. The correctly filtered iteration gate still passed, so the validation run remained eligible.
- The improvement is concentrated in the 2 m temperature diagnostic while other target variables remain essentially unchanged under the RMSE guardrails.

## Anomalies

- Cache reuse: incumbent metrics reused for iteration and validation; no recomputation and no cache invalidation found.
- Resource limits: none hit. Iteration used 4 requested/effective GPU workers for `229` chunks; validation used 4 requested/effective GPU workers for `46` chunks.
- Failed or restarted commands: no pytest or evaluation command failed or restarted.
- Nonfinite or unstable outputs: none observed in candidate or incumbent diagnostics or finite metric checks.
- Local scoring helper correction: the first quick guardrail calculation did not filter persistence rows; corrected model-row calculations are the values recorded in `scores.json` and above.

## Recommendation To Orchestrator

Measured gates pass and cached incumbent reuse is valid. Scorer recommends Orchestrator review the candidate for acceptance using these measurements; Scorer does not accept or reject the candidate.
