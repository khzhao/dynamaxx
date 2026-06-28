# Implementation: gradient-wind-surface-diagnostic

- Baseline commit: `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`
- Candidate commit: not committed by Implementer
- Candidate model: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - Added default-false `use_gradient_wind_10m_diagnostic`.
  - Added side-by-side factory derived from `analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model()`.
  - Added a post-residual output-only 10 m wind diagnostic scaling path.
  - Added a bounded gradient-wind speed factor using smoothed lowest-layer vorticity, lowest-model wind speed, lowest-layer geopotential gradients, latitude tapering, sign consistency, finite fallback, and a hard 15 percent cap.
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - Exported the new Dinosaur candidate factory.
- `src/dynamaxx/dycore/registry.py`
  - Registered the requested candidate model name.
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - Added factory-difference coverage and focused gradient-wind diagnostic tests for zero curvature, curved-flow activation, equatorial tapering, cap enforcement, and nonfinite fallback.
- `tests/dycore/models/dinosaur/test_dependency.py`
  - Added import/registration coverage for the new factory and registry name.
- `tests/dycore/test_registry.py`
  - Added registry listing and side-by-side factory-difference coverage.
- `.logbook/history/2026-06-20_17-12-34_gradient-wind-surface-diagnostic/implementation.md`
  - Recorded implementation notes.

## Tests And Checks

- Passed: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Result: `133 passed`
- Passed: `uv run pytest`
  - Result: `199 passed, 2 skipped`
- Passed: `git diff --check`
- Passed: lightweight registry/import comparison
  - `create_dycore_model(candidate_name)` resolves.
  - Candidate differs from incumbent only by `name` and `use_gradient_wind_10m_diagnostic`.
- Passed optional sanity: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag`
  - Result: `failed=False`, `issues=0`, `records=120`, `primary_score=-0.538692`
  - Metrics path: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_gradient_10m_diag.json`

## Repair Attempts

- Fixed an implementation indentation error found by a quick import/compile check.
- Corrected the curvature proxy to use lowest-model wind speed, matching the selected proposal, while keeping final 10 m wind scaling output-only.

## Known Limitations

- The diagnostic uses lowest-layer geopotential as the pressure-gradient proxy rather than surface pressure.
- The adjustment is applied after near-surface residual correction so the accepted residual memory path remains unchanged; only final emitted 10 m wind components are scaled.
- Constants were fixed before scoring and were not tuned against fast-eval output.
