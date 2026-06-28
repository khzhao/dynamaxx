# Implementation Record

## Identity

- Proposal slug: dry-consistent-geopotential-diagnostic
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
- Baseline commit: a7833574e9ade1a5271bd8cbef2fa1357465f5a8
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/implementation.md

## Implementation Summary

Registered the side-by-side candidate
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential`.
The candidate preserves the incumbent DFI, weak Held-Suarez relaxation,
near-surface residual correction, log-pressure initialization, hydrostatic
layer-mean temperature initialization, vertical advection, T80 defaults, 900 s
inner step, zero orography, finite pressure interpolation, passive humidity
transport/output, and output contract.

Added a `use_dry_geopotential_diagnostic` adapter flag. During a dry rollout,
the candidate passes `specific_humidity=None` to
`primitive_equations.get_geopotential_on_sigma` for geopotential reconstruction
only. Humidity remains in the carried tracers and in requested humidity outputs,
and temperature, winds, surface pressure, MSLP, near-surface residuals, and
pressure-level interpolation continue through the existing paths.

Focused tests verify that the candidate factory preserves incumbent settings,
the candidate registry key constructs the expected model, direct conversion
changes only pressure-level geopotential outputs with nonzero passive humidity,
humidity output remains unchanged, and a small non-JIT forecast is finite.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | All checks passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 62 passed in 58.15s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.12386`, metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential.json`. |
| `git diff --check` | pass | No whitespace errors. |

## Repair Attempts

- Failure observed: none.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not applicable.
- Follow-up command and result: not applicable.

## Known Limitations

- Limitation: Fast sanity was run locally, but iteration and validation scoring remain for the Scorer/Orchestrator under the fixed protocol.
- Limitation: The implementation intentionally does not evaluate or tune constants against validation data.

## Rollback Notes

Revert the additions in `adapter.py`, `__init__.py`, `registry.py`, and the
three focused test files listed above. Remove this implementation record only if
the Orchestrator explicitly requests history cleanup; otherwise leave the
history artifact intact.
