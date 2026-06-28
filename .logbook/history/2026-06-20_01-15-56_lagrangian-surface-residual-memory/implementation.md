# Implementation Record

## Identity

- Proposal slug: lagrangian-surface-residual-memory
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
- Baseline commit: ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6
- Candidate commit: not available before acceptance; candidate is the current uncommitted worktree.

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate adds a side-by-side Dinosaur factory and registry key on top of
the accepted scale-separated surface-residual incumbent. It preserves the
prognostic trajectory and the incumbent high-mode near-surface residual path,
then applies bounded backward semi-Lagrangian advection to the low-mode
residual component for `2m_temperature` and `10m_u_component_of_wind`.

The implementation uses requested-lead forecast 10 m winds when both horizontal
wind channels are available, caps displacement, keeps lead zero exact, and
falls back to the stationary scale-separated incumbent behavior when wind
channels, shapes, grid metadata, or finite checks are not valid. Non-near-
surface channels remain unchanged relative to the incumbent residual output.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_primitive_equations.py` | passed | 125 tests passed. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | passed | Passed after an import-order repair. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian` | passed | Fast diagnostics clean, failed=false, issues=0, primary_score approximately -0.7109. |

## Repair Attempts

- Failure observed: a focused implementation test showed nonfinite wind fields could still propagate NaNs after an invalid-advection flag was computed.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no production forecast NaN/Inf; this was a synthetic helper-test issue.
- Fix attempted: return stationary incumbent residuals when advection inputs are invalid or nonfinite.
- Follow-up command and result: focused pytest passed; Ruff passed.

## Known Limitations

- Iteration and validation scores were not produced by the Implementer; those are delegated to the Scorer.
- If `10m_v_component_of_wind` is unavailable or wind fields are invalid, the candidate intentionally falls back to the stationary incumbent residual path.
- The fast primary score was poor, but fast is treated as a finite-diagnostics sanity gate; promotion depends on the fixed iteration gate.

## Rollback Notes

If rejected, revert the six implementation files listed above to the baseline
commit while preserving this history directory and raw candidate evaluation
outputs under `outputs/eval/`.
