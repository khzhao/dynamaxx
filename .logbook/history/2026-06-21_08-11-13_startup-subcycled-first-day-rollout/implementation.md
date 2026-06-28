# Implementation Record

## Identity

- Proposal slug: `startup-subcycled-first-day-rollout`
- Candidate model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_startup_subcycle`
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

The implementation added an opt-in `apply_startup_subcycling` flag and one
side-by-side `_startup_subcycle` registry entry derived from the incumbent.
For the candidate only, the positive-time rollout used half-size inner steps
during the startup window and then returned to the incumbent step schedule for
later saved leads. DFI remained on the incumbent timestep and solver path. The
trajectory helper included finite fallback to the incumbent first-day path when
the startup-subcycled first-day prefix or endpoint was nonfinite.

The incumbent model factory, default model behavior, forecast API, lead
indexing, target variables, metrics, and fixed evaluation protocols were not
changed.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore` | 0 | Implementer compile gate passed. |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py -k "startup_subcycle or startup_subcycled or default_dinosaur_configuration_keeps_t80_with_stable_inner_step or analysis_offset_hs_eq_factory_preserves_incumbent_except_selector"` | 0 | Focused startup/registry tests passed after a test-only repair. |
| `uv run pytest tests/dycore/test_registry.py` | 0 | 19 passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py` | 0 | 18 passed. |
| `uv run pytest` | 0 | Orchestrator full gate: 201 passed, 2 skipped in 148.60s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_startup_subcycle` | 0 | Implementer and Scorer fast gates passed with clean diagnostics. Scorer primary score: `-0.5445913579727705`. |

## Repair Attempts

- Failure observed: focused pytest initially failed because a test-only DFI
  observation path did not account for lazy trajectory construction.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: repaired the focused test setup and reran the selected tests.
- Follow-up command and result: focused pytest passed with 10 selected tests.
- Orchestrator review repair: tightened finite fallback so any nonfinite
  startup prefix frame as well as the day-one endpoint selects the incumbent
  startup path.

## Known Limitations

- The candidate did not reach validation because the fixed iteration gate
  failed.
- The candidate adds trajectory complexity for a mechanism that empirically
  worsened early mean sea level pressure under the iteration split.

## Rollback Notes

Rollback is the reverse of `candidate.diff` over the six changed source/test
files. Rejected code was not committed and should not update the leaderboard.
