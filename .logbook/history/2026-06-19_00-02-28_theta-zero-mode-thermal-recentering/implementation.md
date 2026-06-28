# Implementation Record

## Identity

- Proposal slug: theta-zero-mode-thermal-recentering
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
- Baseline commit: cb5bbd1c15744b4fc00ecca5de78da188685a33d
- Candidate commit: c359ee1b016ccd92412585997a799a7c644a65c5

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-19_00-02-28_theta-zero-mode-thermal-recentering/implementation.md

## Implementation Summary

Implemented the side-by-side candidate factory and registry entry for the theta mean recentering model. The incumbent factory and behavior remain unchanged.

The candidate adds one rollout-only post-step filter. The filter diagnoses sigma-layer pressure and full temperature from the previous and next states, converts both to dry potential temperature, computes area-weighted horizontal layer means, and changes only the modal zero coefficient of the next state's `temperature_variation` so each layer's theta mean matches the previous state. Vorticity, divergence, log surface pressure, tracers, sim time, output variables, and the forecast contract are unchanged. If pressure, theta, conversion factors, or the corrected modal temperature are nonfinite, the filter returns the incumbent next-state temperature variation.

The wrapper is appended only to positive-time rollout filters. Digital filter initialization receives the incumbent filter set without the theta recentering wrapper.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 1 | Initial focused run failed one new test because the existing horizontal diffusion filter name is `_filter`, not `step_filter`. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 103 passed in 84.91s after the test-only expectation repair. |
| `uv run pytest` | 0 | 169 passed, 2 skipped in 92.73s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter` | 0 | Fast protocol completed with `failed=False`, `issues=0`, `records=120`, `primary_score=-0.79923`; metrics JSON written under `outputs/eval/`. |

## Repair Attempts

- Failure observed: new DFI-isolation test assumed the existing horizontal diffusion filter name was `step_filter`.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: changed the test to assert the recentering wrapper is the final rollout filter and that DFI filters equal the rollout filters excluding that wrapper, without depending on the incumbent diffusion filter's private name.
- Follow-up command and result: focused pytest command passed with 103 tests.

## Known Limitations

- Limitation: Iteration, validation, and golden protocols were not run by the Implementer role, per Orchestrator instruction.
- Limitation: The fast eval sanity check verifies finite candidate forecasts and diagnostics, but acceptance decisions require Scorer/Orchestrator comparison against the incumbent on fixed iteration and validation gates.

## Rollback Notes

If rejected, revert only this experiment's implementation changes by restoring the changed source and test files listed above and removing this implementation record if the Orchestrator requests logbook rollback. Do not touch prior accepted commits, unrelated logbook history, leaderboard state, or raw evaluation outputs unless explicitly instructed by the Orchestrator.
