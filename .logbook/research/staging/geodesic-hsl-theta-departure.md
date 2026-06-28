---
schema_version: 1
slug: geodesic-hsl-theta-departure
title: Great-Circle Departure Geometry for HSL Theta
status: staging
created_at: 2026-06-23T06:08:19Z
author_role: Researcher
target_model: dino_hsl2_theta
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

# Great-Circle Departure Geometry for HSL Theta

## Hypothesis

The accepted HSL theta path computes backward departure points by applying
local longitude and latitude angular displacements, with a small safe cosine
near the poles. That is robust, but it is still a coordinate displacement on
the lat-lon grid rather than a spherical great-circle displacement. The
accepted HSL and midpoint results show trajectory geometry matters, while the
failed qmono, Picard, mean-neutral, and Eulerian/HSL blend results argue
against changing interpolation order or adding another local tendency blend.

A great-circle departure map for theta only may reduce high-latitude phase and
metric errors without changing the remap order, pressure work, vertical
transport, or momentum state.

## Mechanism

Add one side-by-side candidate alias, for example `dino_hsl_geo`, extending
`dino_hsl2_theta`.

For this candidate only:

- preserve the accepted midpoint HSL theta branch, bilinear remap, finite
  fallback, CFL cap, DFI, weak-HS analysis equilibrium, symmetric Coriolis
  split, theta mean recentering, ocean bulk sensible heat flux, residuals, and
  outputs;
- replace only the conversion from nodal wind to departure longitude/latitude
  in the theta HSL path;
- map each grid point to a unit vector on the sphere, convert the local
  horizontal wind into a tangent displacement vector for the capped time step,
  rotate along the great circle by the capped angular distance, and convert the
  departure point back to longitude/latitude;
- use the same bilinear remap from the resulting departure longitude/latitude;
- retain the incumbent coordinate-displacement HSL2 calculation as a fallback
  whenever the geodesic mapping, angular distance, or returned coordinates are
  nonfinite or outside the expected latitude range;
- leave momentum, log-surface-pressure, vertical theta transport, pressure-work
  terms, humidity, filters, and pressure-level output interpolation unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one short side-by-side model alias such as `dino_hsl_geo`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, metrics, and
    deterministic gates stay fixed.
- Tests to update:
  - Verify zero wind reproduces the incumbent HSL departure.
  - Verify small equatorial displacements match the existing coordinate method
    to first order.
  - Verify near-pole departures remain finite and inside valid latitude bounds.
  - Verify nonfinite geodesic diagnostics fall back to `dino_hsl2_theta`.
  - Verify the candidate factory preserves every incumbent option except the
    new theta-departure geometry selector and model name.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if polar
    or high-latitude theta phase errors feed hydrostatic thickness and mass
    adjustment.
  - `2m_temperature` in high-latitude lower-column cases after residual memory
    decays.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain near incumbent because the wind
    state and surface wind diagnostic are unchanged.
- Possible regressions:
  - Most grid points are away from the poles, so score movement may be small.
  - The current coordinate displacement may already be empirically aligned with
    the bilinear lat-lon remap; geodesic coordinates could shift theta phase in
    a way that hurts early Z500 or MSLP.

## Risks

- Numerical stability:
  - Low to moderate. The candidate changes only theta departure geometry and
    keeps incumbent fallback, but spherical coordinate inversion must be
    guarded carefully.
- Compute cost:
  - Low to moderate. It adds local trigonometric operations per theta HSL
    tendency and no extra trajectories or transforms.
- Data leakage:
  - None. It uses only current forecast wind and fixed grid geometry.
- Physical plausibility:
  - High. Trajectories on a sphere are naturally represented by great-circle
    motion for short tangent-plane displacements, especially near coordinate
    singularities.
- Rollback complexity:
  - Low. Remove one helper/selector, one factory/export, one registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_geo`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_geo --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failures, and
    iteration primary delta at least `+0.002` against cached `dino_hsl2_theta`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_geo --workers 4` only
    after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with clean
    diagnostics and unchanged guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show lat-lon coordinate
    departure geometry is already adequate for the fixed score. Any early MSLP,
    Z500, or wind guardrail failure would show the geodesic departure disrupts
    the accepted HSL balance.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` implements
  `_horizontal_semilagrangian_theta_departure_displacement`,
  `_horizontal_semilagrangian_theta_midpoint_departure_displacement`, and the
  bilinear HSL theta remap used by `dino_hsl2_theta`.
- Dynamaxx history:
  `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
  and
  `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
  show local positive evidence that HSL theta trajectory geometry is high
  leverage.
- Dynamaxx history:
  `.logbook/history/2026-06-22_18-14-00_qmono-hsl-theta-remap/decision.md` and
  `.logbook/history/2026-06-22_21-59-29_picard-hsl-theta-departure/decision.md`
  are negative evidence against higher-order remap and extra Picard trajectory
  correction.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: a review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Williamson, D. L. 2007. The evolution of dynamical cores for global
  atmospheric models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of recent HSL failures. It does not blend Eulerian and
HSL tendencies, does not change the interpolation order, does not add a Picard
iteration, does not remove mean modes, and does not alter vertical theta
transport. It is also distinct from staged `rotational-hsl-theta-departure`,
`vertical-coherent-hsl-theta`, and `static-stability-gated-hsl-theta`: those
change the departure wind content or select between existing HSL tendencies,
while this proposal changes only the spherical geometry used to map a capped
tangent displacement to departure coordinates.

## Evaluator Notes

### 2026-06-23T06:12:09Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

This is implementable and mechanistically distinct from the recently rejected
HSL variants. It keeps bilinear remapping, midpoint HSL, pressure work,
vertical theta transport, momentum, output channels, and fixed protocols
unchanged, so it avoids the failed patterns from `cfl-blended-hsl-theta`,
`qmono-hsl-theta-remap`, `picard-hsl-theta-departure`,
`mean-neutral-hsl-theta-transport`, and
`charney-phillips-interface-theta-advection`. The accepted first-order and
midpoint HSL results remain positive evidence that theta departure geometry is
a real lever.

It should wait behind the Coriolis-centered proposal. The expected score signal
is more geographically localized: away from high latitudes, the existing
coordinate displacement should already approximate the short great-circle
step, and the current bilinear lat-lon remap may be empirically matched to
that coordinate displacement. A geodesic coordinate inversion also carries
extra implementation edge cases near the poles and latitude clipping. Keep it
staged as a later, bounded geometry experiment if the next theta-departure
candidate is neutral or if diagnostics show high-latitude phase error is a
dominant remaining source.
