# Implementation Record

## Identity

- Proposal slug: zonal-mean-theta-recentering
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_zonal_recenter
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
- Baseline commit: 8ead91209dfbd2abc3ffc31082653cf29aa962dd
- Candidate commit: not created; implementation remains uncommitted at baseline HEAD

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-19_05-12-07_zonal-mean-theta-recentering/implementation.md

## Implementation Summary

Added a side-by-side zonal theta recentering candidate without changing the
forecast API, output variables, evaluation protocols, or incumbent factory.
The new `apply_theta_zonal_mean_recentering` selector is rollout-only and takes
precedence over the accepted global recentering selector, so the candidate does
not stack both filters.

The new filter diagnoses previous and next pressure, full temperature, and dry
potential temperature using the same pressure-to-theta conversion as the
accepted global recentering filter. It computes a previous-minus-next
longitude-mean theta increment at each layer and latitude, converts it back to
a nodal temperature increment using the next-state longitude-mean conversion
factor, broadcasts that increment over longitude, transforms it to modal space,
keeps only m=0, leaves total wavenumbers n <= 8 unchanged, and applies a
smooth taper to zero by n >= 16. The filtered modal increment is added only to
`temperature_variation`; vorticity, divergence, log surface pressure, tracers,
and sim time are copied from the next state.

If pressure, theta, conversion, or modal reconstruction diagnostics are
nonfinite, the zonal filter falls back to the accepted global theta recentering
result for that step.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "theta_zonal or theta_mean_recenter or trajectory_function_applies_theta"` | 0 | 8 passed, 70 deselected |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py -k "theta_zonal or theta_mean_recenter or registry_lists_default or canonical"` | 0 | 6 passed, 26 deselected |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py` | 0 | 110 passed |
| `git diff --check` | 0 | No whitespace errors |
| `uv run pytest` | 0 | 176 passed, 2 skipped |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_zonal_recenter` | 0 | failed=False, issues=0, records=120, primary_score=-1.15249; metrics JSON written under `outputs/eval/` |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: not applicable
- Follow-up command and result: not applicable

## Known Limitations

- The latitude smoother constants were kept fixed before scoring: n <= 8 is
  unchanged and n >= 16 is zeroed by construction. No post-score tuning was
  performed.
- The filter exactly preserves only the representable low-mode zonal theta
  increment after smoothing; higher-l latitude structure is intentionally
  damped by the fixed smoother.
- Per instruction, iteration, validation, and golden protocols were not run.

## Rollback Notes

Revert this experiment by removing the zonal recentering selector, helper, and
factory from `adapter.py`, removing the factory export from
`src/dynamaxx/dycore/models/dinosaur/__init__.py`, removing the registry entry
and factory from `src/dynamaxx/dycore/registry.py`, and reverting the tests and
this implementation record added for the candidate. Do not touch unrelated
logbook history or evaluation outputs unless the Orchestrator requests it.
