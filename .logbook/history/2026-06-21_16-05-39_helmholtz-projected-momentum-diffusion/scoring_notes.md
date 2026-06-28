# Scoring Notes: Helmholtz-Projected Momentum Diffusion

## Gate Summary

- Candidate: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion`
- Incumbent: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq`
- Fast gate: passed using reused candidate artifact `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion.json`. Primary `-0.5307152780364869`, diagnostics `failed=False`, issues `0`, records `120`.
- Iteration gate: did not promote to validation. Candidate primary `-0.5150752074995624` versus incumbent `-0.5150627015910243`, signed delta `-1.2505908538074095e-05`, required delta `+0.002`.
- Iteration diagnostics: passed with `failed=False` and issues `0`.
- Early day 1-5 mean RMSE guardrail: passed. Worst positive relative regression was `4.811324437525059e-10` (`4.8113244375250585e-08%`) for `10m_u_component_of_wind` / `10 m zonal wind`.
- Variable+lead RMSE guardrail: passed. Worst positive relative regression was `2.1726286536216773e-09` (`2.1726286536216772e-07%`) for `2m_temperature` / `2 m temperature` at lead hour `96`.
- Validation: not run because the iteration promotion gate failed the primary-score threshold.

## Commands And Status

| Command | Exit status | Notes |
| --- | ---: | --- |
| `uv run pytest` | `0` | Not rerun by Scorer; Orchestrator provided passing full-suite verification: 200 passed, 2 skipped in 129.84s. |
| `uv run python - <<'PY' ... from dynamaxx.dycore.registry import get_model ... PY` | `1` | Non-scoring probe failed because `get_model` is not a registry API; corrected immediately. |
| `uv run python - <<'PY' ... create_dycore_model, dycore_model_names ... PY` | `0` | Candidate and incumbent are registered and instantiate. |
| `uv run python - <<'PY' ... validate outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion.json ... PY` | `0` | Existing candidate fast artifact validated and reused. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion --workers 4` | `0` | Candidate iteration run completed; wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion.csv`. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion --workers 4` | not run | Skipped because iteration did not promote. |

## Incumbent Cache Reuse

- Leaderboard path: `.logbook/leaderboard.json`.
- Incumbent cache for iteration: reused from `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`.
- Requested incumbent matched `.logbook/leaderboard.json.incumbent_model_name`.
- Leaderboard `eval_code_commit` matched current HEAD `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`; current worktree changes are candidate dycore/registry/tests and do not invalidate the accepted incumbent cache under the protocol.
- Iteration artifact checks passed: readable, finite primary, 120 records, matching incumbent model name, finite record metrics, `failed=false`, and zero diagnostic issues.
- Validation incumbent artifacts `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv` were also readable and compatible, but were not used for a candidate validation comparison because validation was skipped.
- No incumbent rerun was performed.

## Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion.csv`
- Candidate validation JSON/CSV: not produced
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`

## Anomalies And Lessons

- Orchestrator reported an earlier pre-repair fast artifact with nonfinite/null metrics. The final clean fast artifact overwrote it and is the only fast artifact scored here.
- The candidate was stable and guardrail-clean, but its iteration primary score was lower than the cached incumbent by `1.2505908538074095e-05`.
- RMSE changes were numerical-scale only; the largest positive variable+lead RMSE regression was far below the 10% guardrail.
- The measured result suggests this bounded Helmholtz momentum diffusion setting does not add useful fixed-protocol skill beyond the accepted analysis-HS-equilibrium incumbent.
