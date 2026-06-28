# Implementation Record

## Identity

- Proposal slug: scale-selective-hyperdiffusion
- Candidate model name: dinosaur_hyperdiffusion
- Incumbent model name: dinosaur
- Baseline commit: 4beb6c221f8655f80b6530713ffc75697e9c654e
- Candidate commit: uncommitted implementation diff on baseline commit

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/test_registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py

## Implementation Summary

The implementation registered a side-by-side `dinosaur_hyperdiffusion` candidate so the accepted `dinosaur` incumbent and leaderboard artifacts could remain comparable. The candidate factory returned `DinosaurPrimitiveEquationsDycoreModel(name="dinosaur_hyperdiffusion", horizontal_diffusion_order=4)`.

The incumbent `dinosaur` factory stayed unchanged with `horizontal_diffusion_order == 2`. No forecast API, fixed evaluation protocol, metric, split, target variable, lead time, or output-contract changes were made.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py` | 0 | 23 passed. |
| `uv run pytest` | 0 | 89 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_hyperdiffusion` | 0 | Diagnostics passed, issue count 0, primary score -1.3371938385977156. |
| `uv run dynamaxx-eval iteration --model dinosaur_hyperdiffusion --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.376430535805006. |
| `uv run dynamaxx-eval validation --model dinosaur_hyperdiffusion --workers 4` | not_run | Not run because iteration promotion failed. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: no implementation or diagnostic failure; scientific candidate failed the iteration promotion gate.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none; no bounded implementation repair was indicated.
- Follow-up command and result: Scorer compared candidate iteration to incumbent baseline and found primary-score and early-wind RMSE gate failures.

## Known Limitations

- Fourth-order horizontal diffusion worsened the fixed iteration primary score relative to the accepted finite `dinosaur` baseline.
- The candidate also regressed early 10m zonal wind RMSE by more than the 2% gate over lead days 1-5.

## Rollback Notes

Revert only the six files listed above to remove the `dinosaur_hyperdiffusion` factory, package export, registry entry, and focused tests. Preserve `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/` and ignored raw evaluation artifacts under `outputs/eval/`.
