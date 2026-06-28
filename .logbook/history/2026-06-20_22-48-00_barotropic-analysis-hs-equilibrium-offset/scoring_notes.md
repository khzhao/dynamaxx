# Scoring Notes

## Gate Status

- Registration: confirmed. Candidate and incumbent are both listed by `dycore_model_names()` and constructible with `create_dycore_model()`.
- Full test gate: passed. `uv run pytest` exited `0` with `199 passed, 2 skipped in 134.23s`.
- Fast gate: passed. Candidate fast exited `0` with `failed=false`, `issues=0`, `records=120`, primary score `-0.531600314575064`.
- Iteration promotion gate: did not pass. Candidate primary score `-0.5151407484276682`; cached incumbent primary score `-0.5150627015910243`; signed delta `-0.00007804683664391909`, below the required `+0.002`.
- Iteration diagnostics and guardrails: clean. Candidate diagnostics were `failed=false`, `issues=0`; no early day-1-through-day-5 mean RMSE regression exceeded `2%`, and no variable-lead RMSE regression exceeded `10%`.
- Validation acceptance gate: not measured. Validation was skipped because the candidate did not pass the iteration promotion gate.
- Golden: not run.

## Commands

- `uv run python - <<'PY' ... from dynamaxx.dycore.registry import get_model ... PY`: exit status `1`. Initial registration probe used a nonexistent helper and failed with `ImportError`; no model or artifact state changed.
- `uv run python - <<'PY' ... from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names ... PY`: exit status `0`.
- `uv run pytest`: exit status `0`.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_barotropic_analysis_hs_eq`: exit status `0`.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_barotropic_analysis_hs_eq --workers 4`: exit status `0`.
- Candidate validation command: not run.
- Incumbent evaluation commands: not run.

## Diagnostics

- Candidate fast: `failed=false`, issue count `0`, records `120`.
- Candidate iteration: `failed=false`, issue count `0`, records `120`.
- Cached incumbent iteration: `failed=false`, issue count `0`, records `120`.
- Cached incumbent validation: `failed=false`, issue count `0`, records `120`.

## RMSE Guardrails

Iteration early day-1-through-day-5 mean RMSE changes:

- `10m_u_component_of_wind`: `-0.3404109148787204%`.
- `2m_temperature`: `-0.19747194655357855%`.
- `geopotential_500`: `+0.20038365739247346%`.
- `mean_sea_level_pressure`: `-0.5044342718228488%`.

Iteration max variable-lead RMSE regression:

- `10m_u_component_of_wind`, day `15.0` (`360` hours): `+3.657273076145462%`; candidate RMSE `7.174298400524877`, incumbent RMSE `6.9211722319327444`.

Guardrail calculation note: each metrics JSON contains 120 records: 60 evaluated-model rows and 60 persistence rows. Guardrails used only rows whose `model_name` exactly matched the candidate or incumbent.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_barotropic_analysis_hs_eq.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_barotropic_analysis_hs_eq.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_barotropic_analysis_hs_eq.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_barotropic_analysis_hs_eq.csv`
- Cached incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Cached incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Cached incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Cached incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`

## Cache Reuse

- Iteration incumbent metrics were reused from `.logbook/leaderboard.json`; no incumbent iteration command was run.
- Validation incumbent metrics were checked from `.logbook/leaderboard.json`, but no candidate validation comparison was made because validation was skipped.
- Cache checks: requested incumbent equals leaderboard incumbent; incumbent commit is `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`; leaderboard fingerprint matches data path, target variables, lead range, and eval code commit; cached iteration and validation artifacts exist, are readable, have finite primary scores, contain 120 records, and have clean diagnostics.
- No recomputation reason: the cache is valid under `roles/SCORER.md` and the explicit Orchestrator instruction; candidate source edits in adapter, registry, and tests do not invalidate the accepted incumbent cache.

## Measurement Lessons

- The candidate changed iteration by only `-0.00007804683664391909` primary score units and therefore does not support promotion despite clean diagnostics and guardrails.
- The largest RMSE regression was late-lead `10m_u_component_of_wind`, while early mean `mean_sea_level_pressure` improved by `-0.5044342718228488%` and early mean `geopotential_500` regressed only `+0.20038365739247346%`.
- Future scoring helpers should keep exact `model_name` filtering explicit because persistence baseline rows duplicate the same channel and lead keys.

## Anomalies

- Resource limits: no resource failure observed. Iteration dispatched with requested workers `4`, effective workers `4`, GPU count `4`.
- Failed or restarted commands: one failed registration probe due to a nonexistent helper, corrected immediately with the repository's actual registry API. No evaluation command failed or restarted.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Report the measured gate status and caveats. Scorer does not accept or reject the candidate.
