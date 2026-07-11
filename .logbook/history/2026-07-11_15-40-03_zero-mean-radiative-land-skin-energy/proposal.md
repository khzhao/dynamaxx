---
schema_version: 1
slug: zero-mean-radiative-land-skin-energy
title: Zero-Mean Radiative Energy for the Prognostic Land Skin
status: ready
created_at: 2026-07-11T15:31:00Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/radiation.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Zero-Mean Radiative Energy for the Prognostic Land Skin

## Hypothesis

The accepted analysis-initialized land skin supplies a useful slowly evolving
lower-boundary state, but after initialization it exchanges heat only with the
lowest atmospheric layer and its fixed deep node. It has no diurnally phased
radiative energy source or nonlinear longwave loss. The two accepted endpoint
experiments show that late T2m remains sensitive to the physical evolution of
the surface state, while the rejected realized-flux observer shows that
reinterpreting the vertical profile away from those endpoints is harmful.

A zero-net radiative tendency applied to the prognostic land skin, not to the
atmosphere or output observer, can evolve the accepted endpoint with local solar
phase and Stefan-Boltzmann cooling without changing its mean heat inventory,
analysis anchor, Richardson geometry, cap, mask, or ramp. This tests missing
surface-energy physics rather than another endpoint interpolation.

## Mechanism

Register one side-by-side descendant of the incumbent. Preserve every accepted
trajectory and output path except for one additional term in the land-skin
reservoir update:

- use the existing orbital/local-time utilities to compute top-of-atmosphere
  insolation on the current model grid and model time;
- form the local-time insolation anomaly by subtracting its land-area-weighted
  mean at each step, so the shortwave term adds exactly zero net land energy;
- use a single frozen broadband absorbed fraction of `0.7`, corresponding to a
  canonical `0.3` surface albedo, with no land-class or seasonal variants;
- add a unit-emissivity Stefan-Boltzmann exchange proportional to
  `T_deep**4 - T_skin**4`, then remove its land-area-weighted mean as well so the
  candidate changes spatial/diurnal structure but not total land-skin energy;
- convert radiative power to a skin-temperature tendency using the existing
  accepted air/skin heat-capacity ratio and exchange-depth air heat capacity,
  rather than adding a separately fitted thermal inertia;
- multiply the radiative term by the unchanged accepted land-skin forecast-time
  ramp and land weight, and include it under the existing `0.05 K` per-step skin
  increment cap;
- leave the accepted air-skin exchange, deep restore, analyzed initialization,
  ocean path, RI2m observer, residual memory, and all non-T2m outputs unchanged;
- return the exact incumbent update for missing time, invalid geometry, empty
  land, or any nonfinite radiative diagnostic.

The shortwave amplitude, albedo, emissivity, heat capacity, ramp, and cap are
frozen before scoring. No alternative radiation branch or coefficient may be
tested after model-selection results.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for one selector, model-time
    and longitude/latitude plumbing, the bounded land-skin radiative increment,
    and one factory.
  - `src/dynamaxx/dycore/models/dinosaur/radiation.py` only if a small existing-
    utility wrapper is needed; do not introduce a radiation package.
  - Dinosaur exports, registry, and focused tests.
- Registry changes:
  - Suggested suffix: `_rskin` on the current incumbent key.
- API changes:
  - None. The deterministic single-trajectory input/output contract and target
    variables remain unchanged; the skin remains private carry state.
- Tests to update:
  - Exact selector-off, pre-ramp, ocean, empty-land, missing-time, and nonfinite
    fallback.
  - Shortwave longitude/local-time phase and exact land-area neutrality.
  - Longwave sign, exact land-area neutrality, and zero deep/skin contrast.
  - Heat-capacity conversion and retention of the accepted total per-step cap.
  - Exact non-T2m output and factory parity, registry/dependency, and finite
    smoke coverage.

## Expected Metric Movement

- Expected improvements:
  - Late land `2m_temperature`, especially where the accepted skin endpoint
    retains the correct mean state but lacks diurnal phase evolution.
  - A plausible primary gain is `+0.002` to `+0.006` if the missing zero-net
    surface-energy redistribution is broad across the iteration years.
- Expected neutral metrics:
  - Ocean T2m, MSLP, Z500, U10, and all outputs through 120 hours should remain
    exact or at numerical trajectory-coupling scale.
- Possible regressions:
  - Top-of-atmosphere insolation without clouds, vegetation, snow, or soil
    moisture can overstate local surface forcing even when its mean is removed.
  - Radiative evolution may move the accepted analyzed skin endpoint away from
    the empirically useful persistence signal.

## Risks

- Numerical stability:
  - Low to moderate. The term changes private skin carry only and retains the
    accepted cap/fallback, but nonlinear fourth-power temperatures require safe
    finite evaluation.
- Compute cost:
  - Low. It adds local radiation algebra per skin step and no extra trajectory.
- Data leakage:
  - None. It uses forecast time, grid geometry, forecast skin/deep state, and
    fixed physical constants only.
- Physical plausibility:
  - Moderate. Surface shortwave and longwave energy are physical; exact mean
    removal and the reduced heat capacity make this a controlled anomaly
    closure rather than a full land model.
- Rollback complexity:
  - Low to moderate. Remove one selector/helper/plumbing path, factory/export,
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run focused/full tests and fixed candidate fast; require finite output and
    clean diagnostics.
- Iteration gate:
  - Run candidate-only iteration with four workers against the valid cached
    incumbent. Require delta at least `+0.002`, clean diagnostics, and both
    fixed RMSE guardrails.
- Validation gate:
  - Run exactly once only after promotion and require delta at least `+0.001`
    with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold iteration result, or late T2m regression, means the
    accepted skin benefits from persistence rather than this reduced radiative
    evolution. Scrap without varying albedo, emissivity, heat capacity, ramp,
    cap, or mean-removal domain.

## Citations

- Sellers, W. D. 1965. Physical Climatology. University of Chicago Press.
- Dickinson, R. E. 1984. Modeling evapotranspiration for three-dimensional
  global climate models. *Climate Processes and Climate Sensitivity*.
  https://doi.org/10.1029/GM029p0058
- Stefan, J. 1879 and Boltzmann, L. 1884, summarized in standard surface-energy
  balance formulations; the implementation should use the repository's fixed
  SI constants and established radiation utilities.
- Local positive evidence:
  `.logbook/history/2026-07-10_23-59-52_analysis-2m-initialized-land-skin-memory/decision.md`.
- Local negative evidence:
  `.logbook/history/2026-07-11_11-07-05_realized-flux-screen-temperature-observer/decision.md`.

## Researcher Notes

This is not a surface-profile, flux-similarity, inferred-roughness, residual-
decay, analysis-anchor, or cap/ramp variant. It changes the private prognostic
skin energy budget while preserving the accepted observer exactly. It is also
not staged `solar-weighted-thermal-tendency` or `clear-sky-longwave-relaxation`,
which force atmospheric temperature; this candidate applies an exactly
land-energy-neutral anomaly only to the accepted skin carry. The fixed mean
removal is a conservation constraint, not a score-calibrated bias correction.

## Evaluator Notes

### 2026-07-11T15:36:45Z

Decision: move to `ready`; ranked #1 of the eight evaluated ideas and selected
as the sole bounded next experiment.

The fresh realized-flux observer result is direct negative evidence against
another profile reinterpretation: it worsened iteration score by
`-0.0033294021286252445`, late T2m RMSE by `+1.0835601461%`, and the worst T2m
lead by `+1.6351374594%` despite clean non-T2m diagnostics. This proposal leaves
that observer, RI2m geometry, and all nearby roughness/profile choices unchanged.
Instead it tests physical positive-time evolution of the accepted private land
skin, whose analysis initialization supplied `+0.0168874870` iteration and
`+0.0172148378` validation. T2m is the only negative target skill, so this is
more direct than spending balance margin on a mass-field or momentum change.

The experiment is frozen as follows. Derive one candidate directly from
`dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori`
with only the radiative skin-update selector enabled. For each initialization,
use the existing `SolarRadiation` implementation referenced to that sample's
fixed initial time. Use absorbed shortwave `0.7 * F_TOA` and unit-emissivity
`sigma_SB * (T_deep**4 - T_skin**4)`; remove each field's native-grid-area and
active-land-weighted mean before multiplying by the unchanged active land
weight. Convert the resulting power with the existing 50 m exchange depth,
heat-capacity ratio `4.0`, forecast-state lowest-layer ideal-gas density, and
repository `c_p`, with no new thermal-inertia coefficient. Apply the unchanged
120-240 h scalar ramp. If the radiative skin increment exceeds `0.05 K` in any
active cell, apply one common scalar reduction to the whole radiative field so
its zero-net land-energy property is retained; do not pointwise clip it. Any
missing time, invalid geometry, empty active-land domain, nonpositive
temperature/density, or nonfinite intermediate returns the exact incumbent
skin update for that step.

No albedo, emissivity, heat capacity, coefficient, cap, ramp, mask, anchor,
mean-removal domain, observer, or atmospheric-radiation variant is permitted.
The fixed protocols and forecast contract remain unchanged. The main guardrail
risk is that clear-sky TOA phase forcing can move the useful analyzed skin
memory in the wrong direction; a clean subthreshold score or any late-T2m
regression falsifies this exact formulation without a retune.
