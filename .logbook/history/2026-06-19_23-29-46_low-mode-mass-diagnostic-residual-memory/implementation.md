# Implementation Record

## Identity

- Proposal slug: low-mode-mass-diagnostic-residual-memory
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
- Baseline commit: ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6
- Candidate commit: not available before acceptance; candidate is the current uncommitted worktree.

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate adds a side-by-side Dinosaur factory and registry key on top of
the accepted scale-separated surface-residual incumbent. It preserves the
prognostic rollout and near-surface residual path, then applies an output-only
low-wavenumber residual correction to `mean_sea_level_pressure` and
`geopotential_500` when both the initial analysis channel and the raw lead-zero
Dinosaur diagnostic are available. The mass residual path uses fixed low-mode
spectral masks, channel-specific decays, lead-zero exactness, a norm cap, and
channel-local fallback to the incumbent output on incompatible or nonfinite
transforms.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "low_mode_mass or scale_separated_residual_mask or scale_separated_residual_split"` | passed | 8 tests passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | 35 tests passed. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | passed | Initial formatting/import-order findings were repaired, then the command passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_primitive_equations.py` | passed | 126 tests passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual` | passed | Fast diagnostics clean, failed=false, issues=0, primary_score=-0.54726. |

## Repair Attempts

- Failure observed: Ruff reported import ordering and one extra blank line in touched files.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: formatting-only cleanup.
- Follow-up command and result: Ruff passed after cleanup; full focused pytest passed.

## Known Limitations

- Iteration and validation scores were not produced by the Implementer; those are delegated to the Scorer.
- The candidate is output-only, so it cannot correct dynamical mass-field phase errors that are not well represented by lead-zero low-mode diagnostic residuals.

## Rollback Notes

If rejected, revert the six implementation files listed above to the baseline
commit while preserving this history directory and raw candidate evaluation
outputs under `outputs/eval/`.
