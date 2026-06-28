# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual` exited 0 with `failed=False`, `issues=0`, 120 raw records, and primary score `-0.5472551712514075`.
- Iteration promotion gate: did not pass. Candidate iteration primary score `-0.5312654903142987` versus cached incumbent `-0.532053269893688` gives signed delta `0.0007877795793892473`, below the required `+0.002`. Candidate diagnostics were clean (`failed=False`, `issues=0`). Early day-1-through-day-5 guardrails passed with 0 regressions over 2%, and variable-by-lead guardrails passed with 0 regressions over 10%.
- Validation acceptance gate: not run. Validation was allowed only if iteration promoted, and the iteration primary-score threshold failed.

## Commands And Artifacts

- `uv run pytest`: exit 0; full suite reported `192 passed, 2 skipped in 114.25s`.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual`: exit 0; raw JSON `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual.json`, raw CSV `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual.csv`.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual --workers 4`: exit 0; raw JSON `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual.json`, raw CSV `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual.csv`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual --workers 4`: not run because the iteration promotion gate failed.
- Golden was not run.

## Primary Scores

- Fast candidate: `-0.5472551712514075`.
- Iteration candidate: `-0.5312654903142987`.
- Iteration incumbent cache: `-0.532053269893688`.
- Iteration signed delta: `0.0007877795793892473`; absolute delta: `0.0007877795793892473`.
- Validation incumbent cache, checked but not used for a candidate comparison: `-0.5219023378614627`.

## RMSE Guardrails

- Max early day-1-through-day-5 mean RMSE regression: `10m_u_component_of_wind` at `1.0738222579756654e-05` percent.
- Early day-1-through-day-5 regressions over 2%: `0`.
- Max variable-lead RMSE regression: `geopotential_500` lead `168` h at `0.045501263254104925` percent.
- Variable-lead regressions over 10%: `0`.

## Cache Reuse

- Iteration incumbent metrics were reused from `.logbook/leaderboard.json`: JSON `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json`, CSV `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv`. Validation checks: requested incumbent matched leaderboard incumbent; fingerprint data path, targets, lead range, and protocol were compatible; `HEAD` matched eval code commit `ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6`; there were no local diffs under `src/dynamaxx/eval`, `pyproject.toml`, or `uv.lock`; artifact parsed with finite primary score, 120 raw records, and 60 incumbent model rows. Incumbent iteration was not rerun.
- Validation cache was also checked and valid at JSON `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json`, CSV `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv`, but it was not used for a candidate comparison because candidate validation was not run. Incumbent validation was not rerun.
- Candidate dycore, registry, and test edits were not treated as incumbent-cache invalidations, per protocol.

## Measurement Lessons

- The candidate gives a small positive aggregate iteration movement with clean diagnostics, but the score movement is below the fixed promotion threshold.
- Guardrails were not the limiting factor; future variants would need materially larger aggregate gain while preserving the same clean early/mid-lead behavior.
- The low-mode mass residual mostly reduced early mass-field RMSE, but later `geopotential_500` leads carried the largest tiny positive regressions.

## Anomalies

- Resource limits: none observed. Iteration ran with requested `--workers 4`; evaluator reported GPU dispatch to four workers.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported.
- Incumbent reruns: none.

## Recommendation To Orchestrator

Report this as a clean, non-promoting iteration measurement. No accept/reject decision is made by the Scorer.
