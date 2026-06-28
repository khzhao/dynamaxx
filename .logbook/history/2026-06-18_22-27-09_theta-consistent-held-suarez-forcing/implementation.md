# Implementation Record

## Identity

- Proposal slug: theta-consistent-held-suarez-forcing
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_hs
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
- Baseline commit: cb5bbd1c15744b4fc00ecca5de78da188685a33d
- Candidate commit: not created by Implementer

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_22-27-09_theta-consistent-held-suarez-forcing/implementation.md

## Implementation Summary

Added a default-off `use_potential_temperature_held_suarez_relaxation` selector
to `DinosaurPrimitiveEquationsDycoreModel` and threaded it into the existing
weak Held-Suarez composition path. The default forcing path still computes the
incumbent temperature-space nodal tendency.

When the selector is enabled, `_TracerSafeHeldSuarezForcingSigma` diagnoses
sigma-layer pressure as `sigma * exp(log_surface_pressure)`, converts current
temperature and the unchanged Held-Suarez equilibrium temperature to dry
potential temperature using the existing primitive-equation conversion helpers,
relaxes theta with the unchanged `kt()` coefficient, and converts the resulting
theta tendency back to temperature tendency at local pressure. If the pressure,
theta, or converted tendency diagnostics are nonfinite, the wrapper returns the
incumbent temperature-space tendency for that forcing call. Vorticity,
divergence, log-surface-pressure, and tracer tendencies remain zero.

Registered the side-by-side candidate factory
`theta_held_suarez_dinosaur_dycore_model()` and the requested registry name
without changing the incumbent factory behavior or forecast contract.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `git diff --check` | 0 | Passed before and after focused repair. |
| `python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Syntax check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 1 | First focused run failed in two new synthetic forcing tests. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Rerun passed: 103 passed. |
| `uv run pytest` | 0 | Passed: 169 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_hs` | 0 | Passed: failed=False, issues=0, records=120, primary_score=-0.800824. |

## Repair Attempts

- Failure observed: the first focused pytest run failed because the no-op
  equilibrium test built an analytic Held-Suarez equilibrium field that was not
  exactly preserved by the small spectral transform round-trip.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: changed the synthetic test to pin the local equilibrium target
  exactly to the current nodal temperature so it tests the forcing branch rather
  than spectral projection error.
- Follow-up command and result: focused pytest rerun passed with 103 passed.

- Failure observed: the first focused pytest run failed because the fallback
  stress value overflowed the incumbent temperature-space tendency as well as
  the theta diagnostics.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: reduced the synthetic stress temperature so theta diagnostics
  are nonfinite while the incumbent fallback tendency remains finite.
- Follow-up command and result: focused pytest rerun passed with 103 passed.

## Known Limitations

- The opt-in forcing path adds local pressure and theta conversions inside the
  weak-HS wrapper but does not change weak-HS coefficients, equilibrium formula,
  DFI span, transport, diffusion, output variables, or evaluation protocols.
- The finite-diagnostic fallback is whole-call rather than gridpoint-local,
  matching the existing guarded theta-tendency pattern in the primitive
  equations.
- Since current temperature and equilibrium temperature are converted at the
  same local pressure before converting the tendency back, finite-state behavior
  may be very close to temperature-space relaxation. The fixed scoring gates
  should determine whether any implementation-level differences matter.
- Iteration, validation, golden, leaderboard updates, commits, and
  accept/reject decisions were not performed by the Implementer.

## Rollback Notes

If rejected, revert the new model factory, registry entry, package export,
default-off selector, theta-space branch in `_TracerSafeHeldSuarezForcingSigma`,
focused tests added for this candidate, and this implementation record. Do not
revert unrelated accepted dycore history or raw evaluation outputs.
