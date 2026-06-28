# Implementation Record

## Identity

- Proposal slug: centered-dfi-offcenter-rollout
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_centered_dfi
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
- Baseline commit: 54375ce2994827fcc2dfe09ce0df3924cbaa6c75
- Candidate commit: not committed; worktree implementation only

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-19_10-17-34_centered-dfi-offcenter-rollout/implementation.md

## Implementation Summary

Added `use_centered_dfi_solver_with_offcentered_rollout`, defaulting to false,
on `DinosaurPrimitiveEquationsDycoreModel`. The positive-time rollout still uses
`self._ode_solver()`, so the accepted offcentered incumbent keeps
`semi_implicit_offcentering=0.05`. When the new selector is enabled, DFI receives
the centered `time_integration.imex_rk_sil3` function object; otherwise DFI
keeps the same solver object as rollout.

Registered a side-by-side candidate factory that starts from the current
offcentered incumbent and only changes the model name plus the centered-DFI
selector. Existing DFI equation setup, filters, span, cutoff, weights, Coriolis
handling, theta recentering, residual correction, output packing, and forecast
API were left unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py::test_centered_dfi_offcenter_rollout_factory_preserves_incumbent_except_selector tests/dycore/models/dinosaur/test_primitive_equations.py::test_trajectory_function_threads_offcentered_solver_to_rollout_and_dfi tests/dycore/models/dinosaur/test_primitive_equations.py::test_trajectory_function_uses_centered_dfi_with_offcentered_rollout tests/dycore/models/dinosaur/test_primitive_equations.py::test_centered_dfi_offcenter_rollout_candidate_forecast_is_finite tests/dycore/test_registry.py::test_registry_creates_centered_dfi_offcenter_rollout_candidate_model tests/dycore/models/dinosaur/test_dependency.py::test_dinosaur_centered_dfi_offcenter_rollout_is_registered` | 0 | 6 passed |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py` | 0 | 116 passed |
| `uv run pytest` | 0 | 182 passed, 2 skipped |
| `git diff --check` | 0 | No whitespace errors |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_centered_dfi` | 0 | failed=False, issues=0, records=120, primary_score=-0.557899; metrics JSON/CSV written under `outputs/eval/` |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: not applicable
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: candidate is not committed; `Candidate commit` remains unavailable until the Orchestrator commits or otherwise snapshots the implementation.
- Limitation: only the fast gate was run by the Implementer; iteration, validation, and golden were not run per role instructions.

## Rollback Notes

Revert this experiment by removing the selector and DFI solver branch from
`adapter.py`, deleting the centered-DFI/offcenter-rollout factory/export and
registry entry, and removing the focused tests plus this implementation record.
The existing offcentered incumbent factory and its solver wiring can remain as
implemented before this experiment.
