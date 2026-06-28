# Scoring Notes: picard-hsl-theta-departure

## Summary

Candidate `dino_hsl_picard` completed fast and iteration scoring with clean diagnostics. The cached incumbent `dino_hsl2_theta` metrics were reused from `.logbook/leaderboard.json`; no incumbent rerun was performed.

Iteration did not promote to validation. Candidate iteration primary score was `-0.31286871436185787` versus cached incumbent `-0.31282890543336245`, for delta `-3.9808928495421725e-05`. The required promotion delta is `+0.002`.

## Commands

- `sed -n '1,240p' roles/PROTOCOL.md`; exit `0`.
- `sed -n '1,260p' roles/SCORER.md`; exit `0`.
- `python - <<'PY' ... import registry and instantiate dino_hsl_picard and dino_hsl2_theta ... PY`; exit `0`. Both models instantiated as `DinosaurPrimitiveEquationsDycoreModel`.
- `uv run dynamaxx-eval fast --model dino_hsl_picard`; exit `0`. Result: failed `False`, issues `0`, primary `-0.3155223766814108`, metrics `outputs/eval/fast_dino_hsl_picard.json`.
- `uv run dynamaxx-eval iteration --model dino_hsl_picard --workers 4`; exit `0`. Result: failed `False`, issues `0`, primary `-0.31286871436185787`, metrics `outputs/eval/iteration_dino_hsl_picard.json`.
- `uv run dynamaxx-eval validation --model dino_hsl_picard --workers 4`; skipped. Reason: iteration primary delta `-3.9808928495421725e-05` did not meet `+0.002`.

The Orchestrator-provided test record was reused: ruff changed files passed, `git diff --check` passed, focused pytest selection `20 passed, 143 deselected`, and full `uv run pytest` `229 passed, 2 skipped in 187.72s`.

## Cache Reuse

- Iteration incumbent cache reused from `outputs/eval/iteration_dino_hsl2_theta.json` and `outputs/eval/iteration_dino_hsl2_theta.csv`.
- Validation incumbent cache was checked and available at `outputs/eval/validation_dino_hsl2_theta.json` and `outputs/eval/validation_dino_hsl2_theta.csv`, but candidate validation was not run.
- Cache checks passed: requested incumbent matched leaderboard; HEAD matched leaderboard `eval_code_commit` `72efada4e0afbd8e34e3184dbcef90cb91cc051c`; leaderboard protocols include iteration and validation; target variables and 1..15 day leads matched artifacts; incumbent artifact model names matched `dino_hsl2_theta`; primary scores were finite; guardrail records were present.
- Candidate source edits were not treated as cache invalidation under `roles/SCORER.md`.

## Gate Status

- Fast gate: passed. Candidate diagnostics failed `False`, issue count `0`.
- Iteration diagnostics: clean. Candidate diagnostics failed `False`, issue count `0`.
- Iteration primary delta gate: failed. Delta `-3.9808928495421725e-05` is below `+0.002`.
- Iteration RMSE guardrails: clean. Early mean guardrail violations `0`; per-variable/lead guardrail violations `0`.
- Validation: not run because iteration did not promote.

## Iteration Guardrails

Model-specific records: candidate `60`, incumbent `60`. Persistence rows were present in raw artifacts and excluded from guardrail comparisons.

Early day 1-5 mean RMSE relative regressions:
- `10m_u_component_of_wind`: `2.476201357291007e-05`; candidate mean `4.456723199372067`, incumbent mean `4.456612844664318`; passes 2% guardrail `True`.
- `2m_temperature`: `-1.212156765792373e-05`; candidate mean `4.822720981015117`, incumbent mean `4.822779440662406`; passes 2% guardrail `True`.
- `geopotential_500`: `5.330341545975514e-05`; candidate mean `613.8837458692572`, incumbent mean `613.8510255130138`; passes 2% guardrail `True`.
- `mean_sea_level_pressure`: `3.474470433707831e-05`; candidate mean `814.9745686778344`, incumbent mean `814.9462536112021`; passes 2% guardrail `True`.

Worst variable+lead RMSE regression: `mean_sea_level_pressure` at `360` hours, relative `0.00010533637568576736`, absolute `0.1488164647632857`, candidate RMSE `1412.9225500819641`, incumbent RMSE `1412.7737336172008`. This passes the 10% guardrail.

## Artifacts

- Candidate fast: `outputs/eval/fast_dino_hsl_picard.json`, `outputs/eval/fast_dino_hsl_picard.csv`.
- Candidate iteration: `outputs/eval/iteration_dino_hsl_picard.json`, `outputs/eval/iteration_dino_hsl_picard.csv`; run directory `outputs/eval/runs/iteration_dino_hsl_picard`.
- Candidate validation: not produced.
- Incumbent iteration cache: `outputs/eval/iteration_dino_hsl2_theta.json`, `outputs/eval/iteration_dino_hsl2_theta.csv`.
- Incumbent validation cache: `outputs/eval/validation_dino_hsl2_theta.json`, `outputs/eval/validation_dino_hsl2_theta.csv`.

## Anomalies

Fast and iteration completed normally. Both had quiet startup/compile intervals before progress output, but no infrastructure failure, nonfinite metric, diagnostic issue, or resource failure was observed. Golden was not run.

## Measurement Lessons

Evaluation artifacts include persistence baseline rows in addition to model rows; scoring comparisons must filter by `model_name`. The Picard-corrected departure was effectively neutral to slightly negative versus `dino_hsl2_theta` on the fixed iteration primary score while leaving RMSE guardrails clean.
