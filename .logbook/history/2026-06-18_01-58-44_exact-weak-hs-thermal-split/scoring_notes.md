# Scoring Notes

## Gate Status

- Registration: confirmed both `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs` and `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init` are registered.
- Tests: `uv run pytest` exited 0 with `131 passed, 2 skipped in 63.18s`.
- Fast gate: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs` exited 0. Candidate fast primary score was `-1.123073080183006`; diagnostics `failed=False`, issue count `0`.
- Iteration promotion gate: did not promote. Candidate iteration primary score was `-1.1439279880915845`; incumbent iteration primary score was `-1.143975258592661`; delta was `+0.000047270501076557`, below the required `+0.002`.
- Validation acceptance gate: not evaluated. The validation command was not run because validation may run only if the iteration promotion gate passes.

## Commands And Exit Statuses

| Command | Exit Status | Notes |
| --- | ---: | --- |
| Registration check shown below | 0 | Candidate and incumbent both printed `True`. |
| `uv run pytest` | 0 | `131 passed, 2 skipped in 63.18s`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs` | 0 | `failed=False`, `issues=0`, `records=120`, primary `-1.123073080183006`. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs --workers 4` | 0 | `failed=False`, `issues=0`, `records=120`, primary `-1.1439279880915845`. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs --workers 4` | not run | Skipped because iteration did not promote. |

Registration command:

```bash
uv run python - <<'PY'
from dynamaxx.dycore.registry import dycore_model_names
candidate = 'dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs'
incumbent = 'dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init'
registered = set(dycore_model_names())
for name in (candidate, incumbent):
    print(f'{name}: {name in registered}')
if not {candidate, incumbent}.issubset(registered):
    raise SystemExit(1)
PY
```

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs.csv`
- Candidate validation JSON/CSV: not produced.
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`

## Guardrails

- Diagnostics: candidate fast and candidate iteration both had `failed=False` and `0` issues. Reused incumbent iteration and validation artifacts also had `failed=False` and `0` issues.
- Record filtering: raw iteration JSON files contained `120` records each, including persistence baseline rows. Guardrails used only the `60` records where `model_name` matched the evaluated candidate or incumbent.
- Early day 1-5 mean RMSE guardrail: no variable exceeded the `2%` regression limit. Relative changes were `-0.012807%` for `2m_temperature`, `+0.000660%` for `mean_sea_level_pressure`, `+0.000739%` for `geopotential_500`, and `-0.002251%` for `10m_u_component_of_wind`.
- Variable+lead RMSE guardrail: no variable+lead exceeded the `10%` regression limit. The largest positive regression was `geopotential_500` at lead `360h` with `+0.017602%`.

## Measurement Lessons

- The exact weak-HS thermal split was numerically clean under the fixed fast and iteration protocols, but its primary-score gain was too small for promotion.
- Preserve the prior scoring lesson: filter raw metric records by evaluated `model_name` before computing candidate-vs-incumbent guardrails, because persistence baseline rows are present in the JSON and CSV outputs.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused from the Orchestrator-provided compatible outputs. Candidate iteration reported `cached=0 pending=229`, so no candidate chunk cache was reused.
- Resource limits: no CPU, RAM, GPU, disk, timeout, or worker failure was observed.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Report only the measurement result: iteration did not promote to validation because the primary delta was below threshold. I did not run validation, update `.logbook/leaderboard.json`, commit, or make an accept/reject decision.
