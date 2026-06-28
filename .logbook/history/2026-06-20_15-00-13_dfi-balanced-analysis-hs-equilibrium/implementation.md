# Implementation Record

## Identity

- Proposal slug: dfi-balanced-analysis-hs-equilibrium
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_dfi_hs_eq
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
- Baseline commit: 6094c73fe9b98b46c3ac9bfbb430bafd332d628f
- Candidate commit: not committed

## Files Changed

- src/dynamaxx/dycore/models/dinosaur/adapter.py
- src/dynamaxx/dycore/models/dinosaur/__init__.py
- src/dynamaxx/dycore/registry.py
- tests/dycore/models/dinosaur/test_primitive_equations.py
- tests/dycore/models/dinosaur/test_dependency.py
- tests/dycore/test_registry.py
- .logbook/history/2026-06-20_15-00-13_dfi-balanced-analysis-hs-equilibrium/implementation.md

## Implementation Summary

Added a default-false `use_dfi_balanced_analysis_offset_weak_held_suarez_equilibrium` selector on `DinosaurPrimitiveEquationsDycoreModel`. The accepted raw analysis-offset path remains the default whenever that selector is false.

Registered one side-by-side factory derived from `analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model()`. The candidate differs from the incumbent only by model name and the new selector.

Factored trajectory construction so DFI initialization can be built separately from positive-time rollout. In the new candidate path, the model computes the raw analysis-HS offset for the accepted DFI initialization, applies DFI once, computes the same bounded low-mode analysis-HS offset from the DFI-balanced state, and starts positive-time rollout from that same balanced state without a second DFI pass. If the balanced state or balanced offset is nonfinite, the path rolls out the already-computed DFI-balanced state with the incumbent raw offset, preserving the raw-offset fallback behavior and forecast shape.

The offset cap, low-mode mask, weak-HS rates, DFI parameters, theta tendency, theta mean recentering, off-centered SIL3, Coriolis Strang split, scale-separated surface residuals, output diagnostics, and forecast contract were not changed.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 133 passed in 140.94s |
| `uv run pytest` | pass | 199 passed, 2 skipped in 146.73s |
| `git diff --check` | pass | no whitespace errors |
| registry/import equivalence check using `create_dycore_model(candidate_name)` | pass | candidate resolves and differs from incumbent only by `name` and `use_dfi_balanced_analysis_offset_weak_held_suarez_equilibrium` |
| `uv run dynamaxx-eval fast --model <candidate>` | not run | optional only; skipped to avoid writing protected `outputs/eval` artifacts during implementation |

## Repair Attempts

- Initial focused pytest failure: the new balanced-offset test combined a nodal clipping assertion with a strict spectral high-mode-zero assertion. Because physical-space clipping can reintroduce high modes, the test was split into separate compatible cap and low-mode-mask checks.
- Diff hygiene repair: an initial targeted formatter run introduced unrelated formatting churn in allowed source and test files. Those unrelated formatting edits were restored manually so the final diff stays scoped to the selected proposal.
- Implementation-owned NaN/Inf forecast issue: none observed in local smoke tests.

## Known Limitations

- No fast, iteration, validation, or golden scoring was run by the Implementer.
- The candidate uses local unit and smoke coverage only. Scoring can start with the fixed fast/iteration protocol from the Scorer.
