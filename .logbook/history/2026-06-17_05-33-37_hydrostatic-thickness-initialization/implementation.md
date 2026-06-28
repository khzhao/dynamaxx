# Implementation Record

## Identity

- Proposal slug: hydrostatic-thickness-initialization
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init
- Baseline commit: bc39a2b7fbbe5fbab0aa568afcf90c32b7a4b41c
- Candidate commit: 4f4b397d90551cd87e35604fb8431f2c08c79606

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side candidate factory and registry entry named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init`. The
candidate preserves the current incumbent configuration: digital-filter
initialization, near-surface residual correction, weak wind-sparing
Held-Suarez relaxation, log-pressure pressure-to-sigma initialization, T80
resolution, 900 s inner step, default diffusion, vertical advection, 250 K
reference temperature, finite pressure-level output packing, and the unchanged
forecast API.

The only candidate behavior change is pressure-level temperature
initialization. When a complete pressure-level geopotential stack is present,
the candidate estimates dry temperature from geopotential thickness using
finite differences in `log(p)`: one-sided differences at the top and bottom
levels and centered differences at interior levels. When a complete humidity
stack is present, the helper converts the hydrostatic virtual-temperature
estimate to dry temperature with same-time specific humidity. It falls back to
the analyzed temperature when geopotential is incomplete, or pointwise when the
reconstructed value is non-finite or non-positive.

Focused tests cover registry exposure, candidate configuration preservation,
isothermal hydrostatic reconstruction, virtual-to-dry temperature conversion,
fallback behavior, and a no-JIT finite forecast smoke test.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported exit 0. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported exit 0 with 50 tests passing. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init` | passed | Implementer reported exit 0, diagnostic `failed=False`, zero issues, 120 records, primary score `-1.1192003138561368`. |
| `git diff --check` | passed | Implementer reported exit 0. |

## Repair Attempts

- Failure observed: one Ruff import-order issue.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: fixed import ordering.
- Follow-up command and result: lint, focused tests, fast eval, and
  `git diff --check` passed.

## Known Limitations

- Full iteration and validation scoring were not run by the Implementer; these
  remain Scorer responsibilities.
- The helper falls back to analyzed temperature for incomplete/missing
  geopotential stacks, and pointwise for non-finite or non-positive
  reconstructed temperatures, to preserve finite initialization.
- Candidate changes are uncommitted until the Orchestrator accepts the scored
  result.

## Rollback Notes

If rejected, revert only the implementation files listed above and remove the
ready proposal after preserving this history record. Leave the accepted
log-pressure initialization incumbent and its evaluation artifacts unchanged.
