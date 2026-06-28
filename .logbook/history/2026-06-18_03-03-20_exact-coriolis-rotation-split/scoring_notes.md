# Scoring Notes

## Commands

| Step | Command | Exit |
| --- | --- | --- |
| Registration check | `uv run python -c 'from dynamaxx.dycore.registry import dycore_model_names; names=set(dycore_model_names()); expected={"dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split", "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init"}; missing=sorted(expected-names); print("registered models:", ", ".join(sorted(expected))); assert not missing, f"missing registered models: {missing}"'` | 0 |
| Tests | `uv run pytest` | 0 |
| Fast | `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split` | 0 |
| Iteration | `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split --workers 4` | 0 |
| Validation | `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split --workers 4` | 0 |

`uv run pytest` reported 132 passed and 2 skipped in 66.09s. `golden` was not run.

## Raw Artifacts

| Protocol | Candidate JSON | Candidate CSV | Incumbent JSON | Incumbent CSV |
| --- | --- | --- | --- | --- |
| Fast | `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.json` | `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.csv` | not run | not run |
| Iteration | `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.json` | `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.csv` | `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json` | `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv` |
| Validation | `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.json` | `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split.csv` | `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json` | `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv` |

The compatible incumbent iteration and validation artifacts provided by the Orchestrator were reused. The candidate iteration run started with 229 chunks, cached=0. The candidate validation run started with 46 chunks, cached=0.

## Gate Status

- Fast gate: passed. Candidate primary score `-1.100687123234284`, diagnostics `failed=False`, issues `0`.
- Iteration promotion gate: passed. Candidate primary score `-1.127914598973564`; incumbent primary score `-1.143975258592661`; delta `+0.016060659619097084`, above the `+0.002` threshold.
- Validation gate: passed as a measured gate calculation. Candidate primary score `-1.11604278330304`; incumbent primary score `-1.1301883620649706`; delta `+0.014145578761930677`, above the `+0.001` threshold.

The Scorer does not decide acceptance or rejection.

## Diagnostics And Guardrails

Raw metric JSON records include persistence baseline rows. Candidate-versus-incumbent guardrails were computed after filtering records by the evaluated `model_name`; each compared side had 60 model records and 60 persistence rows filtered out.

| Protocol | Candidate diagnostics | Incumbent diagnostics | Max early day 1-5 mean RMSE regression | Early >2% violations | Max variable+lead RMSE regression | Variable+lead >10% violations |
| --- | --- | --- | --- | --- | --- | --- |
| Iteration | `failed=False`, issues `0` | `failed=False`, issues `0` | `10m_u_component_of_wind`, `+0.005768322676610353` | 0 | `geopotential_500` at 24h, `+0.06691402994855757` | 0 |
| Validation | `failed=False`, issues `0` | `failed=False`, issues `0` | `10m_u_component_of_wind`, `+0.005104589610438858` | 0 | `geopotential_500` at 24h, `+0.06762772928563493` | 0 |

No nonfinite metric values were found in the checked candidate fast/iteration/validation JSON records or reused incumbent iteration/validation JSON records.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused; candidate iteration and validation had no cached chunks.
- Resource limits: none observed.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none observed in diagnostics or metric-value checks.

## Measurement Lessons

- Keep filtering raw metric records by evaluated `model_name`; persistence baseline rows are present in every metric JSON and would corrupt guardrail calculations if included.
- The largest measured regression for both iteration and validation was day-1 `geopotential_500` RMSE, around `+6.7%`, below the `+10%` guardrail. Future related proposals should watch short-lead geopotential spin-up even when aggregate primary score improves.
