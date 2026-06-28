# Scoring Notes

## Gate Status

- Registration gate: candidate `dino_hsl_mean` and incumbent `dino_hsl2_theta` both registered and constructible.
- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_hsl_mean` exited 0 with `failed=False`, 0 issues, and primary score `-0.31548604596241886`.
- Iteration gate: did not promote to validation. Candidate iteration primary score was `-0.31273598260124896`; cached incumbent iteration primary score was `-0.31282890543336245`; delta was `+0.00009292283211348451`, below the required `+0.002`.
- Validation gate: not run. Validation was allowed by the Orchestrator only if iteration passed the promotion gates.

## Cache Reuse

- Read `.logbook/leaderboard.json`; requested incumbent matched leaderboard incumbent `dino_hsl2_theta`.
- Reused cached incumbent iteration artifacts: `outputs/eval/iteration_dino_hsl2_theta.json` and `outputs/eval/iteration_dino_hsl2_theta.csv`.
- Incumbent iteration cache checks passed: artifact readable, `model_name=dino_hsl2_theta`, finite `primary_score=-0.31282890543336245`, diagnostics `failed=False`, 0 issues, and 60 incumbent model records after filtering out persistence rows.
- Did not rerun incumbent iteration because the cache was valid under `roles/PROTOCOL.md` and `roles/SCORER.md`.
- Cached incumbent validation artifacts were readable at `outputs/eval/validation_dino_hsl2_theta.json` and `outputs/eval/validation_dino_hsl2_theta.csv`, with finite `primary_score=-0.3072374345999185`; no validation comparison was needed because candidate iteration did not promote.

## Guardrails

- Diagnostics: candidate iteration `failed=False`, 0 issues; incumbent iteration `failed=False`, 0 issues.
- Record filtering: candidate and incumbent iteration artifacts each had 120 records total, 60 model-specific records after filtering by `model_name`; persistence rows were excluded from comparisons.
- Early day 1-5 mean RMSE deltas:
  - `10 m zonal wind`: `+0.00027903216842606327` RMSE regression.
  - `2 m temperature`: `-0.00010164103265974944`.
  - `500 hPa geopotential`: `-0.009776888161923125`.
  - `Mean sea level pressure`: `-0.043327683350185`.
- Worst variable+lead RMSE regression: `500 hPa geopotential` at 216 hours, candidate `1188.3836458072471` vs incumbent `1188.313688021434`, delta `+0.06995778581313061`.
- Positive per-variable/per-lead RMSE regressions: 30 of 60 compared model records.

## Commands

- Orchestrator test record reused: ruff passed; `git diff --check` passed; focused pytest selection had 22 passed and 143 deselected in 55.30s; full `uv run pytest` had 231 passed and 2 skipped in 185.57s.
- Registration check exited 0.
- `uv run dynamaxx-eval fast --model dino_hsl_mean`: started `2026-06-23T00:54:53Z`, finished `2026-06-23T00:59:05Z`, exit 0.
- `uv run dynamaxx-eval iteration --model dino_hsl_mean --workers 4`: started `2026-06-23T00:59:09Z`, finished `2026-06-23T02:59:30Z`, exit 0.
- `uv run dynamaxx-eval validation --model dino_hsl_mean --workers 4`: skipped by protocol gate.

## Measurement Lessons

- Mean-neutral HSL theta transport gave only a very small iteration primary improvement over the incumbent and introduced small RMSE regressions in 30 of 60 model records.
- Early lead pressure and geopotential improved slightly on average, but the largest individual RMSE regression occurred in 500 hPa geopotential at day 9.
- Future proposals should target larger primary-score movement before spending validation compute; this candidate did not meet the validation promotion threshold.

## Anomalies

- Resource limits: none observed.
- Failed or restarted commands: none for fixed scoring commands.
- Nonfinite or unstable outputs: none observed.
- Runtime: candidate iteration completed successfully but took about 2 hours with 4 workers.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. Do not accept or reject the candidate from the Scorer role.
