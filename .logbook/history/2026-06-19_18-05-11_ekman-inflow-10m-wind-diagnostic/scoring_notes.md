# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast completed with `primary_score=-0.5566127759175437`, `failed=False`, and `issues=0`.
- Iteration promotion gate: failed. Candidate iteration `primary_score=-0.5706118440326521`; recomputed incumbent iteration `primary_score=-0.5719865269927361`; delta `candidate - incumbent = 0.0013746829600840282`, below the required `+0.002`.
- Iteration diagnostics: passed. Candidate and incumbent iteration both had `failed=False` and `issues=0`.
- Iteration early day 1-5 RMSE guard: passed. The largest early mean relative change was `2m_temperature` at `0.000012%`; `0` variables exceeded the +2% threshold.
- Iteration variable+lead RMSE guard: passed. The largest positive variable+lead change was `mean_sea_level_pressure` day `13.0` at `0.000946%`; `0` variable+lead rows exceeded the +10% threshold.
- Validation acceptance gate: not run. Validation was allowed only if iteration promoted, and iteration did not meet the primary-score threshold.
- Golden: not run.

## Cache Reuse

- Fast: no incumbent fast comparison is required; candidate fast was freshly run with the fixed command.
- Iteration incumbent cache: not reused. The candidate modifies shared Dinosaur adapter/source in `src/dynamaxx/dycore/models/dinosaur/adapter.py` and shared registry source in `src/dynamaxx/dycore/registry.py`, so the incumbent factory runs against modified shared code. Under `roles/SCORER.md`, this fails incumbent metric reuse.
- Before overwriting the incumbent iteration artifact path, I snapshotted the existing files to `.logbook/history/2026-06-19_18-05-11_ekman-inflow-10m-wind-diagnostic/cache_snapshots/leaderboard_iteration_incumbent_before_ekman_rerun.json` and `.logbook/history/2026-06-19_18-05-11_ekman-inflow-10m-wind-diagnostic/cache_snapshots/leaderboard_iteration_incumbent_before_ekman_rerun.csv`.
- Incumbent iteration was recomputed with `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter --workers 4 --restart`; the run started with `cached=0` and `pending=229`.
- Validation cache reuse: not attempted because validation was skipped.

## Commands And Artifacts

- Registration confirmation with `create_dycore_model`: exit 0.
- Pytest was not rerun by the Scorer; the provided full-test record says `uv run pytest` passed with 188 passed, 2 skipped.
- Candidate fast: exit 0; artifacts `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_ekman_inflow_10m_wind.json` and `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_ekman_inflow_10m_wind.csv`.
- Candidate iteration: exit 0; artifacts `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_ekman_inflow_10m_wind.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_ekman_inflow_10m_wind.csv`.
- Incumbent iteration rerun: exit 0; artifacts `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter.csv`.
- Candidate validation and incumbent validation: not run.

## Measurement Lessons

- The Ekman inflow 10 m wind diagnostic stayed numerically stable on fast and iteration, with zero diagnostic issues.
- The primary-score gain was too small for promotion: `+0.0013746829600840282` versus the `+0.002` threshold.
- Guardrails did not block this candidate; the blocker was the primary delta. The largest variable+lead RMSE regression was `mean_sea_level_pressure` day `13.0` at `0.000946%`.
- Future output-only 10 m wind diagnostics need a stronger direct 10 m wind gain or lower collateral changes, because small primary improvements below threshold cannot justify validation.

## Anomalies

- Cache reuse: rejected for iteration as described above.
- Resource limits: no resource failure observed with `--workers 4`; both iteration runs used 4 effective GPU workers.
- Failed or restarted commands: no evaluation command failed. The incumbent used `--restart` intentionally to avoid stale chunk reuse.
- Nonfinite or unstable outputs: none observed in fast or iteration metrics.

## Recommendation To Orchestrator

Measured gate status: fast passed, iteration did not promote to validation, validation and golden were not run. As Scorer, I do not accept or reject the candidate.
