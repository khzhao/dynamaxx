# Implementation Record

## Identity

- Proposal slug: offcentered-semi-implicit-gravity-wave
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
- Baseline commit: 8ead91209dfbd2abc3ffc31082653cf29aa962dd
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/time_integration.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/implementation.md

## Implementation Summary

Implemented the selected side-by-side candidate by adding an optional
`implicit_offcentering` keyword to `time_integration.imex_rk_sil3`. The default
`0.0` path returns the original centered SIL3 tableau step. Positive values
build a row-sum-preserving implicit tableau variant by moving a fixed weight
from previous implicit coefficients onto the current-stage diagonal coefficient,
including the stiffly accurate final implicit row. The offcentered step is
locally guarded: if it emits any nonfinite state leaf, the same call falls back
to the centered SIL3 step.

Added `semi_implicit_offcentering` to the Dinosaur adapter with default `0.0`.
The incumbent therefore keeps passing the original `time_integration.imex_rk_sil3`
function object. The candidate factory sets the fixed proposal value `0.05` and
uses a local keyword-bound solver for both positive rollout and DFI. Explicit
terms, forcing, RK explicit coefficients, filters, inner step length, theta mean
recentering, residual correction, and output packing were left unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "imex_rk_sil3 or semi_implicit_offcenter or threads_offcentered" tests/dycore/test_registry.py -k "semi_implicit_offcenter or lists_default" tests/dycore/models/dinosaur/test_dependency.py -k "semi_implicit_offcenter or imports_without_external or canonical"` | 0 | Passed 6 selected tests; superseded by the corrected combined-filter run. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py -k "imex_rk_sil3 or semi_implicit_offcenter or threads_offcentered or lists_default or imports_without_external or canonical"` | 0 | Passed 11 selected tests. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Passed 111 tests. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run pytest` | 0 | Passed 177 tests, skipped 2. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.557905`; metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter.json`. |

## Repair Attempts

- Failure observed: none.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none required.
- Follow-up command and result: not applicable.

## Known Limitations

- Limitation: no iteration, validation, or golden evaluation was run by the Implementer role.
- Limitation: the candidate remains uncommitted, as requested.

## Rollback Notes

Revert the source and test changes listed above, remove the candidate registry
entry and package export, and remove this implementation record if the
Orchestrator rejects this experiment. The generated fast metrics artifact under
`outputs/eval/` can be removed separately if the Orchestrator wants evaluation
outputs cleaned up.
