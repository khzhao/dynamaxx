# Implementation Record

## Identity

- Proposal slug: potential-temperature-thermodynamic-tendency
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind
- Baseline commit: 257f79d871482727b4256b624490122a84982c69
- Candidate commit: cb5bbd1c15744b4fc00ecca5de78da188685a33d

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/implementation.md

## Implementation Summary

Implemented one side-by-side theta-tendency candidate. The incumbent path keeps the default `temperature` thermodynamic tendency formulation. The candidate opts into `potential_temperature`, which diagnoses sigma-layer pressure from `sigma * surface_pressure`, converts the temperature anomaly to a dry potential-temperature anomaly with 1000 hPa reference pressure, transports that anomaly horizontally and vertically, converts the summed theta transport back to temperature with the local Exner factor, and adds the existing `omega / p` pressure-work tendency.

The same option is passed into both rollout and DFI equation construction. Vorticity, divergence, log-surface-pressure, tracers, Coriolis splitting, initialization, diffusion, residual correction, 10 m wind diagnostics, output interpolation, and the forecast API are unchanged for the incumbent path. Pressure/theta diagnostics are guarded; if pressure, theta, converted transport, or candidate temperature tendency are nonfinite, the temperature tendency falls back to the incumbent temperature-form tendency for that equation call.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m py_compile src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py` | 0 | Syntax check before pytest. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 1 | First run failed due three new tests calling `_forecast_input` with positional `lead_steps`. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 96 passed in 80.27s. |
| `uv run pytest` | 0 | 162 passed, 2 skipped in 88.12s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency` | 0 | failed=False, issues=0, records=120, primary_score=-0.800526; metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency.json`. |

## Repair Attempts

- Failure observed: focused pytest failed in three new theta-tendency tests with `TypeError: _forecast_input() takes 1 positional argument but 2 were given`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: changed those calls to pass `lead_steps=(0,)` by keyword.
- Follow-up command and result: focused pytest passed with 96 passed; full pytest passed with 162 passed and 2 skipped; fast eval completed with `failed=False` and `issues=0`.

## Known Limitations

- Limitation: The theta-form path changes only the explicit sigma thermodynamic tendency. The semi-implicit linearized temperature terms remain the incumbent formulation by design.
- Limitation: The finite fallback is equation-call-wide for the temperature tendency, not pointwise, to avoid mixing two thermodynamic discretizations within one spectral tendency.
- Limitation: The accepted model has passed fast, iteration, and validation gates, but golden was not run because the protocol reserves it for locked final reporting.

## Rollback Notes

To revert only this experiment, remove the theta conversion helpers, `temperature_tendency_formulation` option, theta tendency methods, and candidate factory/export/registry entry; then remove the added tests and this implementation record. Do not modify the incumbent factory or unrelated logbook/eval artifacts.
