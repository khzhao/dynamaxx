# Implementation Record

## Identity

- Proposal slug: virtual-theta-richardson-10m-wind
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_virtual_ri_wind
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

The candidate keeps the accepted analysis-Held-Suarez incumbent unchanged by default and registers a side-by-side model that enables one additional diagnostic selector. The selector passes sigma-level specific humidity into the existing surface-layer Richardson 10 m wind diagnostic so the stability term uses virtual potential temperature when humidity is finite and shape-compatible.

The humidity path is bounded to the diagnostic only. Specific humidity is clipped to 0.0 through 0.04 kg/kg, nonfinite lower or upper humidity falls back to the dry potential-temperature diagnostic per column, and absent or shape-incompatible humidity preserves the incumbent dry wind diagnostic exactly. Rollout dynamics, pressure-level outputs, 2 m temperature, MSLP, and geopotential diagnostics are not changed by this selector.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `git diff --check` | 0 | No whitespace errors. |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Candidate source and focused tests compile. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 134 passed in 123.18s. |
| `uv run pytest` | 0 | 200 passed, 2 skipped in 129.82s. |
| `uv run dynamaxx-eval fast --model <candidate_model>` | pending | Delegated to Scorer. |

## Repair Attempts

- Failure observed: none during orchestrator verification after the user's stash apply restored the candidate worktree.
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none after resuming the restored worktree.
- Follow-up command and result: not applicable.

## Known Limitations

- The candidate changes only the 10 m wind diagnostic; any score movement is expected to be concentrated in 10m wind and should be neutral for the other fixed variables.
- Validation must remain skipped unless the candidate first clears iteration promotion gates.

## Rollback Notes

If rejected, revert only the six source and test files listed above to `HEAD`. Preserve this history directory and raw evaluation outputs for reproducibility.
