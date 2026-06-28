# Implementation Record

## Identity

- Proposal slug: land-sea-contrast-surface-temperature
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
- Baseline commit: 6094c73fe9b98b46c3ac9bfbb430bafd332d628f
- Candidate commit: 681fe7c0d37fadbc1a91159a8d9a7f9f2543f185

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Added a side-by-side Dinosaur candidate that preserves the accepted analysis-HS
incumbent and changes only `2m_temperature` residual memory in the existing
scale-separated near-surface correction path. The candidate loads a
WeatherBench2 `land_sea_mask` through `WeatherBench2Source.read_constants`,
requires exact longitude/latitude alignment and finite `[0, 1]` values, and
falls back to the incumbent uniform residual correction whenever the static mask
cannot be read or validated.

For `land_sea_fraction = 1`, the `2m_temperature` residual decay is identical
to the incumbent. For ocean points, the candidate lengthens residual memory by
raising the incumbent decay to a fixed exponent of `0.5`; coastline points blend
continuously. Lead-zero exactness and all non-`2m_temperature` channels remain
on incumbent behavior.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Implementer compile check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Focused tests passed: 135 passed. |
| `uv run pytest` | 0 | Full suite passed: 201 passed, 2 skipped in 130.52s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface` | 0 | Fast primary score -0.5137008061625102; diagnostics clean. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: initial mask-loading fallback did not catch every constant
  materialization failure.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: hardened the mask load path so failures disable only the
  land-sea blend and preserve incumbent correction behavior.
- Follow-up command and result: compile, focused pytest, fast, and `git diff
  --check` all passed after the repair.

## Known Limitations

- The ocean persistence exponent is a fixed simple value, not tuned against
  iteration or validation.
- Because `ForecastInput` has no source handle, this candidate uses the default
  local `WeatherBench2Source()` internally and requires exact grid alignment.

## Rollback Notes

Revert this experiment's source and test changes with
`git apply -R .logbook/history/2026-06-21_23-32-41_land-sea-contrast-surface-temperature/candidate.diff`
if the candidate is rejected. Keep the history artifacts and raw evaluation
outputs.
