# Implementation Record

## Identity

- Proposal slug: ekman-pressure-work-thermal-coupling
- Candidate model name: dino_ri2m_ekman_pwork
- Incumbent model name: dino_ri2m_ekman_coupled
- Baseline commit: 7fc50528eae6327ad790c1346a95266e0dc753c2
- Candidate commit: uncommitted-candidate-worktree

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side Dinosaur candidate, `dino_ri2m_ekman_pwork`, that preserves the accepted coupled Ekman closure and adds an optional dry pressure-work thermal response. The response uses the accepted Ekman log-surface-pressure increment as a lower-layer temperature tendency proportional to `kappa * T * d(log p)`, tapers it vertically through the existing Ekman lower-layer taper, removes each layer's area mean, projects through the modal/nodal grid, and caps each step at 0.02 K.

The incumbent `dino_ri2m_ekman_coupled` remains unchanged because the new selector defaults to false and the candidate is registered under a new model key. Tests cover factory parity with the incumbent, zero-pressure exact no-op behavior, area-neutral lower-layer thermal response, cap enforcement, nonfinite fallback, dependency exports, and registry discovery.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Main-session syntax check passed. |
| `git diff --check` | 0 | Whitespace check passed. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Ruff check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k 'ekman_pressure_work or ekman_coupled_filter or canonical_model_factories or registry_lists_default_models'` | 0 | 11 passed, 203 deselected. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_pwork` | 0 | Implementer-run sanity gate passed; artifact `outputs/eval/fast_dino_ri2m_ekman_pwork.json` has primary score -0.1668477749881733 and zero recorded issues. |

## Repair Attempts

- Failure observed: none during main-session verification.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none needed after Implementer handoff.
- Follow-up command and result: not applicable.

## Known Limitations

- The response is intentionally conservative and bounded; it may be too weak to improve the fixed WeatherBench2 iteration gate.
- Validation must not be run unless the candidate first clears the iteration promotion gate.
- The incumbent comparison should reuse valid cached leaderboard artifacts rather than rerunning `dino_ri2m_ekman_coupled`.

## Rollback Notes

Revert only this experiment's implementation by applying `.logbook/history/2026-06-29_13-02-18_ekman-pressure-work-thermal-coupling/candidate.diff` in reverse. Preserve the history directory and unrelated untracked `gifs/`.
