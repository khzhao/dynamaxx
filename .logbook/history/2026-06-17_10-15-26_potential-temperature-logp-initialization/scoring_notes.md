# Scoring Notes

## Gate Status

- Fast gate: passed by compatible artifact verification. `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init.json` has exact candidate `model_name`, case `fast`, `failed=false`, `issues=0`, `records=120`, and primary score `-1.1259234428450748`.
- Iteration promotion gate: failed. Candidate iteration primary score was `-1.1448887048318772`; incumbent iteration primary score was `-1.143975258592661`; delta was `-0.0009134462392161868`, below the required `+0.002`.
- Validation acceptance gate: not run. Validation was allowed only if the iteration gate passed.

## Iteration Guardrails

- Diagnostics were clean for both candidate and incumbent iteration artifacts: `failed=false`, `issues=0`.
- Exact filtering was used before comparison: candidate artifact contained 60 evaluated candidate rows and 60 persistence rows; incumbent artifact contained 60 evaluated incumbent rows and 60 persistence rows. Persistence rows were excluded from all guardrail calculations.
- Early day 1-5 mean RMSE relative changes: `geopotential_500` `+0.060270%`, `10m_u_component_of_wind` `+0.037662%`, `mean_sea_level_pressure` `+0.029653%`, and `2m_temperature` `-0.009950%`. No early mean RMSE regression exceeded the 2% guardrail.
- Variable+lead RMSE guardrail passed. The largest single variable+lead RMSE regression was `mean_sea_level_pressure` at 168h: `+0.144944%` (`1982.0993870855154` candidate RMSE versus `1979.2306024453237` incumbent RMSE), below the 10% threshold.
- Largest single variable+lead RMSE improvements were small and short-lead: `2m_temperature` 48h `-0.037320%`, `10m_u_component_of_wind` 48h `-0.033969%`, and `10m_u_component_of_wind` 24h `-0.032688%`.

## Commands And Artifacts

- `uv run python - <<'PY' ... registry check ... PY`: exit `0`; confirmed candidate and incumbent are registered and construct with exact names.
- `uv run pytest`: exit `0`; `132 passed, 2 skipped in 66.55s`.
- `python - <<'PY' ... fast artifact verification ... PY`: exit `0`; reused compatible candidate fast artifact.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init --workers 4`: exit `0`; wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init.json` and `.csv`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init --workers 4`: not run because iteration did not promote.

## Measurement Lessons

- Potential-temperature log-pressure initialization is numerically stable and has clean diagnostics, but it worsened the fixed iteration primary score relative to the incumbent.
- The RMSE movements were all small and guardrail-clean, so the score loss appears to be broad aggregate skill drift rather than a localized catastrophic regression.
- Future temperature-remap proposals should show a clearer mechanism for improving weighted aggregate skill, because preserving thermodynamic form alone did not improve this benchmark.

## Anomalies

- Cache reuse: candidate fast artifact was reused after exact compatibility checks; incumbent iteration and validation artifacts from the leaderboard were reused. Candidate iteration was a fresh run with `cached=0`.
- Resource limits: none observed. Iteration used 4 effective GPU workers across 4 GPUs.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status: fast passed, iteration did not promote to validation because primary delta was negative. Guardrails and diagnostics were clean. This scorer report does not accept or reject the candidate.
