# Implementation Record

## Identity

- Proposal slug: dfi-theta-mean-recenter
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_dfi_theta
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
- Baseline commit: 54375ce2994827fcc2dfe09ce0df3924cbaa6c75
- Candidate commit: uncommitted worktree implementation; HEAD remains 54375ce2994827fcc2dfe09ce0df3924cbaa6c75

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-19_11-55-13_dfi-theta-mean-recenter/implementation.md

## Implementation Summary

Added `apply_theta_layer_mean_recentering_in_dfi`, defaulting to false, to keep incumbent behavior unchanged. The adapter still builds rollout filters and DFI filters separately; when `apply_theta_layer_mean_recentering` and the new selector are both true, the existing `_theta_layer_mean_recenter_step_filter` is appended to `dfi_filters`.

Registered the side-by-side candidate named above. Its factory matches the offcentered incumbent except for the candidate name and the new DFI-theta selector. The positive-time rollout filters remain horizontal diffusion plus theta recentering, and the offcentered SIL3 solver is still threaded into rollout and DFI.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python - <<'PY' ... candidate finite smoke ... PY` | pass | Tiny non-JIT candidate forecast with real DFI returned finite `(2, 1, 5, 4, 3)` output before adding the permanent smoke test. |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Edited Python files compiled. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 117 passed in 111.63s. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run pytest` | pass | 183 passed, 2 skipped in 120.28s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_dfi_theta` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.55807`; metrics JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_dfi_theta.json`. |

## Repair Attempts

- Failure observed: none in final executed tests or fast gate.
- Implementer-owned failure: no final failure; one accidental duplicate/stray test edit was caught during diff review and removed before test runs completed.
- NaN/Inf forecast observed: no.
- Fix attempted: restored the unintentionally touched local test chunks and removed the duplicate stubbed smoke test before final verification.
- Follow-up command and result: focused pytest, full pytest, `git diff --check`, and candidate fast gate all passed.

## Known Limitations

- The implementation is uncommitted, as requested.
- Fast gate was run only as a sanity check. Iteration, validation, and golden protocols were not run.
- No accept/reject scoring decision is made by the Implementer.

## Rollback Notes

Revert only the files listed above to remove this experiment. The incumbent offcentered model remains protected by the default-false selector and unchanged incumbent factory.
