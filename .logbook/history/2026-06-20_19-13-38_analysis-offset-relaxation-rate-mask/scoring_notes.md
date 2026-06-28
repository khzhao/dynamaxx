# Scoring Notes

## Gate Status

- Registration: passed. The candidate and incumbent were both listed by `dycore_model_names()` and constructible with `create_dycore_model()`.
- Full test gate: passed. `uv run pytest` exited `0` with `199 passed, 2 skipped in 129.96s`.
- Fast gate: passed. Candidate fast exited `0` with `failed=false`, `issues=0`, `records=120`, and primary score `-0.5474015011136666`.
- Iteration promotion gate: did not pass. Candidate iteration primary was `-0.5313755627331137`; cached incumbent iteration primary was `-0.5150627015910243`; delta was `-0.016312861142089408`, below the required `+0.002`.
- Iteration diagnostics were clean (`failed=false`, `issues=0`), but RMSE guardrails were not clean. Day 1..5 mean RMSE exceeded the `2%` regression limit for `2m_temperature` (`+57.31598628733586%`) and `mean_sea_level_pressure` (`+3.232225060994042%`). Variable-lead RMSE had `48` regressions over the `10%` limit; the worst was `2m_temperature` at lead hour `240`, `+171.11436565406353%`.
- Validation acceptance gate: not evaluated. Validation was allowed only after iteration promotion, so the candidate validation command was skipped.

## Cache Reuse

- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`; no incumbent evaluation was run.
- Reused incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`.
- Reused incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`.
- Incumbent validation cache was checked and valid, but it was not used because candidate validation was not run.
- Cached incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`.
- Cache validity checks passed: requested incumbent matched the leaderboard, current `HEAD` matched leaderboard eval code commit `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`, the fingerprint matched data path, target variables, lead days, and protocols, and cached artifacts were readable, finite, and had 120 incumbent model records for guardrail comparisons.

## Commands

- Run: `uv run python - <<'PY' ... get_model_factory ... PY` exited `1`; this was an incorrect preliminary registration probe and did not run evaluation.
- Run: `uv run python - <<'PY' ... dycore_model_names/create_dycore_model ... PY` exited `0`; candidate and incumbent registration confirmed.
- Run: `uv run pytest` exited `0`.
- Run: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask` exited `0`.
- Run: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask --workers 4` exited `0`.
- Skipped: `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask --workers 4` because the iteration gate failed.
- Not run: incumbent fast, incumbent iteration, incumbent validation, and golden.

## Measurement Lessons

- The analysis-offset weak-HS rate mask was numerically finite on fast and iteration, but it materially degraded the iteration primary score.
- The strongest RMSE regressions were thermal and pressure-field related: day 1..5 `2m_temperature` mean RMSE regressed by `57.31598628733586%`, day 1..5 `mean_sea_level_pressure` by `3.232225060994042%`, and longer-lead `mean_sea_level_pressure` reached a `+71.53642432348649%` variable-lead regression at day 12.
- The candidate also worsened long-lead wind and Z500 guardrails despite not directly changing wind diagnostics, consistent with the rate mask weakening a stabilizing thermal source enough to alter coupled mass and momentum evolution.

## Anomalies

- Cache reuse: no anomaly. Incumbent iteration was reused as instructed, and incumbent validation cache was checked valid but not used.
- Resource limits: no resource anomaly observed. Candidate iteration used `--workers 4`, effective GPU workers `4`, and completed `229` chunks.
- Failed or restarted commands: no gate command failed or restarted. One preliminary registration probe failed because it used a nonexistent helper, then the correct registry API confirmed registration.
- Nonfinite or unstable outputs: none reported by diagnostics.
- Golden: not run, as prohibited.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. This Scorer artifact does not accept or reject the candidate.
