---
schema_version: 1
slug: vertical-coherent-hsl-theta
title: Vertically Coherent Departure Winds for HSL Theta
status: staging
created_at: 2026-06-22T17:30:10Z
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

# Vertically Coherent Departure Winds for HSL Theta

## Hypothesis

The accepted `dino_hsl2_theta` incumbent improves horizontal dry-theta anomaly
transport by tracing a midpoint horizontal trajectory in each sigma layer. The
trajectory velocity is currently the layer-local nodal wind. That is responsive
to vertical shear, but it can also imprint layer-to-layer grid noise from
pressure-to-sigma wind interpolation and spectral truncation onto the theta
departure points.

A compact mass-weighted vertical smoother applied only to the departure winds
used by HSL theta transport should make theta parcel trajectories more coherent
through the hydrostatic column while leaving the actual momentum state
unchanged. If some remaining Z500, MSLP, or late 2 m temperature error comes
from vertically noisy theta remap geometry rather than from the theta variable
itself, this should improve skill without adding a reservoir, changing vertical
advection, or retuning filters.

## Mechanism

Add one side-by-side candidate with short alias `dino_hsl_vcoh` targeting
`dino_hsl2_theta`.

For the candidate only:

- preserve all accepted `dino_hsl2_theta` behavior, including midpoint HSL
  theta departure, bilinear theta remap, finite fallback, CFL cap, DFI,
  weak-HS analysis equilibrium, symmetric Coriolis split, theta mean
  recentering, semi-implicit off-centering, scale-separated residuals,
  land-sea/ocean bulk surface handling, and output packing;
- before computing HSL theta departure displacements, build a vertically
  coherent copy of `aux_state.cos_lat_u`;
- apply one fixed compact vertical smoother to `u_cos_lat` and `v_cos_lat`,
  using sigma-layer thickness weights where available and normalized one-sided
  weights at the top and bottom layers;
- use the smoothed copy only for first-order and midpoint HSL theta departure
  wind estimates;
- remap theta itself exactly as the accepted incumbent does, from the unmodified
  theta anomaly field;
- leave the actual vorticity, divergence, wind diagnostics, pressure, vertical
  velocity, vertical advection, weak-HS forcing, ocean heat flux, residuals,
  passive humidity, and all output variables unchanged;
- fall back to the exact `dino_hsl2_theta` departure calculation if the smoothed
  departure winds or resulting displacements are nonfinite.

This is a trajectory regularization for the accepted theta remap. It is not a
momentum smoother, not a vertical-advection change, not a passive-humidity HSL
extension, and not another midpoint estimate.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one registered side-by-side model named `dino_hsl_vcoh`.
- API changes:
  - None. Forecast inputs, output variables, lead times, target metrics, and
    evaluation splits remain fixed.
- Tests to update:
  - Verify the candidate factory preserves all `dino_hsl2_theta` options except
    the new vertical-coherent HSL departure selector and model name.
  - Unit-test the vertical smoother preserves a column-constant wind profile.
  - Unit-test top and bottom one-sided weights are normalized and finite.
  - Unit-test the smoother changes only HSL departure winds, not state
    vorticity, divergence, pressure, temperature, or tracer tendencies.
  - Verify nonfinite smoothed winds fall back to the accepted `dino_hsl2_theta`
    departure path.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if
    vertically noisy theta departure points currently perturb hydrostatic
    thickness and mass-field phase.
  - `2m_temperature` at medium and late leads if lower-column theta transport
    benefits from smoother columnwise trajectory geometry after residual memory
    decays.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because the actual
    momentum equation, wind state, Coriolis split, and Richardson 10 m
    diagnostic are unchanged.
- Possible regressions:
  - Real vertical shear in jets and frontal zones may be useful for layerwise
    theta advection, so departure-wind smoothing can under-transport
    baroclinic tilt.
  - If the accepted layer-local departure winds are already clean, the smoother
    may act like mild extra thermal diffusion.

## Risks

- Numerical stability:
  - Low to moderate. The change only modifies HSL theta departure diagnostics
    and has an exact incumbent fallback, but it affects every thermodynamic
    transport evaluation.
- Compute cost:
  - Low. It adds local vertical algebra on existing nodal wind arrays and no
    extra rollout steps, transforms, output volume, or evaluation protocols.
- Data leakage:
  - None. It uses only the current forecast state and fixed sigma geometry.
- Physical plausibility:
  - Moderate. Hydrostatic columns generally have vertically coherent horizontal
    trajectories at resolved scales, but the model must still respect real
    vertical shear.
- Rollback complexity:
  - Low. Remove one smoother/helper, one selector, one factory/export, one
    registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_vcoh`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_vcoh --workers <worker_count>`.
  - Support requires primary-score improvement against cached `dino_hsl2_theta`,
    clean diagnostics, and no fixed guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_vcoh --workers <worker_count>`
    only after iteration promotion.
  - Require validation support under the unchanged fixed gates.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show layer-local
    departure winds are preferable for the accepted HSL theta signal. Any early
    wind, Z500, or MSLP guardrail failure would show the smoothed trajectories
    disrupt baroclinic balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  computes `aux_state.cos_lat_u`, bounded HSL theta displacements, midpoint
  departure winds, and bilinear remaps for `dino_hsl2_theta`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py`
  exposes sigma layer thicknesses that can support normalized vertical weights.
- Dynamaxx history:
  `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
  accepted the current midpoint HSL trajectory estimate with clean diagnostics
  and validation delta `+0.007196436070573853`.
- Dynamaxx history:
  `.logbook/history/2026-06-21_02-46-40_vector-wind-pchip-sigma-init/decision.md`
  is negative evidence against changing initialized wind profiles directly;
  this proposal therefore leaves the momentum state untouched and regularizes
  only theta departure diagnostics.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: a review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric
  transport schemes: desirable properties and a semi-Lagrangian view on
  finite-volume discretizations. In Numerical Techniques for Global Atmospheric
  Models. https://doi.org/10.1007/978-3-642-11640-7_8
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This proposal explicitly targets `dino_hsl2_theta` and is adjacent to the
proven theta-transport signal without duplicating the accepted sequence. It
does not add another midpoint estimate and does not replace the theta remap.
Instead it asks whether the wind used to locate theta departure points should
be vertically coherent while the forecast wind state remains untouched.

It is distinct from staged `smoothed-sigma-dot-vertical-advection`,
`theta-upwind-vertical-advection`, and `vertical-courant-limited-advection`,
because those change vertical transport or sigma-dot behavior. It is distinct
from staged `horizontal-semilagrangian-passive-humidity` because humidity
remains unchanged. It also avoids recent rejected or staged SST/sea-ice,
snow/soil, reservoir, convective adjustment, lead-dependent smoothing, and
forecast-contract infrastructure ideas.

## Evaluator Notes

### 2026-06-22T17:34:01Z

Decision: move to `staging`; rank 2 of 2 current proposals.

The idea is scientifically plausible and not a duplicate of the staged vertical
advection family: it smooths only the horizontal winds used to locate HSL theta
departure points, not the momentum state, sigma-dot, vertical transport,
humidity, or output diagnostics. It also preserves the accepted midpoint remap
and finite fallback path. The semi-Lagrangian literature supports trajectory
quality as a relevant numerical issue, and local source inspection confirms
there is a localized HSL departure-wind hook.

Keep it staged rather than ready because the expected benefit is less direct
than the CFL-blend proposal and the failure mode is more physically sensitive.
The accepted midpoint candidate already improved the layer-local departure
estimate with clean diagnostics, so smoothing departure winds across sigma
levels risks erasing real vertical shear and baroclinic tilt in jets and frontal
zones. The negative `vector-wind-pchip-sigma-init` history is not an exact
duplicate because that changed initialized winds directly, but it is cautionary
evidence that vertical wind-profile regularization can be stable yet
score-negligible. Active staged `smoothed-sigma-dot-vertical-advection` and
`vertical-courant-limited-advection` also make the vertical-smoothing family
crowded and riskier than a localized HSL weighting test.

This should be reconsidered after the CFL-blend experiment or after diagnostics
show layer-to-layer departure-wind noise as a concrete error source. If promoted
later, require fixed, documented vertical weights, no validation tuning, tests
showing only HSL departure diagnostics change, and guardrails for early Z500,
MSLP, and wind balance.

### 2026-06-22T21:57:42Z

Decision: remain in `staging`; not promoted for the next cycle.

The rejection of `cfl-blended-hsl-theta` makes local fallback stability more
important, and the rejection of `qmono-hsl-theta-remap` argues against costly
or more diffusive theta remap variants. This proposal avoids both failure
patterns and remains scientifically plausible, but it regularizes the
departure wind by smoothing across sigma levels, which can erase real vertical
shear and baroclinic tilt. The Picard proposal is a narrower continuation of
the accepted midpoint mechanism: it preserves layer-local full-wind departures
and only improves trajectory iteration. Keep vertical coherence staged until
there is evidence that layer-to-layer departure-wind noise, rather than
trajectory fixed-point error, is the limiting term.
