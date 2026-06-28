# Implementation Record

## Identity

- Proposal slug: `mass-weighted-theta-recentering`
- Candidate model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_mass_weighted`
- Incumbent model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq`
- Baseline commit: `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`
- Candidate commit: none; rejected candidate was evaluated from the working tree.

## Files Changed

- Path: `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- Path: `src/dynamaxx/dycore/registry.py`
- Path: `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Path: `tests/dycore/models/dinosaur/test_dependency.py`
- Path: `tests/dycore/test_registry.py`

## Implementation Summary

The candidate added a side-by-side Dinosaur model that preserved the incumbent
DFI, weak Held-Suarez, exact Coriolis, semi-implicit offcentering,
scale-separated near-surface residual, and analysis-HS equilibrium settings.
The only model selector changed was the theta recentering weighting: the
candidate used quadrature weights multiplied by sigma-layer thickness and local
surface pressure instead of area weights when preserving the rollout-only layer
theta moment.

The implementation registered and exported the `_mass_weighted` candidate and
added focused tests for factory parity, registry exposure, non-JIT finite
forecast behavior, mass-weighted theta preservation, area-vs-mass distinction,
zero-mode-only temperature edits, non-temperature state preservation, and DFI
exclusion.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q ...` | 0 | Implementer compile sanity check over changed modules. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -q -k "mass_weighted or theta_layer_mean_recenter or trajectory_function_applies_mass_weighted"` | 1 | Initial focused failure; Implementer repaired lazy analysis-HS test setup. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -q -k "mass_weighted or theta_layer_mean_recenter or trajectory_function_applies_mass_weighted"` | 0 | Focused retest passed. |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py -q` | 0 | Registry/export tests passed. |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py -q` | 0 | Focused dycore suite passed: 133 passed. |
| `uv run pytest` | 0 | Full repository suite passed: 199 passed, 2 skipped in 150.33s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_mass_weighted` | 0 | Candidate fast gate passed with score `-0.5313481378897001`, failed=`false`, issues=0. |

## Repair Attempts

- Failure observed: initial focused pytest failure in the mass-weighted and theta-recenter test subset.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: adjusted the test setup for the lazy analysis-HS trajectory path while preserving the selected implementation scope.
- Follow-up command and result: focused pytest, registry/dependency pytest, and the full dycore focused suite passed.

## Known Limitations

- The candidate was not committed because it failed iteration promotion.
- Validation was not run because the candidate iteration delta was negative.
- No fixed evaluation protocol, metric, target variable, split, or lead setting was changed.

## Rollback Notes

Revert only the six files listed under `Files Changed`. Preserve this history
directory and the raw `outputs/eval/fast_*_mass_weighted.*` and
`outputs/eval/iteration_*_mass_weighted.*` artifacts.
