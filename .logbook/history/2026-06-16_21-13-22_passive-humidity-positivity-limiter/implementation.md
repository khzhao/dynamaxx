# Implementation Record

## Identity

- Proposal slug: passive-humidity-positivity-limiter
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_qpos
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
`dinosaur_dfi_surface_residual_weak_hs_qpos`. The candidate preserved the
accepted weak-Held-Suarez incumbent, including digital-filter initialization,
near-surface residual correction, weak thermal Held-Suarez coefficients,
`use_humidity_in_dynamics=False`, the `900.0` second inner step, horizontal
diffusion, pressure grid, and residual correction.

The only behavioral change was a default-off diagnostic flag that applies
`jnp.maximum(specific_humidity, 0.0)` to passive humidity during output
conversion, before hydrostatic geopotential diagnostics and sigma-to-pressure
interpolation. The stored Dinosaur trajectory and prognostic humidity tracer
were not mutated.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore` | pass | Implementer record. |
| `uv run ruff format ...` | pass | Implementer record. |
| `uv run ruff check ...` | pass | Implementer record. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 43 passed. |
| `uv run pytest` | pass | 109 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_qpos` | pass | Primary `-1.1909729416286097`; diagnostics clean. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_qpos --workers 4` | pass | Primary `-1.2218428097613614`; diagnostics clean; did not promote. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_qpos --workers 4` | not_run | Skipped because iteration primary delta failed promotion threshold. |
| `git diff --check` | pass | Implementer record. |

## Repair Attempts

- Failure observed: none during implementation
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: The diagnostic humidity floor produced only numerical-scale metric
  movement and slightly worsened aggregate iteration primary score.

## Rollback Notes

The candidate was rejected and not committed. Rollback was completed by
restoring the six implementation files listed above to the baseline commit
state. Evaluation and logbook artifacts were retained for reproducibility.
