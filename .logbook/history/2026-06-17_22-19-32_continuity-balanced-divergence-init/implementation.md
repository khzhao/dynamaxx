# Implementation Record

## Identity

- Proposal slug: continuity-balanced-divergence-init
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
- Baseline commit: a7833574e9ade1a5271bd8cbef2fa1357465f5a8
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-17_22-19-32_continuity-balanced-divergence-init/implementation.md

## Implementation Summary

Implemented a side-by-side Dinosaur candidate that preserves the incumbent DFI,
near-surface residual correction, weak Held-Suarez relaxation, log-pressure
initialization, hydrostatic layer-mean temperature initialization, vertical
advection, T80 truncation, 900 s inner step, spectral filter, and
`use_humidity_in_dynamics=False`.

The new opt-in adapter flag applies once in `weather_state_to_dinosaur_state`,
before DFI receives the state. It computes the nodal sigma-column continuity
residual from the existing diagnostic relation `divergence + u dot grad(log ps)`,
forms a vertically uniform divergence-only correction, transforms it to modal
space, clips the modal tail with the existing horizontal clip helper, and caps
the modal correction norm to 50% of the incumbent divergence norm. Vorticity,
temperature variation, log surface pressure, tracers, and simulation time are
copied unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 1 | First run exposed a nodal/modal broadcast shape bug in the new correction helper. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 1 | Second run passed implementation behavior but failed the cap test by float32 roundoff tolerance. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | 64 passed in 57.02 s. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | All checks passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced` | 0 | failed=False, issues=0, records=120, primary_score=-1.12417, metrics=outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced.json. |

## Repair Attempts

- Failure observed: residual was nodal shape `[1, longitude, latitude]` but was broadcast to modal divergence shape.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: broadcast the residual over `coords.nodal_shape` before transforming the correction to modal space; also made cap dtype explicitly real-valued.
- Follow-up command and result: focused pytest rerun reduced failures to only a float32 tolerance assertion.

- Failure observed: cap test exceeded the analytical cap by approximately 1.1e-5 absolute on a norm near 31 due to float32 arithmetic.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: changed the assertion to use a small relative tolerance.
- Follow-up command and result: focused pytest passed with 64 tests passing.

## Known Limitations

- Limitation: the correction is intentionally approximate and vertically uniform; it does not perform a full Helmholtz wind re-projection or normal-mode balance.
- Limitation: the global norm cap can leave a large residual partially corrected when the diagnosed residual is much larger than the incumbent divergence scale.

## Rollback Notes

Revert the adapter flag/helper/factory, the `dinosaur` package export, the
registry factory entry, and the focused tests listed above. No leaderboard,
golden output, fixed evaluation protocol, or committed history was changed.
