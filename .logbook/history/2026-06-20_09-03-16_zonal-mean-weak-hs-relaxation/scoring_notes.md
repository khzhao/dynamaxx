# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast primary score was `-0.5879939219257758`; diagnostics reported `failed=False` and `issues=0`.
- Iteration promotion gate: failed. Candidate iteration primary score was `-0.5703935108265198`; cached incumbent iteration primary score was `-0.532053269893688`; delta was `-0.03834024093283184`, below the required `+0.002`.
- Iteration diagnostics: passed with `failed=False` and `issues=0`.
- Iteration RMSE guardrails: failed the early day 1-5 mean RMSE guardrail for `2m_temperature` at `+2.265840139901215%`, above the `2%` threshold. The largest variable+lead RMSE regression was `10m_u_component_of_wind` at 360 hours: `+4.732425514257608%`, below the `10%` threshold.
- Validation acceptance gate: not run because iteration did not promote.
- Golden: prohibited and not run.

## Commands And Exit Status

- Recorded implementation check, not rerun: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` exited `0` per Implementer/Orchestrator record.
- Recorded implementation check, not rerun: `uv run pytest` exited `0` per Implementer/Orchestrator record.
- Recorded implementation check, not rerun: `git diff --check` exited `0` per Implementer/Orchestrator record.
- Candidate fast: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs` exited `0`.
- Candidate iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs --workers 4` exited `0`.
- Candidate validation: `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs --workers 4` was not run because the iteration gate failed.
- Incumbent evaluation commands: none run.

## Scores

- Candidate fast primary score: `-0.5879939219257758`.
- Candidate iteration primary score: `-0.5703935108265198`.
- Cached incumbent iteration primary score: `-0.532053269893688`.
- Iteration delta: `-0.03834024093283184`.
- Cached incumbent validation primary score: `-0.5219023378614627`.
- Candidate validation primary score and validation delta: not applicable because validation was not run.

## Regression Summary

Early day 1-5 mean RMSE regressions against the cached incumbent:

- `2m_temperature`: candidate `6.120556079311558`, incumbent `5.984946753420834`, regression `+2.265840139901215%` (guardrail failed).
- `10m_u_component_of_wind`: candidate `4.811864186228919`, incumbent `4.758669282008804`, regression `+1.1178525143831748%`.
- `mean_sea_level_pressure`: candidate `871.4829599279557`, incumbent `865.1986304850349`, regression `+0.7263452832094498%`.
- `geopotential_500`: candidate `644.5643250108046`, incumbent `641.9791671931931`, regression `+0.4026856243504147%`.

Maximum variable+lead RMSE regression:

- `10m_u_component_of_wind` at 360 hours: candidate `7.786903889202761`, incumbent `7.43504588093656`, regression `+4.732425514257608%`.

Issue counts:

- Candidate fast diagnostics: `failed=False`, `issues=0`.
- Candidate iteration diagnostics: `failed=False`, `issues=0`.
- Cached incumbent iteration diagnostics: `failed=False`, `issues=0`.
- Cached incumbent validation diagnostics: `failed=False`, `issues=0`.

## Cache Reuse

Incumbent iteration and validation metrics were reused from `.logbook/leaderboard.json`. They were not recomputed.

Validation checks performed for the iteration cache:

- Requested incumbent matched `.logbook/leaderboard.json.incumbent_model_name`.
- Leaderboard incumbent commit matched the Orchestrator-validated commit `ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6`.
- Iteration JSON/CSV artifacts existed and were readable.
- Artifact model name matched the requested incumbent.
- Primary score was finite and matched the leaderboard value `-0.532053269893688`.
- Artifact contained 120 records with 60 incumbent model rows for guardrail comparison.
- Fingerprint data path, target variables, lead range, protocol, and eval code commit were compatible.
- Candidate source edits do not invalidate the accepted incumbent cache.

Validation checks performed for the validation cache:

- Requested incumbent matched `.logbook/leaderboard.json.incumbent_model_name`.
- Validation JSON/CSV artifacts existed and were readable.
- Artifact model name matched the requested incumbent.
- Primary score was finite and matched the leaderboard value `-0.5219023378614627`.
- Artifact contained 120 records with 60 incumbent model rows.
- Fingerprint data path, target variables, lead range, protocol, and eval code commit were compatible.
- Candidate source edits do not invalidate the accepted incumbent cache.

No incumbent recomputation reason: the strict cache policy was satisfied, and the Orchestrator had already validated the cache immediately before scoring. Candidate source edits do not invalidate the accepted incumbent cache.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs.csv`
- Cached incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json`
- Cached incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv`
- Cached incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json`
- Cached incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv`

## Measurement Lessons

- The zonal-mean weak-Held-Suarez forcing candidate degraded the fixed iteration primary score relative to the accepted scale-separated surface residual incumbent.
- The score loss aligned with a day 1-5 `2m_temperature` mean RMSE guardrail failure, so validation would not add permitted selection evidence for this candidate state.
- The largest single variable+lead degradation was in long-lead `10m_u_component_of_wind`, but it stayed below the fixed `10%` variable+lead guardrail.

## Anomalies

- A read-only registration probe initially imported a non-existent registry helper and exited `1`; the corrected registry check using `dycore_model_names` exited `0`. No source code or evaluation artifact was changed by the failed probe.
- No resource failure, nonfinite output, or eval restart occurred.
