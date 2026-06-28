# Implementation Record

## Identity

- Proposal slug: helmholtz-wind-initialization
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind
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
`dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind`. The candidate
preserves the current incumbent configuration: digital-filter initialization,
near-surface residual correction, weak wind-sparing Held-Suarez relaxation,
log-pressure temperature and humidity pressure-to-sigma initialization, T80
resolution, 900 s inner step, default diffusion, vertical advection, 250 K
reference temperature, finite pressure-level output packing, and the unchanged
forecast API.

The only candidate behavior change is wind initialization. The incumbent
continues interpolating pressure-level vector winds to sigma before converting
to modal vorticity and divergence. The candidate instead computes pressure-
level modal vorticity and divergence from pressure-level winds, converts those
scalar diagnostics back to nodal pressure-level stacks, remaps those scalar
diagnostics to sigma levels with the same pressure-to-sigma interpolation used
by the incumbent initialization path, and initializes modal Dinosaur vorticity
and divergence from the remapped scalar diagnostics.

Focused tests cover registry exposure, candidate configuration preservation,
incumbent-path isolation, nondivergent wind behavior, divergent-wind remapping,
and a no-JIT finite forecast smoke test.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported exit 0. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer reported final exit 0 with 49 tests passing. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind` | passed | Implementer reported exit 0, diagnostic `failed=False`, zero issues, primary score `-1.5147626128130018`. |
| `git diff --check` | passed | Implementer reported exit 0. |

## Repair Attempts

- Failure observed: initial focused pytest run failed two new test expectations.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: repaired the test expectations around the new transform path.
- Follow-up command and result: targeted repaired tests and full requested
  focused tests passed.

## Known Limitations

- The fast primary score was much worse than the incumbent, but fast diagnostics
  were clean. Iteration scoring remains the protocol promotion gate.
- Full iteration and validation scoring were not run by the Implementer; these
  remain Scorer responsibilities.
- Candidate changes are uncommitted until the Orchestrator accepts the scored
  result.

## Rollback Notes

If rejected, revert only the implementation files listed above and remove the
ready proposal after preserving this history record. Leave the accepted
log-pressure initialization incumbent and its evaluation artifacts unchanged.
