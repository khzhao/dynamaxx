# Implementation Record

## Identity

- Proposal slug: coherent-u-residual-gate
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_u_residual_coherence_gate
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

Added an opt-in u10 residual coherence gate on top of the accepted
analysis-HS incumbent. The candidate leaves the raw Richardson 10 m wind
diagnostic, trajectory, pressure-level outputs, mass fields, and non-u residual
paths unchanged. It computes same-time lower-column u-wind coherence from the
Dinosaur trajectory and applies a bounded factor only to the
`10m_u_component_of_wind` residual before the existing scale-separated residual
split and lead decay.

The candidate preserves requested lead-zero exactness by retaining the existing
lead-zero overwrite with the analyzed initial state. Missing,
shape-incompatible, or nonfinite coherence inputs return the ungated incumbent
scale-separated residual path.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Implementer compile check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Focused tests passed: 133 passed. |
| `uv run pytest` | 0 | Full suite passed: 199 passed, 2 skipped in 131.38s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_u_residual_coherence_gate` | 0 | Fast primary score -0.5306239565147497; diagnostics clean. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: none reported after final implementation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not applicable.
- Follow-up command and result: not applicable.

## Known Limitations

- The coherence gate uses fixed, simple bounded constants and is not tuned
  beyond the proposal.
- The gate only dampens u10 residual memory; it cannot correct raw 10 m wind
  diagnostic errors or trajectory wind errors.

## Rollback Notes

Revert this experiment's source and test changes with
`git apply -R .logbook/history/2026-06-21_21-39-17_coherent-u-residual-gate/candidate.diff`
if the candidate is rejected. Keep the history artifacts and raw evaluation
outputs.
