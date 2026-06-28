# Scoring Notes

## Scope

- Candidate: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag`
- Incumbent: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq`
- Role: Scorer only; no acceptance decision made.
- Golden: prohibited and not run.

## Commands

- Verified provided focused tests: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` -> exit 0, 133 passed.
- Verified provided full tests: `uv run pytest` -> exit 0, 199 passed, 2 skipped.
- Verified provided `git diff --check` -> exit 0.
- Verified existing fast artifact for `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag` -> clean artifact, not rerun.
- Ran registry helper with unavailable `get_model_config` -> exit 1, no scoring impact; reran registry check with `dycore_model_names` -> exit 0.
- Ran `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag --workers 4` -> exit 0.
- Did not run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag --workers 4` because the iteration promotion gate failed.
- Did not run any incumbent evaluation. Did not run golden.

## Cache Reuse

- Reused incumbent iteration artifact: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`.
- Incumbent iteration cache checks passed: requested incumbent matched leaderboard, data path/target variables/lead range/protocol matched, eval-code commit `6094c73fe9b98b46c3ac9bfbb430bafd332d628f` matched current HEAD, artifact was readable with finite primary and complete incumbent guardrail rows.
- Incumbent validation artifact `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` was readable and compatible, but was not used for candidate comparison because validation was not run.
- Candidate source edits in the current worktree were not treated as cache invalidation under the protocol.

## Fast Sanity

- Artifact: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag.json`
- Primary: `-0.5386920433977409`
- Diagnostics: failed=False, issues=0, candidate rows=60, total records=120.

## Iteration Result

- Candidate artifact: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag.json`
- Candidate CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag.csv`
- Candidate primary: `-0.5230417460160705`
- Incumbent primary: `-0.5150627015910243`
- Primary delta, candidate minus incumbent: `-0.007979044425046156`.
- Diagnostics: failed=False, issues=0.

## Iteration Gate Calculation

- Diagnostics clean: `True`.
- Primary delta threshold `+0.002`: `-0.007979044425046156` -> `False`.
- Early day 1..5 mean RMSE guardrail threshold 2%: pass=`False`, max variable regression=`0.03152849221777053` on `10m_u_component_of_wind`.
- Variable+lead RMSE guardrail threshold 10%: pass=`True`, max regression=`0.037877328233780046` at `10m_u_component_of_wind` day `1.0`.
- Iteration promotion gate passes: `False`.

## Guardrail Details

- Early day 1..5 `10m_u_component_of_wind`: candidate mean RMSE `4.911944878359132`, incumbent `4.761812121930365`, relative delta `0.03152849221777053`.
- Early day 1..5 `2m_temperature`: candidate mean RMSE `5.945388271418108`, incumbent `5.945387535832323`, relative delta `1.2372377422645148e-07`.
- Early day 1..5 `geopotential_500`: candidate mean RMSE `640.6547511223441`, incumbent `640.6546577581639`, relative delta `1.4573246143066215e-07`.
- Early day 1..5 `mean_sea_level_pressure`: candidate mean RMSE `868.6675366431439`, incumbent `868.6677331033576`, relative delta `-2.2616266983134728e-07`.

Top variable+lead RMSE regressions:

- `10m_u_component_of_wind` day `1.0`: candidate RMSE `3.227009664933752`, incumbent `3.1092399623232483`, relative delta `0.037877328233780046`.
- `10m_u_component_of_wind` day `2.0`: candidate RMSE `4.23379706168324`, incumbent `4.1016193427457175`, relative delta `0.03222574010221037`.
- `10m_u_component_of_wind` day `3.0`: candidate RMSE `5.102439798705917`, incumbent `4.946273245939985`, relative delta `0.03157256888185799`.
- `10m_u_component_of_wind` day `4.0`: candidate RMSE `5.756605997853493`, incumbent `5.58896506896514`, relative delta `0.029994985980363816`.
- `10m_u_component_of_wind` day `5.0`: candidate RMSE `6.239871868619261`, incumbent `6.062962989677735`, relative delta `0.02917861765653448`.

## Validation

- Validation was not run because the iteration promotion gate did not pass. This follows the task constraint that validation is allowed only if the candidate passes the iteration promotion gate.
- Cached incumbent validation primary available for reference only: `-0.5044433981077879`.

## Anomalies And Lessons

- Informational anomaly: the first registry helper command used a nonexistent helper and exited 1; a corrected registry membership command exited 0 for both model names.
- Measurement lesson: the gradient-wind 10 m diagnostic candidate kept diagnostics clean but lowered the iteration primary score relative to the cached incumbent, so validation was not reached.
