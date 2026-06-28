# Implementation Record

## Identity

- Proposal slug: exponential-integrator-newtonian-relaxation
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_exprelax
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
- Baseline commit: 681fe7c0d37fadbc1a91159a8d9a7f9f2543f185
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/time_integration.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Added a side-by-side Dinosaur candidate that starts from the accepted land-sea
incumbent and opt-in wraps the weak Held-Suarez thermal relaxation in an exact
Strang-style exponential update. The incumbent explicit-HS path remains the
default and is retained as a nonfinite fallback for the candidate step.

The candidate builds the primitive-equation dynamics with weak-HS explicit
terms disabled, applies exact half-step weak-HS relaxation before and after the
dynamics step, and uses precomposed forward/backward step functions so DFI uses
the same exact-relaxation treatment. A small
`digital_filter_initialization_from_steps` helper was added to avoid changing
the public forecast contract or fixed evaluation protocols.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Implementer compile check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Focused tests passed: 142 passed. |
| `uv run pytest` | 0 | Full suite passed: 208 passed, 2 skipped in 145.95s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_exprelax` | 0 | Fast primary score -0.5144139357247745; diagnostics failed false; issues 0; records 120. |
| `git diff --check` | 0 | Implementer reported no whitespace errors. |

## Repair Attempts

- Failure observed: two initial focused-test failures in new exact-relaxation
  tests due to modal truncation in synthetic expected values.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: corrected test expectations to compare against the actual
  nodal state after modal reconstruction.
- Follow-up command and result: focused pytest, candidate fast, `git diff
  --check`, and full pytest all passed after the repair.

## Known Limitations

- The incumbent weak-HS forcing subclass is currently thermal-only in explicit
  tendencies because the accepted weak-HS path sets `kf_per_day=0.0`. The exact
  wrapper includes drag support for nonzero `kf`, but this registered candidate
  changes only thermal relaxation in practice.
- Fast primary score was worse than the incumbent fast score, but fast is a
  sanity gate only; iteration is required for candidate promotion.

## Rollback Notes

Revert this experiment's source and test changes with
`git apply -R .logbook/history/2026-06-22_03-19-03_exponential-integrator-newtonian-relaxation/candidate.diff`
if the candidate is rejected. Keep the history artifacts and raw evaluation
outputs.
