# Implementation Record

## Identity

- Proposal slug: helmholtz-projected-momentum-diffusion
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
- Baseline commit: 6094c73fe9b98b46c3ac9bfbb430bafd332d628f
- Candidate commit: uncommitted worktree candidate

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate registers a side-by-side model that keeps the accepted analysis-Held-Suarez incumbent unchanged by default and enables one additional positive-time filter selector. When enabled, the rollout and DFI filter list use an adapter-local Helmholtz-projected momentum diffusion filter instead of the incumbent scalar-tree diffusion filter.

The filter still applies incumbent scalar horizontal diffusion to non-momentum leaves: `temperature_variation`, `log_surface_pressure`, tracers, and `sim_time`. For momentum, it reconstructs nodal vector wind from vorticity/divergence, applies the same diffusion scale and order to modal `u` and `v`, converts the diffused wind back to vorticity/divergence, and emits only those projected momentum leaves. If the projected path is nonfinite or increases mean wind energy beyond a small roundoff tolerance, it falls back to the incumbent scalar-filtered vorticity/divergence.

No forecast inputs, returned variables, lead handling, fixed metrics, splits, DFI protocol, weak-Held-Suarez forcing, theta recentering, residual memory, or output diagnostics were changed.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Candidate source and focused tests compile. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 134 passed after fixing a test-only deferred construction issue. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_helmholtz_momentum_diffusion` | 0 | Initial run produced nonfinite forecast metrics; after bounded guard repair, final primary -0.5307152780364869 with clean diagnostics and 0 issues. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run pytest` | 0 | 200 passed, 2 skipped in 129.84s. |

## Repair Attempts

- Failure observed: first fast evaluation emitted null metrics and sentinel primary score due to nonfinite forecast behavior.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: yes, through fast evaluation metrics.
- Fix attempted: added a finite projection guard and a bounded mean wind-energy guard that falls back to incumbent scalar-filtered momentum when projected vector diffusion is unsafe.
- Follow-up command and result: final `uv run dynamaxx-eval fast --model <candidate>` exited 0 with primary -0.5307152780364869, failed false, and 0 issues.

## Known Limitations

- The fallback guard can make the candidate locally identical to incumbent scalar momentum diffusion when projected vector diffusion is unsafe or non-dissipative.
- The fast score is clean but negative; promotion depends entirely on the fixed iteration gate.
- Validation must remain skipped unless the candidate first clears iteration promotion gates.

## Rollback Notes

If rejected, revert only the six source and test files listed above to `HEAD`. Preserve this history directory and raw evaluation outputs for reproducibility.
