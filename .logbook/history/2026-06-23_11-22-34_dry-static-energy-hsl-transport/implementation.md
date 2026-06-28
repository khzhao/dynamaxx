# Implementation

- Baseline commit: `72efada4e0afbd8e34e3184dbcef90cb91cc051c`
- Candidate model: `dino_hsl2_theta_dse_hsl`
- Incumbent model: `dino_hsl2_theta`
- Candidate commit: not committed by Implementer

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-23_11-22-34_dry-static-energy-hsl-transport/implementation.md`

## Summary

Implemented a side-by-side `dino_hsl2_theta_dse_hsl` factory and registry entry.
The candidate preserves `dino_hsl2_theta` options except for the new
default-false `use_dry_static_energy_hsl_transport` selector.

In the potential-temperature thermal tendency branch, the candidate diagnoses
dry static energy from full nodal temperature plus dry hydrostatic sigma
geopotential using `get_geopotential_on_sigma` and the model's nodal orography.
It subtracts a layerwise quadrature-weighted horizontal mean, uses
`horizontal_scalar_advection` for the Eulerian DSE fallback tendency, reuses
`horizontal_semilagrangian_theta_transport` for the accepted HSL2 midpoint
departure/remap path, and converts the resulting horizontal DSE tendency back to
temperature tendency through `Cp`. Vertical theta transport and the adiabatic
pressure-work helper are unchanged. Nonfinite DSE/geopotential/converted-DSE
diagnostics fall back to the accepted theta-HSL tendency.

## Tests And Checks

- PASS: `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
- PASS: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'dse_hsl or dry_static or hsl2_theta or hsl_theta' tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
- PASS: `git diff --check`
- PASS: `uv run pytest` (`231 passed, 2 skipped`)

## Repair Attempts

- Fixed ruff import ordering in `tests/dycore/models/dinosaur/test_primitive_equations.py`.

## Limitations

- WeatherBench scoring was not run by the Implementer; that remains Scorer
  responsibility.
- The DSE selector is active only for the new side-by-side model and is guarded
  by finite-diagnostic fallback rather than tuned against evaluation metrics.
