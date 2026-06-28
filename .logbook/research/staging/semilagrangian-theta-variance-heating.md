---
schema_version: 1
slug: semilagrangian-theta-variance-heating
title: Return Bounded Heating from HSL Theta Interpolation Damping
status: staging
created_at: 2026-06-23T11:17:35Z
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

# Return Bounded Heating from HSL Theta Interpolation Damping

## Hypothesis

The accepted HSL2 theta path likely improves RMSE by making horizontal thermal
transport less phase-erroneous, but bilinear semi-Lagrangian interpolation is
not energy conserving. Over 15-day rollouts it can damp resolved theta variance
without returning any dissipated thermal energy to the column. The current
incumbent has increasingly cold `2m_temperature` bias, reaching about `-1.56 K`
by day 15 in the cached iteration artifact, so a small missing-energy term is a
plausible remaining error source.

A bounded heating return tied only to diagnosed HSL theta-variance loss should
be more physical than a free thermal ramp and safer than the rejected
pressure-work additions, because it uses a local numerical dissipation budget
from the already accepted transport path.

## Mechanism

Register `dino_hsl2_theta_hsl_heat` as a side-by-side model. Preserve all
incumbent dynamics and HSL2 departure geometry. Inside the HSL theta transport
helper, estimate layerwise area-weighted theta-anomaly variance before and
after the accepted remap. When the remap reduces variance, convert a fixed,
small, bounded fraction of the diagnosed loss into a positive temperature
tendency distributed within the same sigma layer.

The first implementation should:

- use the same HSL2 remapped theta already computed for the thermal tendency;
- compute only layerwise global variance loss, not local pointwise heating from
  noisy gradients;
- cap the returned temperature increment per inner step and per day;
- remove the layer mean from the transport tendency before applying the existing
  theta mean recentering, so this mechanism does not fight the incumbent zero
  mode;
- fallback to zero returned heating if any variance or conversion diagnostic is
  nonfinite.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused primitive-equation and registry tests
- Registry changes:
  - Add one side-by-side model, `dino_hsl2_theta_hsl_heat`.
- API changes:
  - None.
- Tests to update:
  - Verify zero heating when HSL remap preserves theta variance or diagnostics
    are nonfinite.
  - Verify the heating cap bounds synthetic large variance loss.
  - Verify non-thermal tendencies and output routing remain unchanged.
  - Verify the candidate factory preserves all incumbent flags except the new
    interpolation-heating selector.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 5-15 if interpolation damping contributes to the
    incumbent cold drift.
  - `geopotential_500` through warmer, more realistic column thickness at
    medium leads.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because momentum and the
    Richardson diagnostic are unchanged.
  - `mean_sea_level_pressure` should be less exposed than in pressure-work
    candidates because no log-pressure or divergence tendency is added.
- Possible regressions:
  - Returning heat from numerical damping can warm the lower troposphere for the
    wrong synoptic situations and degrade thickness or MSLP.

## Risks

- Numerical stability:
  - Low to moderate with strict caps; unbounded heating is not acceptable.
- Compute cost:
  - Low. The remapped theta field already exists; the new work is layerwise
    reductions and local additions.
- Data leakage:
  - None. The budget is computed only from the forecast step.
- Physical plausibility:
  - Moderate. Energy fixers for numerical dissipation are common, but mapping
    scalar interpolation damping to heat is approximate.
- Rollback complexity:
  - Low. Remove one option/helper, one factory/export, registry entry, and
    tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_theta_hsl_heat`
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_theta_hsl_heat --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, no
    early `2m_temperature`, Z500, MSLP, or wind guardrail failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_theta_hsl_heat --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold delta would show HSL interpolation energy loss is not a
    material score source. Any MSLP/Z500 short-lead guardrail failure would show
    the returned heating is dynamically inconsistent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  computes HSL remapped theta and can diagnose the before/after anomaly fields.
- Cached incumbent artifact: `outputs/eval/iteration_dino_hsl2_theta.csv`
  records `2m_temperature` bias drifting from `-0.146 K` at 24 h to
  `-1.563 K` at 360 h.
- Dynamaxx research comparison:
  `.logbook/research/staging/theta-diffusion-dissipative-heating.md` and
  `.logbook/research/staging/dissipative-heating-from-horizontal-diffusion.md`
  target explicit diffusion losses; this proposal targets HSL interpolation
  damping specifically.
- Lauritzen, P. H., Skamarock, W. C., Prather, M. J., and Taylor, M. A. 2012.
  A standard test case suite for two-dimensional linear transport on the
  sphere. Geoscientific Model Development.
  https://doi.org/10.5194/gmd-5-887-2012
- Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
  Atmospheric Models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is not a simple heat-source amplitude or ramp variant. The heating budget
is computed from the accepted HSL remap's own diagnosed damping and is capped
before it reaches the model state. It is also not a pressure-work proposal:
there is no added `omega alpha`, divergence, or log-surface-pressure tendency.
It differs from staged diffusion-heating ideas by tying the source to
semi-Lagrangian interpolation loss, the transport mechanism that produced the
current incumbent.

## Evaluator Notes

### 2026-06-23T11:21:12Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

The idea is mechanistically plausible but not the best next score-producing
experiment. It is distinct from diffusion-heating staging because it diagnoses
variance loss from the accepted HSL theta remap rather than from the horizontal
diffusion filter. It also avoids the rejected pressure-work path by adding no
log-pressure, divergence, or omega-alpha tendency. That makes it worth keeping
as a future bounded energy-accounting test.

Do not promote it ahead of `dry-static-energy-hsl-transport`. The proposed
heating is positive definite, globally diagnosed by layer, and applied every
inner step, so it can easily warm the wrong columns and perturb Z500/MSLP even
with caps. The current staging queue already contains related thermodynamic
energy-return ideas (`theta-diffusion-dissipative-heating`,
`dissipative-heating-from-horizontal-diffusion`, and
`surface-drag-theta-dissipation`), all of which carry the same balance risk.
The DSE transport proposal is a cleaner first test because it changes the
transported invariant without adding a new heat source.
