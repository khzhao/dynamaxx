# Implementation Record

## Identity

- Proposal slug: barotropic-analysis-hs-equilibrium-offset
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_barotropic_analysis_hs_eq
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
- Baseline commit: 6094c73fe9b98b46c3ac9bfbb430bafd332d628f
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Added a side-by-side Dinosaur dycore candidate that preserves the accepted
analysis-offset Held-Suarez equilibrium path, then optionally projects that
accepted offset onto a vertically coherent thermal target. The projection forms
a sigma-layer-mass-weighted column mean at each horizontal grid point,
re-expands it with a fixed broad lower/mid-tropospheric taper, reapplies the
existing low-horizontal-wavenumber mask, and reapplies the existing Kelvin cap.
Shape-incompatible or nonfinite projections return the accepted incumbent
offset exactly.

The candidate factory, package export, and registry entry use the required
model name. DFI, weak-HS rates, Coriolis splitting, theta tendency, theta
recentering, off-centering, residual corrections, output packing, evaluation
protocols, and metrics were not changed.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 133 passed in 127.45s |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_barotropic_analysis_hs_eq` | 0 | failed=False, issues=0, records=120, primary_score=-0.531592 |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: not applicable
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: The vertical taper is fixed and deterministic; it was not tuned
  against iteration, validation, or golden results.
- Limitation: Iteration, validation, and golden protocols were intentionally
  not run by the Implementer.

## Rollback Notes

Revert the candidate factory, barotropic projection helper and flag, package
export, registry entry, focused tests, and this implementation record. Do not
remove proposal files or scorer/leaderboard artifacts.
