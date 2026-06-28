# Implementation Record

## Identity

- Proposal slug: analysis-offset-held-suarez-equilibrium
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
- Baseline commit: ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6
- Candidate commit: not committed

## Files Changed

- src/dynamaxx/dycore/models/dinosaur/adapter.py
- src/dynamaxx/dycore/models/dinosaur/__init__.py
- src/dynamaxx/dycore/registry.py
- tests/dycore/models/dinosaur/test_primitive_equations.py
- tests/dycore/models/dinosaur/test_dependency.py
- tests/dycore/test_registry.py
- .logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium/implementation.md

## Implementation Summary

Added a default-false `use_analysis_offset_weak_held_suarez_equilibrium` selector to the Dinosaur dycore dataclass. The selected side-by-side candidate is registered from the scale-separated surface-residual incumbent with only the model name and this selector changed.

The selected path computes a per-initial-state nodal Held-Suarez equilibrium offset from the initialized Dinosaur sigma state. It subtracts the standard Held-Suarez equilibrium from the initialized nodal absolute temperature, transforms the offset to modal space, keeps only valid low-order modes with `abs(m) <= 3` and `l <= 12`, transforms back to nodal space, clips to `+/-20 K` in model nondimensional units, and falls back to zero offset if the filtered result is nonfinite.

The weak Held-Suarez forcing now accepts an optional nodal equilibrium-temperature offset. With no offset, the incumbent path is unchanged; with a zero offset, the forcing tendency matches the incumbent. When the selector is enabled, `trajectory_fn(dinosaur_state)` computes the offset from the incoming initialized Dinosaur state and passes the same dynamic offset into both rollout and DFI weak-HS equations. Forecast inputs, output variables, DFI settings, Strang Coriolis split, off-centered SIL3, theta tendency/recentering, scale-separated near-surface residual correction, and evaluation code were not changed.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 127 passed in 117.36s |
| `uv run pytest` | pass | 193 passed, 2 skipped in 123.12s |
| `git diff --check` | pass | no whitespace errors |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq` | not_run | Orchestrator instructed not to run model-selection eval; Scorer will run later |

## Repair Attempts

- Failure observed: none during required checks
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: not applicable
- Follow-up command and result: not applicable

## Known Limitations

- The candidate has only unit and smoke forecast coverage locally. No fast, iteration, validation, or golden model-selection eval was run by the Implementer.
- The analysis-derived offset is fixed for the rollout from each initialized Dinosaur state and is intentionally low-order and bounded; it does not update during the trajectory.

## Rollback Notes

Revert the selector, offset helper, optional forcing offset, candidate factory/export/registry entry, and the focused tests listed above. Do not modify leaderboard files, evaluation outputs, or unrelated dycore models.
