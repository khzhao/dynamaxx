---
schema_version: 1
slug: coriolis-centered-hsl-theta-departure
title: Coriolis-Centered Departure Winds for HSL Theta
status: ready
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

# Coriolis-Centered Departure Winds for HSL Theta

## Hypothesis

The accepted incumbent already uses symmetric exact Coriolis splitting for the
prognostic wind state, but the HSL theta departure estimate samples the
diagnosed horizontal wind without applying a matching half-step Coriolis
centering inside the theta trajectory calculation. The accepted midpoint HSL
result suggests time-centering the trajectory is useful, while the neutral
Picard result suggests more fixed-point iteration is not. A narrower way to
improve temporal trajectory consistency is to rotate only the departure wind by
a local half-step Coriolis angle before computing the HSL theta displacement.

This targets balanced inertial turning in the advecting velocity, not remap
order, pressure work, mass continuity, or vertical theta transport.

## Mechanism

Add one side-by-side candidate alias, for example `dino_hsl_corcen`, extending
`dino_hsl2_theta`.

For this candidate only:

- preserve every accepted `dino_hsl2_theta` setting, including exact symmetric
  Coriolis split of the actual state, midpoint HSL theta departure, bilinear
  remap, finite fallback, CFL cap, DFI, weak-HS analysis equilibrium, theta
  mean recentering, ocean bulk sensible heat flux, residuals, and outputs;
- before computing first-order and midpoint HSL theta departure displacements,
  form a diagnostic copy of `aux_state.cos_lat_u`;
- rotate that diagnostic wind vector by a fixed local half-step Coriolis angle
  `f * dt / 2`, using latitude-dependent Coriolis parameter from the grid and
  model physics;
- use the rotated diagnostic wind only for theta departure geometry;
- leave the actual vorticity, divergence, `cos_lat_u` diagnostics used by
  momentum, log-pressure continuity, vertical velocity, vertical theta
  transport, pressure-work terms, tracers, filters, and output diagnostics
  unchanged;
- if the rotated wind or resulting displacement is nonfinite, fall back exactly
  to the accepted `dino_hsl2_theta` full-wind departure path.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one short side-by-side model alias such as `dino_hsl_corcen`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, metrics, and
    fixed deterministic gates remain unchanged.
- Tests to update:
  - Verify zero rotation at the equator leaves departure winds unchanged.
  - Verify small-angle rotation matches the analytic linearized Coriolis turn.
  - Verify the actual prognostic wind and non-theta tendencies are unchanged by
    the selector.
  - Verify nonfinite rotated diagnostics fall back to incumbent HSL2 behavior.
  - Verify the candidate factory preserves every incumbent option except the
    new Coriolis-centered departure selector and model name.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 2 to 10 if
    balanced thermal advection phase is limited by a small Coriolis timing error
    in the theta departure velocity.
  - `2m_temperature` at medium leads if lower-column theta phase benefits from
    more consistent inertial turning.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because the
    forecast wind state and Richardson 10 m diagnostic are unchanged.
- Possible regressions:
  - The symmetric Coriolis split may already handle the relevant wind evolution
    before the theta tendency is evaluated, so rotating the diagnostic
    departure wind could double-count part of the turning.
  - In strongly ageostrophic or divergent flow, a simple Coriolis rotation may
    be less accurate than the accepted midpoint full-wind estimate.

## Risks

- Numerical stability:
  - Low to moderate. The operation is norm-preserving for the diagnostic wind,
    but it changes theta departure every inner step and must keep finite
    fallbacks.
- Compute cost:
  - Low. It adds local sine/cosine or small-angle rotation algebra and no extra
    remap, transform, trajectory, or output volume.
- Data leakage:
  - None. It uses only current forecast state, model time step, latitude, and
    fixed physical constants.
- Physical plausibility:
  - Moderate to high. Semi-Lagrangian trajectory accuracy depends on temporal
    centering of the advecting velocity, and Coriolis turning is a known issue
    in semi-Lagrangian spectral models.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_corcen`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_corcen --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failures, and
    iteration primary delta at least `+0.002` against cached `dino_hsl2_theta`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_corcen --workers 4`
    only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with the same
    fixed guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the accepted
    midpoint HSL trajectory already captures useful temporal centering. Early
    MSLP, Z500, or wind guardrail failures would show Coriolis-centering the
    diagnostic departure wind disrupts the accepted balance.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` enables the accepted exact
  symmetric Coriolis split, and
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` computes HSL
  theta departure winds from `aux_state.cos_lat_u`.
- Dynamaxx history:
  `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
  accepted midpoint HSL departure with validation delta
  `+0.007196436070573853`.
- Dynamaxx history:
  `.logbook/history/2026-06-22_21-59-29_picard-hsl-theta-departure/decision.md`
  rejected an additional Picard departure correction as neutral to slightly
  negative, motivating a targeted physical centering rather than another
  generic fixed-point iteration.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: a review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Temperton, C. 1997. Treatment of the Coriolis terms in semi-Lagrangian
  spectral models. Atmosphere-Ocean.
  https://doi.org/10.1080/07055900.1997.9687359
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of the accepted midpoint departure or rejected Picard
departure. It does not improve the trajectory by another remapped wind sample;
it applies a physically motivated Coriolis half-step to the diagnostic
departure wind while keeping the accepted midpoint fallback chain.

It is also distinct from staged `rotational-hsl-theta-departure`, which removes
the divergent wind component; staged `vertical-coherent-hsl-theta`, which
smooths departure winds in the vertical; and staged
`static-stability-gated-hsl-theta`, which selects first-order HSL in selected
columns. This proposal keeps the full wind content and changes only the
time-centering of that wind for the theta departure estimate.

## Evaluator Notes

### 2026-06-23T06:12:09Z

Decision: move to `ready`; ranked 1 of 3 new proposals and recommended as the
next implementation candidate.

This is the strongest next model-selection candidate in the current batch. It
is narrow, reversible, immediately implementable, and produces a real dycore
candidate score under the unchanged `fast`, `iteration`, and conditional
`validation` gates. The mechanism is genuinely different from recent HSL
failures: it does not add another Picard remap, change interpolation order,
blend Eulerian and HSL tendencies, remove mean modes, or alter vertical theta
transport. It only changes the diagnostic wind used for theta departure
time-centering, leaving the prognostic wind, pressure, vertical transport,
pressure work, humidity, filters, outputs, metrics, and splits fixed.

The main risk is double-counting because `dino_hsl2_theta` already applies an
exact symmetric Coriolis split to the prognostic wind state. That risk is
bounded by the proposal's half-step diagnostic-only rotation and exact fallback
to incumbent HSL2 behavior on nonfinite diagnostics. Compared with the
geodesic proposal, this has a broader expected signal outside the polar
geometry corner case and a smaller implementation surface because existing
Coriolis-rotation code paths and tests can guide the helper. Compared with the
pressure-work sidecar, it is a score-producing candidate, which matches the
current loop need. Reuse cached incumbent metrics unless the leaderboard cache
is concretely invalid; do not run golden.
