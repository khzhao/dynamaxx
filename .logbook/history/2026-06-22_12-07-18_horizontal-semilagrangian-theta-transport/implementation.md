# Implementation Record

## Identity

- Proposal slug: horizontal-semilagrangian-theta-transport
- Candidate model name: dino_hsl_theta
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf
- Baseline commit: 329dd5758204b7e77f1abb258b1dab9ee5d9b2c8
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Added one side-by-side candidate, `dino_hsl_theta`, by wrapping the accepted
ocean-bulk sensible-heat-flux incumbent and changing only the model name plus
`use_horizontal_semilagrangian_theta_transport`.

The new primitive-equation path is limited to
`PrimitiveEquationsSigma.temperature_tendency_potential_temperature_form`.
For the theta-form thermal tendency, the candidate replaces only the horizontal
dry-theta anomaly contribution with a bounded backward-departure bilinear remap
on the existing nodal longitude-latitude grid. Departure increments are computed
from the current `cos_lat_u` diagnostics, converted to angular displacement with
the model radius and current inner-step size, and capped at 0.5 local grid-cell
spacing in longitude and latitude. Vertical theta advection, pressure-work
temperature tendency, log-surface-pressure tendency, momentum tendencies,
filters, DFI, weak-Held-Suarez forcing, theta mean recentering, residual
corrections, and ocean bulk sensible heat flux remain on the incumbent path.

The helper falls back to the incumbent theta horizontal tendency when horizontal
wind is exactly zero, the remap diagnostics are nonfinite, the step/radius is
invalid, or the remapped tendency is nonfinite. The existing theta-form fallback
to the temperature-form tendency remains in place for broader pressure/theta
diagnostic failures.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Syntax check before focused tests. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 1 then 0 | Initial failure was import ordering and two new-test `dict()` style issues; final run passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py -k "hsl_theta or semilagrangian or theta_transport or ocean_bulk_shf"` | 1, then 1, then 0 | Final run: 14 passed, 117 deselected. |
| `uv run python - <<'PY'\nfrom dynamaxx.dycore.registry import create_dycore_model\nmodel = create_dycore_model('dino_hsl_theta')\nprint(model.name)\nprint(getattr(model, 'use_horizontal_semilagrangian_theta_transport', None))\nPY` | 0 | Output: `dino_hsl_theta`, `True`. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py -k registered` | 0 | 17 passed, 2 deselected; verifies updated complete registry tuple. |
| `uv run dynamaxx-eval fast --model dino_hsl_theta` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.322437`, metrics at `outputs/eval/fast_dino_hsl_theta.json`. |
| `uv run pytest` | 0 | Orchestrator full unit gate passed: 216 passed, 2 skipped in 157.63s. |

## Repair Attempts

- Failure observed: direct construction of `primitive_equations.PrimitiveEquations`
  failed with unexpected keyword arguments for the new selector.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: added selector and step forwarding to the deprecated dry,
  moist, and cloud-moisture Sigma compatibility constructors.
- Follow-up command and result: focused pytest advanced to one helper assertion
  failure.

- Failure observed: bounded-displacement helper test exceeded the longitude cap
  by float32 roundoff at the exact cap boundary.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: added a `1.0e-6` assertion tolerance in the test only.
- Follow-up command and result: focused pytest passed with 14 selected tests.

## Known Limitations

- The horizontal theta transport is a first-order nodal bilinear remap, not a
  conservative flux-form transport scheme.
- Departure points are clipped at the meridional domain boundaries rather than
  transported across poles.
- Only the fast sanity protocol was run by the Implementer; iteration,
  validation, and golden protocols were not run.

## Rollback Notes

Revert this experiment by removing the new theta semi-Lagrangian selector and
helper methods from `primitive_equations.py`, removing selector plumbing and the
`horizontal_semilagrangian_theta_transport_dinosaur_dycore_model` factory from
`adapter.py`, dropping its export from `__init__.py`, removing the
`dino_hsl_theta` registry wrapper and factory entry from `registry.py`, and
reverting the added/updated focused tests in
`tests/dycore/models/dinosaur/test_primitive_equations.py`,
`tests/dycore/models/dinosaur/test_dependency.py`, and
`tests/dycore/test_registry.py`.
