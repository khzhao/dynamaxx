# Implementation Record

## Identity

- Proposal slug: hypsometric-thickness-hs-offset
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_thickness_hs_eq
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

## Implementation Summary

Added a side-by-side Dinosaur candidate that preserves the accepted analysis-HS
incumbent behavior except for the source of the weak Held-Suarez equilibrium
temperature offset. The candidate computes a pressure-level hypsometric
thickness temperature from the single initial analysis, maps that state through
the existing Dinosaur initialization path, and threads the resulting bounded
low-mode offset into both DFI and positive-time rollout forcing.

The helper falls back to the accepted incumbent analysis-HS offset when
pressure-level geopotential is missing, shape-incompatible, or nonfinite. The
candidate does not change the forecast API, output variables, pressure-level
output interpolation, evaluation protocols, metrics, or data splits.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Implementer compile check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Focused tests passed: 134 passed. |
| `uv run pytest` | 0 | Full suite passed: 200 passed, 2 skipped in 135.44s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_thickness_hs_eq` | 0 | Fast primary score -0.5306894176832982; diagnostics clean. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: none during implementation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not applicable.
- Follow-up command and result: not applicable.

## Known Limitations

- The valid-source test path is expected to be close to incumbent behavior
  because the incumbent already uses hydrostatic layer initialization before
  computing the accepted analysis-HS offset.
- This experiment tests only the offset source. It intentionally does not add
  new tuning constants or validation-informed choices.

## Rollback Notes

Revert this experiment's source and test changes with
`git apply -R .logbook/history/2026-06-21_19-52-48_hypsometric-thickness-hs-offset/candidate.diff`
if the candidate is rejected. Keep the history artifacts.
