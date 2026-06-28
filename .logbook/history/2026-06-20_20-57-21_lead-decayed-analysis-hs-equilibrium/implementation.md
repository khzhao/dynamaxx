# Implementation Record

## Identity

- Proposal slug: lead-decayed-analysis-hs-equilibrium
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay
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
- Path: .logbook/history/2026-06-20_20-57-21_lead-decayed-analysis-hs-equilibrium/implementation.md

## Implementation Summary

Added a side-by-side Dinosaur candidate that preserves the accepted analysis-offset Held-Suarez equilibrium setup and applies a rollout-only exponential decay to the equilibrium_temperature_offset with tau = 10 days. The accepted low-mode clipped offset is still computed from the raw initialized state. DFI rebuilds the forcing with the full constant offset and no decay timescale, and positive-time rollout starts with sim_time = 0 only for the decay candidate. Missing or nonfinite sim_time falls back to the incumbent constant offset for that tendency evaluation.

The decay applies only to the equilibrium offset in `_TracerSafeHeldSuarezForcingSigma`; weak-HS rates, residual correction, initialization, Coriolis splitting, theta tendency/recentering, off-centering, output packing, evaluation protocols, and metrics are unchanged. The 10-day timescale is nondimensionalized through Dinosaur physics specs.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 135 passed in 129.06s |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay` | 0 | failed=False, issues=0, records=120, primary_score=-0.530605, metrics=outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay.json |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: not applicable
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: iteration, validation, and golden protocols were not run, per Orchestrator instruction.
- Limitation: candidate source is uncommitted, so there is no candidate commit hash.

## Rollback Notes

Remove the decay flag, 10-day timescale constant, sim_time rollout initialization helper, forcing decay path, decayed factory/export/registry entry, focused tests, and this implementation record. Leave proposal and scorer/decision artifacts untouched.
