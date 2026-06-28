# Implementation Record

## Identity

- Proposal slug: layer-mean-thermal-recentering
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init
- Baseline commit: bc39a2b7fbbe5fbab0aa568afcf90c32b7a4b41c
- Candidate commit: not committed; pending scoring decision

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side candidate factory and registry entry named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter`. The
candidate preserves the current incumbent configuration: digital-filter
initialization, near-surface residual correction, weak wind-sparing
Held-Suarez relaxation, log-pressure pressure-to-sigma initialization, T80
resolution, 900 s inner step, default diffusion, vertical advection, 250 K
reference temperature, finite pressure-level output packing, and the unchanged
forecast API.

The only candidate behavior change is a forward-rollout step filter. After the
normal positive-time IMEX step and existing horizontal diffusion filter, the new
filter copies `temperature_variation[..., 0, 0]` from the previous state into
the next state for every sigma layer. It leaves nonzero temperature modes,
vorticity, divergence, log surface pressure, tracers, and `sim_time` unchanged.
The filter is not added to the `filters` sequence passed into
`digital_filter_initialization`, so the DFI path remains the incumbent path.

Focused tests cover registry exposure, candidate configuration preservation,
exact modal recentering behavior, forward filter ordering, DFI isolation, and a
no-JIT finite forecast smoke test.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported exit 0. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported exit 0 with 50 tests passing. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter` | passed | Implementer reported exit 0, diagnostic `failed=False`, zero issues, primary score `-1.1901240466487215`. |
| `git diff --check` | passed | Implementer reported exit 0. |

## Repair Attempts

- Failure observed: first ruff run found import ordering and a mock closure issue.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: repaired imports and mock closure.
- Follow-up command and result: ruff passed.
- Failure observed: first focused pytest run found the mocked IMEX stepper did
  not accept `time_step=`.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: adjusted the test mock signature.
- Follow-up command and result: focused pytest passed.

## Known Limitations

- Full iteration and validation scoring were not run by the Implementer; these
  remain Scorer responsibilities.
- Candidate changes are uncommitted until the Orchestrator accepts the scored
  result.

## Rollback Notes

If rejected, revert only the implementation files listed above and remove the
ready proposal after preserving this history record. Leave the accepted
log-pressure initialization incumbent and its evaluation artifacts unchanged.
