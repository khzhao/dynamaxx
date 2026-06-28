# Implementation Record

## Identity

- Proposal slug: exact-coriolis-rotation-split
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
- Baseline commit: a7833574e9ade1a5271bd8cbef2fa1357465f5a8
- Candidate commit: uncommitted working tree pending scoring

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate adds a side-by-side model factory and registry entry for
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split`.
It preserves the incumbent DFI, weak Held-Suarez forcing, near-surface residual
correction, log-pressure initialization, hydrostatic layer-mean temperature
initialization, vertical advection, T80 spectral truncation, 900 second inner
step, horizontal diffusion, and forecast API.

The adapter now has a default-false `apply_exact_coriolis_rotation_split`
option. When enabled, the positive-time rollout builds primitive equations with
`angular_velocity=0.0` while preserving all other unit constants. A post-step
filter then converts modal vorticity/divergence to nodal winds, applies the
source-sign-consistent exact Coriolis rotation using the original angular
velocity, and converts the rotated winds back to modal vorticity/divergence.
Temperature variation, log surface pressure, tracers, and `sim_time` are
preserved from the post-dynamics state.

DFI remains on the incumbent path: it uses the normal-rotation primitive
equation, normal weak-HS composition, and the incumbent horizontal-diffusion
filter only.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py` | 0 | Implementer reported pass. |
| `JAX_PLATFORMS=cpu uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Implementer reported `66 passed`. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Re-run by Orchestrator after cleanup; passed. |
| `git diff --check -- src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Re-run by Orchestrator after cleanup; passed. |
| `uv run pytest` | pending | Delegated to Scorer. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split` | pending | Delegated to Scorer. |

## Repair Attempts

- Failure observed: Ruff import-order issue.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: reordered imports.
- Follow-up command and result: Ruff check passed.
- Failure observed: Ruff format check reported touched files needing formatting.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: applied formatting, then the Orchestrator trimmed unrelated
  formatting churn in pre-existing code.
- Follow-up command and result: focused pytest, Ruff check, and diff check passed.

## Known Limitations

- Full pytest, fixed fast evaluation, iteration evaluation, and any gated
  validation were not run by the Implementer.
- Candidate code remains uncommitted and must be either accepted and committed
  by the Orchestrator or reverted after rejection.

## Rollback Notes

Revert the implementation edits in the six changed source/test files listed
above. Preserve this history directory and any raw evaluation artifacts under
`outputs/eval/`.
