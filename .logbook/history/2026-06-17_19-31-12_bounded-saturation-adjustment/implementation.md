# Implementation Record

## Identity

- Proposal slug: bounded-saturation-adjustment
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
- Baseline commit: a7833574e9ade1a5271bd8cbef2fa1357465f5a8
- Candidate commit: not committed
- Baseline note: prompt baseline `a7833574e9ade1a5271bd1bd8cbef2fa1357465f5a8` is not a valid git commit in this checkout; `git rev-parse HEAD` matched the Orchestrator-observed `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`.

## Files Changed

- Path: `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- Path: `src/dynamaxx/dycore/registry.py`
- Path: `tests/dycore/models/dinosaur/test_dependency.py`
- Path: `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Path: `tests/dycore/test_registry.py`
- Path: `.logbook/history/2026-06-17_19-31-12_bounded-saturation-adjustment/implementation.md`

## Implementation Summary

Implemented one side-by-side Dinosaur candidate named `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust`.

The candidate preserves the incumbent DFI, weak Held-Suarez relaxation, near-surface residual correction, log-pressure initialization, hydrostatic layer initialization, vertical advection, T80 truncation, 900 s inner step, output API, and `use_humidity_in_dynamics=False`.

The only new mechanism is an opt-in forward step filter. After the positive-time IMEX step and existing horizontal-diffusion filter, it converts temperature variation and `specific_humidity` to nodal sigma fields, clips humidity to `[0, 0.08]`, diagnoses sigma-layer pressure from log surface pressure, computes guarded Bolton-style saturation specific humidity over liquid water, removes supersaturation from the humidity tracer, and adds `L_v / c_p * condensed_q` to dry temperature. Vorticity, divergence, log surface pressure, non-humidity tracers, and `sim_time` are preserved. The DFI initializer receives only the reversible pre-existing filters, so saturation adjustment is not run in the time-reversed initialization.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `git cat-file -e a7833574e9ade1a5271bd1bd8cbef2fa1357465f5a8^{commit}` | 128 | Prompt baseline hash was invalid; used valid HEAD recorded above. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Touched-file lint passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | 66 passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.13397`; metrics at `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust.json`. |

## Repair Attempts

- Failure observed: self-review caught an invalid overly long registry function definition before running checks.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: replaced the malformed registry function with a short internal factory while preserving the exact registered model name.
- Follow-up command and result: touched-file `ruff`, focused `pytest`, and `dynamaxx-eval fast` all passed.

## Known Limitations

- The adjustment is a minimal warm-liquid saturation closure only; it does not add cloud condensate storage, precipitation fallout, ice-phase saturation, radiation coupling, or re-evaporation.
- The filter is local and bounded but still changes forward thermodynamics every inner step, so iteration and validation scoring remain necessary to determine skill impact.

## Rollback Notes

Revert the changes in the six scoped Python files listed above and remove this implementation record to roll back only this experiment. No commit was created and the leaderboard was not touched.
