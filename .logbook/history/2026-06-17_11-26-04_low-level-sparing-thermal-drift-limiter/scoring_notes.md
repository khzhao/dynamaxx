# Scoring Notes

## Gate Status

- Fast gate: passed by compatible artifact verification. `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter.json` has exact candidate `model_name`, case `fast`, `failed=false`, `issues=0`, `records=120`, and primary score `-1.1248138532182568`.
- Iteration promotion gate: failed. Candidate iteration primary score was `-1.1454928597212104`; incumbent iteration primary score was `-1.143975258592661`; delta was `-0.001517601128549373`, below the required `+0.002`.
- Validation acceptance gate: not run. Validation was allowed only if the iteration gate passed.
- Golden: not run, as required by the protocol and Orchestrator instructions.

## Iteration Guardrails

- Diagnostics were clean for both candidate and incumbent iteration artifacts: `failed=false`, `issues=0`.
- Exact filtering was used before comparison: candidate artifact contained 60 evaluated candidate rows and 60 persistence rows; incumbent artifact contained 60 evaluated incumbent rows and 60 persistence rows. Persistence rows were excluded from all guardrail calculations.
- Early day 1-5 mean RMSE relative changes: `geopotential_500` `+0.108127%`, `10m_u_component_of_wind` `+0.086147%`, `mean_sea_level_pressure` `+0.064972%`, and `2m_temperature` `+0.018222%`. No early mean RMSE regression exceeded the 2% guardrail.
- Variable+lead RMSE guardrail passed. The largest single variable+lead RMSE regression was `10m_u_component_of_wind` at 144h: `+0.217026%` (`12.108369232386915` candidate RMSE versus `12.082147845212761` incumbent RMSE), below the 10% threshold.
- Largest single variable+lead improvements were small and late pressure improvements: `mean_sea_level_pressure` 360h `-0.072926%`, 336h `-0.018929%`, 24h `-0.001222%`, and 312h `-0.001156%`.

## Commands And Artifacts

- `uv run python - <<'PY' ... registry check ... PY`: exit `0`; confirmed candidate and incumbent are registered and construct with exact names.
- `uv run pytest`: exit `0`; `130 passed, 2 skipped in 65.90s`.
- `uv run python - <<'PY' ... fast artifact verification ... PY`: exit `0`; reused compatible candidate fast artifact.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter --workers 4`: exit `0`; wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter.json` and `.csv`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter --workers 4`: not run because iteration did not promote.

## Measurement Lessons

- The low-level-sparing upper thermal limiter was numerically stable and avoided the large near-surface wind guardrail failure that motivated the proposal, but it did not recover the prior full-column thermal recentering score gain.
- The candidate worsened the aggregate iteration primary score while producing only small guardrail-clean RMSE changes, so the loss appears to be broad weak degradation rather than a localized catastrophic failure.
- The largest regressions remained in `10m_u_component_of_wind` at mid-range leads, suggesting future thermal drift controls should be even more isolated from momentum-coupled balanced dynamics or justified by a separate mechanism.

## Anomalies

- Cache reuse: candidate fast artifact was reused after exact compatibility checks; incumbent iteration and validation artifacts from the leaderboard were reused. Candidate iteration was a fresh run with `cached=0`.
- Resource limits: none observed. Iteration used 4 effective GPU workers across 4 GPUs.
- Failed or restarted commands: one initial exploratory registration probe imported a non-existent `get_forecast_model` helper and exited `1`; the correct registry API check passed before scoring continued.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status: fast passed, iteration did not promote to validation because primary delta was negative. Guardrails and diagnostics were clean. This scorer report does not accept or reject the candidate.
