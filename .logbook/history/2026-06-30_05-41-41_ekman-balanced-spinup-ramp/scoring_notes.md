# Scoring Notes

## Gate Status

- Registration gate: passed after corrected registry API check. Both `dino_ri2m_ekman_spinup` and `dino_ri2m_ekman_coupled` were listed by `dycore_model_names()` and instantiated via `create_dycore_model()`.
- Test gate: passed from Implementer evidence, not rerun by Scorer. Recorded result was `uv run pytest` with 283 passed and 2 skipped.
- Fast gate: passed from existing candidate artifacts, not rerun by Scorer. `outputs/eval/fast_dino_ri2m_ekman_spinup.json` has `failed=false`, 0 issues, 120 records, and primary score `-0.16944049595409852`.
- Iteration promotion gate: failed. Candidate iteration primary was `-0.16669329268791927`; cached incumbent iteration primary was `-0.16500618979404214`; delta was `-0.0016871028938771349`, below the required `+0.002`.
- Validation acceptance gate: not evaluated. Validation was skipped because the iteration promotion gate failed.

## Cache Reuse

- Iteration incumbent metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` and `.csv`. The artifact was readable, matched incumbent model `dino_ri2m_ekman_coupled`, had finite primary score `-0.16500618979404214`, clean diagnostics, 120 records, target variables compatible with the candidate protocol, and lead range 1..15 days.
- Validation incumbent metrics were validated for cache reuse but not compared to a candidate validation run: `outputs/eval/validation_dino_ri2m_ekman_coupled.json` and `.csv`. The artifact was readable, matched the incumbent model, had finite primary score `-0.16591150807771451`, clean diagnostics, and compatible target variables/leads.
- No incumbent evaluation was rerun. Candidate source edits did not invalidate the accepted incumbent cache, and committed changes after accepted source commit `d187308d30a242bf38aabe5b7eb530fca522a68f` were logbook metadata.

## Guardrails

- Candidate iteration diagnostics were clean: `failed=false`, 0 issues.
- Mean RMSE regression over leads 1-5 days was numerical-noise scale for all variables: `10m_u_component_of_wind=-1.6786016268854628e-10`, `2m_temperature=7.637519481944547e-10`, `geopotential_500=-2.8063621466846174e-10`, `mean_sea_level_pressure=4.009995492379207e-10`.
- Maximum per-variable/lead RMSE regression was also numerical-noise scale, with the largest observed relative regression `2.947238311114127e-09` for `mean_sea_level_pressure` at 24h.
- Guardrails did not block promotion; the primary score gate did.

## Commands

- `uv run python - <<'PY' ... from dynamaxx.dycore.registry import list_models ... PY`: exit 1. Scorer probe used a nonexistent helper name; no files were modified.
- `uv run python - <<'PY' ... dycore_model_names/create_dycore_model registration check ... PY`: exit 0.
- `uv run pytest`: exit 0 from Implementer evidence; not rerun by Scorer.
- `uv run dynamaxx-eval fast --model dino_ri2m_ekman_spinup`: exit 0 from existing Implementer artifact; not rerun by Scorer.
- `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_spinup --workers 4`: exit 0. Wrote `outputs/eval/iteration_dino_ri2m_ekman_spinup.json` and `.csv`.
- `uv run dynamaxx-eval validation --model dino_ri2m_ekman_spinup --workers 4`: skipped because iteration did not promote.

## Anomalies

- The only command anomaly was the initial scorer registration probe importing `list_models`, which does not exist in this registry. The corrected registration check passed and the failed probe did not affect candidate evaluation.
- The iteration run was long but made steady chunk progress and completed without restart.
- No nonfinite or unstable forecast diagnostics were reported.

## Measurement Lessons

- The positive-time Ekman spinup ramp left RMSE nearly indistinguishable from the incumbent at the reported precision, but reduced the primary skill enough to miss the promotion threshold.
- Future variants of this idea should justify a mechanism that can improve skill, not only preserve RMSE, before spending validation compute.

## Recommendation To Orchestrator

Report this as a measured non-promotion. The candidate should not proceed to validation under the fixed gate because iteration primary delta was negative.
