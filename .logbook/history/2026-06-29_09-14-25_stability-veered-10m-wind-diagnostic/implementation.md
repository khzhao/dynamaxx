# Implementation Record

- Proposal slug: `stability-veered-10m-wind-diagnostic`
- Candidate model: `dino_ri2m_ekman_veered_10m`
- Incumbent model: `dino_ri2m_ekman_coupled`
- Baseline HEAD before implementation: `453b8dd8646fe67f73a2888060e53a1a7b33fda5`
- Candidate commit before scoring: not committed; implementation exists as tracked worktree diff and `candidate.diff`.

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

- Added `use_surface_layer_veered_10m_wind_diagnostic` as an opt-in output diagnostic selector.
- Added side-by-side factory and registry key `dino_ri2m_ekman_veered_10m`.
- Added `_surface_layer_veered_10m_wind`, which computes the accepted Richardson 10 m wind first, then applies bounded hemisphere-aware stable-column turning while preserving diagnosed speed.
- Kept the correction output-only: rollout tendencies, coupled Ekman stress-pumping, log pressure, temperature, T2m, MSLP, and Z500 are unchanged.
- Added fallback tests for invalid diagnostics and weak shear, speed preservation tests, output-contract tests, factory tests, and registry/dependency tests.

## Local Checks

- `uv run python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: passed.
- `git diff --check`: passed.
- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py`: passed.
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'veered_10m or surface_layer_veered' tests/dycore/models/dinosaur/test_dependency.py -k 'veered_10m or canonical' tests/dycore/test_registry.py -k 'veered_10m or lists_default'`: passed, 9 passed and 206 deselected.

## Known Limitations

- Scientific evaluation had not been run at implementation handoff; scoring will run fixed fast, iteration, and validation gates as required.
