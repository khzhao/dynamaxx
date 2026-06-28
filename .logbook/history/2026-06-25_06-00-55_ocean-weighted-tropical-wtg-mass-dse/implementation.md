# Implementation Record

## Scope

- Proposal slug: `ocean-weighted-tropical-wtg-mass-dse`
- Candidate model: `dino_hsl2_mass_dse_wtg_ocean`
- Incumbent model: `dino_hsl2_mass_dse_wtg`
- Baseline commit: `d8561caebb78ca096263d8c412217570ff2d1f46`

## Changes

- Added `use_ocean_weighted_tropical_wtg` as an opt-in selector on
  `DinosaurPrimitiveEquationsDycoreModel`.
- Reused the existing WeatherBench2 land-sea fraction loading and validation
  path to derive an ocean fraction in Dinosaur latitude order only when the
  ocean-weighted WTG selector is active.
- Passed an optional ocean weight into the rollout-only tropical WTG mass-DSE
  filter.
- Multiplied the accepted WTG latitude mask and tropical mean weights by the
  optional ocean weight. Missing, malformed, out-of-range, or nonfinite masks
  fall back to the incumbent unweighted WTG behavior.
- Added the side-by-side factory/export/registry entry for
  `dino_hsl2_mass_dse_wtg_ocean`.
- Added focused tests for factory/registry preservation, all-ocean equivalence,
  all-land suppression, invalid-mask incumbent fallback, and a small finite
  non-JIT forecast.

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Verification

- Implementer targeted checks passed.
- Orchestrator full test gate passed:
  `uv run pytest` -> `249 passed, 2 skipped in 272.47s`.

## Notes

The implementation keeps the forecast contract, fixed evaluation protocols,
target variables, and lead schedules unchanged. It does not implement the
staged zonal-anomaly or first-baroclinic WTG variants.
