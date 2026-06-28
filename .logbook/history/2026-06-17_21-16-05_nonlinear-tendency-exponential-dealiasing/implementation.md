# Implementation Record

## Identity

- Proposal slug: nonlinear-tendency-exponential-dealiasing
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
- Baseline commit: a7833574e9ade1a5271bd8cbef2fa1357465f5a8
- Candidate commit: not created; implementation remains as uncommitted worktree changes on baseline HEAD

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/filtering.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing/implementation.md

## Implementation Summary

Added a default-off nonlinear explicit-tendency dealiasing option to `PrimitiveEquationsSigma.explicit_terms`. The sigma primitive equation still computes the incumbent explicit tendency and clips final total wavenumbers as before; when enabled, the returned tendency `State` is passed through `filtering.exponential_filter` with cutoff `2/3`, order `18`, and attenuation `16`.

Threaded the option through the Dinosaur adapter and registered the side-by-side candidate `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias`. The candidate preserves the incumbent DFI, weak Held-Suarez, near-surface residual correction, log-pressure initialization, hydrostatic layer-mean temperature initialization, vertical advection, T80 truncation, 900 s inner step, and `use_humidity_in_dynamics=False`.

Tightened `filtering._preserves_shape` so leaves that cannot broadcast safely with the modal scaling are left unchanged instead of raising. Added tests for registration, factory flags, finite forecast smoke behavior, low-mode preservation, high-tail damping, and incompatible-leaf passthrough.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | 62 passed in 56.87s |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/filtering.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | All checks passed |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.11826`, metrics at `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias.json` |

## Repair Attempts

- Failure observed: none from focused tests, lint, or fast sanity check.
- Implementer-owned failure: no command failure observed.
- NaN/Inf forecast observed: no.
- Fix attempted: while implementing the required safe State filtering behavior, added a `ValueError` guard to `_preserves_shape` so incompatible leaves are skipped by the existing filter semantics.
- Follow-up command and result: focused tests, touched-file lint, and fast sanity check all passed.

## Known Limitations

- The filter is a global modal tail filter on explicit tendencies, not a physical subgrid closure.
- The fast sanity check confirms registration, finite diagnostics, and protocol compatibility only; iteration and validation scoring remain for the Scorer/Orchestrator.
- The implementation intentionally does not change hybrid-coordinate behavior.

## Rollback Notes

Revert only this experiment's edits in the files listed above. Removing the candidate factory/export/registry entry and the default-off primitive-equation dealiasing fields restores incumbent behavior; the incumbent factory remains default-off throughout this implementation.
