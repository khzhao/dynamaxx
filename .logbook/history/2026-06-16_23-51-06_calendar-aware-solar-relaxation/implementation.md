# Implementation Record

## Identity

- Proposal slug: `calendar-aware-solar-relaxation`
- Candidate model name: `dinosaur_dfi_surface_residual_weak_hs_seasonal`
- Incumbent model name: `dinosaur_dfi_surface_residual_weak_hs`
- Baseline commit: `4756cc9a4b69c41eec60e2177fb03a73974f0e2d`
- Candidate commit: uncommitted during scoring

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

The candidate adds a default-off seasonal weak-Held-Suarez adapter option and a
side-by-side factory named `dinosaur_dfi_surface_residual_weak_hs_seasonal`.
The incumbent factory remains unchanged.

The seasonal forcing is thermal-only, tracer-safe, and wind-sparing. It uses
the accepted weak relaxation rates and `kf=0.0`, preserves the existing
Held-Suarez pressure and vertical terms, and replaces the meridional
`sin(latitude) ** 2` equilibrium factor with
`(sin(latitude) - sin(declination)) ** 2`. Solar declination is computed from
the existing Dinosaur radiation helpers using the WeatherBench reference
datetime. The adapter initializes `State.sim_time` from each
`ForecastInput.initial_times` only for the seasonal path.

Digital-filter initialization uses the accepted nonseasonal weak-Held-Suarez
equation. The seasonal forcing is applied only during the scored positive-time
forecast rollout, with the initialization datetime restored after DFI.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 44 passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_seasonal` | 0 | Fast diagnostics clean; `failed=false`, zero issues, 60 exact candidate records, primary score `-1.2291930627718617`. |
| `git diff --check` | 0 | Passed. |

## Repair Attempts

- Failure observed: none after the initial edit.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none.
- Follow-up command and result: ruff, focused pytest, fast evaluation, and diff check all exited 0.

## Known Limitations

- Full repository pytest, iteration scoring, and validation scoring are delegated
  to the Scorer.
- Candidate code is uncommitted until the Orchestrator makes the final decision.

## Rollback Notes

If rejected, remove the seasonal weak-Held-Suarez adapter option, seasonal
forcing class, sim-time threading, side-by-side factory, registry entry, and
associated tests while keeping this history directory and raw evaluation
artifacts.
