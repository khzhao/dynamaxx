# Implementation Record

## Identity

- Proposal slug: standard-atmosphere-reference-profile
- Candidate model name: dinosaur_dfi_ref_profile
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

The candidate added a side-by-side `dinosaur_dfi_ref_profile` factory and registry entry. It preserved the incumbent `dinosaur_dfi` behavior while enabling DFI plus a fixed standard-atmosphere reference-temperature profile. The profile mapped sigma-layer centers to `sigma * 1000 hPa`, interpolated a small 1976 U.S. Standard Atmosphere pressure-temperature table in log pressure, and clipped the resulting reference temperatures to 200 K through 300 K.

The reference vector was threaded through the same adapter locations as the existing constant reference temperature: pressure-to-sigma initialization, primitive-equation construction, DFI setup, and output reconstruction. The forecast API, emitted variables, fixed metrics, splits, lead times, and WeatherBench2 evaluation commands were unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff format ...` | 0 | Implementer formatted the touched source and test files. |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py` | 0 | 30 passed. |
| `uv run pytest` | 0 | 96 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_ref_profile` | 0 | Diagnostics passed, issue count 0, primary score -1.2826846667797114. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_ref_profile --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.3205664654977811. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: no implementation or numerical failures were observed in tests or fast evaluation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none needed.
- Follow-up command and result: iteration scoring completed cleanly but did not meet the promotion threshold.

## Known Limitations

- The standard-atmosphere profile was fixed before scoring and was not tuned against iteration or validation outputs.
- The candidate changed only the numerical reference split and did not add missing physics, terrain, or surface-layer diagnostics.
- Validation was not run because the iteration primary-score gain was below the required promotion threshold.

## Rollback Notes

The rejected implementation was never committed. Restore the six changed source/test files to baseline commit `cfdc344723cee1f267b892ddd924fc5d07b89f2d` and preserve this history directory plus the raw `dinosaur_dfi_ref_profile` fast and iteration artifacts.
