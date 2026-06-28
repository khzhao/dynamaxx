# Implementation Record

## Identity

- Proposal slug: `dry-dfi-weak-hs-split`
- Candidate model name: `dinosaur_dfi_surface_residual_weak_hs_dry_dfi`
- Incumbent model name: `dinosaur_dfi_surface_residual_weak_hs`
- Baseline commit: `4756cc9a4b69c41eec60e2177fb03a73974f0e2d`
- Candidate commit: uncommitted during scoring

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

The candidate adds a default-off `use_dry_dfi_equation` adapter option and a
side-by-side factory named `dinosaur_dfi_surface_residual_weak_hs_dry_dfi`.
When this option is enabled, the forecast rollout still uses the incumbent
weak Held-Suarez composed equation, while digital-filter initialization receives
a freshly built primitive-equation object without weak Held-Suarez forcing.
The dry DFI equation keeps the same coordinate system, reference temperature,
humidity choice, vertical-advection flag, horizontal diffusion filters, DFI
span, and cutoff as the forecast model.

The incumbent `dinosaur_dfi_surface_residual_weak_hs` factory remains on the
existing single-equation path.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Passed after import-order repair. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 42 passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_dry_dfi` | 0 | Fast diagnostics clean; `failed=false`, zero issues, primary score approximately `-1.19097`. |

## Repair Attempts

- Failure observed: ruff import ordering.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: reordered imports according to ruff.
- Follow-up command and result: ruff rerun exited 0; focused pytest exited 0; fast evaluation exited 0.

## Known Limitations

- Full repository pytest, iteration scoring, and validation scoring are delegated
  to the Scorer.
- Candidate code is uncommitted until the Orchestrator makes the final decision.

## Rollback Notes

If rejected, remove the dry-DFI factory and registry entry, remove the
`use_dry_dfi_equation` adapter option and split DFI branch, and revert the
associated tests while keeping this history directory and raw evaluation
artifacts.
