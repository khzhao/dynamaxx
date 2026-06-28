# Implementation Record

## Identity

- Proposal slug: full-grid-spectral-truncation
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_t120
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
`dinosaur_dfi_surface_residual_weak_hs_t120`. The candidate preserved the
accepted weak-Held-Suarez incumbent settings, including digital-filter
initialization, near-surface residual correction, weak thermal Held-Suarez
coefficients, the `900.0` second inner step, vertical advection, humidity
behavior, horizontal diffusion, pressure grid, and output diagnostics.

The only scientific change was setting `spectral_wavenumbers=120` in the
candidate factory. The forecast API, output variables, fixed evaluation
commands, splits, metrics, and lead times were unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore` | pass | Implementer record. |
| `uv run ruff format ...` | pass | One file reformatted. |
| `uv run ruff check ...` | pass | Implementer record. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 42 passed. |
| `uv run pytest` | pass | 108 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_t120` | fail | Command exited 0 but diagnostics failed with nonfinite forecast and nonfinite metric records. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_t120 --workers 4` | not_run | Skipped because fast diagnostics failed. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_t120 --workers 4` | not_run | Skipped because iteration was not allowed. |
| `git diff --check` | pass | Implementer record. |

## Repair Attempts

- Failure observed: fast diagnostics failed with nonfinite forecast output and
  nonfinite metric records.
- Implementer-owned failure: no
- NaN/Inf forecast observed: yes
- Fix attempted: formatting only; stabilizing T120 would require changing
  diffusion, time step, truncation value, or another protected setting, which
  would broaden the selected proposal.
- Follow-up command and result: fast artifact verified by Scorer; earliest
  nonfinite candidate metrics occur at lead hour 24 for all four target
  variables.

## Known Limitations

- Limitation: Fixed T120 truncation is unstable under the incumbent's existing
  time step, filters, and forcing setup.

## Rollback Notes

The candidate was rejected and not committed. Rollback was completed by
restoring the six implementation files listed above to the baseline commit
state. Evaluation and logbook artifacts were retained for reproducibility.
