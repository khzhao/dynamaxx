# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast primary score `-0.5660098645675776`, diagnostics `failed=false`, issue count `0`.
- Iteration promotion gate: did not pass. Candidate iteration primary score `-0.5510108000467965`; cached incumbent iteration primary score `-0.532053269893688`; delta `-0.018957530153108526` versus required `+0.002`.
- Iteration diagnostics: passed with `failed=false` and issue count `0`.
- Iteration early RMSE guardrail: did not pass. `2m_temperature` day 1-5 mean RMSE changed from `5.984946753420834` to `6.229912152127065`, a `0.04093025532202365` relative regression.
- Iteration variable-lead RMSE guardrail: passed. No variable-lead RMSE regression exceeded `0.10`; maximum was `2m_temperature` at lead hour `48`, `0.04397305518436211` relative regression.
- Validation acceptance gate: not run. Validation is allowed only if iteration promotes, and this candidate failed the iteration primary and early RMSE gates.

## Commands And Artifacts

- `uv run pytest`: exit status `0`; `189 passed, 2 skipped in 115.74s`.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_seasonal_stability_surface_residual`: exit status `0`; JSON `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_seasonal_stability_surface_residual.json`; CSV `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_seasonal_stability_surface_residual.csv`.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_seasonal_stability_surface_residual --workers 4`: exit status `0`; JSON `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_seasonal_stability_surface_residual.json`; CSV `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_seasonal_stability_surface_residual.csv`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_seasonal_stability_surface_residual --workers 4`: not run because iteration did not promote.

## Cache Reuse

- Iteration incumbent metrics: reused from `.logbook/leaderboard.json` pointer `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv`. Checks performed: requested incumbent matched leaderboard incumbent; fingerprint data path, target variables, lead range, protocol, and eval commit were compatible; JSON parsed, primary score was finite, and 120 records were present.
- Validation incumbent metrics: reused from `.logbook/leaderboard.json` pointer `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv` for reference only. Candidate validation did not run because the iteration gate failed.
- Incumbent was not rerun. Candidate source edits do not invalidate the accepted incumbent cache under `roles/SCORER.md`.

## Measurement Lessons

- The candidate worsened iteration primary by `-0.018957530153108526` with clean diagnostics.
- The regression is concentrated in `2m_temperature`; the early day 1-5 mean RMSE regression was `4.093025532202365` percent.
- Pressure, geopotential, and 10 m wind guardrail movement was near numerical noise, and there were no variable-lead regressions over 10 percent.

## Anomalies

- Resource limits: no resource failure observed; iteration completed on 4 GPU-dispatched workers.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none observed in parsed metrics.
- Long runtime: candidate iteration took about 75 minutes, but completed normally.

## Recommendation To Orchestrator

Report measured gate status only: fast passed, iteration did not promote to validation, and validation was not run. Acceptance or rejection remains with the Orchestrator.
