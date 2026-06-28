# Implementation Record

## Scope

- Proposal slug: `mass-neutral-clipped-wtg-dse`
- Candidate model: `dino_hsl2_mass_dse_wtg_mneutral`
- Incumbent model: `dino_hsl2_mass_dse_wtg`
- Baseline commit: `d8561caebb78ca096263d8c412217570ff2d1f46`

## Changes

- Added `use_mass_neutral_clipped_wtg_dse` as an opt-in selector on
  `DinosaurPrimitiveEquationsDycoreModel`.
- Passed the selector into the existing rollout-only tropical WTG mass-DSE
  filter while preserving the incumbent default branch.
- Added a selected branch that computes the accepted raw WTG temperature
  increment and cap, then removes a pressure-thickness-weighted clipped
  mass-DSE offset instead of the incumbent area-mean temperature offset.
- Preserved the accepted WTG latitude envelope, sigma envelope, low-mode mask,
  relaxation timescale, temperature cap, finite fallback, and positive-time
  rollout placement.
- Added the side-by-side factory/export/registry entry for
  `dino_hsl2_mass_dse_wtg_mneutral`.
- Added focused tests for factory/registry preservation, explicit false
  selector equivalence, masked mass-DSE neutralization on a nonuniform pressure
  synthetic state, invalid-pressure fallback, and existing WTG behavior.

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Verification

- Implementer targeted checks passed:
  - `uv run ruff check ...`
  - `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "tropical_wtg"`
  - `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py`
- Orchestrator targeted WTG check passed:
  `8 passed, 126 deselected in 63.74s`.
- Orchestrator full test gate passed:
  `uv run pytest` -> `249 passed, 2 skipped in 246.32s`.

## Notes

The implementation keeps the forecast contract, fixed evaluation protocols,
target variables, and lead schedules unchanged. It does not implement the
staged time-centered WTG or scrapped virtual-static-energy variants.
