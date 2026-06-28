# Scoring Notes

## Commands

| Step | Command | Exit |
| --- | --- | --- |
| Registration check | `uv run python -c 'from dynamaxx.dycore.registry import dycore_model_names; names=set(dycore_model_names()); expected={"dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang", "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split"}; missing=sorted(expected-names); print("registered models:", ", ".join(sorted(expected))); assert not missing, f"missing registered models: {missing}"'` | 0 |
| Tests | `uv run pytest` | 0 |
| Fast | `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang` | 0 |
| Iteration | `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang --workers 4` | 0 |
| Validation | `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang --workers 4` | 0 |

`uv run pytest` reported 139 passed and 2 skipped in 68.70s. `golden` was not run.

## Raw Artifacts

| Protocol | Candidate JSON | Candidate CSV | Incumbent JSON | Incumbent CSV |
| --- | --- | --- | --- | --- |
| Fast | `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json` | `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv` | not run | not run |
| Iteration | `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json` | `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv` | `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.json` | `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.csv` |
| Validation | `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json` | `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv` | `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.json` | `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.csv` |

The compatible incumbent iteration and validation artifacts provided by the Orchestrator were reused. The candidate fast artifact was rerun by the Scorer. Candidate iteration started with 229 chunks, cached=0; candidate validation started with 46 chunks, cached=0.

## Gate Status

- Fast gate: passed. Candidate primary score `-1.0962491137938128`, diagnostics `failed=False`, issues `0`.
- Iteration promotion gate: passed. Candidate primary score `-1.1241936221835356`; incumbent primary score `-1.127914598973564`; delta `+0.003720976790028363`, above the `+0.002` threshold.
- Validation measured gate: passed. Candidate primary score `-1.1127999773519712`; incumbent primary score `-1.11604278330304`; delta `+0.003242805951068739`.

The Scorer does not decide acceptance or rejection.

## Diagnostics And Guardrails

Raw metric JSON records include persistence baseline rows. Candidate-versus-incumbent guardrails were computed after filtering records by the evaluated `model_name`; each compared side had 60 model records and 60 persistence rows filtered out.

| Protocol | Candidate diagnostics | Incumbent diagnostics | Max early day 1-5 mean RMSE regression | Early >2% violations | Max variable+lead RMSE regression | Variable+lead >10% violations |
| --- | --- | --- | --- | --- | --- | --- |
| Iteration | `failed=False`, issues `0` | `failed=False`, issues `0` | `mean_sea_level_pressure`, `+0.00786522356115319` | 0 | `mean_sea_level_pressure` at 96h, `+0.020735194152026865` | 0 |
| Validation | `failed=False`, issues `0` | `failed=False`, issues `0` | `mean_sea_level_pressure`, `+0.008699505158908783` | 0 | `mean_sea_level_pressure` at 96h, `+0.019700886228756508` | 0 |

No nonfinite metric values were found in candidate fast/iteration/validation JSON records or reused incumbent iteration/validation JSON records.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused; candidate iteration and validation had no cached chunks.
- Resource limits: none observed.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none observed in diagnostics or metric-value checks.
- Worktree caveat: the worktree was dirty before scoring due to implementer source/test edits; the Scorer did not change dycore source code or revert edits.

## Measurement Lessons

- Keep filtering raw metric records by evaluated `model_name`; persistence baseline rows are present in every metric JSON and would corrupt guardrail calculations if included.
- The largest measured regression for both iteration and validation was 96h `mean_sea_level_pressure` RMSE, around `+2%`, below the `+10%` variable+lead guardrail.
- Short-lead `mean_sea_level_pressure` should be watched in future split-timing proposals because it was the only positive early day 1-5 mean RMSE regression, though still below the `+2%` guardrail.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. Do not accept or reject the candidate here.
