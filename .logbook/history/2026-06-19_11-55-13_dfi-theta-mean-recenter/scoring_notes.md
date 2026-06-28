# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast completed with `primary_score=-0.5580695796244858`, `failed=False`, and `issues=0`.
- Iteration promotion gate: failed. Candidate iteration `primary_score=-0.5721268800247525`; fresh incumbent iteration `primary_score=-0.5719847137456165`; delta `candidate - incumbent = -0.00014216627913599122`, below the required `+0.002`.
- Iteration diagnostics: passed. Candidate and incumbent iteration both had `failed=False` and `issues=0`.
- Iteration guardrails: passed. No early day 1-5 mean RMSE regression exceeded 2%; no variable+lead RMSE regression exceeded 10%. The largest variable+lead RMSE regression was `10m_u_component_of_wind` at day 15, `+0.07849195911340257%`.
- Validation acceptance gate: not run. Validation was allowed only if iteration promoted, and iteration did not promote.
- Golden: not run.

## Cache Reuse

- Iteration incumbent cache: not reused. The candidate modified shared incumbent source in `src/dynamaxx/dycore/models/dinosaur/adapter.py`, and `src/dynamaxx/dycore/registry.py` had uncommitted registry/evaluation changes. Under `roles/SCORER.md`, this fails incumbent metric reuse even though the new selector defaults false.
- Before overwriting the leaderboard incumbent iteration artifact path, I snapshotted the existing artifacts to `.logbook/history/2026-06-19_11-55-13_dfi-theta-mean-recenter/cache_snapshots/leaderboard_iteration_incumbent_before_rerun.json` and `.logbook/history/2026-06-19_11-55-13_dfi-theta-mean-recenter/cache_snapshots/leaderboard_iteration_incumbent_before_rerun.csv`.
- Incumbent iteration was recomputed with `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter --workers 4 --restart`.
- Validation cache reuse: not attempted because validation was skipped.

## Commands And Artifacts

- Registration probe with nonexistent `list_dycore_models`: exit 1; corrected with `dycore_model_names`.
- Registration confirmation with `dycore_model_names` and `create_dycore_model`: exit 0.
- Candidate fast: exit 0; artifacts `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_dfi_theta.json` and `.csv`.
- Candidate iteration: exit 0; artifacts `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_dfi_theta.json` and `.csv`.
- Incumbent iteration rerun: exit 0; artifacts `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter.json` and `.csv`.
- Pytest was not rerun by the Scorer; I recorded the Implementer-provided passing record from `implementation.md`, including full `uv run pytest` as `183 passed, 2 skipped`.

## Measurement Lessons

- DFI-time theta mean recentering was numerically clean but did not improve the incumbent on iteration; the measured primary delta was slightly negative.
- The largest RMSE changes were very small, so this result looks like a neutral-to-slightly-worse physics/initialization change rather than an instability.
- Shared adapter changes invalidate leaderboard cache reuse for the incumbent even when behavior is intended to remain default-false; future implementations should capture immutable pre-change incumbent metrics if they want to avoid recomputing.

## Anomalies

- Cache reuse: rejected for iteration as described above.
- Resource limits: no resource failure observed with `--workers 4`.
- Failed or restarted commands: one registration probe failed due to an incorrect helper name; the corrected probe passed. The incumbent iteration used `--restart` intentionally to avoid stale chunks.
- Nonfinite or unstable outputs: none observed in fast or iteration metrics.

## Recommendation To Orchestrator

Report the measured gate status and decide separately. As Scorer, I do not accept or reject the candidate.
