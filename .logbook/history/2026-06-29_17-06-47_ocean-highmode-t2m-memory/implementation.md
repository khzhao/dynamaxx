# Implementation Record

## Identity

- Proposal slug: ocean-highmode-t2m-memory
- Candidate model name: dino_ri2m_ekman_ocean_t2m_himem
- Incumbent model name: dino_ri2m_ekman_coupled
- Baseline commit: 206bc415a6de19ab3e52d62aa2309e0277ee5bd7
- Candidate commit: uncommitted-candidate-worktree

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side Dinosaur candidate, `dino_ri2m_ekman_ocean_t2m_himem`, that derives from `dino_ri2m_ekman_coupled` and adds one default-false final-output selector: `use_ocean_high_mode_t2m_memory`.

The new T2m-only correction subtracts the accepted broad land/ocean low-mode residual from the initialized T2m residual, smooths the remainder by open-ocean land-sea weight, filters it through a tapered high-mode spectral band, then adds a late-ramped finite-memory extra correction above the incumbent high-mode decay. Fixed constants are ramp 72h to 144h, decay 240h, and cap 0.75 K. Lead zero is preserved exactly, non-T2m variables follow the incumbent path, and invalid masks, zero ocean weight, invalid high-mode filtering, or nonfinite corrections fall back to incumbent behavior.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Main-session syntax check passed. |
| `uv run ruff format ...` | 0 | Implementer ran formatting on touched Python files. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Main-session Ruff check passed after Implementer fixed one import ordering issue. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k 'ocean_high_mode_t2m_memory or ekman_coupled_factory or canonical_model_factories or registry_lists_default_models'` | 0 | Main-session focused tests: 9 passed, 206 deselected. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_ocean_t2m_himem` | 0 | Implementer-run sanity gate passed; artifact `outputs/eval/fast_dino_ri2m_ekman_ocean_t2m_himem.json` has primary score -0.16799229809051633 and zero recorded issues. |
| `git diff --check` | 0 | Main-session whitespace check passed. |

## Repair Attempts

- Failure observed: Ruff import ordering issue during Implementer checks.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: import order was corrected.
- Follow-up command and result: Ruff check passed; focused tests and fast sanity gate passed.

## Known Limitations

- Full pytest, iteration, and validation are left to the Scorer.
- The fast primary score is worse than the previous fast score for the incumbent lineage, so this candidate may fail the iteration promotion gate.
- The correction is output-only for `2m_temperature`; it is not expected to affect pressure, geopotential, wind, or trajectory variables except through metric aggregation.

## Rollback Notes

Revert only this experiment's implementation by applying `.logbook/history/2026-06-29_17-06-47_ocean-highmode-t2m-memory/candidate.diff` in reverse. Preserve the history directory, raw evaluation outputs, staged research files, and unrelated untracked `gifs/`.
