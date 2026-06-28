# Implementation Record

## Identity

- Proposal slug: conservative-pressure-thickness-init-remap
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
- Baseline commit: a7833574e9ade1a5271bd8cbef2fa1357465f5a8
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: tests/dycore/models/dinosaur/test_vertical_interpolation.py
- Path: .logbook/history/2026-06-17_08-03-52_conservative-pressure-thickness-init-remap/implementation.md

## Implementation Summary

Implemented the selected side-by-side candidate only. The new model preserves the incumbent DFI, weak Held-Suarez relaxation, near-surface residual correction, log-pressure initialization flag, layer-mean hydrostatic temperature initialization, T80 defaults, 900 s inner step, vertical advection, zero-orography trajectory setup, and output interpolation contract.

The implementation adds `use_conservative_pressure_initialization_remap` to the Dinosaur adapter and registers `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init`. When that flag is enabled, pressure-level initialization of temperature, u wind, v wind, and humidity uses `interp_pressure_to_sigma_conservative_log_pressure` instead of center-sampled pressure/log-pressure interpolation.

The remap treats source pressure centers as finite log-pressure layers bounded by log-pressure midpoints with extrapolated outer finite bounds. Target sigma layers use `sigma_coords.boundaries * surface_pressure_hpa` in each column, clamped to the existing small minimum pressure before taking logs. Interior target/source overlap is averaged conservatively in log-pressure thickness. Target portions above the finite source top or below the finite source bottom are assigned to the nearest source layer, so rows remain finite and column-constant fields are preserved.

Output sigma-to-pressure interpolation was not changed.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_vertical_interpolation.py` | passed | `All checks passed!` |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_vertical_interpolation.py` | passed | 65 passed in 57.90s |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init` | passed | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.12634`, metrics at `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init.json` |
| `git diff --check` | passed | No whitespace errors |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: not applicable
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: The source pressure-level analyses are interpreted as finite layer averages for this candidate, although the upstream data may behave partly like point samples.
- Limitation: The outer source layer bounds are finite extrapolations from log-pressure center spacing; portions outside those finite bounds use bounded nearest-layer assignment as required by the proposal.
- Limitation: Only the requested focused tests and fast protocol were run. Iteration, validation, and golden were not run by the Implementer.

## Rollback Notes

Revert this experiment by removing the conservative remap helper and bounded-weight helper from `vertical_interpolation.py`, removing `use_conservative_pressure_initialization_remap` and `conservative_initialization_dinosaur_dycore_model` from `adapter.py`, removing the public export from `dinosaur/__init__.py`, removing the registry factory/key, and removing the tests added or updated for the conservative candidate. Do not remove unrelated logbook history or evaluation outputs unless the Orchestrator explicitly requests it.
