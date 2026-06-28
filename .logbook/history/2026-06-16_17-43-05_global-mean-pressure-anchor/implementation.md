# Implementation Record

## Identity

- Proposal slug: global-mean-pressure-anchor
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_pressure_anchor
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs
- Baseline commit: 4756cc9a4b69c41eec60e2177fb03a73974f0e2d
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side Dinosaur candidate named
`dinosaur_dfi_surface_residual_weak_hs_pressure_anchor`. The candidate kept the
accepted incumbent mechanisms, including digital-filter initialization,
near-surface residual correction, and weak thermal Held-Suarez relaxation, and
added one optional step filter.

The step filter copied only the previous state's zero-wavenumber
`log_surface_pressure` modal coefficient into the next state after each inner
step. All nonzero `log_surface_pressure` modes, wind fields, temperature
variation, tracers, and simulation time were preserved from the next state.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore` | pass | Implementer record. |
| `uv run ruff format ...` | pass | Implementer record for changed Python files. |
| `uv run ruff check ...` | pass | Implementer record for changed Python files. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 42 passed. |
| `uv run pytest` | pass | 108 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_pressure_anchor` | pass | Primary `-1.1909823513604236`; diagnostics clean. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_pressure_anchor --workers 4` | pass | Primary `-1.2218418099192239`; diagnostics clean; did not promote. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_pressure_anchor --workers 4` | not_run | Skipped because iteration primary delta failed promotion threshold. |
| `git diff --check` | pass | Implementer record. |

## Repair Attempts

- Failure observed: none during implementation
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: The global pressure-mode anchor was numerically benign but
  produced only floating-point-scale metric movement relative to the incumbent.
  It did not satisfy the fixed iteration promotion threshold.

## Rollback Notes

The candidate was rejected and not committed. Rollback was completed by
restoring the six implementation files listed above to the baseline commit
state. Evaluation and logbook artifacts were retained for reproducibility.
