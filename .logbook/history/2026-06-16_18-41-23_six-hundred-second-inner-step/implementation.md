# Implementation Record

## Identity

- Proposal slug: six-hundred-second-inner-step
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_600s
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
`dinosaur_dfi_surface_residual_weak_hs_600s`. The candidate preserved the
accepted weak-Held-Suarez incumbent mechanisms, including digital-filter
initialization, near-surface residual correction, and weak thermal
Held-Suarez relaxation, while changing only `inner_step_seconds` from `900.0`
to `600.0`.

The DFI time span and cutoff, near-surface residual decay, weak Held-Suarez
coefficients, output variables, forecast contract, and fixed evaluation
protocols were unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore` | pass | Implementer record. |
| `uv run ruff format ...` | pass | Changed files were already formatted. |
| `uv run ruff check ...` | pass | Implementer record. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 44 passed. |
| `uv run pytest` | pass | 110 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_600s` | pass | Primary `-1.1911638361399597`; diagnostics clean. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_600s --workers 4` | pass | Primary `-1.2220957940878374`; diagnostics clean; did not promote. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_600s --workers 4` | not_run | Skipped because iteration primary delta failed promotion threshold. |
| `git diff --check` | pass | Implementer record. |

## Repair Attempts

- Failure observed: none during implementation
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: The finer time step increased iteration runtime to about 60
  minutes at 4 workers and slightly degraded the fixed iteration primary score.

## Rollback Notes

The candidate was rejected and not committed. Rollback was completed by
restoring the six implementation files listed above to the baseline commit
state. Evaluation and logbook artifacts were retained for reproducibility.
