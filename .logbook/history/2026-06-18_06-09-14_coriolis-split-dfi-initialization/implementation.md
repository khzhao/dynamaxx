# Implementation Record

## Identity

- Proposal slug: coriolis-split-dfi-initialization
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
- Baseline commit: 30a496b1f2ed8f894511404341c7774288bdb4c8
- Candidate commit: not committed; working tree based on 30a496b1f2ed8f894511404341c7774288bdb4c8

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_06-09-14_coriolis-split-dfi-initialization/implementation.md

## Implementation Summary

Registered the side-by-side candidate
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis`.
The candidate preserves the Strang incumbent rollout options and adds one
default-off adapter flag,
`apply_digital_filter_exact_coriolis_rotation_split`.

For that flag only, DFI now uses the zero-angular-velocity primitive-equation
operator and the existing diffusion filter, then applies an exact Coriolis
rotation filter whose sign is derived from the DFI step time direction. The
candidate sets `sim_time=0` only inside DFI so the shared DFI helper can
distinguish forward and time-reversed legs through the existing filter API, and
clears `sim_time` before the forecast rollout. Older registered models keep the
existing normal-angular-velocity DFI path.

Focused tests cover factory option preservation, registry/import coverage,
legacy Strang unsplit DFI behavior, candidate zero-angular-velocity DFI setup,
opposite signed exact rotations for forward and backward DFI legs, and a finite
small non-JIT forecast.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python - <<'PY' ... PY` | 0 | Focused import/registration check for incumbent and candidate names; verified only the candidate has `apply_digital_filter_exact_coriolis_rotation_split=True`. |
| `JAX_PLATFORMS=cpu uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 79 passed in 41.73s. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 6 files left unchanged. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 1 | Initial lint run failed only on import ordering in `__init__.py` and `test_primitive_equations.py`. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Passed after import-order repair. |
| `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 6 files already formatted. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.09526`; metrics JSON written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis.json`. |

## Repair Attempts

- Failure observed: `uv run ruff check ...` reported unsorted imports in `src/dynamaxx/dycore/models/dinosaur/__init__.py` and `tests/dycore/models/dinosaur/test_primitive_equations.py`.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: reordered the newly added imports to match Ruff's import ordering.
- Follow-up command and result: reran `uv run ruff check ...`; exit status 0.

## Known Limitations

- Limitation: No iteration, validation, or golden protocols were run, per Implementer scope.
- Limitation: The fast sanity score is only a smoke diagnostic and is not an acceptance decision.
- Limitation: The signed DFI rotation uses the existing DFI filter API by temporarily enabling `sim_time` during DFI and clearing it before rollout.

## Rollback Notes

To revert only this experiment, remove the candidate flag, signed DFI filter
helper, DFI setup branch, candidate factory/export, registry entry/factory, and
the focused tests added for
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis`.
Do not remove unrelated logbook history or eval outputs unless explicitly
requested.
