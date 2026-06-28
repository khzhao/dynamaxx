# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast had `failed=False`, `issues=0`, `records=120`, and `primary_score=-0.7109022071059753`.
- Iteration gate: failed. Candidate iteration primary score was `-0.6992577344425344`; cached incumbent iteration primary score was `-0.532053269893688`; delta was `-0.1672044645488464`, below the `+0.002` promotion threshold.
- Iteration diagnostics: passed with `failed=False` and `issues=0`.
- Iteration guardrails: failed. Day 1-5 mean RMSE for `2m_temperature` regressed by `62.79058980554264%`, exceeding the `2%` guardrail. The largest variable-lead RMSE regression was `2m_temperature` at 24 hours, regressing by `113.24920750881391%`, exceeding the `10%` guardrail.
- Validation gate: not run. Validation is allowed only if the iteration promotion gate passes.
- Golden: not run.

## Cache Reuse

Incumbent iteration metrics were reused from `.logbook/leaderboard.json` and were not recomputed. The cache was valid because the requested incumbent matched the leaderboard incumbent, the leaderboard fingerprint matched the fixed data path, target variables, lead range, and evaluation code commit, and the iteration artifact parsed with a finite primary score and 120 records.

Cached incumbent validation metrics also parsed and matched the leaderboard, but candidate validation was not run because the iteration gate failed. No validation incumbent rerun was performed.

Candidate source edits in the worktree were not treated as invalidating the accepted incumbent cache, per `roles/SCORER.md`.

## Commands And Artifacts

- Tests: `uv run pytest` -> exit status `0`; `191 passed, 2 skipped`.
- Candidate fast: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian` -> exit status `0`.
- Candidate iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian --workers 4` -> exit status `0`.
- Candidate validation: not run because iteration failed.
- Candidate fast artifacts: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian.json` and matching `.csv`.
- Candidate iteration artifacts: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian.json` and matching `.csv`.
- Cached incumbent iteration artifacts: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json` and matching `.csv`.
- Cached incumbent validation artifacts: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json` and matching `.csv`.

## Measurement Lessons

- The lagrangian low-mode near-surface residual candidate leaves pressure and geopotential essentially unchanged, but it injects a large near-surface temperature error immediately at day 1.
- The primary score collapse is consistent with the 2 m temperature guardrail failures, so validation would not add useful selection evidence for this iteration.
- The candidate iteration was fully uncached (`cached=0`, `pending=229`) and took substantially longer than the cached incumbent comparison path.

## Anomalies

- Cache reuse: incumbent iteration reused from leaderboard; incumbent validation cache validated for reference but not used in a candidate validation comparison.
- Resource limits: none observed; 4 requested workers mapped to 4 effective GPU workers.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none observed.
- Evaluation record shape: each JSON had 120 records because each channel/lead includes a scored-model row and a persistence-reference row. Guardrails used the scored-model row for each channel/lead.

## Recommendation To Orchestrator

Measured iteration gate status is failed; validation was not run. This is a measurement report only and does not accept or reject the candidate.
