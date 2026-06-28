# Scoring Notes

## Gate Status

- Fast gate: passed. Command `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter` exited 0 with `failed=False`, `issues=0`, and primary score `-0.5305863627049654`.
- Iteration promotion gate: did not pass. Candidate iteration primary score was `-0.5150758260293438`; cached incumbent iteration primary score was `-0.5150627015910243`; candidate-minus-incumbent delta was `-0.000013124438319467302`, below the required `+0.002`.
- Validation acceptance gate: not evaluated. Validation was allowed by the Orchestrator only if iteration passed promotion; candidate validation was skipped because the iteration primary delta did not meet the `+0.002` threshold.

## Commands And Status

- Protocol files read before scoring:
  - `sed -n '1,240p' roles/PROTOCOL.md` -> exit 0.
  - `sed -n '1,260p' roles/SCORER.md` -> exit 0.
- Read-only context and cache checks:
  - `git status --short` -> exit 0. Worktree had candidate source/test edits only before scoring artifacts were written.
  - `git rev-parse HEAD` -> exit 0, `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`.
  - `sed -n '1,240p' .logbook/leaderboard.json` -> exit 0.
  - `rg -n "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq(_first_step_div_filter)?" src/dynamaxx/dycore roles .logbook/history/2026-06-21_10-27-50_first-step-divergence-balance-filter` -> exit 0.
  - `find .logbook/history/2026-06-21_10-27-50_first-step-divergence-balance-filter -maxdepth 1 -type f -print` -> exit 0.
  - `rg -n "first_step|div_filter|analysis_hs_eq" src/dynamaxx/dycore/registry.py src/dynamaxx/dycore/models/dinosaur` -> exit 0.
  - `git diff --name-only -- src/dynamaxx/eval src/dynamaxx/evaluation src/dynamaxx/metrics src/dynamaxx/cli pyproject.toml uv.lock` -> exit 0 with no output.
  - `rg -n "dynamaxx-eval|def .*iteration|validation|lead_days|target_variables|primary_score" src tests pyproject.toml` -> exit 0.
  - `ls -l outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv` -> exit 0.
  - `sed -n '1,220p' src/dynamaxx/eval/runner.py` -> exit 0.
  - `sed -n '1,210p' src/dynamaxx/eval/protocols.py` -> exit 0.
  - `sed -n '1,280p' src/dynamaxx/dycore/registry.py` -> exit 0.
  - `find outputs/eval -maxdepth 1 -type f -name '*dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter*' -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n'` -> exit 0.
  - `sed -n '1,190p' src/dynamaxx/cli.py` -> exit 0.
  - `find roles/templates -maxdepth 1 -type f -print` -> exit 0.
  - `find roles/templates -maxdepth 2 -type f -name '*score*' -print` -> exit 0.
  - `sed -n '1,260p' roles/templates/scores.json` -> exit 0.
  - `sed -n '1,260p' roles/templates/scoring_notes.md` -> exit 0.
  - `date -u +%Y-%m-%dT%H:%M:%SZ` -> exit 0, `2026-06-21T12:12:40Z`.
- Registration checks:
  - `uv run python - <<'PY' ... registered_model_names ... PY` -> exit 1. This attempted helper does not exist and was superseded before any evaluation run.
  - `uv run python - <<'PY' ... dycore_model_names ... PY` -> exit 0. Output confirmed `candidate_registered=True`, `incumbent_registered=True`, `registered_count=18`.
- Evaluation and comparison:
  - Orchestrator-provided test record: `uv run pytest` -> exit 0, `200 passed, 2 skipped in 131.31s`; Scorer did not rerun.
  - `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter` -> exit 0.
  - `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter --workers 4` -> exit 0.
  - `uv run python - <<'PY' ... compare candidate and cached incumbent metric JSON files ... PY` -> exit 0.
  - `uv run python - <<'PY' ... compute per-variable early-lead RMSE summaries ... PY` -> exit 0.
  - `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter --workers 4` -> not run.
- `golden` was not run. No incumbent evaluation was rerun.

## Artifact Paths

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Candidate validation artifacts: none, because validation was skipped.

## Guardrails

- Diagnostics: passed. Candidate fast and iteration both had `failed=False` and `issues=0`. Cached incumbent iteration and validation also had `failed=False` and `issues=0`.
- Early day 1-5 mean RMSE regression: passed. Candidate mean `380.00732055510656`, incumbent mean `380.0073976298211`, relative change `-2.0282424776122887e-07`, threshold `+0.02`.
- Worst variable+lead RMSE regression: passed. Worst relative increase was `3.3883458252312426e-05` for `mean_sea_level_pressure` at lead hour `288` / day `12`, threshold `+0.10`.
- Variable+lead RMSE regression violations above 10%: `0`.

## Cache Reuse

- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`; no incumbent iteration rerun was performed.
- Cache validation checks: requested incumbent matched leaderboard incumbent; `HEAD` matched `evaluation_fingerprint.eval_code_commit`; checked fixed eval/CLI paths had no local diffs; cached iteration artifact existed, was readable, had finite primary score, had incumbent rows, had 120 records, and had the per-variable/per-lead RMSE records required for guardrails.
- Incumbent validation metrics existed and were readable with finite primary score `-0.5044433981077879`, but candidate validation was not run because iteration did not promote.
- Candidate source edits did not invalidate the cached incumbent under `roles/SCORER.md`.

## Measurement Lessons

- The first-step divergence filter was essentially neutral on fixed RMSE guardrails but slightly reduced iteration primary skill versus the incumbent.
- Registry verification should use `dycore_model_names()` from `dynamaxx.dycore.registry`; `registered_model_names` is not part of the current API.

## Anomalies

- Resource limits: none observed. Iteration dispatch reported `mode=gpu`, `requested_workers=4`, `effective_workers=4`, `gpu_count=4`, and worker devices `0:0,1:1,2:2,3:3`.
- Failed or restarted commands: one exploratory registry helper import failed with exit 1 before evaluation; no evaluation command failed or restarted.
- Nonfinite or unstable outputs: none observed.
- Fixed protocols changed: no evidence found; no fixed protocol files were edited by Scorer.

## Recommendation To Orchestrator

Report the measured gate status to the Orchestrator. The candidate did not reach validation because the iteration primary delta was below the promotion threshold; Scorer does not accept or reject the candidate.
