# Implementation Record

## Identity

- Proposal slug: variable-selective-pressure-initialization
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
- Baseline commit: 30a496b1f2ed8f894511404341c7774288bdb4c8
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_10-29-23_variable-selective-pressure-initialization/implementation.md

## Implementation Summary

Added a default-false `use_variable_selective_pressure_initialization` option
to the Dinosaur primitive-equation adapter and passed it through forecast
initialization. When enabled, `weather_state_to_dinosaur_state` still computes
the accepted pressure-level hydrostatic layer-mean temperature before latitude
ordering, unit conversion, or pressure-to-sigma interpolation. It then
interpolates `u_component_of_wind` and `v_component_of_wind` through the
existing log-pressure pressure-to-sigma helper while interpolating
`temperature` and optional `specific_humidity` through the existing
pressure-linear helper.

Registered and exported only the side-by-side candidate
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init`.
The Strang incumbent factory and default behavior are unchanged unless the new
selector is enabled.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Changed Python files compile. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 81 passed in 65.40s. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Orchestrator review reformatted one focused test file. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 81 passed in 65.69s after formatting. |
| `uv run python - <<'PY' ...` | 0 | Candidate import/export/registry check passed. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.10212`; metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init.json`. |

## Repair Attempts

- Failure observed: none.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none needed.
- Follow-up command and result: not applicable.

## Known Limitations

- Limitation: This implementation intentionally uses separate existing helper
  calls rather than adding broad nonfinite fallback logic; it relies on the
  same finite extrapolation behavior already used by the existing
  pressure-to-sigma helpers.
- Limitation: Full iteration and validation protocols were not run by the
  Implementer; those remain Scorer or Orchestrator responsibilities under the
  fixed protocol.

## Rollback Notes

Revert the new adapter selector/helper/factory, remove the package export and
registry entry for
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init`,
and remove the focused tests and this implementation record. Do not remove
unrelated logbook history or evaluation outputs unless the Orchestrator
explicitly requests cleanup.
