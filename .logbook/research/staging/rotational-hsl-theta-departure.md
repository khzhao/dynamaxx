---
schema_version: 1
slug: rotational-hsl-theta-departure
title: Rotational-Wind Departure for Horizontal Semi-Lagrangian Theta
status: staging
created_at: 2026-06-22T18:07:59Z
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

# Rotational-Wind Departure for Horizontal Semi-Lagrangian Theta

## Hypothesis

The accepted HSL theta candidates show that horizontal thermal phase is a
high-signal remaining error source. The current `dino_hsl2_theta` departure
uses the full horizontal wind diagnosed from vorticity and divergence. In the
incumbent, divergent gravity-wave motion is already controlled by SIL3
off-centering, DFI, and symmetric Coriolis splitting, but any residual
ageostrophic/divergent noise still enters the HSL theta departure directly.

Using only the rotational, vorticity-derived component of the horizontal wind
for the theta departure may make the semi-Lagrangian theta remap follow the
balanced advecting flow while leaving divergent heating, pressure work,
vertical motion, and log-pressure continuity on the incumbent path. The expected
benefit is less noisy thermal displacement near fronts and jets, improving
`geopotential_500` and `mean_sea_level_pressure` without adding damping,
reservoir memory, or a new evaluation protocol.

## Mechanism

Add one side-by-side candidate with short alias `dino_hsl_rotwind`.

For the candidate only:

- preserve all `dino_hsl2_theta` model components, output variables, lead
  schedule, and evaluation protocols;
- compute a rotational-only `cos_lat_u` diagnostic from the current modal
  vorticity with modal divergence set to zero, using the same
  `spherical_harmonic.get_cos_lat_vector` operator as the incumbent diagnostic
  path;
- use that rotational wind only for the accepted midpoint HSL theta departure
  estimate and theta remap;
- keep the incumbent full-wind diagnostics for the Eulerian fallback theta
  tendency, vertical theta transport, sigma-dot diagnostics, pressure-work
  term, momentum tendencies, log-surface-pressure tendency, tracers, residual
  corrections, and output diagnostics;
- retain the current displacement CFL caps, midpoint fallback to first-order
  HSL, zero-wind guard, and finite fallback to the accepted `dino_hsl2_theta`
  full-wind path;
- do not alter semi-implicit off-centering, Coriolis splitting, ocean bulk
  sensible heat flux, surface residuals, humidity handling, filters, or
  forecast packing.

This is a departure-velocity decomposition experiment. It is not an Eulerian/
HSL blend, not a vertical-coherent HSL proposal, not a passive-humidity HSL
proposal, not a divergence damping filter, and not a lower-boundary reservoir.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model registered as `dino_hsl_rotwind`.
- API changes:
  - None. Forecast input/output contract, target variables, lead times, metrics,
    and protocols remain fixed.
- Tests to update:
  - Verify rotational-only departure equals incumbent departure when modal
    divergence is zero.
  - Verify a pure-divergence synthetic wind leaves the rotational departure
    zero and falls back safely rather than producing nonfinite theta transport.
  - Verify full-wind diagnostics still drive log-pressure, vertical theta, and
    momentum tendencies.
  - Verify nonfinite rotational wind diagnostics fall back to the accepted
    full-wind `dino_hsl2_theta` tendency.
  - Verify the candidate factory preserves every incumbent flag except the new
    departure-wind selector and model name.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 3 to 10 if noisy
    divergent departures are degrading balanced theta phase.
  - `2m_temperature` at later leads if lower-column theta advection benefits
    from a cleaner rotational departure.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should stay close to incumbent because prognostic
    momentum and the Richardson 10 m wind diagnostic are unchanged.
- Possible regressions:
  - Divergent horizontal flow physically advects theta. Removing it from the HSL
    departure could under-transport thermal anomalies in convergent frontal
    regions.
  - The accepted full-wind HSL path may already have the best empirical
    balance; a rotational-only departure could be too geostrophic and degrade
    early MSLP/Z500 phase.

## Risks

- Numerical stability:
  - Low to moderate. The change reduces departure wind content and keeps exact
    fallback to the accepted full-wind HSL path, but it touches theta transport
    every inner step.
- Compute cost:
  - Low to moderate. It adds one vorticity-only wind diagnostic per theta
    tendency evaluation and reuses existing HSL remap machinery.
- Data leakage:
  - None. It uses only current forecast vorticity, divergence shape metadata,
    and fixed grid operators.
- Physical plausibility:
  - Moderate. Balanced rotational flow dominates synoptic thermal advection,
    but divergent flow is physically meaningful; this is an empirical dycore
    decomposition test rather than a conservation improvement.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_rotwind`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_rotwind --workers <worker_count>`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failure, and a
    primary-score improvement against cached `dino_hsl2_theta` artifacts.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_rotwind --workers <worker_count>`
    only after iteration promotion.
  - Support requires validation improvement with clean diagnostics under the
    unchanged gates.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show full-wind theta HSL
    departure is already preferable. Early MSLP/Z500 guardrail failure would
    show that removing divergent departure motion breaks useful balanced
    coupling.

## Citations

- Local evidence:
  - `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
    and `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
    show that theta HSL and midpoint departures improved both iteration and
    validation scores.
  - `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/decision.md`
    shows local Eulerian/HSL blending is risky; this proposal changes the
    advecting wind decomposition instead of blending tendencies.
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` diagnoses
    full `cos_lat_u` from vorticity and divergence in
    `compute_diagnostic_state_sigma` and uses that diagnostic for the accepted
    HSL theta departure.
  - `outputs/eval/iteration_dino_hsl2_theta.csv` still shows negative
    long-lead skill for `2m_temperature`, `mean_sea_level_pressure`, and
    `10m_u_component_of_wind`, leaving room for balanced-flow phase changes to
    matter.
- Literature:
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
    to Geophysics, second edition. Springer.
    https://doi.org/10.1007/978-1-4419-6412-0
  - Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
    atmospheric models: a review. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
  - Temperton, C. 1997. Treatment of the Coriolis terms in semi-Lagrangian
    spectral models. Atmosphere-Ocean.
    https://doi.org/10.1080/07055900.1997.9687359

## Researcher Notes

This proposal explicitly targets `dino_hsl2_theta` and avoids duplicates of the
accepted sequence. The accepted HSL theta mechanism, midpoint departure,
bilinear remap, finite fallback, and theta-only scope remain intact; the only
new question is whether the departure wind should exclude divergent noise while
the rest of the primitive-equation dynamics still use the full wind.

It is distinct from staged `vertical-coherent-hsl-theta`, which changes
vertical coherence of departures; staged `horizontal-semilagrangian-passive-
humidity`, which transports humidity; staged `rotational-sparing-divergence-
drag`, which damps divergence; and staged `geostrophic-surface-wind-residual`,
which is a surface diagnostic residual. It also avoids SST/sea-ice anchors,
snow/soil reservoirs, lead-dependent spectral smoothing, passive humidity HSL,
and moist convective adjustment.

## Evaluator Notes

### 2026-06-22T18:10:43Z

Decision: move to `staging`; rank 2 of 2 current proposals.

This is plausible and implementable, but it is not the best next experiment.
It targets the accepted HSL-theta departure mechanism and avoids the rejected
CFL-blend pattern, but replacing the departure velocity with a rotational-only
diagnostic is physically less direct than improving the remap. Divergent
horizontal flow can advect theta in fronts and convergence zones, and removing
that component from the semi-Lagrangian departure could spend early MSLP/Z500
guardrail margin even if full-wind dynamics remain unchanged elsewhere.

The idea also overlaps an already crowded rotational/divergence research
neighborhood. Staged `rotational-sparing-divergence-drag` and related
divergence-filter ideas test whether divergent noise is a remaining error
source, while staged `vertical-coherent-hsl-theta` tests a different
departure-wind regularization for the same incumbent. This proposal is not a
strict duplicate because it changes only HSL theta departure wind
decomposition, but it should wait until the narrower remap experiment or a
clear diagnostic points to divergent departure noise.

Keep it staged with fixed evaluation gates unchanged. If promoted later, require
tests proving rotational-only departure equals the incumbent when divergence is
zero, pure-divergence diagnostics fall back safely, full-wind tendencies still
drive pressure, vertical transport, and momentum, and any invalid rotational
diagnostic selects the accepted `dino_hsl2_theta` full-wind path.

### 2026-06-22T21:57:42Z

Decision: remain in `staging`; not promoted for the next cycle.

After the `qmono-hsl-theta-remap` rejection, future HSL-theta experiments
should avoid expensive interpolation changes and prefer departure-geometry
questions. This proposal fits that broad direction, but it is still a less
direct test than `picard-hsl-theta-departure`. Removing divergent wind from the
theta departure changes the physical advecting velocity, while Picard keeps the
incumbent full wind and asks only whether the implicit midpoint trajectory can
be solved a little more accurately. The rotational-only path should wait for a
diagnostic or failed Picard result indicating divergent departure noise rather
than residual trajectory error.
