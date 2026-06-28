# Implementation Record

## Identity

- Proposal slug: log-pressure-output-interpolation
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init
- Baseline commit: bc39a2b7fbbe5fbab0aa568afcf90c32b7a4b41c
- Candidate commit: not committed; pending scoring decision

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side candidate factory and registry entry named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output`. The candidate
preserves the current incumbent trajectory configuration: digital-filter
initialization, near-surface residual correction, weak wind-sparing
Held-Suarez relaxation, log-pressure pressure-to-sigma initialization, T80
resolution, 900 s inner step, default diffusion, vertical advection, 250 K
reference temperature, and the unchanged forecast API.

The only candidate behavior change is sigma-to-pressure output packing for
pressure-level fields. The new output helper interpolates each column in
`log(pressure)` using source coordinates
`log(max(sigma_center * surface_pressure_hpa, eps))` and target coordinates
`log(pressure_level_hpa)`. It keeps the accepted nearest-level bounded
extrapolation policy for finite pressure outputs. The incumbent
`dinosaur_dfi_surface_residual_weak_hs_logp_init` continues to use the existing
linear sigma-to-pressure output interpolation.

Focused tests cover registry exposure, candidate configuration preservation,
explicit output-coordinate selection, log-pressure interpolation on a
log-linear profile, and a no-JIT finite smoke forecast for the candidate.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported exit 0. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported exit 0 with 49 tests passing. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output` | passed | Implementer reported exit 0, diagnostic `failed=False`, zero issues, 120 records, primary score `-1.1830482379849583`. |
| `git diff --check` | passed | Implementer reported exit 0. |

## Repair Attempts

- Failure observed: first focused pytest run exposed a vectorization shape error
  in the column-varying interpolation helper.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: changed the helper to vmap over target pressure levels before
  vmapping over horizontal columns.
- Follow-up command and result: affected tests, full requested focused tests,
  ruff, fast eval, and `git diff --check` passed.

## Known Limitations

- Full iteration and validation scoring were not run by the Implementer; these
  remain Scorer responsibilities.
- Candidate changes are uncommitted until the Orchestrator accepts the scored
  result.

## Rollback Notes

If rejected, revert only the implementation files listed above and remove the
ready proposal after preserving this history record. Leave the accepted
log-pressure initialization incumbent and its evaluation artifacts unchanged.
