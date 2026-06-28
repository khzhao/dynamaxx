# Scoring Notes

## Gate Status

- Fast gate: passed. Reused candidate fast artifact `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_thickness_hs_eq.json` with primary `-0.5306894176832982`, diagnostics `failed=False`, issue count `0`.
- Iteration promotion gate: failed. Candidate iteration primary `-0.5150654718773497` versus cached incumbent iteration primary `-0.5150627015910243` gives delta `-2.770286325448623e-06`, below the `+0.002` threshold.
- Iteration diagnostics: clean. Candidate iteration diagnostics were `failed=False` with `0` issues.
- Iteration guardrails: passed. Worst early day 1-5 mean RMSE relative regression was `3.4570851671668364e-07`; worst variable-lead relative regression was `1.1408463981766875e-05` for `10 m zonal wind` at `264` hours.
- Validation acceptance gate: not evaluated. Validation was skipped because iteration did not promote.
- Golden gate: not run.

## Cache Reuse

- Incumbent iteration was reused from `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`.
- Incumbent validation was verified from `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`, but not used for a candidate validation comparison because candidate validation was skipped.
- No incumbent iteration or validation command was run.
- Cache validation checks: requested incumbent matched the leaderboard incumbent, data path exists, fixed protocols include iteration/validation, target variables and lead range match, `eval_code_commit` matches HEAD `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`, metrics JSON/CSV are readable, primary scores are finite, incumbent rows needed for guardrails are present, and cached diagnostics are clean.
- Candidate source edits were not treated as cache invalidation, per `roles/SCORER.md`.

## Commands

- `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` => exit 0, provided by Orchestrator.
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` => exit 0, provided by Orchestrator, 134 passed.
- `uv run pytest` => exit 0, provided by Orchestrator, 200 passed, 2 skipped in 135.44s.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_thickness_hs_eq` => exit 0, provided by Orchestrator and artifact verified/reused.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_thickness_hs_eq --workers 4` => exit 0, run by Scorer.
- Candidate validation command was not run because the iteration gate failed.
- Incumbent iteration command was not run because the leaderboard cache was valid.
- Incumbent validation command was not run because the leaderboard cache was valid.

## Primary Scores

- Candidate fast: `-0.5306894176832982`.
- Candidate iteration: `-0.5150654718773497`.
- Incumbent iteration: `-0.5150627015910243`.
- Iteration delta: `-2.770286325448623e-06`.
- Incumbent validation cache: `-0.5044433981077879`.
- Candidate validation: not run.
- Validation delta: not computed.

## Guardrail Regressions

| Variable | Lead range | Candidate mean RMSE | Incumbent mean RMSE | Relative regression |
| --- | ---: | ---: | ---: | ---: |
| 10 m zonal wind | 24..120 | 4.761813768129371 | 4.761812121930365 | 3.4570851671668364e-07 |
| 2 m temperature | 24..120 | 5.945388100851399 | 5.945387535832323 | 9.503486064880243e-08 |
| 500 hPa geopotential | 24..120 | 640.6545893732291 | 640.6546577581639 | -1.0674227369225865e-07 |
| Mean sea level pressure | 24..120 | 868.6676502207607 | 868.6677331033576 | -9.541346329851211e-08 |

Worst variable-lead regression: `1.1408463981766875e-05` for `10 m zonal wind` at `264` hours, candidate RMSE `6.8696227512601284`, incumbent RMSE `6.8695443803104945`.

## Measurement Lessons

- The candidate is effectively score-neutral and very slightly worse on iteration, so it should not proceed to validation under the fixed gate.
- Guardrail regressions are tiny and well within limits; the issue is lack of primary-score gain, not stability.
- Future dycore proposals should avoid another near-no-op variant of the accepted analysis-offset path unless they materially change the rollout forcing or output reconstruction.

## Anomalies

- Two read-only helper checks exited 1 before the candidate iteration run: one used a non-existent `get_model` registry helper, and one assumed every record row belonged to the incumbent even though the evaluation artifact also stores persistence rows. These checks did not modify files, did not run incumbent evaluation, and were superseded by an explicit successful cache diagnostic.
- No resource failure, restart, nonfinite output, or diagnostic issue occurred during the candidate iteration command.

## Recommendation To Orchestrator

Report the measured gate status and make the accept/reject decision. As Scorer, no decision is made here.
