# Implementation Record

## Identity

- Proposal slug: mass-neutral-weak-hs-forcing
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs
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

The candidate adds a side-by-side Dinosaur factory and registry entry for
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs`.
It preserves the incumbent DFI, near-surface residual correction, weak
Held-Suarez coefficients, log-pressure initialization, hydrostatic layer-mean
temperature initialization, vertical advection, spectral resolution, timestep,
and forecast API.

The existing tracer-safe weak Held-Suarez forcing was factored so the nodal
temperature tendency is computed separately from the modal tendency packaging.
The mass-neutral subclass subtracts the horizontal quadrature-weighted mean
from each sigma layer before converting the thermal tendency back to modal
space. Vorticity, divergence, log surface pressure, tracer, and sim-time
tendency leaves remain the same zero-valued leaves as the incumbent forcing.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Implementer reported `64 passed`. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Initial import-order issue was fixed, then rerun passed. |
| `git diff --check` | 0 | No whitespace errors reported. |
| `timeout 900 uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs` | 0 | Implementer reported `failed=False`, `issues=0`, `records=120`, `primary_score=-1.17006`. Scorer will rerun fixed gates. |
| `uv run pytest` | pending | Delegated to Scorer. |

## Repair Attempts

- Failure observed: invalid intermediate long registry helper during implementation.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: simplified the registry helper and reran focused tests.
- Follow-up command and result: focused pytest passed.
- Failure observed: Ruff import ordering.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: reordered imports.
- Follow-up command and result: Ruff check passed.

## Known Limitations

- The candidate changes only the forecast source formulation; no WeatherBench2
  iteration or validation result was available at implementation handoff.
- Candidate code remains uncommitted and must be either accepted and committed
  by the Orchestrator or reverted after rejection.

## Rollback Notes

Revert the implementation edits in the six changed source/test files listed
above. Preserve this history directory and any raw evaluation artifacts under
`outputs/eval/`.
