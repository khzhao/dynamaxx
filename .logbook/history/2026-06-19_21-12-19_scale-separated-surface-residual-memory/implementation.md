# Implementation Record

## Identity

- Proposal slug: scale-separated-surface-residual-memory
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
- Baseline commit: 54375ce2994827fcc2dfe09ce0df3924cbaa6c75
- Candidate commit: ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-19_21-12-19_scale-separated-surface-residual-memory/implementation.md

## Implementation Summary

Added a side-by-side Dinosaur candidate factory and registry entry for
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual`.
The incumbent registry key and default residual correction path are unchanged
unless the new `use_scale_separated_near_surface_residual` selector is true.

For the candidate, initial residuals for the existing corrected channels
`2m_temperature` and `10m_u_component_of_wind` are transformed through the
existing Dinosaur horizontal spherical harmonic grid in model latitude order.
A fixed low-mode mask preserves total wavenumber `n <= 12`, applies a cosine
taper, and is zero by `n >= 20`. The high-mode residual is the gridpoint
remainder, so low plus high reconstructs the original residual within transform
tolerance. Low modes use a fixed 96 hour base memory scaled by the incumbent
stability-aware local multiplier, while high modes use the incumbent
stability-aware decay capped by the existing 72 hour maximum. Lead-zero outputs
for corrected channels are still replaced by the initial analysis values.

If the spectral split is unavailable, shape-incompatible, or nonfinite, the
candidate falls back to the incumbent residual correction. Non-corrected output
channels are not modified by the new helper.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | No syntax errors. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k "scale_separated or dinosaur_imports_without_external_dinosaur_package"` | pass | 8 passed, 110 deselected. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 118 passed. |
| `uv run pytest` | pass | 184 passed, 2 skipped. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.519179`; metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json` and `.csv`. |

## Repair Attempts

- Failure observed: none.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none required.
- Follow-up command and result: not applicable.

## Known Limitations

- Iteration, validation, and golden protocols were not run by the Implementer.
- The candidate was accepted and committed as ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6.
- The spectral split adds initialization-time spherical harmonic transforms for
  the two corrected near-surface channels, but it remains output-only and does
  not feed back into the prognostic trajectory.

## Rollback Notes

Revert only the changes in the files listed above. The incumbent model key
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter`
should remain registered and unchanged. Generated fast-eval artifacts under
`outputs/eval/` are ignored by git and can be left for scorer inspection unless
the Orchestrator requests cleanup.
