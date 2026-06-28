# Implementation Record

## Identity

- Proposal slug: potential-temperature-logp-initialization
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init
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
- Path: .logbook/history/2026-06-17_10-15-26_potential-temperature-logp-initialization/implementation.md

## Implementation Summary

Registered the side-by-side candidate
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init`.
It preserves the accepted incumbent configuration and adds only
`use_potential_temperature_log_pressure_initialization`.

The adapter still computes the accepted layer-mean hydrostatic dry temperature
estimate first. The incumbent log-pressure pressure-to-sigma interpolation is
then applied to all fields. For the theta candidate only, the sigma temperature
entry is replaced by a dry-potential-temperature remap: source dry temperature
is converted to theta with fixed `p0 = 1000 hPa` and `physics_specs.kappa`,
theta is interpolated in log pressure to the same sigma target pressure, and
the result is converted back to dry temperature. U/V wind and passive humidity
remain on the incumbent direct log-pressure interpolation path.

The theta helper falls back pointwise to the incumbent direct temperature
interpolation when target pressure is nonpositive, source theta is nonfinite,
interpolated theta is nonfinite, reconstructed temperature is nonfinite, or
reconstructed temperature is nonpositive.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Passed after import-order repair. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 66 passed in 58.78s after fixture repair. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.12592`; metrics at `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init.json`. |
| `git diff --check` | pass | No whitespace errors. |

## Repair Attempts

- Failure observed: initial focused pytest run failed four new helper tests because `SigmaCoordinates.from_centers` was given Python lists.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: converted new test center inputs to `np.asarray(..., dtype=np.float32)`.
- Follow-up command and result: reran focused pytest command; 66 passed in 58.78s.

## Known Limitations

- Limitation: no full `iteration`, `validation`, or `golden` evaluation was run by the Implementer role. The task explicitly requested no golden run; fast sanity passed.
- Limitation: the candidate is not committed, per instruction.

## Rollback Notes

Revert only this experiment by removing the new theta initialization flag,
helper, factory, export, registry entry, and associated tests from the files
listed above. Keep the immutable proposal and implementation logbook records
unless the Orchestrator explicitly requests history cleanup.
