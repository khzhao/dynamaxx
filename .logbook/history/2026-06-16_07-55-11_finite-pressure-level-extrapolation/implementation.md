# Implementation Record

## Identity

- Proposal slug: finite-pressure-level-extrapolation
- Candidate model name: dinosaur
- Incumbent model name: dinosaur
- Baseline commit: 3f517232303e37bc947361cb29c214b13b249438
- Candidate commit: 4beb6c221f8655f80b6530713ffc75697e9c654e

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py

## Implementation Summary

The repair adds a bounded nearest-level extrapolation helper for vertical interpolation and uses it only when packing Dinosaur sigma-coordinate trajectories back to pressure-level WeatherState outputs. Input pressure-to-sigma initialization keeps the existing bounded-safe interpolation behavior.

The canonical `dinosaur` model name, registry, forecast API, emitted channel set, fixed diagnostics, metrics, target variables, splits, and lead times are unchanged. The change makes out-of-column pressure-level diagnostics finite instead of returning NaN for below-surface or above-column requested pressure levels.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py` | 0 | 13 passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py tests/eval/test_runner.py` | 0 | 14 passed. |
| `uv run pytest` | 0 | 85 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur` | 0 | Diagnostics passed, issue count 0, primary score -1.2882176100657747. |
| `uv run dynamaxx-eval iteration --model dinosaur --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.3251884351511753. |
| `uv run dynamaxx-eval validation --model dinosaur --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.3128324262513928. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: pre-repair canonical `dinosaur` fast diagnostics reported `nonfinite_forecast` with value 4567590.
- Implementer-owned failure: yes, as an adapter output packing issue.
- NaN/Inf forecast observed: yes before repair; no after repair under fast, iteration, and validation scoring.
- Fix attempted: pressure-level output interpolation now uses bounded nearest-level extrapolation outside the local sigma column.
- Follow-up command and result: fast, iteration, and validation all passed diagnostics with zero issues.

## Known Limitations

- Below-surface pressure-level outputs are finite diagnostic extrapolations using nearest sigma-layer values, not reconstructed physical atmospheric layers below terrain.
- This is infrastructure repair. It establishes comparable finite baselines; it is not evidence that a new dycore model improved skill.

## Rollback Notes

Revert commit `4beb6c221f8655f80b6530713ffc75697e9c654e` to remove this accepted repair if a future investigation finds the bounded nearest-level extrapolation unacceptable. Preserve the history and raw evaluation artifacts when rolling back.
