# Implementation Record

## Identity

- Proposal slug: migrating-pressure-tide-forcing
- Candidate model name: dino_hsl2_mass_dse_pressure_tide
- Incumbent model name: dino_hsl2_mass_dse
- Baseline commit: 2c70bb5b77370a074330c2b46954f74f20771f12
- Candidate commit: unavailable

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-24_18-53-21_migrating-pressure-tide-forcing/implementation.md

## Implementation Summary

Added an opt-in `apply_migrating_surface_pressure_tide` selector on
`DinosaurPrimitiveEquationsDycoreModel` and registered the side-by-side
`dino_hsl2_mass_dse_pressure_tide` factory as a `dino_hsl2_mass_dse` derivative.

The tide is a rollout-only step filter that directly updates
`log_surface_pressure` by applying `pattern(next_time) - pattern(prev_time)`.
Patterns use forecast initialization UTC hour plus primitive-equation
`sim_time`, include fixed small semidiurnal wavenumber-2 and diurnal wavenumber-1
components, use a smooth tropical/subtropical latitude envelope, subtract the
quadrature area mean, convert Pa to nondimensional log-pressure increments with
a guarded surface pressure, and cap each increment. The filter falls back to the
input `next_state` for nonfinite time, pressure, pattern, increment, or corrected
modal log-pressure diagnostics.

DFI filter lists intentionally exclude the pressure-tide filter. The candidate
sets `sim_time=0` only when the selector is enabled and threads the scalar
initial UTC hour into the jitted trajectory function without changing the public
`ForecastInput` or `WeatherState` API.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/radiation.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Run after implementation and again after repair. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "pressure_tide or tide or mass_dse"` | passed | 12 passed, 122 deselected. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | 47 passed. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_pressure_tide` | passed | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.285491`, metrics at `outputs/eval/fast_dino_hsl2_mass_dse_pressure_tide.json`. |

## Repair Attempts

- Failure observed: The first focused pytest run failed in the new non-JIT smoke test because it asserted lead-zero diagnostic MSLP exactly equaled the raw structured input field. Existing Dinosaur sigma/spectral conversion does not preserve that diagnostic field exactly.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: Removed the unrelated raw-input exactness assertion and kept the smoke test focused on finite candidate execution. Exact zero-elapsed pressure-tide behavior remains covered by the direct filter test.
- Follow-up command and result: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "pressure_tide or tide or mass_dse"` passed.

## Known Limitations

- Limitation: Tide amplitudes and phases are fixed literature-scale constants and were not tuned against fast, iteration, or validation results.
- Limitation: Only the requested local tests and fast protocol were run; iteration and validation scoring remain for the Scorer/Orchestrator.
- Limitation: The pressure tendency is applied directly to the prognostic mass field, so later dynamical feedback is possible even though the filter itself changes only `log_surface_pressure`.

## Rollback Notes

Remove the `apply_migrating_surface_pressure_tide` selector, pressure-tide helper
functions, candidate factory/export, registry entry, focused tests, and this
implementation record. Do not modify unrelated worktree contents such as the
pre-existing untracked `gifs/` directory.
