# Implementation Record

## Identity

- Proposal slug: theta-hydrostatic-pressure-output-reconstruction
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_hydrostatic_output
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
- Baseline commit: 6094c73fe9b98b46c3ac9bfbb430bafd332d628f
- Candidate commit: uncommitted experiment patch

## Files Changed

- Path: `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- Path: `src/dynamaxx/dycore/registry.py`
- Path: `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Path: `tests/dycore/models/dinosaur/test_dependency.py`
- Path: `tests/dycore/test_registry.py`

## Implementation Summary

The candidate adds a default-disabled `reconstruct_theta_hydrostatic_pressure_output`
selector to the Dinosaur adapter and registers a side-by-side model extending the
accepted analysis-offset Held-Suarez equilibrium incumbent with the
`_theta_hydrostatic_output` suffix.

When enabled, `dinosaur_state_to_weather_state` first computes the incumbent
pressure-level fields, then replaces only pressure-level temperature and
geopotential with a guarded theta/hydrostatic reconstruction. The reconstruction
diagnoses sigma pressure from sigma centers and forecast surface pressure,
converts sigma-level temperature to dry potential temperature, interpolates theta
through the existing finite sigma-to-pressure path, converts it back to
temperature at the requested pressure levels, and samples the same moist
hydrostatic sigma geopotential profile on pressure levels. Winds, humidity,
surface pressure, mean sea-level pressure, 2 m temperature, and 10 m wind outputs
remain on the incumbent paths. Any nonfinite or nonpositive column diagnostic
falls back to the incumbent pressure-level temperature and geopotential fields.

The implementation was produced by the delegated Implementer worker before it
was shut down for lack of a final response; the Orchestrator reviewed the patch
and completed verification.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | ---: | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Syntax/import compile check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 134 passed in 126.75s. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_hydrostatic_output` | 0 | Primary `-0.5436511302724413`, `failed=False`, 0 issues, 120 records. |
| `uv run pytest` | 0 | 200 passed, 2 skipped in 134.56s. |

## Repair Attempts

- Failure observed: none during Orchestrator verification.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not applicable.
- Follow-up command and result: not applicable.

## Known Limitations

- The geopotential path remains a guarded sampling of the same moist sigma
  hydrostatic profile used by the incumbent, so the largest expected behavioral
  difference is pressure-level temperature reconstructed through dry theta.
- The candidate is output-only and does not change the prognostic trajectory.

## Rollback Notes

Revert this experiment by applying the archived
`.logbook/history/2026-06-21_18-05-20_theta-hydrostatic-pressure-output-reconstruction/candidate.diff`
in reverse after preserving score artifacts.
