# Implementation Record

## Identity

- Proposal slug: `polar-vector-wind-initialization-taper`
- Candidate model name:
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_polar_wind_taper`
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
- `tests/dycore/test_registry.py`

## Implementation Summary

The implementation adds a side-by-side candidate model that preserves the
incumbent DFI, weak Held-Suarez relaxation, near-surface residual correction,
log-pressure initialization, hydrostatic temperature initialization, and
layer-mean hydrostatic temperature initialization. The only new behavior is the
`apply_polar_wind_initialization_taper` adapter flag.

When enabled, the adapter zeroes exact-pole latitude rows in the pressure-level
`u_component_of_wind` and `v_component_of_wind` stacks after conversion into
Dinosaur latitude order and before pressure-to-sigma remapping. The helper uses
the local Dinosaur grid latitudes to identify exact pole rows, leaves all
interior rows unchanged, returns unchanged arrays for grids without exact
poles, and does not touch temperature, humidity, geopotential, surface pressure,
output interpolation, or evaluation protocols.

The candidate is registered as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_polar_wind_taper`.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | `64 passed in 56.96s` |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_polar_wind_taper` | 0 | `failed=False`, `issues=0`, `records=120`, primary score approximately `-1.12329` |

## Repair Attempts

- Failure observed: none during Implementer-owned focused tests or fast sanity.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none required.
- Follow-up command and result: not applicable.

## Known Limitations

- The candidate is exact-pole-only and may be too small to move global fixed
  WeatherBench2 metrics.
- The implementation intentionally does not reconstruct a smooth polar vector
  basis, smooth a broader polar cap, tune latitude widths, or change any
  non-wind initialization field.

## Rollback Notes

If rejected, revert only the six files listed above. The logbook history and raw
evaluation artifacts should remain as the immutable experiment record.
