# Implementation Record

## Identity

- Proposal slug: theta-skew-symmetric-scalar-advection
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_skew_scalar_adv
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
- Baseline commit: cb5bbd1c15744b4fc00ecca5de78da188685a33d
- Candidate commit: not committed by Implementer

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_20-37-51_theta-skew-symmetric-scalar-advection/implementation.md

## Implementation Summary

Added a default-off `scalar_advection_formulation` selector to `PrimitiveEquationsSigma`. The default `product_rule` branch returns the existing `scalar * divergence` plus modal `-div_sec_lat(u * scalar, v * scalar, grid)` path exactly. The opt-in `skew_symmetric` branch computes a direct advective-gradient nodal tendency by converting the nodal scalar to modal space, using `coords.horizontal.cos_lat_grad(..., clip=False)`, converting gradients back to nodal space, and applying the same metric convention as `u_dot_grad_log_sp`. It returns the requested fixed 50/50 decomposition: nodal `0.5 * (product_nodal + direct_gradient_nodal)` and modal `0.5 * product_modal`.

Threaded the selector through the Dinosaur adapter so the same scalar form is used when building rollout and DFI equations. Registered the side-by-side candidate factory without changing the incumbent theta-tendency factory or forecast contract.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `git diff --check` | 0 | No whitespace errors. |
| `python -m py_compile src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Syntax check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 1 | First run exposed an overstrict constant-scalar test expectation; repaired the test only. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 104 passed. |
| `uv run pytest` | 0 | 170 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_skew_scalar_adv` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.800745`. |

## Repair Attempts

- Failure observed: the first focused pytest run failed in `test_skew_scalar_advection_constant_scalar_matches_product_total_tendency`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: changed the test to verify a spatially constant scalar under zero horizontal flow has no spurious product-rule or skew-symmetric total tendency. This matches the fixed 50/50 implementation while avoiding an unrelated nonzero truncation residual from a divergent synthetic wind.
- Follow-up command and result: reran the focused pytest command; exit 0 with 104 passed.

## Known Limitations

- The direct-gradient branch adds one scalar-to-modal transform, one horizontal gradient, and one gradient-to-nodal transform for each scalar transported by the sigma primitive equation.
- The Implementer ran only the requested local gates and fast sanity evaluation. Iteration and validation scoring are intentionally left to the Scorer.

## Rollback Notes

Revert the scalar advection selector and direct-gradient helper from `primitive_equations.py`, remove the adapter field/factory plumbing, remove the `skew_scalar_advection_dinosaur_dycore_model` export, remove the registry factory and model name, and remove the focused tests added for this candidate. Do not remove prior accepted theta, Richardson, residual, Coriolis, initialization, or DFI mechanisms.
