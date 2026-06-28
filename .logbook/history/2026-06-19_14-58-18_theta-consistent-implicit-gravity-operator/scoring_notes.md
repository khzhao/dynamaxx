# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast completed with `primary_score=-0.650884383009584`, `failed=False`, and `issues=0`.
- Iteration promotion gate: failed. Candidate iteration `primary_score=-0.6751099222964386`; fresh incumbent iteration `primary_score=-0.5719887262109961`; delta `candidate - incumbent = -0.10312119608544257`, below the required `+0.002`.
- Iteration diagnostics: passed. Candidate and incumbent iteration both had `failed=False` and `issues=0`.
- Iteration guardrails: failed. Early day 1-5 mean RMSE regressed by `+11.168302602462047%` for `mean_sea_level_pressure` and `+4.042683689707392%` for `10m_u_component_of_wind`. Fourteen variable+lead RMSE regressions exceeded 10%, led by `mean_sea_level_pressure` day 14 at `+16.29340937522116%`.
- Validation acceptance gate: not run. Validation was allowed only if iteration promoted, and iteration did not promote.
- Golden: not run.

## Cache Reuse

- Iteration incumbent cache: not reused. The candidate modified shared incumbent source in `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` and `src/dynamaxx/dycore/models/dinosaur/adapter.py`, and `src/dynamaxx/dycore/registry.py` had uncommitted registry/evaluation changes. Under `roles/SCORER.md`, this fails incumbent metric reuse.
- Before overwriting the leaderboard incumbent iteration artifact path, I snapshotted the existing artifacts to `.logbook/history/2026-06-19_14-58-18_theta-consistent-implicit-gravity-operator/cache_snapshots/leaderboard_iteration_incumbent_before_rerun.json` and `.logbook/history/2026-06-19_14-58-18_theta-consistent-implicit-gravity-operator/cache_snapshots/leaderboard_iteration_incumbent_before_rerun.csv`.
- Incumbent iteration was recomputed with `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter --workers 4 --restart`.
- Validation cache reuse: not attempted because validation was skipped.

## Commands And Artifacts

- Registration probe with nonexistent `get_model`/`list_models`: exit 1; corrected with `dycore_model_names`/`create_dycore_model`.
- Registration confirmation with `dycore_model_names` and `create_dycore_model`: exit 0.
- Candidate fast: exit 0; artifacts `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_implicit.json` and `.csv`.
- Candidate iteration: exit 0; artifacts `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_implicit.json` and `.csv`.
- Incumbent iteration rerun: exit 0; artifacts `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter.json` and `.csv`.
- Pytest was not rerun by the Scorer; I recorded the provided passing records, including full `uv run pytest` as `184 passed, 2 skipped`.

## Measurement Lessons

- The theta-consistent implicit gravity operator stayed finite, but it substantially degraded pressure-related iteration skill.
- The largest RMSE regressions cluster in `mean_sea_level_pressure` from days 3 through 15, which suggests the theta implicit operator is changing the pressure/gravity coupling in a harmful way rather than causing a broad numerical failure.
- Shared primitive-equation and adapter edits invalidate leaderboard cache reuse for the incumbent even when a candidate is registered side by side; future runs need immutable pre-change incumbent artifacts to avoid recomputation.

## Anomalies

- Cache reuse: rejected for iteration as described above.
- Resource limits: no resource failure observed with `--workers 4`.
- Failed or restarted commands: one registration probe failed due to incorrect registry helper names; the corrected probe passed. The incumbent iteration used `--restart` intentionally to avoid stale chunks.
- Nonfinite or unstable outputs: none observed in fast or iteration metrics.

## Recommendation To Orchestrator

Measured gate status: iteration did not promote to validation. As Scorer, I do not accept or reject the candidate.
