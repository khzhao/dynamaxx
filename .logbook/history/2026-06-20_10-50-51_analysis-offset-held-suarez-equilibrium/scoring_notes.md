# Scoring Notes

## Gate Status

- Fast gate: passed. Command exited 0 with `failed=false`, `issues=0`, `records=120`, primary score `-0.5307193588405017`.
- Iteration promotion gate: passed. Candidate primary score `-0.5150627015910243`; cached incumbent primary score `-0.532053269893688`; delta `+0.016990568302663656`, above the `+0.002` promotion threshold. Candidate diagnostics were clean. No early day-1-through-day-5 mean RMSE regression exceeded `2%`, and the max variable-lead RMSE regression was `0.5666053698017305%`.
- Validation acceptance gate: measured as passed. Candidate primary score `-0.5044433981077879`; cached incumbent primary score `-0.5219023378614627`; delta `+0.01745893975367474`, above the `+0.001` validation threshold. Candidate diagnostics were clean. No early day-1-through-day-5 mean RMSE regression exceeded `2%`; the max variable-lead RMSE regression was `0.6206428681060913%`.
- Golden: not run. Golden is prohibited for this scoring task.

## Commands

- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq`: exit status 0.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq --workers 4`: exit status 0.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq --workers 4`: exit status 0.

Implementation checks were not rerun by Scorer because the Orchestrator supplied valid passing records:

- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: exit status 0, `127 passed in 117.36s`.
- `uv run pytest`: exit status 0, `193 passed, 2 skipped in 123.12s`.
- `git diff --check`: exit status 0.

## Diagnostics

- Candidate fast: `failed=false`, issue count `0`.
- Candidate iteration: `failed=false`, issue count `0`.
- Candidate validation: `failed=false`, issue count `0`.
- Cached incumbent iteration: `failed=false`, issue count `0`.
- Cached incumbent validation: `failed=false`, issue count `0`.

## RMSE Guardrails

Iteration early day-1-through-day-5 mean RMSE regressions:

- `10m_u_component_of_wind`: `+0.09201215296149504%`.
- `2m_temperature`: `-0.48566957987585563%`.
- `geopotential_500`: `-0.16467856724247645%`.
- `mean_sea_level_pressure`: `+0.33519333257628225%`.

Iteration max variable-lead RMSE regression:

- `mean_sea_level_pressure`, day `4.0` (`96` hours): `+0.5666053698017305%`; candidate RMSE `1105.0848445048084`, incumbent RMSE `1098.8586523739268`.

Validation early day-1-through-day-5 mean RMSE regressions:

- `10m_u_component_of_wind`: `+0.06252905891731159%`.
- `2m_temperature`: `-0.4891139849444605%`.
- `geopotential_500`: `-0.1537770968952067%`.
- `mean_sea_level_pressure`: `+0.3869610662188262%`.

Validation max variable-lead RMSE regression:

- `mean_sea_level_pressure`, day `4.0` (`96` hours): `+0.6206428681060913%`; candidate RMSE `1068.2409846892522`, incumbent RMSE `1061.6519177774549`.

Guardrail calculation note: each JSON contains 120 records: 60 evaluated-model rows and 60 persistence rows. RMSE guardrails above used only rows whose `model_name` matched the candidate or incumbent.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Candidate validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Candidate validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Cached incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json`
- Cached incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv`
- Cached incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json`
- Cached incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv`

## Cache Reuse

- Incumbent iteration and validation metrics were reused from `.logbook/leaderboard.json`; no incumbent evaluation commands were run.
- Reuse checks recorded from the Orchestrator and verified while reading artifacts: requested incumbent equals leaderboard incumbent; incumbent commit is `ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6`; leaderboard fingerprint has matching data path, target variables, lead range, and eval code commit; iteration and validation artifacts exist, are readable, have matching model names, finite primary scores, 120 records, and clean diagnostics.
- No recomputation reason: the cache is valid under `roles/SCORER.md`; candidate source edits do not invalidate the accepted incumbent cache; candidate output paths are distinct from incumbent output paths.

## Measurement Lessons

- The candidate improves primary score on both iteration and validation while keeping fixed RMSE guardrails comfortably below thresholds. The largest measured RMSE regression is mean sea level pressure at day 4.
- Future scoring helpers should always filter metric records by `model_name` before constructing channel-and-lead RMSE maps because persistence baseline rows share the same channel and lead keys.

## Anomalies

- Resource limits: no resource failure observed. Iteration and validation both dispatched with requested workers `4`, effective workers `4`, GPU count `4`.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Measured gates pass under the fixed protocol and cached-incumbent comparison. Scorer does not accept or reject the candidate.
