# Implementation Record

## Identity

- Proposal slug: picard-hsl-theta-departure
- Candidate model name: dino_hsl_picard
- Incumbent model name: dino_hsl2_theta
- Baseline commit: 72efada4e0afbd8e34e3184dbcef90cb91cc051c
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-22_21-59-29_picard-hsl-theta-departure/implementation.md

## Implementation Summary

Implemented `dino_hsl_picard` as a side-by-side alias extending
`dino_hsl2_theta`. The new selector
`use_picard_semilagrangian_theta_departure` defaults to false throughout the
primitive-equation and adapter plumbing, so incumbent behavior is unchanged
unless the candidate factory enables it.

The Picard theta path first computes the accepted midpoint full-step
displacement and accepted midpoint tendency. When the Picard selector is
enabled, it remaps the existing nodal horizontal wind components to a corrected
midpoint using half of the accepted full-step midpoint displacement, recomputes
the bounded full-step departure displacement from that corrected midpoint wind,
and applies the existing bilinear theta-anomaly remap. Invalid Picard
diagnostics fall back to the accepted midpoint tendency, which already falls
back to first-order HSL and then the incumbent Eulerian theta tendency.

Added package export, registry factory/entry, factory parity tests, dependency
and registry coverage, displacement finite/bounded tests, zero/uniform wind
parity tests, corrected-midpoint nonfinite fallback coverage, and a finite
non-JIT smoke forecast for `dino_hsl_picard`.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Changed source and focused tests passed ruff. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'hsl_picard or hsl2_theta or hsl_theta' tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 20 passed, 143 deselected in 57.33s. |
| `uv run pytest` | not_run | Left for Orchestrator; focused implementation checks passed. |
| `uv run dynamaxx-eval fast --model dino_hsl_picard` | not_run | Optional fast eval not run in Implementer pass. |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: Full test suite and fixed fast/iteration/validation evaluations were not run by this role.
- Limitation: Candidate is uncommitted; current HEAD remains the baseline commit.

## Rollback Notes

Remove the Picard selector/helper and transport branch from
`primitive_equations.py`, remove adapter field/factory/plumbing, remove the
package export and registry entry, and remove the Picard-specific tests and
this implementation record. Leave unrelated HSL theta and midpoint behavior
unchanged.
