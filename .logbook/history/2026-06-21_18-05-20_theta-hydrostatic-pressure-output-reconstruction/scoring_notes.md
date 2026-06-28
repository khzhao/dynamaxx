# Scoring Notes

## Gate Status

- Fast gate: passed from verified existing artifact `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_hydrostatic_output.json`; primary `-0.5436511302724413`, failed=`False`, issues=`0`.
- Iteration promotion gate: did not pass. Candidate primary `-0.5291823004046923` versus cached incumbent primary `-0.5150627015910243` gives delta `-0.014119598813667977`; required delta is at least `0.002`.
- Iteration diagnostics: passed, failed=`False`, issues=`0`.
- Early day 1-5 mean RMSE guardrail: passed.
- Worst variable+lead RMSE guardrail: passed; worst regression was `2 m temperature` at `96` hours with `3.0959957598042456e-07` percent RMSE delta.
- Validation acceptance gate: not evaluated because iteration did not promote; candidate validation was not run.

## Primary Scores

- Candidate fast primary: `-0.5436511302724413`.
- Candidate iteration primary: `-0.5291823004046923`.
- Incumbent iteration primary, reused from cache: `-0.5150627015910243`.
- Iteration primary delta: `-0.014119598813667977`.
- Incumbent validation primary, cache available but not used for a validation delta: `-0.5044433981077879`.
- Candidate validation primary and validation delta: not available because validation was skipped.

## RMSE Guardrails

| Variable | Lead window | Candidate mean RMSE | Incumbent mean RMSE | Percent delta | Exceeds 2% |
| --- | --- | ---: | ---: | ---: | --- |
| 10 m zonal wind | 1..5 days | 4.778312126309776 | 4.778312124724008 | 3.318678060359885e-08 | False |
| 2 m temperature | 1..5 days | 2.79382226105272 | 2.793822259777979 | 4.5627124378940354e-08 | False |
| 500 hPa geopotential | 1..5 days | 878.0844080523455 | 878.0844084065939 | -4.034332124824582e-08 | False |
| Mean sea level pressure | 1..5 days | 817.7806713011605 | 817.7806712478796 | 6.515307830968939e-09 | False |


Worst variable+lead RMSE regression: `2 m temperature` at `96` hours (`4.0` days), candidate RMSE `3.1008938848315064`, incumbent RMSE `3.100893875231152`, percent delta `3.0959957598042456e-07`, exceeds 10%=`False`.

## Cache Reuse

- Iteration incumbent metrics were reused from `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`. The requested incumbent matched `.logbook/leaderboard.json`, the leaderboard fingerprint covered the iteration protocol, the JSON was readable, the model name matched, primary score was finite, and 120 records were present.
- Validation incumbent artifacts `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv` were present and readable, but validation comparison was skipped because the candidate did not pass iteration promotion.
- Incumbent was not rerun.

## Commands And Statuses

- `sed -n '1,240p' roles/PROTOCOL.md` -> exit 0.
- `sed -n '1,240p' roles/SCORER.md` -> exit 0.
- `python - <<'PY' ... from dynamaxx.dycore.registry import list_dycore_models ... PY` -> exit 1; wrong helper name, corrected before evaluation.
- `uv run python - <<'PY' ... from dynamaxx.dycore.registry import dycore_model_names ... PY` -> exit 0; candidate and incumbent registered.
- Existing candidate fast artifact read from `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_hydrostatic_output.json` and `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_hydrostatic_output.csv`; fast was not rerun.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_hydrostatic_output --workers 4` -> exit 0.
- Candidate validation command: not run because iteration did not promote.
- Golden command: not run.

## Measurement Lessons

- The theta hydrostatic pressure output reconstruction variant completed iteration without diagnostic failures, but reduced primary skill relative to the incumbent.
- The primary-score miss was decisive; future related proposals should demonstrate a clear iteration-score improvement before spending validation compute.

## Anomalies

- Failed or restarted commands: one non-evaluation registry probe failed due to an incorrect helper import, then the correct registry verification passed. No evaluation command failed or was restarted.
- Resource limits: no resource failure observed with 4 workers.
- Nonfinite or unstable outputs: none observed in fast or iteration diagnostics.
- Cache invalidation: none discovered.

## Recommendation To Orchestrator

Report the measured gate status and caveats. Do not accept or reject the candidate here.
