# Implementation Record

## Identity

- Proposal slug: pressure-aware-sigma-layer-grid
- Candidate model name: dinosaur_dfi_pressure_grid
- Incumbent model name: dinosaur_dfi
- Baseline commit: cfdc344723cee1f267b892ddd924fc5d07b89f2d
- Candidate commit: not committed; rejected after iteration scoring

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/coordinates.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate added an optional pressure-aware sigma-coordinate grid. When enabled, the coordinate builder derived layer interfaces from the inferred pressure levels by sorting the levels, inserting 0 hPa and 1000 hPa outer interfaces, using adjacent pressure-level midpoints as internal interfaces, and normalizing by 1000 hPa. The side-by-side `dinosaur_dfi_pressure_grid` factory kept the accepted DFI initialization enabled while opting into those pressure-aware vertical coordinates.

The canonical `dinosaur` and accepted `dinosaur_dfi` factories continued to use the existing equidistant sigma grid. The forecast API, horizontal grid, spectral truncation, DFI settings, timestepper, diffusion, pressure-level output extrapolation, output variables, fixed metrics, splits, and lead times were unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py` | 0 | 31 passed. |
| `uv run pytest` | 0 | 97 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_pressure_grid` | 0 | Diagnostics passed, issue count 0, primary score -1.4026822509855363. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_pressure_grid --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.4240296998737416. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: no implementation or numerical failures were observed in tests or fast evaluation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none needed.
- Follow-up command and result: iteration scoring completed cleanly but strongly failed the promotion threshold.

## Known Limitations

- The pressure-aware grid was fixed before scoring and was not tuned against iteration or validation outputs.
- The candidate changed vertical layer placement only; it did not add terrain, surface-pressure correction, forcing, or diagnostic residuals.
- Validation was not run because the iteration primary score was much worse than the incumbent.

## Rollback Notes

The rejected implementation was never committed. Restore the seven changed source/test files to baseline commit `cfdc344723cee1f267b892ddd924fc5d07b89f2d` and preserve this history directory plus the raw `dinosaur_dfi_pressure_grid` fast and iteration artifacts.
