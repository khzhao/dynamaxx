# Implementation Record

## Identity

- Proposal slug: passive-humidity-dfi-bypass
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
- Baseline commit: a7833574e9ade1a5271bd8cbef2fa1357465f5a8
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-17_12-29-40_passive-humidity-dfi-bypass/implementation.md

## Implementation Summary

Registered a side-by-side Dinosaur candidate that preserves all incumbent
configuration and adds one candidate-only flag,
`restore_passive_humidity_after_dfi`. When DFI is enabled, the adapter now
optionally replaces only the filtered `specific_humidity` tracer with the
pre-DFI initialized tracer after `initialize_state(dinosaur_state)`. The helper
is inactive for moist-coupled dynamics, missing humidity in the filtered state,
or missing humidity in the unfiltered state. Vorticity, divergence,
temperature variation, log surface pressure, non-humidity tracers, and
`sim_time` are kept from the filtered state.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | All checks passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 64 passed in 58.31s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass` | 0 | `failed=False`, `issues=0`, `records=120`, primary score `-1.123286978926717`; metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass.json`. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: none yet
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: not applicable

## Known Limitations

- This candidate intentionally does not alter humidity values outside the
  post-DFI restore. It does not clip, floor, retune, residual-correct, or add
  moist coupling.
- Validation of score movement is left to the Scorer role.

## Rollback Notes

Revert the changes to the six tracked source/test files listed above. The
logbook implementation record can remain as this experiment's history artifact.
