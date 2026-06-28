# Implementation Record

## Identity

- Proposal slug: near-surface-anomaly-diagnostics
- Candidate model name: dinosaur_dfi_surface_residual
- Incumbent model name: dinosaur_dfi
- Baseline commit: cfdc344723cee1f267b892ddd924fc5d07b89f2d
- Candidate commit: 845de671268f42c6b44b0a60c287e043087364a1

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate keeps the accepted digital filter initialization path and adds an opt-in output-only residual correction for near-surface diagnostic channels. The adapter computes the lead-0 diagnostic mismatch between the initial analysis and the raw Dinosaur output for `2m_temperature` and `10m_u_component_of_wind`, then adds that residual back to requested forecast leads with an exponential 48 hour decay. Lead 0 is forced to match the input analysis for those two channels.

The correction is guarded by `apply_near_surface_residual_correction`, leaves the canonical `dinosaur` and incumbent `dinosaur_dfi` factories unchanged, and is exposed side-by-side as `dinosaur_dfi_surface_residual`. The forecast contract, target variables, lead schedule, deterministic gates, and fixed metrics remain unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore` | 0 | Syntax check passed. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Formatting applied before final tests. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Lint passed after import ordering and unused-local repairs. |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py` | 0 | 30 passed. |
| `uv run pytest` | 0 | 96 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual` | 0 | Diagnostics passed, issue count 0, primary score -1.2475800298776727. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.2854136202685928. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.2725740410982802. |
| `git diff --check` | 0 | No whitespace errors before commit. |

## Repair Attempts

- Failure observed: ruff initially found import ordering and one unused local in the focused tests.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no in accepted fast, iteration, or validation artifacts.
- Fix attempted: let ruff format the touched files and removed the unused local while preserving the focused residual-correction assertions.
- Follow-up command and result: focused tests, full test suite, fast, iteration, validation, and `git diff --check` all passed.

## Known Limitations

- The residual decay time is fixed at 48 hours for this candidate and was not tuned across alternatives.
- The correction targets only `2m_temperature` and `10m_u_component_of_wind`, because those diagnostics showed direct lead-0 output mismatch under the existing forecast contract.
- The mechanism is output-only; it does not feed corrected diagnostics back into the prognostic Dinosaur state.

## Rollback Notes

Revert commit `845de671268f42c6b44b0a60c287e043087364a1` to remove the accepted `dinosaur_dfi_surface_residual` candidate registration, adapter option, and tests. Preserve this history directory and raw evaluation artifacts when rolling back.
