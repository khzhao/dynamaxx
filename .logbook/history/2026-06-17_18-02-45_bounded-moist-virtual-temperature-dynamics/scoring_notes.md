# Scoring Notes

## Scope

- Candidate: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist`
- Incumbent: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- History directory: `.logbook/history/2026-06-17_18-02-45_bounded-moist-virtual-temperature-dynamics`
- Worker count: `4`

## Commands

| Command | Exit status | Notes |
| --- | ---: | --- |
| `uv run python - <<'PY' ... list_models ... PY` | 1 | Initial registration probe failed because `list_models` is not exported by `dynamaxx.dycore.registry`. |
| `uv run python - <<'PY' ... dycore_model_names ... PY` | 0 | Confirmed candidate and incumbent are registered. |
| `uv run pytest` | 0 | `131 passed, 2 skipped in 65.36s`. |
| Fast artifact verification script | 0 | Reused existing candidate fast JSON/CSV; model name matched, `failed=False`, `issues=0`. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist --workers 4` | 0 | Completed 229 chunks, wrote candidate iteration metrics. |

Validation was not run because the iteration gate did not pass. Golden was not run.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`
- Incumbent validation JSON available for reuse: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent validation CSV available for reuse: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`

## Scores

- Fast candidate primary: `-1.1788189813240295`
- Iteration candidate primary: `-1.199169003293556`
- Iteration incumbent primary: `-1.143975258592661`
- Iteration primary delta: `-0.055193744700895`
- Required iteration primary delta: `>= +0.002`

## Diagnostics

- Candidate fast: `failed=False`, `issues=0`
- Candidate iteration: `failed=False`, `issues=0`
- Incumbent iteration: `failed=False`, `issues=0`

## Guardrails

All iteration comparisons filtered records by exact `model_name` because the artifacts also contain `persistence` rows.

- Primary delta gate: failed; delta was `-0.055193744700895`, below `+0.002`.
- Diagnostics gate: passed; candidate iteration diagnostics were clean.
- Early day 1-5 mean RMSE regression: passed; candidate `449.0447501099323`, incumbent `443.9461359445328`, relative regression `0.011484758515921711`.
- Worst variable+lead RMSE regression: passed; `10m_u_component_of_wind` at `24` hours, candidate `5.807337186067861`, incumbent `5.455615913305551`, relative regression `0.06446958113464453`.
- Variable+lead RMSE regressions over 10%: none.

## Gate Status

- Iteration gate: failed.
- Validation gate: not run because iteration gate failed.

## Anomalies And Lessons

- The first registration helper probe was incorrect and exited 1; the corrected `dycore_model_names()` probe confirmed both models are registered.
- The bounded moist candidate kept diagnostics clean but reduced iteration primary score substantially versus the incumbent.
- The largest observed RMSE degradation was below the 10% variable+lead guardrail, so the decisive failure was the primary score delta rather than guardrail or diagnostics failure.
