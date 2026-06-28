# Implementation

- Baseline commit: `72efada4e0afbd8e34e3184dbcef90cb91cc051c`
- Candidate model: `dino_hsl2_theta_pw_ramp`
- Incumbent model: `dino_hsl2_theta`
- Candidate commit: not committed

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-23_08-53-50_ramped-column-neutral-theta-pressure-work/implementation.md`

## Implementation Notes

- Added the default-false selector `use_ramped_theta_pressure_work`.
- Registered side-by-side factory `ramped_theta_pressure_work_dinosaur_dycore_model()`
  as `dino_hsl2_theta_pw_ramp`; it preserves `dino_hsl2_theta` settings except
  model name and the new selector.
- Reused the prior hydrostatic theta/Exner pressure-work diagnostic as an added
  nodal temperature increment relative to `nodal_temperature_adiabatic_tendency`.
- Applied fixed safeguards only to the added increment:
  zero ramp through 24 forecast hours, smoothstep ramp from 24 h to 72 h, maximum
  ramp `0.25`, inert zero ramp when `state.sim_time is None`, pressure/sigma-layer
  weighted column-mean removal, and a fixed `10 K/day`-equivalent bound.
- Candidate fallback returns the accepted incumbent theta-form tendency when the
  pressure-work diagnostics are invalid; the existing theta branch fallback remains
  unchanged for invalid shared theta/pressure diagnostics.
- Left HSL2 theta departure/remap, vertical theta advection, momentum, divergence,
  surface pressure tendency, tracers, DFI, residual corrections, surface fluxes,
  output variables, and evaluation protocols unchanged.

## Tests Run

- PASS: `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
- PASS after repair: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'pw_ramp or pressure_work or hsl2_theta or hsl_theta' tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
- PASS: `git diff --check`
- PASS: `uv run pytest` (`232 passed, 2 skipped`)

## Repair Attempts

- Initial focused pytest run failed one nonpositive-pressure fallback test because
  the test compared the candidate with an invalid pressure diagnostic against an
  incumbent using a valid pressure diagnostic. Repaired the test to compare both
  equations under the same invalid pressure diagnostic, matching the accepted
  incumbent fallback path.
- Rerun of ruff flagged the local fallback helper as a lambda and then a missing
  blank line before a nested function. Repaired both style issues and reran ruff.
- Tightened the pressure-work limiter after the passing test run so projected
  columns are scaled back under the fixed cap while preserving column neutrality;
  reran ruff, focused pytest, and `git diff --check`.

## Limitations

- WeatherBench scoring was not run by the Implementer; that remains a Scorer
  responsibility for this iteration.
- No sweeps, amplitude tuning, static-stability ocean flux, divergence drag,
  diagnostic sidecars, or HSL trajectory changes were implemented.
