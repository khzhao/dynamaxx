# Implementation Record

## Identity

- Proposal slug: smooth-analysis-hs-spectral-taper
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_smooth_taper
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
- Baseline commit: 6094c73fe9b98b46c3ac9bfbb430bafd332d628f
- Candidate commit: uncommitted

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-21_00-52-01_smooth-analysis-hs-spectral-taper/implementation.md

## Implementation Summary

Implemented one side-by-side analysis-HS equilibrium candidate with an opt-in
`use_smooth_analysis_offset_weak_hs_taper` dataclass selector defaulting to
`False`. The incumbent continues to use the existing binary
`_analysis_offset_weak_hs_low_mode_mask` path.

The new candidate selects a compact raised-cosine modal taper only when the
selector is enabled. The smooth mask retains total wavenumber through 9 and
longitude wavenumber through 2, tapers to zero by total wavenumber 14 and
longitude wavenumber 4, is clipped to `[0, 1]`, preserves the area mean mode,
and falls back to the hard mask if the smooth mask is incompatible or nonfinite.
The existing finite offset fallback and Kelvin cap remain after filtering.

Added a factory, export, and registry entry for the exact candidate model name.
Added focused tests for default selector state, hard-mask preservation, smooth
mask bounds and shape, smooth offset filtering, factory parity, registry
coverage, dependency/import coverage, and a finite non-JIT smoke forecast.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Initial post-implementation run passed: 133 passed in 121.65s. |
| `git diff --check` | 0 | Passed before the fast sanity attempt. |
| `python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Syntax sanity check passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_smooth_taper` | 1 | Failed before scoring with a JAX `TracerArrayConversionError` in the smooth mask fallback construction. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Rerun after repair passed: 133 passed in 121.92s. |
| `git diff --check` | 0 | Passed after repair. |
| `python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Syntax sanity check passed after repair. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_smooth_taper` | interrupted | Restarted after repair, reached the single fast evaluation chunk, then the turn was interrupted. A lingering candidate-only process was found and terminated before returning control. No incumbent, iteration, validation, or golden run was started. |

## Repair Attempts

- Failure observed: candidate fast sanity failed with `TracerArrayConversionError` because the smooth helper converted the hard-mask helper's JAX return to NumPy during JIT tracing.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: computed the smooth helper's fallback hard mask directly from static horizontal-grid mask and modal mesh metadata instead of converting a JAX array to NumPy.
- Follow-up command and result: focused pytest rerun passed with 133 tests; `git diff --check` passed. The follow-up fast sanity run was interrupted before completion and then explicitly terminated.

## Known Limitations

- Limitation: candidate fast sanity did not complete after the JIT repair because the turn was interrupted; the Scorer should rerun the candidate protocol as part of scoring.
- Limitation: no iteration, validation, golden, incumbent rerun, leaderboard edit, research-state edit, or output cleanup was performed.

## Rollback Notes

To revert only this experiment, remove the smooth-taper selector, smooth mask
helper, candidate factory/export/registry key, and the focused tests added for
the smooth-taper candidate. Leave unrelated logbook history and evaluation
artifacts untouched unless the Orchestrator explicitly requests cleanup.
