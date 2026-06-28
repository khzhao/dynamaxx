# Scoring Notes

## Gate Status

- Fast gate: passed. Reused candidate fast artifact `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_u_residual_coherence_gate.json`; primary `-0.5306239565147497`, diagnostics `failed=False`, issue count `0`, artifact records `120`.
- Iteration promotion gate: failed. Candidate iteration primary `-0.5149908273392567` versus cached incumbent iteration primary `-0.5150627015910243` gives delta `7.187425176757856e-05`, below the required `+0.002`.
- Iteration diagnostics: clean. Candidate iteration diagnostics were `failed=False` with `0` issues.
- Iteration guardrails: passed. Worst early day 1-5 mean RMSE relative regression was `2.0644810226696808e-07` for `2 m temperature`; worst variable-lead relative regression was `2.51992720719297e-05` for `10 m zonal wind` at `144` hours.
- Validation acceptance gate: not evaluated. Validation was skipped because iteration did not promote.
- Golden gate: not run.

## Cache Reuse

- Incumbent iteration was reused from `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`.
- Incumbent validation cache was verified from `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`, but no validation comparison was performed because candidate validation was skipped.
- No incumbent iteration or validation command was run.
- Cache checks passed: requested incumbent matched the leaderboard incumbent; leaderboard data path exists; fixed protocols include iteration and validation; target variables and lead range match; `eval_code_commit` matches HEAD `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`; metrics JSON/CSV artifacts are readable; primary scores are finite; incumbent rows needed for guardrail comparisons are present; cached diagnostics are clean.
- Candidate source edits were not treated as cache invalidation, per `roles/SCORER.md`.

## Commands

- `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` => exit 0, provided by Orchestrator.
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` => exit 0, provided by Orchestrator, 133 passed.
- `uv run pytest` => exit 0, provided by Orchestrator, 199 passed, 2 skipped in 131.38s.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_u_residual_coherence_gate` => exit 0, provided by Orchestrator and artifact verified/reused.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_u_residual_coherence_gate --workers 4` => exit 0, run by Scorer.
- Candidate validation command was not run because the iteration promotion gate failed.
- Incumbent iteration command was not run because the leaderboard cache was valid.
- Incumbent validation command was not run because the leaderboard cache was valid and candidate validation was skipped.
- A read-only registration probe using `get_model` exited 1 because the local registry API is `create_dycore_model`; the corrected `create_dycore_model` registration check exited 0. No artifacts or source files changed from that failed probe.

## Primary Scores

- Candidate fast: `-0.5306239565147497`.
- Candidate iteration: `-0.5149908273392567`.
- Incumbent iteration: `-0.5150627015910243`.
- Iteration delta: `7.187425176757856e-05`.
- Incumbent validation cache: `-0.5044433981077879`.
- Candidate validation: not run.
- Validation delta: not computed.

## Guardrail Regressions

| Variable | Lead range | Candidate mean RMSE | Incumbent mean RMSE | Relative regression |
| --- | ---: | ---: | ---: | ---: |
| 10 m zonal wind | 24..120 | 4.75835582429845 | 4.761812121930365 | -0.0007258366234143508 |
| 2 m temperature | 24..120 | 5.945388763246297 | 5.945387535832323 | 2.0644810226696808e-07 |
| 500 hPa geopotential | 24..120 | 640.6545125181677 | 640.6546577581639 | -2.267055962639156e-07 |
| Mean sea level pressure | 24..120 | 868.6676106395898 | 868.6677331033576 | -1.4097883815123538e-07 |

Worst variable-lead RMSE relative regression was `2.51992720719297e-05` for `10 m zonal wind` at `144` hours, with candidate RMSE `6.3656669384722875` and incumbent RMSE `6.365506532341303`.

## Measurement Lessons

- The gate improved early `10 m zonal wind` mean RMSE, but the primary score effect was too small to promote.
- The result looks like a bounded near-neutral perturbation rather than an unstable or broadly harmful change.
- Future one-channel residual-memory proposals likely need a stronger mechanism or broader primary-score leverage while preserving the small guardrail footprint observed here.

## Recommendation To Orchestrator

Report the measured gate status and caveats. Do not accept or reject the candidate here.
