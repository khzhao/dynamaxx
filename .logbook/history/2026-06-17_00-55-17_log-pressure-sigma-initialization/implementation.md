# Implementation Record

## Identity

- Proposal slug: log-pressure-sigma-initialization
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs
- Baseline commit: 4756cc9a4b69c41eec60e2177fb03a73974f0e2d
- Candidate commit: not committed; pending scoring decision

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side candidate factory and registry entry named
`dinosaur_dfi_surface_residual_weak_hs_logp_init`. The candidate preserves the
accepted incumbent configuration: digital-filter initialization, near-surface
residual diagnostics, weak wind-sparing Held-Suarez relaxation, T80 resolution,
900 s inner step, default diffusion, vertical advection, 250 K reference
temperature, and output packing.

The only model behavior changed for the candidate is pressure-level to sigma
initialization. `weather_state_to_dinosaur_state` now selects the existing
linear-pressure remap by default and selects a new log-pressure remap only when
`use_log_pressure_initialization=True`. The new helper interpolates 3D
pressure-level fields against `log(pressure_hpa)` and target
`log(max(sigma_center * surface_pressure_hpa, eps))` while keeping the existing
bounded extrapolation behavior. Surface pressure, vorticity/divergence
conversion, DFI, forcing, forecast rollout, sigma-to-pressure output
interpolation, and finite output extrapolation remain unchanged.

Focused tests cover registry exposure, incumbent default behavior, candidate
configuration preservation, log-pressure interpolation behavior, initialization
path selection, and a no-JIT finite forecast smoke test for the candidate.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported exit 0. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported exit 0 with 43 tests passing. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init` | passed | Implementer reported exit 0, diagnostic `failed=False`, zero issues, primary score `-1.1846413205137396`. |
| `git diff --check` | passed | Implementer reported exit 0. |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: not applicable

## Known Limitations

- Iteration and validation scoring were not run by the Implementer; these remain
  Scorer responsibilities.
- Candidate changes are uncommitted until the Orchestrator accepts the scored
  result.

## Rollback Notes

If rejected, revert only the implementation files listed above and remove the
ready proposal after preserving this history record. Leave incumbent artifacts
and accepted commits unchanged.
