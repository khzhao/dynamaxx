---
schema_version: 1
slug: finite-volume-mass-dse-hsl-remap
title: Conservative Finite-Volume Remap for Mass-DSE HSL
status: ready
created_at: 2026-06-24T15:40:00Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Conservative Finite-Volume Remap for Mass-DSE HSL

## Hypothesis

The incumbent `dino_hsl2_mass_dse` improved by transporting
`delta_p * dry_static_energy_anomaly` with the existing semi-Lagrangian remap,
but that remap is still pointwise bilinear interpolation. Bilinear
semi-Lagrangian interpolation is stable but not locally conservative, so it can
move layer-integrated dry static energy in a way that slowly projects onto
thickness, Z500, and MSLP. Replacing only the accepted mass-DSE scalar remap with
a guarded conservative finite-volume remap should retain the accepted physical
signal while reducing numerical integral drift.

## Mechanism

Register a side-by-side candidate, for example
`dino_hsl2_mass_dse_fv_remap`. Preserve the incumbent scalar, midpoint
departure estimate, vertical theta tendency, adiabatic tendency, weak-HS
forcing, ocean bulk sensible heat flux, residual corrections, output variables,
and fixed protocols.

For the candidate only:

- keep the accepted `weighted_dse_anomaly = delta_p * dry_static_energy_anomaly`
  as the transported quantity;
- add a finite-volume remap helper used only by the layer-mass DSE branch;
- compute target-cell departure geometry from the same capped midpoint
  displacement already used by HSL2;
- perform a split conservative remap on the regular longitude-latitude grid:
  first remap zonal cell integrals with periodic longitude boundaries, then
  remap meridional cell integrals with spherical row-area weights;
- preserve each layer's global quadrature integral of `weighted_dse_anomaly`
  to roundoff after the remap;
- fall back pointwise to the incumbent HSL2 bilinear tendency if displacements,
  overlap weights, pressure thickness, or remapped values are nonfinite or
  outside the existing CFL caps.

The local `delta_p` division remains exactly the incumbent accepted operation.
There is no product-rule pressure-thickness correction, hydrostatic inversion,
vertical DSE transport, ocean heat-flux redistribution, or output diagnostic
change.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side registry entry based on `dino_hsl2_mass_dse`.
- API changes:
  - None. `DycoreModel.forecast`, inputs, outputs, lead times, and metric
    protocols stay fixed.
- Tests to update:
  - Unit-test constant-field preservation, finite fallback, longitude
    periodicity, polar-row finite behavior, and layer-integral preservation.
  - Verify the candidate factory preserves all incumbent flags except the new
    mass-DSE remap selector.
  - Verify disabled-selector behavior is incumbent-equivalent.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and late leads if
    nonconservative mass-DSE remap drift is currently leaking into thickness.
  - `2m_temperature` may improve modestly through better lower-column thermal
    phase without changing the surface residual path.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should stay close to incumbent because momentum,
    Coriolis splitting, and the 10 m diagnostic are unchanged.
- Possible regressions:
  - First-order conservative remapping can be more diffusive than bilinear HSL2
    and may soften useful thermal gradients.
  - Extra row/column remap algebra can expose polar geometry mistakes.

## Risks

- Numerical stability:
  - Moderate. The remap is bounded and fallback-guarded, but it touches the
    active thermodynamic tendency every inner step.
- Compute cost:
  - Moderate. Split finite-volume remapping adds overlap/integral work for each
    sigma layer, but only for one scalar branch.
- Data leakage:
  - None. It uses only forecast-state fields, fixed grid geometry, and existing
    physical constants.
- Physical plausibility:
  - High. Conservative transport is a standard objective for atmospheric mass
    and tracer transport schemes.
- Rollback complexity:
  - Low to moderate. Remove one helper/selector, one factory/export, one
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_fv_remap`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_fv_remap --workers 4`.
  - Compare only against the cached incumbent metrics for `dino_hsl2_mass_dse`;
    do not rerun the incumbent.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_fv_remap --workers 4`
    only if iteration promotes under the fixed policy.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that integral drift
    in the bilinear mass-DSE remap is not a material remaining error source.
    Any early MSLP or Z500 guardrail failure would show that the conservative
    remap is too diffusive or geometrically inconsistent.

## Citations

- Lin, S.-J. and Rood, R. B. 1996. Multidimensional flux-form
  semi-Lagrangian transport schemes. *Monthly Weather Review*.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Lauritzen, P. H., Nair, R. D., and Ullrich, P. A. 2010. A conservative
  semi-Lagrangian multi-tracer transport scheme on the cubed sphere.
  *Journal of Computational Physics*. https://doi.org/10.1016/j.jcp.2009.10.036
- Lauritzen, P. H., Nair, R. D., and Ullrich, P. A. 2011. Desirable properties
  and a semi-Lagrangian view on finite-volume discretizations.
  https://doi.org/10.1007/978-3-642-11640-7_8

## Researcher Notes

This is not the recently rejected pressure-thickness-corrected mass-DSE idea:
it does not add a product-rule correction or modify how the accepted tendency is
divided by local `delta_p`. It is also not the rejected hydrostatic-inverted
mass-DSE or vertical-DSE proposals: no hydrostatic inversion is performed and
vertical transport remains the incumbent theta path.

The closest active staged ideas are `area-neutral-mass-dse-hsl` and
`mass-dse-remap-variance-limiter`. This proposal is distinct because it is a
local finite-volume transport test, not a global zero-mean projection and not a
convex variance limiter on the bilinear result. It should be evaluated as a
numerical conservation experiment for the accepted incumbent scalar.

## Evaluator Notes

### 2026-06-24T15:18:56Z

Decision: move to `ready`; rank 1 of 3 new proposals; ready now: yes.

This is the strongest next experiment from the new batch. The accepted
`dino_hsl2_mass_dse` incumbent gained on both iteration and validation by
transporting `delta_p * s_prime`, and the recent negative DSE-family follow-ups
mostly failed when they changed pressure-thickness coupling, hydrostatic
conversion, vertical DSE transport, initialization, or surface heat placement.
This proposal leaves those rejected mechanisms alone and instead tests whether
the remaining bilinear HSL remap of the accepted scalar is the numerical weak
point.

It is not a duplicate of staged `area-neutral-mass-dse-hsl` or
`mass-dse-remap-variance-limiter`. Those are global projection or limiter
probes applied around the incumbent bilinear remap; this proposal replaces the
local remap with a conservative flux-form/finite-volume operator for the same
mass-DSE scalar. The literature check supports the general mechanism:
Lin and Rood 1996 and Lauritzen, Ullrich, and Nair 2011 treat conservative
semi-Lagrangian/finite-volume transport as a standard objective for atmospheric
tracers. Local history is mixed because `qmono-hsl-theta-remap` was expensive
and strongly negative, but that was a theta-remap replacement before the
accepted DSE and mass-DSE discoveries. The narrow scalar target and exact
fallback make this a better conservation test than the older broad remap
failures.

Main risk is implementation surface area: split overlap geometry on a
longitude-latitude grid can be diffusive or polar-sensitive, and a more
conservative remap can still remove useful bilinear phase behavior. Keep it
side-by-side, preserve the cached incumbent comparison, and require tests for
periodicity, polar-row finiteness, constant-field preservation, layer-integral
preservation, and exact fallback to `dino_hsl2_mass_dse`.
