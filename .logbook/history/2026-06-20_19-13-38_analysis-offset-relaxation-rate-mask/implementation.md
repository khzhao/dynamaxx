# Implementation Record

## Identity

- Proposal slug: analysis-offset-relaxation-rate-mask
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask
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

Implemented a side-by-side Dinosaur candidate that preserves the accepted
analysis-offset Held-Suarez equilibrium and adds one opt-in selector,
`use_analysis_offset_weak_held_suarez_rate_mask`. The candidate derives a
bounded thermal relaxation-rate multiplier from the same low-mode equilibrium
temperature offset:

`clip(1 / (1 + abs(offset) / 12 K), 0.55, 1.0)`

The multiplier is passed only to `_TracerSafeHeldSuarezForcingSigma` and only
scales the weak-HS thermal Newtonian relaxation rate. Wind drag, pressure
tendency, vorticity/divergence/log-surface-pressure tendencies, tracers, DFI,
Coriolis splitting, theta tendency/recentering, off-centering, residual
corrections, output packing, and evaluation protocols are unchanged.
Nonfinite offset values fall back elementwise to multiplier `1.0`.

Added focused tests for factory preservation, registry exposure, bounded
multiplier behavior including nonfinite fallback, thermal-only forcing scaling,
and rollout/DFI plumbing of the multiplier.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 133 passed in 120.64s |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask` | 0 | failed=False, issues=0, records=120, primary_score=-0.547367, metrics=outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask.json |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: This implementation only ran focused unit tests and the fast sanity protocol. Iteration, validation, and golden protocols were intentionally not run.
- Limitation: The relaxation-rate mask weakens a stabilizing thermal source in large-offset regions; scoring should watch MSLP and Z500 drift as described in the proposal.

## Rollback Notes

Remove the `use_analysis_offset_weak_held_suarez_rate_mask` flag, rate-mask
helper, optional forcing multiplier, candidate factory/export/registry entry,
and the focused tests added for this experiment. Do not alter the incumbent
analysis-offset equilibrium candidate or fixed evaluation outputs.
