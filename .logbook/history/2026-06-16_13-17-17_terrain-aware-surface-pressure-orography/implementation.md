# Implementation Record

## Identity

- Proposal slug: terrain-aware-surface-pressure-orography
- Candidate model name: dinosaur_dfi_terrain
- Incumbent model name: dinosaur_dfi
- Baseline commit: cfdc344723cee1f267b892ddd924fc5d07b89f2d
- Candidate commit: not committed; rejected after iteration scoring

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate added a side-by-side `dinosaur_dfi_terrain` model that kept the accepted DFI path while enabling terrain-aware lower-boundary handling. The implementation loaded `geopotential_at_surface` from the local WeatherBench2 constants store, verified grid alignment, converted surface geopotential to terrain height meters, nondimensionalized terrain height for Dinosaur orography, and passed filtered modal terrain into the primitive equations.

The candidate also used terrain plus pressure-level geopotential to diagnose surface pressure when `surface_pressure` was absent, passed terrain into sigma-level geopotential diagnostics, and emitted a bounded hydrostatic mean-sea-level-pressure reduction separately from raw surface pressure. Canonical `dinosaur` and accepted `dinosaur_dfi` retained the flat zero-terrain behavior.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 31 passed. |
| `uv run pytest` | 0 | 97 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_terrain` | 0 | Diagnostics passed, issue count 0, primary score -1.0905432571118128. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_terrain --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.122351043157642. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_terrain --workers 4` | 0 | Ran as Scorer anomaly after a parsing mistake; diagnostics passed, issue count 0, primary score -1.126083021438326. |
| `uv run ruff check ...` | 0 | Implementer-provided record. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: one focused test expectation used the standard-gravity conversion where Dinosaur's nondimensional model gravity was the correct comparison for model geopotential.
- Implementer-owned failure: yes, test expectation only.
- NaN/Inf forecast observed: no.
- Fix attempted: adjusted the test to compare terrain geopotential against the model-unit gravity scaling while retaining standard gravity only for WeatherBench surface-geopotential-to-height conversion.
- Follow-up command and result: focused tests, full tests, fast, iteration, and the anomalous validation run all completed with clean diagnostics.

## Known Limitations

- The terrain MSLP reduction was intentionally simple and bounded, not a full operational sea-level-pressure diagnostic.
- The candidate improved primary score but caused large early mass-field RMSE guardrail failures for `geopotential_500` and `mean_sea_level_pressure`.
- Validation metrics exist but were not protocol-allowed after the corrected iteration RMSE guardrail failure.

## Rollback Notes

The rejected implementation was never committed. Restore the six changed source/test files to baseline commit `cfdc344723cee1f267b892ddd924fc5d07b89f2d` and preserve this history directory plus the raw `dinosaur_dfi_terrain` fast, iteration, and anomalous validation artifacts.
