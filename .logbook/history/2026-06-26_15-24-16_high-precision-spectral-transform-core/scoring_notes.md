# Scoring Notes

## Gate Status

- Fast gate: passed from the pre-scoring artifact. `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec.json` reports primary score `-0.22382975498854574`, `failed=false`, `issues=0`, `records=120`, and `model_rows=60`.
- Iteration promotion gate: did not pass. Candidate iteration primary score was `-0.21972592802933302`; cached incumbent iteration primary score was `-0.2197104515448394`; signed delta was `-1.5476484493626153e-05`, below the required `+0.002` threshold.
- Iteration diagnostics and guardrails: diagnostics were clean with zero issues. Early day 1-5 mean RMSE guardrail passed for all variables, and no variable+lead RMSE regression exceeded the `+10%` guardrail.
- Validation acceptance gate: not evaluated. The fixed validation command was not run because iteration did not promote.
- Golden: not run.

## Commands And Status

- Read required instructions: `sed -n '1,240p' roles/PROTOCOL.md`, `sed -n '1,260p' roles/ORCHESTRATOR.md`, `sed -n '1,260p' roles/SCORER.md`, `sed -n '1,220p' roles/templates/scores.json`, and `sed -n '1,220p' roles/templates/scoring_notes.md`; all exited `0`.
- Confirmed registry construction with `uv run python - <<'PY' ... create_dycore_model(...) ... PY`: exit `0` for `dino_hsl2_mass_dse_wtg_vdse_ramp` and `dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec`.
- Checked fixed protocol diffs with `git diff --name-only src/dynamaxx/eval roles .logbook/leaderboard.json`: exit `0`, no output.
- Used provided test record without rerun: `uv run pytest` had already passed with `257 passed`, `2 skipped` in `311.70s`.
- Used provided fast record after artifact verification: `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec` had already exited `0`.
- Ran candidate iteration: `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec --workers 4` exited `0`, wrote `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec.json`, and reported `failed=False`, `issues=0`, `records=120`, primary score `-0.21972592802933302`.
- Computed guardrails with `python - <<'PY' ... load candidate and cached incumbent iteration JSON ... PY`: exit `0`.
- Did not run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec --workers 4` because iteration did not promote.

## Cache Reuse

- Candidate fast was reused from `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec.json` and `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec.csv` after verifying finite primary score, clean diagnostics, and 120 records with 60 candidate rows.
- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Incumbent iteration cache checks passed: requested incumbent matched the leaderboard incumbent, fingerprint fields matched, current HEAD matched `eval_code_commit` `ff40def55ac707e8915c840b856a0aaa3345b046`, fixed eval protocol files were not dirty, the artifact was readable, primary score was finite, model rows were present, and diagnostics were clean.
- Incumbent validation cache was not used for comparison because candidate validation was not run. The available cached paths are `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- No incumbent rerun was performed.

## Guardrail Details

- Early day 1-5 mean RMSE relative regressions: `10m_u_component_of_wind=+1.1463015576076144e-06`, `2m_temperature=+1.2602968186530021e-05`, `geopotential_500=+8.948725415482901e-06`, `mean_sea_level_pressure=+1.8487620322936296e-06`.
- Worst early day 1-5 mean RMSE regression: `2m_temperature`, `+1.2602968186530021e-05`, below the `+0.02` threshold.
- Worst variable+lead RMSE regression: `2m_temperature` at lead `240h`, candidate RMSE `7.489332786669537`, incumbent RMSE `7.4891119868385605`, relative regression `+2.948277864775715e-05`, below the `+0.10` threshold.
- Variable+lead RMSE regressions over `+10%`: none.

## Artifacts

- Candidate fast: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec.json`, `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec.csv`.
- Candidate iteration: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec.json`, `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec.csv`.
- Candidate validation: not run; no candidate validation artifact exists.
- Incumbent iteration cache: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`, `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Incumbent validation cache available but not used: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`, `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Score artifacts written here: `.logbook/history/2026-06-26_15-24-16_high-precision-spectral-transform-core/scores.json` and `.logbook/history/2026-06-26_15-24-16_high-precision-spectral-transform-core/scoring_notes.md`.

## Measurement Lessons

- The high-precision FastSphericalHarmonics transform path produced clean finite metrics but slightly worsened the iteration primary score relative to the cached incumbent.
- Guardrail movement was very small and clean; this result is about effect direction/size, not instability.
- This variant was expensive to evaluate, so future spectral-transform-core candidates should have a stronger expected accuracy mechanism before spending a full iteration run.

## Anomalies

- Cache reuse: no cache invalidation was found; incumbent iteration metrics were reused from the leaderboard pointer.
- Resource limits: no resource failure was observed during the candidate iteration run.
- Failed or restarted commands: an early exploratory registry probe used a nonexistent `get_model` helper and exited `1`; it was superseded by the correct `create_dycore_model` probe, and no files were modified.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status above. The candidate did not promote to validation under the fixed iteration gate; the Scorer does not accept or reject the candidate.
