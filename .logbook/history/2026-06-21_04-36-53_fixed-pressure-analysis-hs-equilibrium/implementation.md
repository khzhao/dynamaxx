# Implementation Record

## Identity

- Proposal slug: `fixed-pressure-analysis-hs-equilibrium`
- Candidate model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_fixed_p_hs_eq`
- Incumbent model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq`
- Baseline commit: `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`
- Candidate commit: not committed

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side candidate factory derived from the accepted analysis-offset Held-Suarez incumbent. The new model enables `use_fixed_pressure_weak_held_suarez_equilibrium`, which routes the weak Held-Suarez base equilibrium through a fixed reference surface pressure so the equilibrium pressure coordinate is `p / p0 = sigma`. The primitive-equation rollout, DFI, Coriolis split, theta tendency and recentering, scale-separated surface residuals, residual decay, output variables, and incumbent model factory remain unchanged.

The implementation adds a narrow option to `_TracerSafeHeldSuarezForcingSigma`, threads that option through weak-HS composition and analysis-offset construction, exports the candidate factory, and registers the candidate model name. Focused tests cover registry exposure, factory parity with the incumbent except for the new selector, and the fixed-pressure equilibrium's independence from local surface pressure.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py::test_fixed_pressure_analysis_hs_eq_factory_preserves_incumbent_except_selector tests/dycore/models/dinosaur/test_primitive_equations.py::test_fixed_pressure_hs_eq_ignores_surface_pressure_in_base_and_offset tests/dycore/models/dinosaur/test_dependency.py::test_dinosaur_fixed_pressure_analysis_hs_eq_is_registered tests/dycore/test_registry.py::test_registry_creates_fixed_pressure_analysis_hs_eq_candidate_model` | 0 | `4 passed` |
| `git diff --check` | 0 | No whitespace errors. |
| `python - <<'PY' ... create_dycore_model(candidate) ... PY` | 0 | Candidate imports, creates, and has both analysis-offset and fixed-pressure selectors enabled. |
| `uv run pytest` | not_run | Full suite reserved for Scorer gate. |
| `uv run dynamaxx-eval fast --model <candidate_model>` | not_run | Fixed scoring gates reserved for Scorer gate. |

## Repair Attempts

- Failure observed: none in focused implementation checks.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no candidate forecast gate has run yet.
- Fix attempted: none required.
- Follow-up command and result: not applicable.

## Known Limitations

- The implementation changes the base weak-HS equilibrium pressure coordinate and uses the same selector when constructing the analysis-offset term. The fixed evaluation gates will determine whether that is a useful distinction from the accepted local-pressure analysis-HS equilibrium.
- The candidate has not yet run the full test suite, fast gate, iteration gate, or validation gate.

## Rollback Notes

If rejected, revert the six changed source/test files listed above and remove the ready proposal file after preserving this history directory and raw evaluation outputs. Do not delete incumbent cached metrics or accepted leaderboard state.
