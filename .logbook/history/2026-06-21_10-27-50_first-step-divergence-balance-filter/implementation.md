# Implementation Record

## Identity

- Proposal slug: `first-step-divergence-balance-filter`
- Candidate model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter`
- Incumbent model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq`
- Baseline commit: `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`
- Candidate commit: not committed; rejected candidate measured from the worktree diff saved in `candidate.diff`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

The implementation added an opt-in `apply_first_step_divergence_filter` flag
and one side-by-side `_first_step_div_filter` registry entry. For the candidate
only, the positive-time trajectory wrapper applied a fixed high-wavenumber
taper to the first modal divergence increment relative to the post-DFI initial
state. Vorticity, temperature variation, log-surface pressure, tracers,
`sim_time`, DFI, weak-HS forcing, exact Coriolis split, theta recentering,
surface residuals, later steps, output variables, lead indexing, and the
forecast API remained on the incumbent path.

The taper preserved low total wavenumbers and weakly attenuated only the high
tail. Finite and shape fallbacks returned the raw incumbent first-step state.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore` | 0 | Implementer compile gate passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Implementer focused gate passed with 117 tests after a test assertion repair. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Orchestrator focused gate passed with 134 tests after adding dependency coverage. |
| `uv run pytest` | 0 | Orchestrator full gate: 200 passed, 2 skipped in 131.31s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_first_step_div_filter` | 0 | Scorer fast gate passed with primary score `-0.5305863627049654`, no diagnostics. |

## Repair Attempts

- Failure observed: implementer focused pytest initially failed due to a test
  expectation issue.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: corrected the test assertion and reran focused tests.
- Orchestrator-owned repair: full pytest exposed missing dependency-test
  coverage for the new registry entry; the dependency expected tuple and import
  assertion were updated and rerun.

## Known Limitations

- The candidate was essentially neutral in RMSE guardrails but did not improve
  primary score enough to reach validation.
- Filtering divergence alone did not produce a useful score signal, reinforcing
  local negative evidence from earlier divergence-family experiments.

## Rollback Notes

Rollback is the reverse of `candidate.diff` over the six changed source/test
files. Rejected code was not committed and should not update the leaderboard.
