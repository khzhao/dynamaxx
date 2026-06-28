# Implementation Record

## Identity

- Proposal slug: snow-soil-land-thermal-reservoir
- Candidate model name: dino_land_soilflux
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf
- Baseline commit: 329dd5758204b7e77f1abb258b1dab9ee5d9b2c8
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-22_10-08-39_snow-soil-land-thermal-reservoir/implementation.md

## Implementation Summary

Added the short side-by-side registry alias `dino_land_soilflux`. The factory reproduces the accepted ocean-bulk incumbent and enables one additional selector, `apply_land_soil_thermal_reservoir`.

The land reservoir path reuses validated land-sea fraction loading. It builds a Dinosaur-latitude-order land weight, validates lead-zero `soil_temperature_level_4` and `snow_depth`, and constructs a reservoir anchor from lead-zero `2m_temperature` when valid, otherwise the lowest model air layer. The deep-soil departure from that screen/air anchor is capped to 3 K.

The new explicit forcing applies only to the lowest sigma-layer temperature tendency, over land weight only, with a 12-day e-folding floor, monotone exponential snow attenuation, and a 0.02 K single-step increment cap. It returns zero tendencies for vorticity, divergence, log surface pressure, and tracers. Missing, nonfinite, negative, or shape-incompatible land fraction, soil, snow, anchor, or coupling diagnostics leave the model on the accepted incumbent path. The land reservoir forcing is excluded from the DFI equation path, matching the accepted ocean-bulk handling.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 1 | Initial run failed on import ordering in `test_primitive_equations.py`. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Passed after import-order repair. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py -k "land_soilflux or soil_reservoir or snow_insulation or ocean_bulk_shf"` | 1 | Initial run failed in the new synthetic land-soil test helper due to an extra selected-channel dimension. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py -k "land_soilflux or soil_reservoir or snow_insulation or ocean_bulk_shf"` | 0 | Passed: 14 passed, 117 deselected. |
| `uv run python - <<'PY' ... create_dycore_model('dino_land_soilflux') ... PY` | 0 | Printed `dino_land_soilflux` and `True`. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Passed after the test-helper repair. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Exact requested ruff command passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py` | 0 | Passed: 19 passed. |
| `uv run dynamaxx-eval fast --model dino_land_soilflux` | 0 | Completed with `failed=False`, `issues=0`, `records=120`, `primary_score=-0.441675`; metrics at `outputs/eval/fast_dino_land_soilflux.json`. |
| `uv run pytest` | 0 | Orchestrator full unit gate passed: 216 passed, 2 skipped in 150.32s. |

## Repair Attempts

- Failure observed: ruff import ordering in `tests/dycore/models/dinosaur/test_primitive_equations.py`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: moved `_LandSoilThermalReservoirForcingSigma` to ruff's sorted import position.
- Follow-up command and result: ruff passed.

- Failure observed: focused pytest failed because `_structured_initial_state_with_land_soil` concatenated `(init, var, lon, lat)` with `(init, 1, 1, lon, lat)`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: selected the `2m_temperature` channel as `(init, lon, lat)` before adding soil and snow singleton variable axes.
- Follow-up command and result: focused pytest passed.

## Known Limitations

- The land reservoir is deliberately simple: it uses only lead-zero deep soil temperature, snow depth, and a static land fraction. It does not model diurnal phasing, soil moisture, vegetation, lakes, or tile-specific exchanges.
- Missing or invalid `snow_depth` causes exact land-reservoir fallback rather than neutral no-snow behavior, matching the requested conservative fallback contract.
- The candidate is uncommitted; the candidate commit is therefore unavailable.

## Rollback Notes

Revert this experiment by removing `apply_land_soil_thermal_reservoir`, the land soil/snow validation helpers, `_LandSoilThermalReservoirForcingSigma`, `_compose_land_soil_thermal_reservoir_equation`, `land_soilflux_dinosaur_dycore_model`, the `dino_land_soilflux` registry entry, and the tests added for the alias and helper behavior. Do not remove unrelated logbook history or accepted ocean-bulk incumbent code.
