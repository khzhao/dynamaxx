# Scoring Notes

## Gate Status

- Fast gate: passed from the Orchestrator-provided candidate fast result. Candidate fast had `failed=false`, `issues=0`, `records=120`, and `primary_score=-0.5141372750454984`.
- Iteration gate: failed. Candidate iteration primary score was `-0.4989518866948269`; cached incumbent iteration primary score was `-0.49843977504709575`; delta was `-0.0005121116477311283`, below the `+0.002` promotion threshold.
- Iteration diagnostics: passed with `failed=false` and `issues=0`.
- Iteration guardrails: passed. No target variable had day 1-5 mean RMSE regression greater than `2%`, and no target variable/lead RMSE regression exceeded `10%`.
- Validation gate: not run. Validation is allowed only if the iteration promotion gate passes.
- Golden: not run.

## Cache Reuse

Incumbent iteration metrics were reused from `.logbook/leaderboard.json` and were not recomputed. The cache was valid because the requested incumbent matched the leaderboard incumbent, the leaderboard fingerprint matched the fixed data path, target variables, lead range, and evaluation code commit, and the iteration artifact parsed with a finite primary score, clean diagnostics, and 120 records with finite RMSE rows.

Cached incumbent validation metrics were also validated from `.logbook/leaderboard.json`, with the same fingerprint and artifact-shape checks. Candidate validation was not run because the iteration gate failed, so no validation comparison was performed. No incumbent validation eval was run.

Candidate source edits in the current worktree were not treated as invalidating the accepted incumbent cache, per `roles/PROTOCOL.md` and `roles/SCORER.md`.

## Commands And Artifacts

- Registry validation: the first probe used `get_forecast_model` and exited `1` because that helper is not exported. The corrected probe used `create_dycore_model` and `dycore_model_names`, exited `0`, and confirmed both candidate and incumbent are registered and instantiate.
- Candidate iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_landsea_wind --workers 4` -> exit status `0`.
- Candidate validation: not run because iteration failed the primary-delta promotion gate.
- Incumbent evals: not run. Incumbent metrics were reused from leaderboard cache.
- Candidate fast artifacts: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_landsea_wind.json` and matching `.csv`.
- Candidate iteration artifacts: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_landsea_wind.json` and matching `.csv`.
- Cached incumbent iteration artifacts: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.json` and matching `.csv`.
- Cached incumbent validation artifacts: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.json` and matching `.csv`.

## Guardrails

Day 1-5 mean RMSE regressions:

| Channel | Candidate mean RMSE | Incumbent mean RMSE | Relative regression |
| --- | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 4.778312127554878 | 4.778312126939291 | 0.000000012882950392448922% |
| `2m_temperature` | 2.7938222604075706 | 2.793822259840022 | 0.00000002031441594842679% |
| `geopotential_500` | 878.0844087031983 | 878.0844091921903 | -0.00000005568849433370405% |
| `mean_sea_level_pressure` | 817.7806708773476 | 817.7806709057728 | -0.000000003475899435344886% |

Largest per-variable single-lead RMSE regressions:

| Channel | Lead hours | Candidate RMSE | Incumbent RMSE | Relative regression |
| --- | ---: | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 168 | 5.3048944354155 | 5.304894429114602 | 0.00000011877519060635271% |
| `2m_temperature` | 48 | 2.666566417582167 | 2.666566409356025 | 0.00000030849192283178415% |
| `geopotential_500` | 24 | 600.0896798281522 | 600.0896776607141 | 0.0000003611856967250104% |
| `mean_sea_level_pressure` | 144 | 953.0460591535004 | 953.0460569986527 | 0.00000022610111073639826% |

## Measurement Lessons

- The land-sea wind residual candidate is numerically clean and does not trip RMSE guardrails, but it slightly worsens the iteration primary score.
- The near-zero RMSE differences indicate the implemented wind residual memory has little measurable effect on the fixed iteration fields, while the aggregate primary still moves in the wrong direction.
- Validation would not add useful selection evidence for this candidate state because the fixed iteration promotion threshold was not met.

## Anomalies

- The only command anomaly was the initial registry probe using a non-existent helper; the corrected registry validation passed.
- No resource failures, nonfinite outputs, failed diagnostics, or metric-shape anomalies were observed.
- Candidate iteration was fully uncached (`cached=0`, `pending=229`) and ran with 4 requested and 4 effective GPU workers.

## Recommendation To Orchestrator

Measured iteration gate status is failed; validation was not run. This is a measurement report only and does not accept or reject the candidate.
