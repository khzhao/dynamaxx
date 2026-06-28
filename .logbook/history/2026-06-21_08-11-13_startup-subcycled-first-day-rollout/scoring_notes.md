# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_startup_subcycle` exited 0 with `failed=False`, `issues=0`, and primary score `-0.5445913579727705`.
- Iteration promotion gate: failed. Candidate iteration primary was `-0.5271979435795002`; cached incumbent iteration primary was `-0.5150627015910243`; delta was `-0.012135241988475931`, below the required `+0.002`.
- Iteration diagnostics: clean for candidate and incumbent (`failed=False`, issue count `0`).
- Iteration early lead guardrail: failed for `mean_sea_level_pressure`, with day 1-5 mean RMSE regression `2.3077781360493983%`, above the `2%` threshold.
- Iteration variable+lead guardrail: passed. The largest positive variable+lead RMSE regression was `mean_sea_level_pressure` at lead hour `24`, `3.5537493303567578%`, below the `10%` threshold.
- Validation acceptance gate: not run. Candidate validation was skipped because iteration did not pass the promotion gate.

## Commands And Artifacts

- Orchestrator-provided tests: `uv run pytest` -> exit `0`, `201 passed, 2 skipped in 148.60s`. Scorer did not rerun pytest.
- Registration check: corrected registry API command using `dycore_model_names()` and `create_dycore_model()` -> exit `0`; both candidate and incumbent are registered.
- Candidate fast: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_startup_subcycle` -> exit `0`.
- Candidate iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_startup_subcycle --workers 4` -> exit `0`.
- Candidate validation: skipped; iteration promotion gate failed.

Raw candidate artifacts:

- Fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_startup_subcycle.json`
- Fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_startup_subcycle.csv`
- Iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_startup_subcycle.json`
- Iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_startup_subcycle.csv`

## Cache Reuse

- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`; no incumbent rerun was performed.
- Reused iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Reused iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Incumbent validation cache was checked and found usable, but not used for comparison because candidate validation was skipped.
- Correct incumbent validation JSON path from the leaderboard: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Correct incumbent validation CSV path from the leaderboard: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Cache checks passed: requested incumbent matched leaderboard incumbent, current HEAD matched `evaluation_fingerprint.eval_code_commit`, artifacts existed and were readable, model names matched, primary scores were finite, diagnostics were present, target channels were present, and lead hours `24..360` were present.

## Measurement Lessons

- The candidate degraded the primary score primarily through worse mean skill, with the largest negative per-record skill movement on `mean_sea_level_pressure` at lead hour `192` (`-0.030899318184460567`).
- Evaluation JSON records include both the evaluated model and `persistence`; guardrail comparisons must filter records by `model_name` before keying by `channel_name` and `lead_hours`.

## Anomalies

- Setup-only anomaly: the first registry check tried to import nonexistent `get_model_registry` and exited `1`. This was corrected before any evaluation command ran and did not affect scoring.
- Resource limits: no resource failures or worker restarts were observed. Iteration ran with requested `--workers 4`, effective workers `4`, GPU dispatch `0:0,1:1,2:2,3:3`.
- Failed or restarted evaluation commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.
- Golden protocol: not run.
- Source, tests, proposals, leaderboard, and commits: not edited by Scorer.

## Recommendation To Orchestrator

Report the measured gate status and caveats only. The candidate did not reach validation under the fixed promotion rules; accept/reject remains the Orchestrator's decision.
