---
schema_version: 1
slug: picard-hsl-theta-departure
title: Picard-Corrected HSL Theta Departure
status: ready
created_at: 2026-06-22T21:55:16Z
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

# Picard-Corrected HSL Theta Departure

## Hypothesis

The accepted `dino_hsl2_theta` incumbent improved both iteration and validation by
using a midpoint estimate for horizontal semi-Lagrangian dry-theta departure
points. That result suggests theta phase error is sensitive to departure-point
accuracy. The current midpoint estimate uses a single half-step wind predictor.
One additional fixed-point correction should make the departure geometry closer
to the implicit midpoint semi-Lagrangian trajectory while preserving the
accepted bilinear theta remap and fallback behavior.

## Mechanism

Add one side-by-side model alias, `dino_hsl_picard`, extending
`dino_hsl2_theta`.

For this candidate only, preserve the accepted first-order and midpoint HSL
theta paths, then add exactly one Picard correction:

- compute the accepted `dino_hsl2_theta` midpoint full-step displacement;
- use one half of that accepted full-step displacement to locate a corrected
  midpoint position;
- remap only the existing nodal horizontal wind components to that corrected
  midpoint position with the incumbent bilinear remap;
- recompute the full-step HSL theta departure displacement from the corrected
  midpoint wind;
- remap the theta anomaly with the unchanged bilinear remap and convert the
  resulting theta tendency through the existing potential-temperature tendency
  path;
- retain the incumbent CFL caps, zero-wind guard, finite diagnostics, fallback
  to first-order HSL, and fallback to the accepted Eulerian theta tendency;
- do not change theta remap order, vertical advection, pressure work, momentum,
  log-pressure continuity, weak-HS forcing, ocean bulk heat flux, residuals,
  humidity, output packing, metrics, or protocols.

This is a single trajectory-accuracy experiment. It is not a higher-order theta
remap, not an Eulerian/HSL blend, not a vertical-coherent departure smoother,
and not a rotational-wind departure decomposition.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model registered as `dino_hsl_picard`.
- API changes:
  - None. Forecast inputs, output variables, lead steps, metrics, splits, and
    worker policy stay fixed.
- Tests to update:
  - Verify `dino_hsl_picard` preserves every `dino_hsl2_theta` option except
    model name and the new Picard departure selector.
  - Unit-test that the Picard displacement is finite, bounded by the same CFL
    caps, and identical to the incumbent midpoint displacement for spatially
    uniform winds.
  - Verify nonfinite corrected midpoint winds fall back to the accepted
    `dino_hsl2_theta` midpoint tendency.
  - Verify zero wind reproduces the accepted incumbent tendency.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if the
    remaining thermal phase error is caused by first-iteration departure-point
    error.
  - `2m_temperature` after the surface residual memory decays if lower-column
    theta advection benefits from the corrected trajectory.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to incumbent because momentum,
    Coriolis splitting, diffusion, and the Richardson 10 m wind diagnostic are
    unchanged.
- Possible regressions:
  - The accepted midpoint estimate may already be optimally diffusive for this
    grid and time step; a sharper corrected trajectory can move fronts too far.
  - Extra trajectory sensitivity near polar CFL caps may perturb early MSLP or
    wind guardrails.

## Risks

- Numerical stability:
  - Low to moderate. The candidate keeps the accepted bilinear remap and finite
    fallback chain, but it changes thermodynamic transport every inner step.
- Compute cost:
  - Low to moderate. It adds one additional wind remap and displacement
    calculation per theta tendency evaluation, with no extra forecast outputs or
    evaluation protocols. The reported 4-worker evaluation budget is sufficient.
- Data leakage:
  - None. It uses only the current forecast state and fixed grid geometry.
- Physical plausibility:
  - High. Fixed-point iteration for semi-Lagrangian departure points is a
    standard trajectory improvement, and this version keeps the accepted
    material variable and interpolation path unchanged.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_picard`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_picard --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failure, and a
    primary-score improvement over cached `dino_hsl2_theta`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_picard --workers 4`
    only after iteration promotion.
  - Support requires validation improvement under the unchanged fixed gates.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the accepted
    one-pass midpoint trajectory already captures the useful departure accuracy.
    Any early MSLP, Z500, or wind guardrail failure would show the correction is
    over-sharpening thermal transport.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
    implements bounded HSL theta displacements, midpoint departure winds,
    bilinear remapping, finite fallbacks, and the theta-form thermodynamic
    tendency used by `dino_hsl2_theta`.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` and
    `src/dynamaxx/dycore/registry.py` expose side-by-side model aliases for the
    accepted HSL theta sequence.
  - Local history:
    `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
    accepted HSL theta transport with large positive iteration and validation
    gains.
  - Local history:
    `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
    accepted the current incumbent with iteration delta `+0.0071755259598786925`
    and validation delta `+0.007196436070573853`.
  - Local history:
    `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/decision.md`
    and `.logbook/history/2026-06-22_18-14-00_qmono-hsl-theta-remap/decision.md`
    are negative evidence against Eulerian/HSL tendency blends and higher-order
    theta remapping at the accepted departure point.
  - Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
    atmospheric models: a review. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
  - Temperton, C. and Staniforth, A. 1987. An efficient two-time-level
    semi-Lagrangian semi-implicit integration scheme. Quarterly Journal of the
    Royal Meteorological Society. https://doi.org/10.1002/qj.49711347709
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
    to Geophysics, second edition. Springer.
    https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This proposal is intentionally adjacent to the accepted HSL theta path because
that is the strongest recent positive evidence, but it is not a duplicate of
existing staging. Staged `vertical-coherent-hsl-theta` changes vertical
regularity of the departure winds, and staged `rotational-hsl-theta-departure`
changes which wind component defines the departure. This proposal keeps the
same full wind and asks only whether one additional fixed-point correction
improves the accepted midpoint trajectory.

It is also distinct from the rejected `qmono-hsl-theta-remap`, because the
theta remap remains the incumbent bilinear remap. It avoids the rejected
`cfl-blended-hsl-theta` failure mode because it never blends Eulerian and HSL
tendencies or introduces spatial CFL weights.

## Evaluator Notes

### 2026-06-22T21:57:42Z

Decision: move to `ready`; rank 1 of current candidates.

This is the strongest next implementation target because it extends the
highest-signal accepted path while staying narrowly scoped. Local history gives
two direct positives: first-order horizontal semi-Lagrangian theta transport
improved iteration by `+0.1070074439676863` and validation by
`+0.10295803136629866`, then midpoint departure improved the new incumbent by
`+0.0071755259598786925` on iteration and `+0.007196436070573853` on
validation with clean diagnostics. A single additional fixed-point correction
tests whether trajectory accuracy still has residual value without changing
the theta remap, transport variable, forecast contract, target metrics, or
evaluation protocols.

The proposal also avoids the two most relevant recent failures. It is not a
pointwise Eulerian/HSL blend, matching the lesson from `cfl-blended-hsl-theta`
failing fast with nonfinite forecasts even after bounded repair. It is not a
higher-order theta remap, matching the lesson from `qmono-hsl-theta-remap`,
which passed fast but failed iteration with delta `-0.05861772497361423`,
early RMSE regressions, and materially higher runtime. Its expected cost is
one extra wind remap and displacement calculation, so runtime risk is real but
substantially lower than qmono's expensive interpolation-order change.

The scientific claim is adequately supported by local source and established
semi-Lagrangian trajectory practice: the incumbent already has bounded
departure displacement, midpoint remapped winds, bilinear remap, and finite
fallback hooks in `primitive_equations.py`, and fixed-point departure
iteration is a standard semi-Lagrangian trajectory refinement. If implemented,
keep the experiment strictly side-by-side as `dino_hsl_picard`, preserve the
accepted bilinear theta remap and fallback chain, and require tests proving
uniform-wind equivalence to the incumbent midpoint path plus fallback on
nonfinite corrected midpoint winds.
