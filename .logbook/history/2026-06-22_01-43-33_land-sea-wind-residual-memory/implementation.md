# Implementation Record

## Identity

- Proposal slug: land-sea-wind-residual-memory
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_landsea_wind
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
- Baseline commit: 681fe7c0d37fadbc1a91159a8d9a7f9f2543f185
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Added a side-by-side Dinosaur candidate that starts from the accepted
land-sea-aware `2m_temperature` incumbent and changes only the existing
scale-separated near-surface output correction for `10m_u_component_of_wind`.
The candidate reuses the accepted WeatherBench2 `land_sea_mask` loading,
alignment, validation, and fallback path.

For 10 m zonal wind, pure-land points retain the incumbent residual decay,
ocean points lengthen only the low-mode residual memory using a bounded
`0.75` exponent, and coastlines blend continuously by land fraction. High-mode
wind residual decay remains incumbent-equivalent to avoid retaining small-scale
analysis noise. The accepted land-sea `2m_temperature` branch is preserved.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Implementer compile check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Focused tests passed: 139 passed. |
| `uv run pytest` | 0 | Full suite passed: 205 passed, 2 skipped in 129.66s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_landsea_wind` | 0 | Fast primary score -0.5141372750454984; diagnostics failed false; issues 0; records 120. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: none reported after implementation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none needed.
- Follow-up command and result: all requested checks passed.

## Known Limitations

- The ocean low-mode wind residual exponent is a fixed bounded value, not tuned
  against iteration or validation.
- Fast primary score was worse than the incumbent fast score, but fast is a
  sanity gate only; iteration is required for candidate promotion.

## Rollback Notes

Revert this experiment's source and test changes with
`git apply -R .logbook/history/2026-06-22_01-43-33_land-sea-wind-residual-memory/candidate.diff`
if the candidate is rejected. Keep the history artifacts and raw evaluation
outputs.
