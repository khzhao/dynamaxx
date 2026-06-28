# Scoring Notes

## Gate Status

- Model registration: candidate and incumbent are both registered in `src/dynamaxx/dycore/registry.py`.
- Incumbent cache: valid and reused from `.logbook/leaderboard.json`; no incumbent `dynamaxx-eval` command was run.
- Fast gate: passed from the Orchestrator-provided artifact, primary `-0.5144139357247745`, diagnostics `failed=false`, issues `0`, records `120`.
- Iteration gate: did not promote. Candidate primary `-0.49861953482554927`; cached incumbent primary `-0.49843977504709575`; delta `-0.00017975977845352542`, below the required `+0.002`.
- Iteration diagnostics: clean, `failed=false`, issues `0`, records `120`.
- Iteration guardrails: clean. Early day-1-to-5 mean RMSE guardrail passed for all target variables, and no variable-lead RMSE regression exceeded `10%`.
- Validation gate: not run because the iteration primary-delta threshold failed.

## Commands Run

| Command | Exit Status | Notes |
| --- | ---: | --- |
| `uv run python - <<'PY' ... dycore_model_names() ... PY` | 0 | Verified candidate and incumbent are registered. |
| `python - <<'PY' ... parse .logbook/leaderboard.json and cached incumbent artifacts ... PY` | 0 | Validated leaderboard cache and inspected artifact schema. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_exprelax --workers 4` | 0 | Candidate iteration only; stream reported `chunks=229 cached=0 pending=229`, then `failed=False issues=0 records=120 primary_score=-0.49862`. |

Commands not run by Scorer: `uv run pytest`, focused pytest, and candidate fast were accepted from the Orchestrator-provided passing records/artifacts. Candidate validation was not run because iteration did not promote. No incumbent eval command was run.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_exprelax.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_exprelax.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_exprelax.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_exprelax.csv`
- Incumbent iteration JSON reused from leaderboard: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.json`
- Incumbent iteration CSV reused from leaderboard: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.csv`
- Incumbent validation JSON validated from leaderboard but not compared: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.json`
- Incumbent validation CSV validated from leaderboard but not compared: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.csv`

## Guardrail Details

Early day-1-to-5 mean RMSE relative regressions:

| Variable | Regression Percent | Passed |
| --- | ---: | --- |
| `10m_u_component_of_wind` | `-3.333499892411371e-08` | yes |
| `2m_temperature` | `-1.0296054288948621e-08` | yes |
| `geopotential_500` | `-9.476601228740212e-08` | yes |
| `mean_sea_level_pressure` | `1.1943544735199726e-08` | yes |

Worst positive variable-lead RMSE regression was `2m_temperature` at day 7: `2.941961191834831e-07%`, well below the `10%` guardrail. There were no fixed guardrail violations.

## Cache Reuse

The incumbent model requested by the Orchestrator matches `.logbook/leaderboard.json.incumbent_model_name`. The leaderboard fingerprint has the same data path, target variables, lead range, and eval-code commit `681fe7c0d37fadbc1a91159a8d9a7f9f2543f185`, and it includes both `iteration` and `validation`. Cached iteration and validation artifacts exist, parse successfully, have finite primary scores, clean diagnostics, and 120 records each.

Incumbent metrics were reused from the leaderboard cache. No incumbent `dynamaxx-eval` command was run.

## Measurement Lessons

- The exact weak-HS exponential relaxation split does not materially change RMSE guardrails relative to the incumbent, but the primary score moved slightly downward on iteration.
- Since the primary delta was negative, the useful conclusion is available from iteration alone; validation would violate the fixed gate discipline.

## Recommendation To Orchestrator

Measured only. The candidate did not pass the iteration promotion gate; validation was not run. Acceptance or rejection remains with the Orchestrator.
