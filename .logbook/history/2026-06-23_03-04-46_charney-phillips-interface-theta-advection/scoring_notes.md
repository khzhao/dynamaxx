# Scoring Notes

## Gate Status

- Fast gate: failed. `uv run dynamaxx-eval fast --model dino_hsl2_theta_cpvert` exited 0, but the metric result reported `diagnostics.failed=true`, 2 diagnostic issues, and `primary_score=-Infinity`.
- Iteration promotion gate: not reached. The fixed protocol requires fast to pass before running `uv run dynamaxx-eval iteration --model dino_hsl2_theta_cpvert --workers 4`.
- Validation acceptance gate: not reached. Validation was allowed by the Orchestrator only if iteration passed the promotion gates.

## Measurements

- Candidate fast artifacts: `outputs/eval/fast_dino_hsl2_theta_cpvert.json` and `outputs/eval/fast_dino_hsl2_theta_cpvert.csv`.
- Candidate fast diagnostics: `nonfinite_forecast` with value `392736960`, and `nonfinite_metric` with value `224`.
- Candidate fast CSV contained 120 total metric rows. Filtering by `model_name == "dino_hsl2_theta_cpvert"` gave 60 candidate rows; those candidate rows contained 224 nonfinite values across `rmse`, `mae`, `bias`, and `skill_vs_persistence`. Persistence rows were not used for candidate scoring.
- The candidate has finite fast rows at lead 24 hours, but all four candidate metric fields are nonfinite from lead 48 hours onward.
- Candidate iteration score: not available because iteration was skipped after fast failure.
- Candidate validation score: not available because validation was skipped after fast failure.
- Cached incumbent iteration score: `-0.31282890543336245` from `outputs/eval/iteration_dino_hsl2_theta.json`.
- Cached incumbent validation score: `-0.3072374345999185` from `outputs/eval/validation_dino_hsl2_theta.json`.
- Iteration primary delta, early day 1-5 mean RMSE regressions, and worst variable+lead RMSE regression were not computed because the candidate did not run iteration.

## Cache Reuse

- Incumbent iteration metrics were reused from the leaderboard pointer. The requested incumbent matches `.logbook/leaderboard.json`, the artifact is readable, `primary_score` is finite, `diagnostics.failed=false`, diagnostic issue count is 0, the CSV has 60 rows after filtering to `dino_hsl2_theta`, and those filtered rows have no nonfinite metric values.
- Incumbent validation metrics were reused from the leaderboard pointer under the same checks. Validation comparison was not reached, but the cache was validated and not rerun.
- No incumbent evaluation was rerun. Candidate source edits do not invalidate the accepted incumbent cache under `roles/PROTOCOL.md` and `roles/SCORER.md`.

## Commands

- `sed -n '1,240p' roles/PROTOCOL.md`: exit 0.
- `sed -n '1,260p' roles/SCORER.md`: exit 0.
- `sed -n '1,240p' .logbook/leaderboard.json`: exit 0.
- Registration check through `DYCORE_MODEL_FACTORIES`: exit 0; `dino_hsl2_theta_cpvert` maps to `dino_hsl2_theta_cpvert_model`, and `dino_hsl2_theta` maps to `dino_hsl2_theta_model`.
- `uv run dynamaxx-eval fast --model dino_hsl2_theta_cpvert`: exit 0; metric result failed.
- `uv run dynamaxx-eval iteration --model dino_hsl2_theta_cpvert --workers 4`: skipped by protocol.
- `uv run dynamaxx-eval validation --model dino_hsl2_theta_cpvert --workers 4`: skipped by protocol.

## Prior Artifacts

- The preserved pre-repair fast failure artifacts remain at `.logbook/history/2026-06-23_03-04-46_charney-phillips-interface-theta-advection/fast_failed_pre_repair.json` and `.logbook/history/2026-06-23_03-04-46_charney-phillips-interface-theta-advection/fast_failed_pre_repair.csv`.
- The post-repair behavior changed from fully nonfinite fast candidate rows to finite day-1 fast rows followed by nonfinite rows from 48 hours onward, but it still fails the fast gate.

## Measurement Lessons

- The bounded fallback did not fully arrest the instability in the 15-day fast forecast. Future repair should inspect the state transition between 24 and 48 hours and should verify that fallback coverage applies to every vertical tendency path that can contaminate theta or downstream prognostic fields.
- The scorer should continue filtering metric rows by `model_name`; candidate artifacts include persistence rows that are useful baselines but must not contaminate candidate diagnostics or guardrail comparisons.

## Anomalies

- Resource limits: no resource failure observed. During fast evaluation, the process was actively using CPU and GPU 0 while stdout was quiet.
- Failed or restarted commands: no command was restarted. The fast command exited 0 but produced a failed metric result.
- Nonfinite or unstable outputs: candidate fast forecast and metrics remained nonfinite after repair.

## Recommendation To Orchestrator

Report the measured gate status and caveats. Do not accept or reject the candidate here.
