# Scoring Notes

## Gate Status

- Fast gate: passed by compatible artifact verification. `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential.json` has exact candidate `model_name`, case `fast`, `failed=false`, `issues=0`, `records=120`, and primary score `-1.123860954738728`.
- Iteration promotion gate: failed. Candidate iteration primary score was `-1.1442516002936804`; incumbent iteration primary score was `-1.143975258592661`; delta was `-0.00027634170101942246`, below the required `+0.002`.
- Validation acceptance gate: not run. The Orchestrator allowed validation only if the iteration gate passed.

## Iteration Guardrails

- Diagnostics were clean for both candidate and incumbent iteration artifacts: `failed=false`, `issues=0`.
- Exact filtering was used before comparison: candidate artifact contained 60 evaluated candidate rows and 60 persistence rows; incumbent artifact contained 60 evaluated incumbent rows and 60 persistence rows. Persistence rows were excluded from all guardrail calculations.
- Early day 1-5 mean RMSE relative changes: `geopotential_500` `+1.877829%`, `mean_sea_level_pressure` `+0.0000059%`, `2m_temperature` `+0.00000021%`, `10m_u_component_of_wind` `-0.0000061%`. No early mean RMSE regression exceeded the 2% guardrail.
- Variable+lead RMSE guardrail failed: `geopotential_500` at 24h regressed by `+19.566144%` (`315.50069562137014` candidate RMSE versus `263.8712637418557` incumbent RMSE), exceeding the 10% threshold.
- Other notable positive Z500 RMSE changes were 48h `+3.176886%`, 72h `+0.548084%`, and 96h `+0.099370%`. Later Z500 leads improved, with the largest relative improvement at 360h `-0.650077%`.

## Commands And Artifacts

- `uv run python - <<'PY' ... registry check ... PY`: exit `0`; confirmed candidate and incumbent are registered and construct with exact names.
- `uv run pytest`: exit `0`; `128 passed, 2 skipped in 66.41s`.
- `python - <<'PY' ... fast artifact verification ... PY`: exit `0`; reused compatible candidate fast artifact.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential --workers 4`: exit `0`; wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential.json` and `.csv`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential --workers 4`: not run because iteration did not promote.

## Measurement Lessons

- The dry geopotential diagnostic caused a large short-lead Z500 degradation even though later Z500 leads improved modestly. For this benchmark, the passive-humidity virtual-temperature diagnostic appears beneficial at the first forecast day.
- Non-geopotential target differences were roundoff-scale, matching the proposal's expectation that the change should be output-path-local.
- Exact `model_name` filtering is required for these eval files because each artifact includes evaluated model rows and persistence rows with duplicate `(channel_name, lead_hours)` keys.

## Anomalies

- Cache reuse: candidate fast artifact was reused after exact compatibility checks; incumbent iteration and validation artifacts from the leaderboard were reused. Candidate iteration was a fresh run with `cached=0`.
- Resource limits: none observed. Iteration used 4 effective GPU workers across 4 GPUs.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status: fast passed, iteration did not promote to validation because primary delta was negative and the variable+lead RMSE guardrail failed. This scorer report does not accept or reject the candidate.
