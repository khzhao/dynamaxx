# Implementation Record

## Identity

- Proposal slug: pressure-thickness-ri2m-temperature
- Candidate model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m
- Incumbent model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag
- Baseline commit: 1fd66d570dea478e34cad87374dc445997b75b4a
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-07-08_02-22-35_pressure-thickness-ri2m-temperature/implementation.md

## Implementation Summary

Added `use_pressure_thickness_weighted_ri2m_temperature` as an opt-in adapter
flag and registered the side-by-side factory
`dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m`.

When the incumbent bulk-Richardson 2 m temperature diagnostic and the new flag
are both enabled, the diagnostic uses fixed shallow sigma bands: the bottom two
layers for the lower reference and the next two layers above for the upper
reference, weighted by positive sigma `layer_thickness`. The existing
Richardson stability algebra, shear floor, departure cap, finite fallback, and
downstream residual correction remain unchanged. Columns with fewer than four
sigma layers or nonfinite weighted references fall back to the incumbent
two-level RI2m diagnostic.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Syntax check before required commands. |
| `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Initial run failed; after formatting, recheck passed. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Initial run failed for import ordering; after fix, recheck passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 244 passed in 296.00s. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m` | pass | failed=False, issues=0, records=120, primary_score=-0.117828. |

## Repair Attempts

- Failure observed: `ruff format --check` reported three files needing formatting.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: ran `uv run ruff format` on the changed source/test files.
- Follow-up command and result: `uv run ruff format --check ...` passed.

- Failure observed: `ruff check` reported import ordering issues in `__init__.py`
  and `test_primitive_equations.py`.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: ran `uv run ruff check --fix` on the changed source/test files.
- Follow-up command and result: `uv run ruff check ...` passed.

## Known Limitations

- This implementation intentionally changes only the raw RI2m 2 m temperature
  diagnostic input state. It does not alter trajectory integration, 10 m wind,
  prognostic mass/wind/geopotential state, DFI, Ekman, orographic lift, terrain
  work drag, evaluation protocols, targets, splits, or lead times.
- Only the requested focused tests and fast pre-scoring sanity check were run;
  iteration and validation scoring remain for the Scorer.

## Rollback Notes

Revert the edits to the six changed source/test files and remove this
implementation record. Leave unrelated work, the pre-existing untracked
`gifs/`, and generated evaluation artifacts untouched unless explicitly
instructed otherwise.
