# Implementation Record

## Identity

- Proposal slug: exact-weak-hs-thermal-split
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs
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
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs`.
It preserves the incumbent DFI, weak Held-Suarez coefficients and equilibrium
geometry, near-surface residual correction, log-pressure initialization,
hydrostatic layer-mean temperature initialization, vertical advection, T80
spectral truncation, 900 second inner step, horizontal diffusion, and forecast
API.

The adapter now has a default-false
`apply_exact_weak_held_suarez_thermal_split` option. When enabled, the
positive-time rollout uses the base primitive-equation dynamics and applies
weak Held-Suarez Newtonian cooling through a post-step exact exponential thermal
filter after horizontal diffusion. The filter computes the same `kt()` and
`equilibrium_temperature()` as the accepted tracer-safe weak-HS forcing and
updates only `temperature_variation`.

DFI remains on the incumbent path: the DFI initializer still receives the
composed weak-HS equation and the incumbent horizontal-diffusion filter only.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Implementer reported `65 passed`; command was run twice. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Implementer reported pass after import-order repair. |
| `git diff --check -- src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | No whitespace errors reported. |
| `uv run pytest` | pending | Delegated to Scorer. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs` | pending | Delegated to Scorer. |

## Repair Attempts

- Failure observed: overlong or invalid intermediate registry wrapper naming.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: simplified the registry wrapper.
- Follow-up command and result: focused pytest passed.
- Failure observed: Ruff import-order finding.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: reordered imports.
- Follow-up command and result: Ruff check passed.

## Known Limitations

- Full pytest, fixed fast evaluation, iteration evaluation, and any gated
  validation were not run by the Implementer.
- Candidate code remains uncommitted and must be either accepted and committed
  by the Orchestrator or reverted after rejection.

## Rollback Notes

Revert the implementation edits in the six changed source/test files listed
above. Preserve this history directory and any raw evaluation artifacts under
`outputs/eval/`.
