# Scoring Notes

## Gate Status

- Fast gate: passed by reused artifact. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z` exited 0 with `failed=False`, `issues=0`, `records=120`, and `primary_score=-1.0960975078999153`.
- Registration gate: passed. The candidate and incumbent were both present in `dycore_model_names()`.
- Iteration promotion gate: failed on primary score. Candidate iteration primary was `-1.124209610114461`; incumbent iteration primary was `-1.1241936221835356`; delta was `-0.00001598793092548894`, below the required `+0.002`.
- Iteration diagnostics: clean. Candidate iteration diagnostics had `failed=False` and `issues=0`.
- Iteration early day 1-5 mean RMSE guardrail: passed. No target variable regressed by more than 2%; the largest early mean regression was `geopotential_500` at `0.9813979668901341%`.
- Iteration variable+lead RMSE guardrail: passed. No target variable and lead regressed by more than 10%; the largest regression was `geopotential_500` at lead 24 hours with `7.385768302790055%`.
- Validation acceptance gate: not run. Validation was allowed only if the iteration primary delta was at least `+0.002` and diagnostics/guardrails were clean; the primary gate failed.

## Measurement Lessons

- The hypsometric geopotential diagnostic changed Z500 enough to produce a short-lead RMSE regression but not enough to cross the fixed RMSE guardrails.
- The aggregate primary score was effectively neutral to slightly worse than the incumbent. Future proposals should not rely on a geopotential-only output diagnostic unless it also improves non-Z500 variables or avoids the day-1 Z500 degradation.
- Exact CSV filtering by `model_name` was necessary because the evaluation CSVs include persistence rows in addition to the evaluated model rows.

## Anomalies

- Cache reuse: reused the Implementer/Main Orchestrator passing test records, `git diff --check`, and the candidate fast artifacts. Reused compatible incumbent iteration and validation artifacts from the leaderboard.
- Resource limits: none observed. The fresh iteration run used `--workers 4`; evaluator dispatch reported `mode=gpu`, `effective_workers=4`, `gpu_count=4`, and `cached=0`.
- Failed or restarted commands: none during Scorer measurement.
- Nonfinite or unstable outputs: none reported by candidate fast or iteration diagnostics.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`

## Recommendation To Orchestrator

Report the measured gate status and caveats. Do not accept or reject the candidate here; Scorer authority ends at measurement.
