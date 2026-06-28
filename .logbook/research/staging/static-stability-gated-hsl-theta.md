---
schema_version: 1
slug: static-stability-gated-hsl-theta
title: Static-Stability Gate for Midpoint HSL Theta
status: staging
created_at: 2026-06-23T00:00:00Z
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

# Static-Stability Gate for Midpoint HSL Theta

## Hypothesis

The accepted `dino_hsl2_theta` midpoint departure improved horizontal
dry-theta transport, while a second Picard correction was clean but neutral.
That suggests the useful trajectory-accuracy gain is mostly exhausted. A
remaining risk is not trajectory order, but occasional local over-displacement
of theta in strongly sheared or frontal columns, where the midpoint HSL
increment can erode dry static stability even though all fields remain finite.

A dry-static-stability gate that reverts only those columns from midpoint HSL
to the accepted first-order HSL theta tendency should preserve most of the
validated midpoint transport while avoiding columns where the midpoint
increment locally weakens vertical theta separation too aggressively. The
expected benefit is lower early-to-medium `geopotential_500` and
`mean_sea_level_pressure` error without adding a higher-order remap, an
Eulerian blend, or another trajectory correction.

## Mechanism

Add one side-by-side model alias, `dino_hsl_stab`, extending `dino_hsl2_theta`.

For this candidate only:

- preserve the accepted `dino_hsl2_theta` stack: DFI, weak-HS analysis
  equilibrium, symmetric Coriolis split, theta-form thermodynamics, theta mean
  recentering, SIL3 off-centering, scale-separated residuals, ocean bulk
  sensible heat flux, midpoint HSL departure, bilinear remap, output variables,
  lead schedule, and evaluation protocols;
- compute the same finite first-order and midpoint HSL horizontal theta
  tendencies already available inside `horizontal_semilagrangian_theta_transport`;
- estimate the local explicit horizontal-theta update from the midpoint
  tendency using the existing inner-step size;
- diagnose adjacent-layer dry-theta differences before and after that midpoint
  horizontal update;
- where a column that was initially statically stable would have any adjacent
  theta separation reduced below a fixed fraction, for example
  `HSL_THETA_STATIC_STABILITY_MIN_FRACTION = 0.25`, select the accepted
  first-order HSL theta tendency for all layers in that column;
- use the accepted midpoint HSL theta tendency everywhere else;
- if first-order diagnostics are also invalid, or if any stability diagnostic is
  nonfinite or shape-incompatible, fall back exactly to the accepted
  `dino_hsl2_theta` fallback chain;
- do not alter the actual wind state, departure geometry in accepted columns,
  remap order, vertical theta transport, pressure-work term, log-pressure
  tendency, momentum equations, humidity, filters, residuals, or output packing.

This is a stability-aware selector between the two already accepted HSL theta
trajectory levels. It is not a CFL-weighted Eulerian/HSL blend, not a qmono or
higher-order remap, not a Picard or multi-iteration trajectory update, not a
vertical-advection rewrite, and not a post-step dry-static-stability adjustment.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model registered as `dino_hsl_stab`.
- API changes:
  - None. Forecast inputs, outputs, lead times, target variables, metrics, and
    protocols remain fixed.
- Tests to update:
  - Verify the candidate factory preserves all `dino_hsl2_theta` options except
    model name and the static-stability HSL selector.
  - Unit-test that stable columns with acceptable midpoint increments select the
    midpoint tendency exactly.
  - Unit-test that a synthetic midpoint increment that erodes adjacent-layer
    theta separation below the fixed fraction selects the first-order HSL
    tendency for that column.
  - Verify columns that are already neutral or inverted do not receive an
    unphysical new stability correction; they follow the accepted incumbent
    finite fallback chain.
  - Verify nonfinite stability diagnostics fall back to accepted `dino_hsl2_theta`
    behavior.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 1 to 8 if rare
    midpoint-overdisplacement columns are seeding hydrostatic and pressure-phase
    errors.
  - `2m_temperature` at medium leads if lower-column thermal structure benefits
    from guarding vertical theta separation in frontal regions.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because the prognostic
    momentum equations, Coriolis split, diffusion, and 10 m wind diagnostic are
    unchanged.
- Possible regressions:
  - The accepted midpoint tendency may already have the best balance, and
    reverting selected columns to first-order HSL may remove useful midpoint
    phase accuracy.
  - A columnwise selector can introduce small discontinuities in the theta
    tendency near the stability threshold.

## Risks

- Numerical stability:
  - Low to moderate. The candidate selects between two existing finite-guarded
    HSL theta tendencies, but the selector touches thermodynamic transport
    every inner step and must avoid nonfinite mask propagation.
- Compute cost:
  - Low. It adds adjacent-layer theta-difference diagnostics and boolean masks
    on existing HSL tendencies; no extra remap, trajectory solve, output, or
    evaluation protocol is required.
- Data leakage:
  - None. It uses only current forecast theta, current-step HSL tendencies, and
    fixed sigma-layer ordering.
- Physical plausibility:
  - Moderate to high. Dry static stability is a core hydrostatic primitive-
    equation constraint, and the gate is conservative in scope because it only
    reverts to the already accepted first-order HSL transport.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_stab`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_stab --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failure, and an
    iteration primary-score improvement of at least `+0.002` against cached
    `dino_hsl2_theta` artifacts.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_stab --workers 4`
    only after iteration promotion.
  - Support requires validation primary-score improvement of at least `+0.001`
    with clean diagnostics and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that midpoint HSL
    static-stability erosion is not a material remaining error source. Any
    early wind, MSLP, or Z500 guardrail failure would show the columnwise
    first-order fallback disrupts the accepted midpoint balance.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` implements the
  current first-order HSL theta fallback, midpoint HSL theta tendency, bilinear
  remap, and finite diagnostics used by `dino_hsl2_theta`.
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` and
  `src/dynamaxx/dycore/registry.py` provide the incumbent side-by-side factory
  and registry pattern.
- Local history:
  `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
  accepted first-order HSL theta with large iteration and validation gains.
- Local history:
  `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
  accepted midpoint HSL theta with additional positive iteration and validation
  deltas.
- Local history:
  `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/decision.md`,
  `.logbook/history/2026-06-22_18-14-00_qmono-hsl-theta-remap/decision.md`,
  and
  `.logbook/history/2026-06-22_21-59-29_picard-hsl-theta-departure/decision.md`
  rule out the nearest failed directions: Eulerian/HSL blending, higher-order
  theta remapping, and extra Picard trajectory correction.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: a review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This proposal avoids the recent failed modes explicitly. It never blends the
Eulerian theta tendency with HSL, so it avoids the nonfinite
`cfl-blended-hsl-theta` failure mode. It keeps the accepted bilinear remap and
does not add qmono/PCHIP interpolation, so it avoids the expensive remap
regression. It does not compute another Picard or fixed-point departure
trajectory, so it avoids repeating the neutral Picard result.

It is distinct from staged `hydrostatic-theta-monotone-initialization`, which
acts only on the initial state, and from scrapped or staged broad dry-static-
stability adjustments, which modify the prognostic state or physical forcing
after a step. This proposal changes only the theta horizontal HSL tendency
selector inside the accepted thermodynamic transport hook. It is also distinct
from staged `vertical-coherent-hsl-theta`, `rotational-hsl-theta-departure`,
`theta-upwind-vertical-advection`, `vertical-courant-limited-advection`,
`mass-flux-theta-transport`, and `semilag-logp-advection`.

## Evaluator Notes

### 2026-06-23T00:40:08Z

Decision: move to `staging`; rank 2 of 2 current proposals.

This is plausible and source-compatible, but it should not be the next target.
It correctly avoids the recent failed modes: it does not blend Eulerian and
HSL tendencies, does not increase remap order, and does not add another
trajectory correction after the neutral Picard result. Selecting between the
accepted first-order and midpoint HSL theta tendencies is also rollbackable and
fits the existing finite fallback structure.

Keep it staged because its main control is a new fixed static-stability
threshold, and the metric benefit depends on rare local midpoint
over-displacements that are not yet documented by diagnostics. A columnwise
first-order fallback can introduce discontinuous theta-tendency masks and may
remove useful midpoint phase accuracy in exactly the frontal and sheared
columns where dry static stability is most sensitive. That is a higher
empirical-tuning and balance risk than the mean-neutral proposal, which tests a
global discrete conservation property without changing trajectory selection.

If promoted later, require a single documented threshold fixed before
evaluation, no validation tuning, exact incumbent behavior for neutral or
already inverted columns, and tests proving non-theta tendencies, pressure,
momentum, tracers, filters, and output packing remain unchanged. The same
fixed gates and incumbent-cache policy apply.
