---
schema_version: 1
slug: mean-neutral-hsl-theta-transport
title: Mean-Neutral Horizontal HSL Theta Transport
status: ready
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

# Mean-Neutral Horizontal HSL Theta Transport

## Hypothesis

The accepted `dino_hsl2_theta` incumbent shows that horizontal
semi-Lagrangian transport of dry-theta anomaly is a high-signal thermodynamic
change. The current bilinear remap is finite and robust, but it is not exactly
area-mean neutral on the discrete spherical grid. Any small layerwise horizontal
theta-mean increment from the remap is later corrected by the accepted
post-step theta recentering filter, after it has already passed through
temperature conversion, pressure work, and the coupled primitive-equation step.

Making the horizontal HSL theta tendency itself area-mean neutral by layer
should reduce spurious zero-mode thermal forcing while preserving the accepted
departure geometry, bilinear interpolation, finite fallback, and forecast
contract. The expected benefit is cleaner hydrostatic thickness and mass-field
coupling without increasing interpolation order or introducing an Eulerian/HSL
blend.

## Mechanism

Add one side-by-side model alias, `dino_hsl_mean`, extending
`dino_hsl2_theta`.

For this candidate only:

- preserve all accepted `dino_hsl2_theta` behavior: midpoint HSL theta
  departure, bilinear remap, finite fallback chain, DFI, weak-HS analysis
  equilibrium, symmetric Coriolis split, theta mean recentering, SIL3
  off-centering, residual corrections, ocean bulk sensible heat flux, output
  variables, lead schedule, and evaluation protocols;
- after the first-order and midpoint HSL theta-anomaly remaps are computed,
  diagnose the quadrature-weighted horizontal layer mean of
  `remapped_theta_anomaly - theta_anomaly`;
- subtract that layer-mean increment from the corresponding remapped theta
  anomaly before converting the remap difference into a horizontal theta
  tendency;
- apply the correction only to accepted finite HSL candidate tendencies, never
  to vertical theta transport, pressure-work terms, momentum tendencies,
  log-pressure continuity, passive humidity, residual corrections, or output
  packing;
- fall back exactly to the accepted `dino_hsl2_theta` tendency if quadrature
  weights, layer-mean increments, corrected remapped theta, or corrected
  tendency are nonfinite or shape-incompatible.

This is a discrete-conservation refinement of the accepted HSL theta path. It
is not a new remap order, not a CFL or Eulerian/HSL tendency blend, not an
additional departure-point iteration, not a vertical-advection change, and not a
post-step thermal recentering replacement.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model registered as `dino_hsl_mean`.
- API changes:
  - None. Forecast inputs, outputs, lead times, target variables, metrics, and
    protocols remain fixed.
- Tests to update:
  - Verify the candidate factory preserves all `dino_hsl2_theta` options except
    model name and the new mean-neutral HSL selector.
  - Unit-test that a corrected HSL theta tendency has zero
    quadrature-weighted horizontal mean in each sigma layer.
  - Verify zero wind still reproduces the accepted incumbent fallback behavior.
  - Verify nonfinite quadrature or corrected-remap diagnostics fall back to the
    accepted `dino_hsl2_theta` tendency.
  - Verify non-theta tendencies, pressure, momentum, tracers, filters, and
    output packing are unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if small
    remap-induced thermal zero modes are feeding hydrostatic thickness or mass
    drift before the post-step recentering filter acts.
  - `2m_temperature` at medium and late leads if lower-column theta anomaly
    transport benefits from removing spurious layer-mean remap increments.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to incumbent because momentum,
    Coriolis splitting, diffusion, and the Richardson 10 m diagnostic are
    unchanged.
- Possible regressions:
  - The accepted bilinear HSL remap may rely on its tiny numerical mean
    increment as part of the empirical balance with pressure work and the
    post-step theta recentering filter.
  - Removing the horizontal zero-mode increment can slightly change thermal
    conversion before the semi-implicit solve and may perturb early MSLP/Z500.

## Risks

- Numerical stability:
  - Low to moderate. The candidate adds a bounded layerwise scalar correction to
    already finite-guarded HSL remaps, but it touches thermodynamic transport
    every inner step.
- Compute cost:
  - Low. It adds one quadrature-weighted mean per layer for existing remapped
    theta fields; grid size, lead count, workers, and remap order are unchanged.
- Data leakage:
  - None. It uses only current forecast state and fixed grid quadrature weights.
- Physical plausibility:
  - High. Horizontal advection of a dry thermodynamic tracer should not create a
    global layer-mean tracer source on a closed sphere.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_mean`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_mean --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failure, and an
    iteration primary-score improvement of at least `+0.002` against cached
    `dino_hsl2_theta` artifacts.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_mean --workers 4`
    only after iteration promotion.
  - Support requires validation primary-score improvement of at least `+0.001`
    with clean diagnostics and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that discrete HSL
    theta mean increments are not a material remaining error source. Any early
    MSLP or Z500 guardrail failure would show the mean-neutral correction
    disrupts the accepted thermal-pressure balance.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` implements the
  accepted bounded HSL theta displacement, bilinear remap, and finite fallback
  chain used by `dino_hsl2_theta`.
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements the accepted
  rollout-only `_theta_layer_mean_recenter_step_filter`, showing that
  layerwise dry-theta means are already a useful invariant in this model family.
- Local history:
  `.logbook/history/2026-06-19_00-02-28_theta-zero-mode-thermal-recentering/decision.md`
  accepted layerwise theta mean recentering with positive iteration and
  validation deltas.
- Local history:
  `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
  and
  `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
  accepted the HSL theta path and midpoint departure refinement.
- Local history:
  `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/decision.md`,
  `.logbook/history/2026-06-22_18-14-00_qmono-hsl-theta-remap/decision.md`,
  and
  `.logbook/history/2026-06-22_21-59-29_picard-hsl-theta-departure/decision.md`
  are negative evidence against Eulerian/HSL blends, higher-order theta remaps,
  and extra trajectory correction after the accepted midpoint path.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: a review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric
  transport schemes: desirable properties and a semi-Lagrangian view on
  finite-volume discretizations. In Numerical Techniques for Global Atmospheric
  Models. https://doi.org/10.1007/978-3-642-11640-7_8

## Researcher Notes

This proposal avoids the recent failed modes explicitly. It does not blend the
Eulerian theta tendency with HSL, so it avoids the nonfinite
`cfl-blended-hsl-theta` pattern. It keeps the bilinear remap and adds only a
layer-mean scalar correction, so it avoids the expensive higher-order qmono
remap that regressed iteration. It does not add another departure-point solve,
so it avoids repeating the neutral Picard trajectory result.

It is not a duplicate of accepted theta mean recentering or rejected
mass-weighted theta recentering because it acts inside the horizontal HSL
theta transport tendency before temperature conversion and the semi-implicit
step, not as a post-step zero-mode temperature filter. It is also distinct from
staged `mass-flux-theta-transport`, `full-state-theta-thermodynamic-tendency`,
`vertical-coherent-hsl-theta`, `rotational-hsl-theta-departure`, and
`semilag-logp-advection`; those change transport form, transported variable,
departure-wind structure, departure-wind decomposition, or log-pressure
advection.

## Evaluator Notes

### 2026-06-23T00:40:08Z

Decision: move to `ready`; rank 1 of 2 current proposals.

This is the strongest next HSL-theta candidate because it is a localized
discrete-conservation refinement of the accepted `dino_hsl2_theta` path. The
recent accepted history shows large positive signal from horizontal HSL theta
transport and a smaller but repeatable gain from midpoint departures, while
the rejected follow-ups warn against Eulerian/HSL blends, higher-order remaps,
and extra trajectory solves. This proposal avoids all three failed patterns:
it keeps the accepted bilinear remap, accepted midpoint geometry, finite
fallback chain, and theta-only scope, then removes only the quadrature-weighted
layer-mean increment introduced by the remap before the tendency feeds thermal
conversion and pressure coupling.

The idea is not a duplicate of the accepted rollout theta recentering. That
filter corrects the post-step state, while this candidate tests whether the
HSL horizontal theta tendency should be mean-neutral before the coupled
primitive-equation step. It is also distinct from active staged ideas:
`vertical-coherent-hsl-theta` and `rotational-hsl-theta-departure` alter the
departure wind, `mass-flux-theta-transport` changes the transport form,
`full-state-theta-thermodynamic-tendency` changes the thermodynamic scalar, and
`semilag-logp-advection` touches mass continuity.

Expected implementation risk is low relative to the potential lesson. The
incumbent source has a narrow `horizontal_semilagrangian_theta_transport` hook
with first-order and midpoint remapped theta anomalies already available, and
the adapter has established side-by-side factory and registry patterns.
Require the fixed gates exactly as specified: `pytest`, `fast`, `iteration
--workers 4`, and `validation --workers 4` only after iteration promotion.
Compare only against authoritative cached `dino_hsl2_theta` leaderboard
artifacts unless a concrete cache invalidity is found.
