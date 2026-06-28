# Implementation Record

## Identity

- Proposal slug: mass-diagnostic-analysis-residuals
- Candidate model name: dinosaur_dfi_surface_mass_residual
- Incumbent model name: dinosaur_dfi_surface_residual
- Baseline commit: 845de671268f42c6b44b0a60c287e043087364a1
- Candidate commit: not committed; rejected after iteration scoring

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate added a side-by-side `dinosaur_dfi_surface_mass_residual` model that preserved the incumbent digital filter initialization and accepted near-surface residual correction. It extended the output-only residual path with a guarded mass-diagnostic option for `mean_sea_level_pressure` and pressure-level `geopotential_*` channels present in both the initial analysis and forecast output variables.

For eligible mass diagnostics, the implementation computed the lead-0 analysis residual between the input channel and raw Dinosaur diagnostic output, then applied that residual at requested leads with the fixed 48 hour exponential decay. The raw prognostic state, zero-orography assumption, sigma coordinates, pressure interpolation, target variables, lead schedule, metrics, and `WeatherState` contract were left unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore` | 0 | Syntax check passed. |
| `uv run ruff format ...` | 0 | Formatting applied to touched Python files. |
| `uv run ruff check ...` | 0 | Initially failed with C420 dict-comprehension style; repaired and passed. |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py` | 0 | 36 passed. |
| `uv run pytest` | 0 | 102 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_mass_residual` | 0 | Diagnostics passed, issue count 0, primary score -1.2470991177529807. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_mass_residual --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.284988567046514. |
| `git diff --check` | 0 | No whitespace errors before scoring. |

## Repair Attempts

- Failure observed: ruff C420 dict-comprehension style issue in the implementation.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no in fast or iteration artifacts.
- Fix attempted: rewrote the flagged dict construction using `dict.fromkeys` while preserving the selected residual mechanism.
- Follow-up command and result: ruff check, focused tests, full tests, fast evaluation, iteration evaluation, and `git diff --check` passed.

## Known Limitations

- The candidate made only a tiny fixed-protocol primary-score movement, below the iteration promotion threshold.
- Validation was not run because the iteration primary delta did not promote.
- The 48 hour mass diagnostic residual decay was fixed before scoring and was not tuned.

## Rollback Notes

The candidate was rejected before commit. Revert the six changed source/test files listed above to restore commit `845de671268f42c6b44b0a60c287e043087364a1`; preserve this history directory and raw evaluation artifacts.
