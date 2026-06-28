# Implementation Record

## Identity

- Proposal slug: vector-wind-pchip-sigma-init
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_vector_wind_pchip_init
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
- Baseline commit: 6094c73fe9b98b46c3ac9bfbb430bafd332d628f
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_vertical_interpolation.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-21_02-46-40_vector-wind-pchip-sigma-init/implementation.md

## Implementation Summary

Implemented a side-by-side wind-only sigma initialization candidate. The incumbent
pressure-to-sigma remap still runs for temperature, humidity, and the default wind
path. When `use_vector_wind_pchip_initialization` is enabled, pressure-level
u/v winds after unit conversion and latitude reordering are remapped in
log-pressure with component-wise monotone PCHIP before
`uv_nodal_to_vor_div_modal`.

The vector-wind helper applies a finite post-interpolation speed cap using the
nearest/bracketing pressure-level speed maximum for each target sigma level. It
falls back to the incumbent wind interpolation for unsupported shapes, fewer than
three pressure levels, nonfinite source winds, or nonfinite PCHIP outputs.

Added the exact requested registry key and a factory/export for the candidate.
The incumbent factory and registry key are unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_vertical_interpolation.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Static syntax check before pytest. |
| `uv run pytest tests/dycore/models/dinosaur/test_vertical_interpolation.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 134 passed in 129.72s. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_vector_wind_pchip_init` | not_run | Skipped because the latest Orchestrator checkpoint explicitly said not to edit `outputs`, and fast eval normally writes evaluation artifacts there. |

## Repair Attempts

- Failure observed: none after implementation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not applicable.
- Follow-up command and result: not applicable.

## Known Limitations

- Limitation: Fast eval sanity was not run due the explicit no-outputs constraint in the latest Orchestrator checkpoint.
- Limitation: The speed guard is an upper cap against the local bracketing speed maximum; it does not force interpolated speeds up to a bracketing minimum.

## Rollback Notes

Revert this experiment by removing the vector-wind PCHIP helper from
`vertical_interpolation.py`, removing the `use_vector_wind_pchip_initialization`
dataclass flag and candidate factory/wiring from `adapter.py`, removing the
export and registry entry, deleting the added vertical-interpolation test file,
and reverting the focused test additions for this candidate.
