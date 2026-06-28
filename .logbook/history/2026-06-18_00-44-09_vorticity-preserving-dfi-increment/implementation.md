# Implementation Record

## Identity

- Proposal slug: vorticity-preserving-dfi-increment
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi
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
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi`.
It preserves the incumbent DFI, weak Held-Suarez forcing, near-surface residual
correction, log-pressure initialization, hydrostatic layer-mean temperature
initialization, vertical advection, T80 spectral truncation, 900 second inner
step, horizontal diffusion, and forecast API.

The adapter now has a default-false `preserve_vorticity_during_dfi` option. When
enabled, the usual `time_integration.digital_filter_initialization` runs first.
The rollout then starts from the DFI state with only the `vorticity` leaf
replaced by the raw pre-DFI vorticity. Divergence, temperature variation, log
surface pressure, tracers, and `sim_time` remain exactly those returned by DFI.
When the option is false, the incumbent DFI path still passes the DFI state
directly to the rollout.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Implementer reported `64 passed`. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Implementer reported pass after one import-order repair. |
| `git diff --check -- src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | No whitespace errors reported. |
| `uv run pytest` | pending | Delegated to Scorer. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi` | pending | Delegated to Scorer. |

## Repair Attempts

- Failure observed: Ruff import-order finding.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: reordered imports and restored incidental formatting churn so the diff remained scoped.
- Follow-up command and result: Ruff check and focused pytest passed.

## Known Limitations

- Full pytest, fixed fast evaluation, iteration evaluation, and any gated
  validation were not run by the Implementer.
- Candidate code remains uncommitted and must be either accepted and committed
  by the Orchestrator or reverted after rejection.

## Rollback Notes

Revert the implementation edits in the six changed source/test files listed
above. Preserve this history directory and any raw evaluation artifacts under
`outputs/eval/`.
