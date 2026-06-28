# Scoring Notes

## Gate Status

- Fast gate: passed from Orchestrator-provided candidate fast artifacts. Primary score was `-0.5137008061625102`, diagnostics failed was `false`, issue count was `0`, and record count was `120`.
- Iteration promotion gate: passed. Candidate iteration primary score was `-0.49843977504709575`; cached incumbent iteration primary score was `-0.5150627015910243`; delta was `+0.01662292654392855`, above the required `+0.002`. Candidate diagnostics were clean, and no fixed iteration guardrail regressed.
- Validation acceptance gate: passed as a measured gate. Candidate validation primary score was `-0.48771725322193726`; cached incumbent validation primary score was `-0.5044433981077879`; delta was `+0.01672614488585067`, above the required `+0.001`. Candidate diagnostics were clean, and no fixed validation guardrail regressed.

## Cache Reuse

- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and matching `.csv`.
- Incumbent validation metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and matching `.csv`.
- Cache validation checks passed: requested incumbent matched the leaderboard incumbent, the fingerprint matched data path, target variables, lead range, and protocols, `HEAD` matched `eval_code_commit` `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`, artifacts parsed with finite primary scores and clean diagnostics, and each artifact contained the required RMSE records.
- Candidate source edits in the worktree were not treated as incumbent cache invalidation. No incumbent `dynamaxx-eval` command was run.

## Commands And Artifacts

- Model registration check: `uv run python - <<'PY' ... PY` exited `0`; candidate and incumbent both registered and instantiated with the requested names.
- Incumbent cache validation script: `python3 - <<'PY' ... PY` exited `0`; leaderboard iteration and validation artifacts were valid for reuse.
- Candidate iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface --workers 4` exited `0`. The CLI resumed `64` cached chunks, completed `165` pending chunks, and wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.json` and matching `.csv`.
- Candidate validation: `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface --workers 4` exited `0`. The CLI ran `46` chunks with `cached=0` and wrote `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.json` and matching `.csv`.
- Full pytest was not rerun by this scorer because the Orchestrator provided a passing record: `201 passed, 2 skipped in 130.52s`.
- Candidate fast was not rerun by this scorer because the Orchestrator provided a passing record and artifacts at `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.json` and matching `.csv`.
- Golden was not run.

## Guardrails

- Iteration day-1-to-5 mean RMSE guardrail: passed. The largest positive regression was `10m_u_component_of_wind` at `+0.00001339784466515046%`, below the `2%` limit. `2m_temperature` improved by `-2.2477759614884976%`.
- Iteration variable-lead RMSE guardrail: passed. The largest positive variable-lead regression was `10m_u_component_of_wind` at 360 hours, `+0.0010151285965083728%`, below the `10%` limit.
- Validation day-1-to-5 mean RMSE guardrail: passed. No target variable had a positive early-lead mean RMSE regression; `2m_temperature` improved by `-2.224646293075073%`.
- Validation variable-lead RMSE guardrail: passed. The largest positive variable-lead regression was `geopotential_500` at 288 hours, `+0.0018690374539547118%`, below the `10%` limit.

## Measurement Lessons

- The candidate produced consistent primary-score gains on both iteration and validation, with clean diagnostics and no guardrail regressions.
- The measured gain is concentrated in `2m_temperature`; pressure, geopotential, and 10 m wind changes are small enough to look near numerical noise under these fixed metrics.
- The interrupted iteration run directory was compatible with the current candidate command, and the CLI resume path correctly reused the first `64` chunks.

## Anomalies

- Cache reuse: incumbent iteration and validation metrics were reused from the leaderboard pointer; no incumbent eval command was run.
- Resource limits: none observed with `--workers 4`; the evaluator selected 4 effective GPU workers.
- Failed or restarted commands: none. Candidate iteration was resumed without `--restart`; candidate validation started from `cached=0`.
- Nonfinite or unstable outputs: none observed. Candidate iteration and validation diagnostics both reported `failed=false` and `issues=0`.

## Recommendation To Orchestrator

Report that the candidate passed the measured iteration and validation gates against cached incumbent metrics. This is a scoring report only; it does not accept or reject the candidate.
