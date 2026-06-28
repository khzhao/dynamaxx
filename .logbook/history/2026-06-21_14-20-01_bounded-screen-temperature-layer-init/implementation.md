# Implementation Record

## Identity

- Proposal slug: bounded-screen-temperature-layer-init
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
- Baseline commit: 6094c73fe9b98b46c3ac9bfbb430bafd332d628f
- Candidate commit: uncommitted worktree candidate

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate registers a side-by-side model that keeps the accepted analysis-Held-Suarez incumbent unchanged by default and enables one additional initialization selector. The selector runs after pressure-to-sigma interpolation and before modal temperature packing.

When same-time `2m_temperature` is available, finite, and shape-compatible with the lowest sigma layer, the candidate adjusts only the lowest sigma temperature by `0.25 * clip(screen_temperature - lowest_sigma_temperature, -2 K, +2 K)`. Missing, nonfinite, or shape-incompatible screen temperature preserves the incumbent initialized temperature exactly. Winds, humidity, surface pressure, rollout dynamics, pressure-level output interpolation, residual correction, evaluation protocols, and forecast contract are unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Candidate source and focused tests compile. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 134 passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init` | 0 | Primary -0.5387762635908023; diagnostics clean with 0 issues. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run pytest` | 0 | 200 passed, 2 skipped in 129.81s. |

## Repair Attempts

- Failure observed: none during implementer or orchestrator verification.
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none after the first complete implementation.
- Follow-up command and result: not applicable.

## Known Limitations

- The adjustment is intentionally capped and lowest-layer-only. If the accepted surface residual path already captures the useful same-time screen-temperature information, score movement may be neutral or negative.
- Validation must remain skipped unless the candidate first clears iteration promotion gates.

## Rollback Notes

If rejected, revert only the six source and test files listed above to `HEAD`. Preserve this history directory and raw evaluation outputs for reproducibility.
