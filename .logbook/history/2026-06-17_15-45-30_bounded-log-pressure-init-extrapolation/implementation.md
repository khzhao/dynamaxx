# Implementation Record

## Identity

- Proposal slug: `bounded-log-pressure-init-extrapolation`
- Candidate model name:
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap`
- Incumbent model name:
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- Baseline commit: `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`
- Candidate commit: not committed at scoring handoff

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_vertical_interpolation.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

The implementation adds a side-by-side candidate model that preserves the
current incumbent configuration and enables only
`use_bounded_log_pressure_initialization_extrapolation`.

When this flag is enabled together with log-pressure initialization, the
adapter passes a vectorized
`vertical_interpolation.linear_interp_with_nearest_extrap` function into
`interp_pressure_to_sigma_log_pressure`. This keeps interior pressure-to-sigma
initialization linear in log pressure while bounding targets outside the
analyzed pressure-level range to the nearest analyzed edge value. The default
incumbent path still calls `interp_pressure_to_sigma_log_pressure` with its
existing interpolation default.

The implementation does not change output interpolation, near-surface residual
correction, DFI, weak Held-Suarez relaxation, hydrostatic temperature
initialization, humidity handling, spectral truncation, step size, or the
forecast API.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_vertical_interpolation.py tests/dycore/test_registry.py` | 0 | `62 passed in 55.91s` |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_vertical_interpolation.py tests/dycore/test_registry.py` | 0 | Touched-file lint passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap` | 0 | `failed=False`, `issues=0`, primary score approximately `-1.12081` |

## Repair Attempts

- Failure observed: none during final focused tests, lint, or fast sanity.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: implementation owner reported cleanup of unrelated formatter
  wrapping churn after `ruff format`.
- Follow-up command and result: final focused tests, lint, and fast sanity
  passed.

## Known Limitations

- The candidate only affects extrapolated pressure-to-sigma initialization
  targets, so the expected fixed-metric signal may be small.
- The implementation intentionally does not alter interior log-pressure
  interpolation, output packing, diagnostics, or any rollout dynamics.

## Rollback Notes

If rejected, revert only the seven files listed above. Preserve this history
directory and raw evaluation artifacts as the immutable experiment record.
