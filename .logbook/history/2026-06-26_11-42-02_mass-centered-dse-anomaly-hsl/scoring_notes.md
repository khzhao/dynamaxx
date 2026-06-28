# Scoring Notes

## Gate Status

- Fast gate: passed by the Orchestrator-provided fast run and Scorer artifact verification. Candidate fast primary score was `-0.2237799449232893`, diagnostics failed `false`, issue count `0`, and the artifact had `120` records.
- Iteration promotion gate: did not pass. Candidate iteration primary score was `-0.21968357037076797` versus cached incumbent `-0.2197104515448394`, for a delta of `+0.000026881174071430314`, below the required `+0.002`.
- Iteration diagnostics: passed. Candidate iteration diagnostics failed `false` with `0` issues.
- Iteration RMSE guardrails: passed. Early day 1-5 mean RMSE regressions were all below the `2%` limit, and the worst single variable/lead RMSE regression was `geopotential_500` at `24h` with `+0.0006775690481942966%`, below the `10%` limit.
- Validation: skipped. Validation is allowed only if the iteration primary delta is at least `+0.002` and diagnostics/guardrails pass; this candidate missed the primary threshold.

## Cache Reuse

- Incumbent iteration metrics were reused from the leaderboard cache: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Reuse checks passed: requested incumbent matched `.logbook/leaderboard.json`, current `HEAD` matched leaderboard `eval_code_commit` `ff40def55ac707e8915c840b856a0aaa3345b046`, the cached artifact was readable with finite primary score, clean diagnostics, `120` records, and `60` exact incumbent model rows for guardrail comparisons.
- Candidate source edits did not invalidate the accepted incumbent cache under `roles/SCORER.md`; no incumbent rerun was performed.
- Incumbent validation cache paths were recorded from the leaderboard but not used for a comparison because candidate validation was skipped.

## Commands

- `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter --workers 4`: exit `0`; wrote `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter.json` and `.csv`.
- `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter --workers 4`: not run; iteration did not promote.
- Pytest and fast evaluation were not rerun by Scorer because Orchestrator supplied passing records and the fast artifact was usable.

## Measurement Lessons

- The mass-centered DSE anomaly HSL variant is numerically clean but nearly neutral relative to the accepted incumbent.
- The tiny positive primary movement is not enough to justify validation under the fixed protocol; future variants need a materially larger aggregate skill gain, not guardrail repair.
- Metric JSON files include persistence reference rows, so guardrail comparisons must continue filtering records by exact candidate and incumbent `model_name`.

## Anomalies

- Candidate iteration ran from `229` uncached chunks and had long quiet intervals between chunk-completion batches, but it completed successfully without restart, worker-count change, or protocol change.
- No nonfinite scores, diagnostic failures, cache invalidations, or raw artifact read failures were observed.

## Recommendation To Orchestrator

Report this candidate as iteration-not-promoted. Do not run validation for this candidate state under the stated gate.
