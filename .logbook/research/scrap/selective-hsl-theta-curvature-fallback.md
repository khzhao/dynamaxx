---
schema_version: 1
slug: selective-hsl-theta-curvature-fallback
title: Selective Curvature Fallback for HSL Theta Transport
status: scrap
created_at: 2026-06-23T03:42:31Z
author_role: Researcher
target_model: dino_hsl2_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Selective Curvature Fallback for HSL Theta Transport

## Hypothesis

The accepted HSL2 theta transport showed that horizontal semi-Lagrangian theta
advection is a strong mechanism, while the follow-on evidence says broad remap
modifications are dangerous: CFL blending became nonfinite, quasi-monotone
remapping regressed strongly, Picard departure refinement was neutral-slightly
negative, and mean-neutral HSL was far below the iteration promotion threshold.

The likely remaining weakness is not the smooth-flow HSL2 trajectory, but
localized front or filament regions where bilinear remapping over a sharply
curved theta anomaly introduces excessive smoothing or phase distortion. A
selective curvature sensor that falls back to the incumbent Eulerian spectral
theta tendency only in those high-curvature cells can protect fronts while
preserving the accepted HSL2 mechanism over most of the sphere.

## Mechanism

Add one side-by-side candidate, for example `dino_hsl2_theta_curv`. Preserve
every incumbent option except the horizontal theta transport selector.

For the candidate only:

- compute the accepted `dino_hsl2_theta` midpoint HSL horizontal theta-anomaly
  tendency and the incumbent Eulerian spectral horizontal theta tendency already
  available as `incumbent_dtheta_dt_horizontal_nodal`;
- diagnose a dimensionless nodal curvature sensor per layer from the current
  theta anomaly, using local second differences divided by local first-gradient
  magnitude plus a small scale-aware floor;
- flag only grid cells where curvature is high relative to the layer's robust
  area-weighted curvature scale, and optionally dilate by one horizontal
  neighbor to avoid checkerboard switching;
- use the HSL2 tendency in smooth regions and the existing Eulerian spectral
  tendency in flagged regions;
- apply a finite global fallback to the unmodified `dino_hsl2_theta` tendency if
  the sensor, switch mask, or blended tendency is nonfinite;
- keep midpoint departure points, vertical theta transport, pressure-work
  conversion, theta mean recentering, DFI, weak-HS forcing, ocean bulk heat
  flux, residual diagnostics, and output packing unchanged.

This is not another limiter applied to the remapped theta field. It is a local
operator-selection guard: preserve HSL2 where the field is smooth and use the
already stable Eulerian tendency where HSL interpolation is most likely to
damage sharp thermal structure.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model, preferably `dino_hsl2_theta_curv`.
- API changes:
  - None.
- Tests to update:
  - Verify spatially linear or constant theta anomalies reproduce incumbent
    HSL2 horizontal theta transport.
  - Verify a synthetic sharp filament selects the Eulerian fallback only near
    the high-curvature feature.
  - Verify nonfinite sensor diagnostics fall back to unmodified HSL2 tendency.
  - Verify the candidate factory preserves all incumbent flags except the new
    selective curvature selector.
  - Add registry coverage and a finite non-JIT forecast smoke test.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if
    localized thermal-front smoothing is feeding thickness and pressure errors.
  - `2m_temperature` may improve where lower-column thermal gradients remain
    too diffuse after residual memory decays.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to incumbent because momentum,
    Coriolis splitting, and the surface wind diagnostic are unchanged.
- Possible regressions:
  - The switch can reintroduce Eulerian Courant or phase error in flagged
    regions.
  - A threshold that is too broad would repeat the qmono lesson by damaging the
    accepted HSL2 operator over too much of the domain.

## Risks

- Numerical stability:
  - Low to moderate. The candidate chooses between two already finite horizontal
    theta tendencies and falls back globally to HSL2 if diagnostics are not
    finite.
- Compute cost:
  - Low. The sensor adds local nodal difference operations per theta tendency
    evaluation and no extra forecast trajectories.
- Data leakage:
  - None. Uses only current forecast theta anomaly and fixed grid geometry.
- Physical plausibility:
  - Moderate to high. Shape-aware or smoothness-aware advection schemes are
    standard ways to avoid remap artifacts near sharp gradients, but the exact
    curvature threshold is empirical.
- Rollback complexity:
  - Low. Remove one selector/helper path, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_theta_curv`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_theta_curv --workers 4`.
  - Support requires clean diagnostics, fixed guardrails passing, and iteration
    primary delta at least `+0.002` against cached incumbent score
    `-0.31282890543336245`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_theta_curv --workers 4`
    only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` against cached
    incumbent validation score `-0.3072374345999185`.
- Outcome that would falsify the hypothesis:
  - A nonfinite fast run would show the sensor introduced an unstable branch.
    A clean near-zero or negative iteration delta would show the accepted HSL2
    remap should not be locally replaced by the Eulerian tendency.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  contains `horizontal_semilagrangian_theta_transport` and the incumbent
  `horizontal_scalar_advection` fallback tendency used by this proposal.
- History:
  `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/decision.md`
  rejected CFL blending after nonfinite fast forecasts.
- History:
  `.logbook/history/2026-06-22_18-14-00_qmono-hsl-theta-remap/decision.md`
  rejected quasi-monotone HSL remapping with iteration delta
  `-0.05861772497361423`.
- History:
  `.logbook/history/2026-06-22_21-59-29_picard-hsl-theta-departure/decision.md`
  rejected Picard departure refinement with iteration delta
  `-3.9808928495421725e-05`.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Leonard, B. P. 1991. The ULTIMATE conservative difference scheme applied to
  unsteady one-dimensional advection. Computer Methods in Applied Mechanics and
  Engineering. https://doi.org/10.1016/0045-7825(91)90232-U

## Researcher Notes

This is intentionally the only nearby HSL-theta proposal in this batch, and it
is not a qmono, CFL-blend, Picard, or mean-neutral variant. The material
difference is that it does not alter the HSL remapped value or departure
trajectory. It uses the accepted HSL2 tendency unchanged in smooth regions and
falls back to an already existing stable Eulerian tendency only where a local
curvature sensor says HSL interpolation is most likely to hurt sharp theta
structure. The CP/interface vertical theta failure is also negative evidence
against changing vertical placement, so this proposal leaves vertical theta
transport untouched.

## Evaluator Notes

### 2026-06-23T03:45:13Z

Decision: move to `scrap`; ranked 2 of 2 current proposals.

This is implementable, but it is too close to the recent failed HSL-theta local
selection family to spend the next fixed evaluation cycle. The strongest
negative precedent is `cfl-blended-hsl-theta`: pointwise mixing between the
accepted HSL path and the pre-HSL Eulerian tendency produced nonfinite fast
forecasts even after a bounded repair. This proposal is a hard local selector
rather than a continuous CFL blend, but it still introduces a spatially varying
Eulerian/HSL switch inside the thermodynamic tendency, with a curvature
threshold and optional dilation that would need empirical tuning. The qmono
remap regression, neutral-slightly-negative Picard correction, and subthreshold
mean-neutral HSL result further reduce the expected value of another HSL-theta
operator refinement right now.

The scientific question is not impossible, but the proposal is weaker than the
pressure-work candidate under the ranking rubric. It depends on undocumented
localized front/filament HSL damage, risks discontinuous masks in the thermal
tendency, and overlaps the active staged HSL-theta queue
(`static-stability-gated-hsl-theta`, `vertical-coherent-hsl-theta`, and
`rotational-hsl-theta-departure`). If curvature damage becomes visible in later
diagnostics, a revised proposal should avoid Eulerian/HSL pointwise switching
or first present evidence that the switch region is rare, finite, and materially
correlated with incumbent errors.
