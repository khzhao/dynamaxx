# Implementation Record

## Identity

- Proposal slug: zonal-mean-weak-hs-relaxation
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
- Baseline commit: ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-20_09-03-16_zonal-mean-weak-hs-relaxation/implementation.md

## Implementation Summary

Added a default-off `use_zonal_mean_weak_held_suarez_relaxation` selector to the
Dinosaur primitive-equation adapter. Existing factories, including the incumbent
scale-separated residual factory, keep the selector false.

The weak Held-Suarez forcing wrapper now exposes the incumbent local nodal
temperature tendency calculation as a shared helper. The new zonal-mean wrapper
computes that same local nodal tendency, averages it over longitude at each
sigma layer and latitude, broadcasts it back over longitude, converts the result
to modal space, and emits zero vorticity, divergence, log-surface-pressure, and
tracer tendencies. If the zonal-mean broadcast is nonfinite, the wrapper falls
back to the local incumbent weak-HS tendency.

Registered the side-by-side candidate factory
`zonal_mean_weak_held_suarez_dinosaur_dycore_model()` based on
`scale_separated_surface_residual_dinosaur_dycore_model()`. The candidate
changes only the model name and the zonal-mean weak-HS selector, preserving DFI,
Strang Coriolis splitting, offcentered SIL3, theta tendency/recentering,
Richardson 10 m wind diagnostics, and scale-separated near-surface residual
memory.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | failed, then pass | First run failed one new assertion comparing projected nodal output to the unprojected nodal longitude mean. After repair, 125 passed in 108.27s. |
| `uv run pytest` | pass | 191 passed, 2 skipped in 115.20s. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs` | not_run | Reserved for Scorer; no model-selection evals were run by the Implementer. |

## Repair Attempts

- Failure observed: the initial targeted pytest run failed
  `test_zonal_mean_weak_held_suarez_matches_local_longitude_mean`.
- Implementer-owned failure: yes; the implementation converts the zonal-mean
  nodal field to modal space, so converting the modal result back to nodal
  applies the grid's spectral projection in latitude.
- NaN/Inf forecast observed: no.
- Fix attempted: changed the test to compare the candidate modal tendency with
  `to_modal(longitude_mean(local_nodal_tendency))`, while keeping a separate
  longitude-constancy check on the projected nodal tendency.
- Follow-up command and result: the targeted pytest command passed with
  125 tests passing; the full pytest suite and `git diff --check` also passed.

## Known Limitations

- Fast, iteration, validation, and golden evals were not run by the Implementer.
- The scientific impact is unscored; the Scorer must run the fixed gates.
- The emitted modal tendency represents the zonal-mean nodal source through the
  existing Dinosaur spectral projection, so nodal reconstruction is the grid's
  projected zonal-mean tendency rather than an arbitrary-latitude exact copy.

## Rollback Notes

If rejected, revert only the seven changed files listed above. The incumbent
model key
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual`
should remain registered and unchanged. Preserve this history directory and any
Scorer-produced evaluation artifacts unless the Orchestrator explicitly requests
cleanup.
