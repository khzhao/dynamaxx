# Implementation Record

## Identity

- Proposal slug: seasonal-stability-surface-residual-decay
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_seasonal_stability_surface_residual
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
the accepted scale-separated surface-residual incumbent. It remains output-only
and changes only the low-mode `2m_temperature` residual decay. The seasonal and
static-stability gate uses initialization time, latitude, and lower-column
temperature stability when available; otherwise it falls back to the accepted
scale-separated residual decay.

High-mode `2m_temperature`, all `10m_u_component_of_wind` residual handling,
lead-zero exactness, pressure/mass diagnostics, and non-corrected variables stay
on the incumbent behavior.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_primitive_equations.py` | passed | 123 tests passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_seasonal_stability_surface_residual` | passed | Fast diagnostics clean, failed=false, issues=0, primary_score approximately -0.566013. |

## Repair Attempts

- Failure observed: none.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: one cleanup preserved incumbent non-stability broadcast shape.
- Follow-up command and result: focused pytest and fast sanity both passed.

## Known Limitations

- Iteration and validation scores were not produced by the Implementer; those are delegated to the Scorer.
- Constants are fixed and intentionally not tuned.
- If seasonal metadata or lower-column temperature stability is unavailable, the candidate falls back to the incumbent scale-separated low-mode decay.

## Rollback Notes

If rejected, revert the six implementation files listed above to the baseline
commit while preserving this history directory and raw candidate evaluation
outputs under `outputs/eval/`.
