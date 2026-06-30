# Implementation Record

## Identity

- Proposal slug: static-roughness-weighted-ekman-coupling
- Candidate model name: dino_ri2m_ekman_z0
- Incumbent model name: dino_ri2m_ekman_coupled
- Baseline commit: d35078e83314b8ef70f0d8a23f9765e03ed3750e
- Candidate commit: uncommitted-candidate-worktree

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side Dinosaur candidate, `dino_ri2m_ekman_z0`, that derives from `dino_ri2m_ekman_coupled` and adds one default-false selector: `use_static_roughness_weighted_ekman_coupling`.

The candidate loads the existing WeatherBench2 `land_sea_mask`, converts it into Dinosaur latitude order, builds one fixed land/coast/ocean drag multiplier, normalizes it to area-weighted mean one, validates finite values, bounds, shape, and mean, then applies it inside the accepted coupled Ekman stress path. Because the same stress then drives the incumbent momentum and pumping calculations, both wind increments and log-pressure pumping use the spatially redistributed drag while preserving incumbent caps, projections, pressure/wind ratio cap, equatorial taper, and finite fallbacks. Missing, invalid, all-one, or out-of-range multipliers fall back to the accepted incumbent behavior.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Main-session syntax check passed. |
| `uv run ruff format ...` | 0 | Implementer ran formatting on touched Python files. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Main-session Ruff check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k 'roughness_weighted_ekman or static_roughness or ekman_coupled_filter or canonical_model_factories or registry_lists_default_models'` | 0 | Main-session focused tests: 14 passed, 203 deselected. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_z0` | 0 | Implementer-run sanity gate passed; artifact `outputs/eval/fast_dino_ri2m_ekman_z0.json` has primary score -0.16771804919483163 and zero recorded issues. |
| `git diff --check` | 0 | Main-session whitespace check passed. |

## Repair Attempts

- Failure observed: none during Implementer or main-session verification.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none needed.
- Follow-up command and result: not applicable.

## Known Limitations

- Full pytest, iteration, and validation are left to the Scorer.
- This first bounded implementation uses only `land_sea_mask` land/coast/ocean classes; it does not use soil type or surface-geopotential proxies because those constants are not guaranteed in the local processed constants store.
- The fast primary score is worse than the incumbent lineage fast context, so this candidate may fail the iteration promotion gate.

## Rollback Notes

Revert only this experiment's implementation by applying `.logbook/history/2026-06-29_21-03-42_static-roughness-weighted-ekman-coupling/candidate.diff` in reverse. Preserve the history directory, raw evaluation outputs, staged research files, and unrelated untracked `gifs/`.
