# Scoring Notes

## Gate Status

- Fast gate: passed using the existing authorized candidate fast artifact. Candidate fast primary_score=`-0.5387762635908023`, failed=`False`, issue_count=`0`.
- Iteration promotion gate: failed. Candidate iteration primary_score=`-0.52227605019974`; cached incumbent iteration primary_score=`-0.5150627015910243`; primary delta=`-0.007213348608715697`, below the `+0.002` promotion threshold.
- Iteration diagnostics: passed. Candidate iteration failed=`False`, issue_count=`0`.
- Iteration early day 1-5 mean RMSE guard: passed. Overall early mean RMSE changed by `0.03378362862626507`%, below the `+2%` regression threshold. By variable: 10m_u_component_of_wind `0.8647481073097583`%, 2m_temperature `0.7591245671512082`%, geopotential_500 `-0.038756714547871746`%, mean_sea_level_pressure `0.07776359653732863`%.
- Iteration variable+lead RMSE guard: passed. Worst positive regression was `1.939879528357435`% for `10 m zonal wind` at `360` h, below the `+10%` threshold. Variable+lead regressions above `+10%`: `0`.
- Validation acceptance gate: not run because the iteration promotion gate failed. Golden was not run.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init.csv`
- Candidate validation JSON/CSV: not produced because validation was skipped.
- Cached incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Cached incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Cached incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Cached incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`

## Incumbent Cache Reuse

- Iteration incumbent cache: reused from `.logbook/leaderboard.json`. Validation checks passed: requested incumbent matched the leaderboard; fingerprint was compatible for data path, target variables, lead range, protocol, and eval code commit; artifacts were readable; primary_score was finite; diagnostics were clean; records covered incumbent rows for all target channels and 24..360 h leads.
- Validation incumbent cache: checked and compatible, but not used for a candidate comparison because validation was skipped. The incumbent was not rerun.
- Candidate source edits in the worktree were not treated as incumbent cache invalidation, per protocol.

## Commands And Exit Statuses

- Reused Orchestrator verification: `git diff --check` exit `0`; `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` exit `0`; focused Dinosaur/registry pytest exit `0` with 134 passed; `uv run pytest` exit `0` with 200 passed, 2 skipped.
- Reused candidate fast command/artifact: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init` exit `0` from prior authorized run.
- Scorer registration precheck: first helper import probe exited `1` because `get_model_registry` does not exist; corrected registry precheck with `dycore_model_names` and `create_dycore_model` exited `0`.
- Scorer iteration command: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init --workers 4` exit `0`.
- Candidate validation command: `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init --workers 4` was not run.

## Measurement Lessons

- The bounded screen-temperature initialization was numerically stable on fast and iteration, but it reduced the fixed iteration primary score by `-0.007213348608715697` versus the accepted incumbent.
- RMSE guardrails did not explain the primary-score loss: early aggregate RMSE was nearly flat at `0.03378362862626507`%, and the worst variable+lead increase was only `1.939879528357435`%.
- The largest RMSE regressions were concentrated in late `10m_u_component_of_wind` leads, with the worst at 360 h.

## Anomalies

- Resource limits: none observed. Candidate iteration used 4 effective GPU workers, 229 chunks, and completed with `cached=0`.
- Failed or restarted scoring commands: none. One non-scoring registry precheck failed due to an incorrect helper name, then the correct registry check passed.
- Nonfinite or unstable outputs: none detected. Candidate fast and iteration diagnostics were clean.
- Protocol deviations: none. Validation and golden were skipped according to the promotion rules.

## Recommendation To Orchestrator

Report measured gate status only. The Scorer does not accept or reject the candidate.
