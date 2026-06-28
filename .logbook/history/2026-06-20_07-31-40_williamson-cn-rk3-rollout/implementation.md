# Implementation Record

## Identity

- Proposal slug: williamson-cn-rk3-rollout
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_cn_rk3_rollout
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

## Implementation Summary

Implemented a side-by-side Dinosaur candidate that uses the existing `time_integration.crank_nicolson_rk3` routine only for positive-time rollout. The adapter now has a default `rollout_time_integrator` selector that preserves the incumbent SIL3 path unless explicitly changed. The candidate factory is based on the accepted scale-separated residual incumbent and changes only the model name plus the rollout selector.

Digital-filter initialization remains on the incumbent SIL3 solver with the accepted off-centering. The patch does not change the CN-RK3 or SIL3 solver implementations, forecast inputs, forecast outputs, target variables, metrics, lead schedule, residual memory, weak-HS forcing, Strang Coriolis split, theta tendency/recentering, or evaluation protocols.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Implementer reported 123 passed. |
| `uv run pytest` | 0 | Implementer reported 189 passed, 2 skipped. |
| `git diff --check` | 0 | Passed after implementation. |
| `uv run dynamaxx-eval fast --model <candidate_model>` | not_run | Reserved for Scorer fixed gates. |

## Repair Attempts

- Failure observed: none.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not applicable.
- Follow-up command and result: targeted pytest, full pytest, and diff check passed.

## Known Limitations

- The candidate removes off-centered SIL3 damping from positive-time rollout, which may hurt fast-mode stability or guardrails even though DFI remains unchanged.

## Rollback Notes

If rejected, revert only the six changed source/test files listed above and remove the selected proposal from `.logbook/research/ready`; preserve this history directory and raw evaluation outputs.
