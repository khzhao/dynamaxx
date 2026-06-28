# Implementation Record

## Summary

Implemented `high-precision-spectral-transform-core` as a side-by-side dycore
candidate named `dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec`.

The candidate preserves the incumbent physics, forecast inputs, forecast output
contract, target variables, and fixed evaluation protocols. The only model
selector change is the spherical-harmonic implementation used when constructing
the Dinosaur forecast grid.

## Baseline

- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Incumbent model: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Candidate model: `dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec`

## Code Changes

- Added optional `spherical_harmonics_impl` plumbing from
  `DinosaurPrimitiveEquationsDycoreModel` into `grid_metadata`.
- Added `high_precision_fast_spherical_harmonics`, which constructs
  `FastSphericalHarmonics` with `jax.lax.Precision.HIGHEST`.
- Added `high_precision_sht_dinosaur_dycore_model` as a replacement of the
  incumbent with only the model name and spherical-harmonic implementation
  selector changed.
- Exported and registered
  `dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec`.
- Added focused tests for factory preservation, registry construction, transform
  shape/dtype/finite contracts, highest-precision selector wiring, and a small
  non-JIT finite forecast smoke test.

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/coordinates.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Validation Before Scoring

- `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py`: passed.
- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/coordinates.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: passed.
- `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/coordinates.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: passed after formatting the implementation.
- `git diff --check`: passed.
- `uv run pytest`: passed with `257 passed, 2 skipped in 311.70s`.
- `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec`: passed with primary score `-0.22382975498854574`, diagnostics failed `false`, issue count `0`, and `120` records.

## Notes

The existing default forecast path uses `RealSphericalHarmonics`, whose local
einsum helper already requests highest precision. This candidate therefore uses
the existing `FastSphericalHarmonics` transform path with highest precision as a
true side-by-side numerical-core experiment. That changes the internal modal
representation while preserving public forecast shapes and variables.
