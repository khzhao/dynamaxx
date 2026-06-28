# Implementation Notes

## Baseline

- Baseline commit before implementation: `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`
- Candidate commit: not committed; implementation remains in the working tree.

## Candidate Model

`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_var_guard`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-20_12-57-53_baroclinic-theta-variance-guard/implementation.md`

## Summary

Implemented the selected theta-variance guard as a side-by-side Dinosaur dycore candidate derived from `analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model()`.

The new default-false selector is `DinosaurPrimitiveEquationsDycoreModel.apply_theta_variance_guard`. When enabled with the existing theta layer mean recentering path, the rollout filter:

- computes dry potential temperature from previous and candidate next states;
- preserves the already-corrected layerwise mean dry theta;
- detects layerwise horizontal theta-anomaly variance drops beyond a fixed tolerance;
- applies a fixed nonzero-mode low-to-synoptic spectral taper to the next theta anomaly;
- caps per-step temperature increments and uses finite no-op fallbacks.

The guard is appended only to positive-time rollout filters after `_theta_layer_mean_recenter_step_filter`. DFI filters and incumbent default behavior remain unchanged.

## Tests And Checks

- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "theta_variance_guard or default_dinosaur_configuration or trajectory_function_applies_theta_recenter" tests/dycore/test_registry.py -k "theta_variance_guard or lists_default" tests/dycore/models/dinosaur/test_dependency.py -k "theta_variance_guard or canonical"`: passed, 10 passed.
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: passed, 136 passed.
- `uv run pytest`: passed, 202 passed, 2 skipped.
- `git diff --check`: passed.
- `uv run python -c "from dynamaxx.dycore.registry import create_dycore_model; name='dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_var_guard'; model=create_dycore_model(name); assert model.name == name; assert model.apply_theta_variance_guard; print(model.name)"`: passed; `create_dycore_model(candidate_name)` resolves and sets `apply_theta_variance_guard`.
- Optional sanity: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_var_guard`: passed with `failed=False`, `issues=0`, `records=120`, `primary_score=-0.530705`.

## Repair Attempts

- Adjusted the trajectory assembly test to invoke the analysis-HS lazy trajectory path before asserting rollout and DFI filter lists.

## Known Limitations

- The guard uses fixed, untuned constants for the variance-drop tolerance, spectral taper, variance floor, maximum scale, and per-step temperature increment cap.
- The correction only amplifies the selected tapered next-state anomaly band; if that band has near-zero variance, the finite floor makes the guard a no-op for that layer.
- No iteration, validation, or golden scoring was run by the Implementer.
