# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_hsl2_mse_hsl` exited `0`; candidate diagnostics had `failed=False`, `issues=0`, and primary_score `-0.26764946011232993`.
- Iteration promotion gate: failed. Candidate iteration primary_score `-0.2673741387223367` versus cached incumbent `-0.26737373217433574` gives delta `-4.0654800093076204e-07`, below the `+0.002` promotion threshold. Candidate iteration diagnostics were clean: `failed=False`, `issues=0`.
- Iteration RMSE guardrails: passed. Worst day 1-5 mean RMSE regression was `mean_sea_level_pressure` at `8.742268421735428e-06%` against the `2%` limit. Worst variable+lead RMSE regression was `2m_temperature` at lead `336` hours with `0.00018122650088975333%` against the `10%` limit.
- Validation acceptance gate: not evaluated. Validation was allowed only if iteration promoted, and the iteration primary delta failed. Candidate validation was not run.
- Golden: not run.

## Commands And Status

| Command | Exit status |
| --- | ---: |
| `sed -n '1,240p' roles/PROTOCOL.md` | 0 |
| `sed -n '1,260p' roles/SCORER.md` | 0 |
| `rg -n "dino_hsl2_mse_hsl|dino_hsl2_theta_dse_hsl" src tests .logbook/leaderboard.json` | 0 |
| `sed -n '1,220p' .logbook/leaderboard.json` | 0 |
| `ls -la .logbook/history/2026-06-23_14-39-53_moist-static-energy-hsl-transport outputs/eval` | 0 |
| `git rev-parse HEAD && git status --short` | 0 |
| `jq ... outputs/eval/iteration_dino_hsl2_theta_dse_hsl.json` | 0 |
| `jq ... outputs/eval/validation_dino_hsl2_theta_dse_hsl.json` | 0 |
| `rg -n "promotion|guardrail|early|worst variable|primary_score|iteration.*pass|validation.*run" roles .logbook/history -g 'scoring_notes.md' -g 'scores.json' -g '*.md'` | 0 |
| `sed -n '1,220p' roles/templates/scoring_notes.md 2>/dev/null || true && ls roles/templates` | 0 |
| `sed -n '340,420p' roles/PROTOCOL.md` | 0 |
| `uv run python - <<'PY' ... import list_dycore_models ... PY` | 1 |
| `sed -n '1,330p' src/dynamaxx/dycore/registry.py` | 0 |
| `uv run python - <<'PY' ... create_dycore_model, dycore_model_names ... PY` | 0 |
| `uv run dynamaxx-eval fast --model dino_hsl2_mse_hsl` | 0 |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mse_hsl --workers 4` | 0 |
| `jq '.model_name, .primary_score, .diagnostics, .records[0], (.records | length)' outputs/eval/iteration_dino_hsl2_mse_hsl.json` | 0 |
| `jq '.model_name, .primary_score, .diagnostics, .records[0], (.records | length)' outputs/eval/iteration_dino_hsl2_theta_dse_hsl.json` | 0 |
| `ls -l outputs/eval/iteration_dino_hsl2_mse_hsl.json outputs/eval/iteration_dino_hsl2_mse_hsl.csv outputs/eval/fast_dino_hsl2_mse_hsl.json outputs/eval/fast_dino_hsl2_mse_hsl.csv outputs/eval/validation_dino_hsl2_theta_dse_hsl.json outputs/eval/validation_dino_hsl2_theta_dse_hsl.csv` | 0 |
| `uv run python - <<'PY' ... write scores.json and scoring_notes.md ... PY` | 0 |

The failed registration probe was a scorer-side helper-name mistake (`list_dycore_models` does not exist). It made no source or metric changes and was followed by a successful registration check using `dycore_model_names`.

## Cache Reuse

- Iteration incumbent cache: reused from `outputs/eval/iteration_dino_hsl2_theta_dse_hsl.json` and `outputs/eval/iteration_dino_hsl2_theta_dse_hsl.csv`. Checks performed: requested incumbent matched `.logbook/leaderboard.json`; fingerprint data path, protocols, target variables, lead range, and eval code commit matched; artifact was readable with finite primary_score `-0.26737373217433574` and all 60 incumbent guardrail rows.
- Validation incumbent cache: retained and verified from `outputs/eval/validation_dino_hsl2_theta_dse_hsl.json` and `outputs/eval/validation_dino_hsl2_theta_dse_hsl.csv` for reference, with finite primary_score `-0.2654819769882763` and all 60 incumbent guardrail rows. Candidate validation did not run because iteration did not promote, so no validation comparison was performed.
- Incumbent rerun: not performed for any protocol. Candidate side-by-side edits did not invalidate the accepted incumbent cache.

## RMSE Guardrails

Iteration early day 1-5 mean RMSE regressions:
- `2m_temperature`: candidate `4.732860661717025`, incumbent `4.732861762229853`, regression `-2.3252587624786165e-05%`, violates 2% guardrail: `false`.
- `mean_sea_level_pressure`: candidate `785.9715552523046`, incumbent `785.9714865405675`, regression `8.742268421735428e-06%`, violates 2% guardrail: `false`.
- `geopotential_500`: candidate `601.6651491533072`, incumbent `601.6651246796225`, regression `4.067658847322691e-06%`, violates 2% guardrail: `false`.
- `10m_u_component_of_wind`: candidate `4.378332177140811`, incumbent `4.378331916002656`, regression `5.964329787363336e-06%`, violates 2% guardrail: `false`.

Worst variable+lead RMSE regression: `2m_temperature` at lead `336` hours; candidate RMSE `7.81043467756656`, incumbent RMSE `7.810420523014741`, regression `0.00018122650088975333%`. Variable+lead regressions over 10%: `0`.

## Measurement Lessons

- The candidate is stable and guardrail-clean under the fixed fast and iteration protocols.
- The MSE-HSL mechanism is effectively neutral relative to the DSE-HSL incumbent; the measured iteration primary delta is slightly negative and therefore does not justify validation under the fixed gate.

## Anomalies

- Cache reuse: no cache invalidation found. Incumbent iteration and validation artifacts were reused or retained from the leaderboard pointer.
- Resource limits: no resource failure observed. Candidate iteration ran with 4 effective GPU workers.
- Failed or restarted commands: one registration probe failed due to a nonexistent helper name, then succeeded with the actual registry API.
- Nonfinite or unstable outputs: none observed in the candidate fast or iteration outputs.

## Recommendation To Orchestrator

Report the measured status as iteration-not-promoted. Do not run validation for this candidate under the fixed gate. Scorer does not accept or reject the candidate.
