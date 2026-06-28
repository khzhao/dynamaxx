# Scoring Notes

## Role And Protocol

- Role: Scorer.
- Candidate: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_virtual_ri_wind`
- Incumbent: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq`
- Worker count: 4.
- Golden was not run.
- Pytest was not rerun because the Orchestrator provided passing verification for this candidate worktree, including `uv run pytest`: 200 passed, 2 skipped in 129.82s.

## Commands

| Command | Exit status | Notes |
| --- | ---: | --- |
| `uv run python - <<'PY' ... from dynamaxx.dycore.registry import available_models ... PY` | 1 | Helper registration probe used a non-existent registry symbol. This was not a scoring failure. |
| `uv run python - <<'PY' ... from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names ... PY` | 0 | Candidate and incumbent were registered and both instantiated as `DinosaurPrimitiveEquationsDycoreModel`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_virtual_ri_wind` | 0 | Candidate fast gate completed with clean diagnostics. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_virtual_ri_wind --workers 4` | 0 | Candidate iteration gate completed with clean diagnostics. |

## Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_virtual_ri_wind.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_virtual_ri_wind.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_virtual_ri_wind.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_virtual_ri_wind.csv`
- Candidate validation artifacts: not produced; validation was skipped because iteration promotion failed.

## Incumbent Cache Reuse

The requested incumbent matches `.logbook/leaderboard.json`. The current HEAD is `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`, matching the leaderboard `evaluation_fingerprint.eval_code_commit`. Current worktree diffs are limited to dycore, registry, and tests; candidate source edits do not invalidate the accepted incumbent cache under the protocol.

Iteration incumbent metrics were reused from:

- `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`

Cache validation checks passed: artifact exists and is readable, model name matches the leaderboard incumbent, primary score is finite and matches the leaderboard value, target variables match, lead days are 1..15, records are present for guardrail comparisons, and the leaderboard protocol list includes `iteration`.

Validation incumbent metrics were checked and available but not used for a candidate comparison because candidate validation was not run:

- `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`

## Scores

| Protocol | Candidate primary | Incumbent primary | Delta |
| --- | ---: | ---: | ---: |
| fast | -0.5314814864406524 | n/a | n/a |
| iteration | -0.5158726264914787 | -0.5150627015910243 | -0.0008099249004543951 |
| validation | not run | -0.5044433981077879 | n/a |

Diagnostics:

- Fast: `failed=false`, issue count 0.
- Iteration: `failed=false`, issue count 0.
- Validation: not run.

## Iteration Promotion Gate

Result: did not pass.

- Diagnostics gate: pass.
- Primary score gate: fail. Required candidate minus incumbent delta is at least `+0.002`; observed delta was `-0.0008099249004543951`.
- Early day 1-5 mean RMSE regression gate: pass for every target variable.
- Worst variable+lead RMSE regression gate: pass.

Early day 1-5 mean relative RMSE regression:

| Variable | Mean relative regression | Gate |
| --- | ---: | --- |
| `10m_u_component_of_wind` | 0.0012622509757270971 | pass |
| `2m_temperature` | -0.00000009992413458892458 | pass |
| `geopotential_500` | -0.000000017729238566133177 | pass |
| `mean_sea_level_pressure` | -0.0000001708673076805667 | pass |

Worst variable+lead RMSE regression:

- Variable: `10m_u_component_of_wind`
- Lead: 192 hours, day 8.
- Candidate RMSE: 6.7917998070003875.
- Incumbent RMSE: 6.759945977853026.
- Absolute RMSE regression: 0.031853829147361346.
- Relative RMSE regression: 0.004712142560269195.
- Gate: pass, below the 10% threshold.

## Validation

Validation was not run. The fixed protocol permits validation only after the iteration promotion gate passes, and this candidate missed the primary-score improvement threshold.

## Anomalies And Lessons

- No scoring anomalies occurred in the fixed fast or iteration evaluation gates.
- Metric files contain both evaluated-model rows and `persistence` rows. Guardrail calculations filtered to candidate rows for the candidate artifact and incumbent rows for the incumbent artifact.
- The virtual-theta Richardson 10 m wind change produced nearly unchanged RMSE guardrails, with a small 10 m wind RMSE regression, but did not improve primary score enough to promote.
