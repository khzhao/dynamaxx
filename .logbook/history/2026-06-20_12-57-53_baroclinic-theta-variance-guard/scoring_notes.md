# Scoring Notes

## Gate Status

- Fast gate: verified clean from the existing candidate fast artifact and Orchestrator-provided record. `failed=false`, `issues=0`, `records=120`, `primary_score=-0.5307052642658794`.
- Iteration promotion gate: did not pass. Candidate iteration `primary_score=-0.5150640253022584`; cached incumbent iteration `primary_score=-0.5150627015910243`; delta `-0.0000013237112340691581`, below the required `+0.002`.
- Iteration diagnostics and RMSE guardrails were clean: `failed=false`, `issues=0`; no early day-1..5 mean RMSE regression exceeded `2%`; no variable+lead RMSE regression exceeded `10%`.
- Validation acceptance gate: not evaluated. Validation was allowed only if iteration promoted, so no validation command was run and no candidate validation artifacts were produced.

## Cache Reuse

- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`; no incumbent evaluation was run.
- Reused incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`.
- Reused incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`.
- The validation incumbent cache was checked and is valid, but it was not used because candidate validation was not run.
- Cache validity checks passed: requested incumbent matched the leaderboard, `HEAD` matched the leaderboard eval code commit `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`, the data path/targets/leads/protocols were compatible, and cached artifacts were readable, finite, and had the expected incumbent model rows.

## Commands

- Verified, not rerun: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` exited `0` in the Implementer/Orchestrator record with `136 passed`.
- Verified, not rerun: `uv run pytest` exited `0` in the Implementer/Orchestrator record with `202 passed, 2 skipped`.
- Verified, not rerun: `git diff --check` exited `0` in the Implementer/Orchestrator record.
- Verified, not rerun: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_var_guard` exited `0` in the provided record and matching artifact.
- Run: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_var_guard --workers 4` exited `0`.
- Skipped: `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_var_guard --workers 4` because the iteration gate failed.

## Measurement Lessons

- The theta variance guard produced nearly identical RMSEs to the incumbent on the iteration set, but the primary score moved slightly negative instead of meeting the required promotion margin.
- The clean guardrails indicate no obvious stability or localized RMSE regression from the scored outputs; the measured blocker for promotion is only the insufficient primary delta.
- Future scoring setup can continue reusing the accepted incumbent cache for this candidate family while the evaluation fingerprint remains unchanged.

## Anomalies

- Cache reuse: no anomaly.
- Resource limits: no anomaly observed during the candidate iteration run; four GPU-backed workers completed all `229` chunks.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Report the measured gate status above. This Scorer role does not accept or reject the candidate.
