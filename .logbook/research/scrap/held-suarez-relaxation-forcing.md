---
schema_version: 1
slug: held-suarez-relaxation-forcing
title: Add Weak Held-Suarez Relaxation Forcing
status: scrap
created_at: 2026-06-16T09:33:33Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add Weak Held-Suarez Relaxation Forcing

## Hypothesis

The current Dinosaur incumbent is a dry, mostly adiabatic primitive-equation
rollout with horizontal diffusion but no thermal relaxation or boundary-layer
momentum sink. The finite incumbent metrics show broad negative skill versus
persistence, with especially large long-lead drift in `2m_temperature`,
`mean_sea_level_pressure`, and `geopotential_500`. Adding the existing
Held-Suarez-style Newtonian temperature relaxation and lower-atmosphere Rayleigh
drag should reduce unphysical free-atmosphere drift over the 1-15 day forecast
window while preserving the fixed WeatherBench2 forecast contract.

## Mechanism

Compose the existing dry sigma-coordinate primitive-equation object with
`held_suarez.HeldSuarezForcingSigma` before constructing the IMEX SIL3 stepper.
The forcing adds zonally symmetric Newtonian relaxation toward an analytic
equilibrium temperature and Rayleigh damping that increases below the
Held-Suarez boundary-layer sigma threshold. The candidate should keep the same
pressure-level input conversion, zero orography, output packing, spectral
truncation, horizontal diffusion filter, lead times, target variables, and
evaluation protocols.

This should be implemented as a guarded adapter option such as
`apply_held_suarez_forcing`, so the Orchestrator can score a side-by-side
candidate or an in-place selected model without changing `ForecastInput` or
`WeatherState`.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Registry changes:
  - None required for the mechanism. If the Orchestrator selects side-by-side
    scoring, add only a small registered factory for a candidate model name.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` remains unchanged.
- Tests to update:
  - Add a deterministic `jit_forecast=False` forecast test showing the forced
    path preserves output variables, shape, and finite values.
  - Add a helper test showing the forced path composes exactly one primitive
    equation with one Held-Suarez explicit forcing through
    `time_integration.compose_equations`.
  - Preserve a dry unforced path test so the incumbent configuration remains
    constructible when the option is disabled.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and long leads if weak thermal relaxation reduces
    the incumbent cold drift recorded in iteration and validation artifacts.
  - `mean_sea_level_pressure` and `geopotential_500` at days 5-15 if reduced
    thermal drift improves column thickness and mass-field evolution.
  - Primary score should improve across more leads than digital-filter
    initialization because the forcing acts throughout the rollout.
- Expected neutral metrics:
  - Early day-1 large-scale fields should remain close to the unforced dycore if
    the forcing is weak relative to resolved synoptic dynamics.
- Possible regressions:
  - `10m_u_component_of_wind` may regress if Rayleigh drag damps useful low-level
    wind structure. The rejected hyperdiffusion history shows that the early
    10 m wind gate is sensitive and should be treated as a hard risk.
  - A zonally symmetric equilibrium temperature may degrade regional or seasonal
    anomalies if it is too strong for weather-scale forecasts.

## Risks

- Numerical stability:
  - Low to moderate. The forcing is an explicit tendency already implemented in
    the vendored Dinosaur source, but the combined equation still needs the
    fixed fast diagnostic gate.
- Compute cost:
  - Low. The forcing adds nodal temperature and velocity tendencies inside the
    existing stepper and does not increase forecast length or output size.
- Data leakage:
  - Low. The analytic Held-Suarez equilibrium and drag coefficients do not use
    future truth, validation statistics, new splits, or target-specific fitting.
- Physical plausibility:
  - Moderate. Held-Suarez forcing is deliberately idealized, but it represents
    missing large-scale radiative relaxation and boundary-layer friction more
    directly than another numerical diffusion change.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter flag and optional
    side-by-side factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Preferred side-by-side candidate name: `dinosaur_held_suarez`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_held_suarez`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_held_suarez --workers 4`.
  - Support for the hypothesis is a primary-score improvement over the finite
    `dinosaur` baseline, preferably led by medium- and long-lead improvements in
    `2m_temperature`, `mean_sea_level_pressure`, or `geopotential_500`.
  - Reject before validation if early leads 1-5 regress by more than the fixed
    gate for `10m_u_component_of_wind`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_held_suarez --workers 4`
    only after iteration promotion.
  - Validation should preserve the same broad direction of thermal and mass-field
    improvement without relying on a single variable or lead.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with worse primary score, or a primary gain
    offset by early 10 m wind failure, would show that the idealized forcing is
    not suitable for this fixed WeatherBench2 contract.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  constructs an unforced dry primitive-equation rollout with zero orography,
  optional humidity, and horizontal diffusion only.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
  implements `HeldSuarezForcingSigma` with Newtonian temperature relaxation and
  lower-atmosphere Rayleigh drag.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements `compose_equations` for combining one implicit-explicit equation
  with explicit forcing terms.
- Held, I. M. and Suarez, M. J. 1994. A Proposal for the Intercomparison of the
  Dynamical Cores of Atmospheric General Circulation Models. Bulletin of the
  American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- ECMWF OpenIFS documentation describes the Held-Suarez case as a dynamical-core
  benchmark using Newtonian temperature relaxation and lower-boundary linear
  drag. https://confluence.ecmwf.int/plugins/viewsource/viewpagesrc.action?pageId=56656082
- CESM documentation describes the Held-Suarez configuration as replacing full
  physics with temperature relaxation and simple lower-boundary linear drag for
  spectral-transform dycore tests. https://www.cesm.ucar.edu/models/simple/held-suarez

## Researcher Notes

This is not a duplicate of the rejected `scale-selective-hyperdiffusion`
candidate: it adds physically interpretable temperature and momentum tendencies
rather than changing the spectral damping curve that already degraded every
iteration target and failed the early 10 m wind gate.

This is also distinct from the staged `balanced-digital-filter-initialization`
idea, which only filters initialization imbalance, and from the staged
`near-surface-anomaly-diagnostics` idea, which is output-only and target-specific.
The finite incumbent artifacts show a broad free-rollout problem: iteration
mean skill is negative for all four scored variables, day-15 `2m_temperature`
bias is about `-8.84 K`, and day-15 `mean_sea_level_pressure` bias is about
`+45.56 Pa`. A weak prognostic forcing candidate is therefore materially broader
than either staged idea while still preserving the fixed forecast contract.

## Evaluator Notes

2026-06-16T09:37:10Z - Move to `staging`.

Source inspection confirms the implementation hooks exist: the adapter currently
constructs an unforced dry primitive-equation rollout, `HeldSuarezForcingSigma`
adds Newtonian temperature relaxation and low-level Rayleigh drag, and
`time_integration.compose_equations` can combine one implicit-explicit equation
with explicit forcing. Literature and model documentation support the
scientific description of Held-Suarez as an idealized dynamical-core benchmark,
not as calibrated real-weather physics: it replaces normal physics with a flat,
zonally symmetric relaxation/drag setup and is commonly run as a spun-up test
case.

Do not promote this ahead of digital filter initialization for iteration 4. The
proposal has a broad mechanism and low nominal compute cost, but the forcing
acts throughout the 1-15 day forecast and directly damps lower-atmosphere wind.
That overlaps the most sensitive failed gate from the rejected hyperdiffusion
candidate: early `10m_u_component_of_wind` RMSE. The implementation also has a
small but real adapter-structure risk because the current real-data state can
carry humidity tracers even when humidity is not active in the dry dynamics;
any composed explicit forcing must preserve matching tracer tendencies rather
than relying on a default empty tracer mapping.

Keep staged as a broader follow-up if the next lower-risk balance experiment
does not improve the finite baseline, or if a Researcher adds evidence for weak
coefficients that avoid low-level wind degradation under the fixed gates. Any
future implementation should remain side-by-side and must not change forecast
contracts, target variables, metrics, splits, or fixed protocols.

2026-06-16T10:58:43Z - Keep in `staging` after re-triage against
`dinosaur_dfi`.

The accepted DFI incumbent changes the comparison baseline and lowers this
proposal's immediate priority. The broad long-lead drift remains real under
`dinosaur_dfi`: existing validation artifacts still show negative mean skill
for all four fixed target variables, including large day-15 2 m temperature,
MSLP, Z500, and 10 m wind errors. A throughout-rollout thermal and momentum
forcing could therefore still teach something useful.

Do not promote it ahead of `standard-atmosphere-reference-profile`. Held-Suarez
forcing is an idealized climate-dycore benchmark, not calibrated weather
physics, and the lower-atmosphere Rayleigh drag directly touches the early
`10m_u_component_of_wind` gate that failed for hyperdiffusion. If selected
later, the proposal should be revised to target the current incumbent with a
side-by-side `dinosaur_dfi_*` candidate that preserves DFI, rather than scoring
against canonical `dinosaur`.

2026-06-16T12:04:45Z - Keep in `staging` after re-triage against
`dinosaur_dfi`.

The broad-drift motivation remains plausible because `dinosaur_dfi` is still a
dry, mostly unforced rollout with negative fixed-protocol validation skill.
Source inspection also confirms the Held-Suarez forcing and equation-composition
hooks are present. A reputable-source check supports the proposal's framing of
Held-Suarez as idealized Newtonian temperature relaxation plus lower-atmosphere
Rayleigh damping for dynamical-core testing.

Do not promote now. The mechanism is less tied to real WeatherBench2 initial
state consistency than the pressure-aware grid or terrain proposals, and it
acts throughout the rollout on both temperature and low-level momentum. That
directly overlaps the sensitive early `10m_u_component_of_wind` guardrail that
failed for hyperdiffusion. The front matter still targets canonical `dinosaur`;
if revived, this should be revised as a side-by-side `dinosaur_dfi_*` candidate
that preserves DFI and uses only fixed, literature-motivated coefficients rather
than validation-tuned relaxation.

2026-06-16T13:02:50Z - Keep in `staging` after Iteration 7 re-triage
against `dinosaur_dfi`.

Rank this second among the active staged ideas, behind terrain/orography. The
recent standard-atmosphere rejection weakens the case for another small
balance-partition experiment, and the pressure-grid rejection points away from
vertical-coordinate changes. Held-Suarez remains a broad missing-tendency idea
with local implementation hooks, but reputable OpenIFS documentation frames it
as an idealized flat-earth dynamical-core benchmark using Newtonian temperature
relaxation and low-level Rayleigh damping, not calibrated real-weather physics.

Do not promote now. The low-level Rayleigh drag directly touches the sensitive
early `10m_u_component_of_wind` guardrail that failed for hyperdiffusion, and
the proposal front matter still targets canonical `dinosaur` rather than the
accepted `dinosaur_dfi` incumbent. It should be revised before implementation
as a side-by-side `dinosaur_dfi_*` candidate with DFI preserved, fixed
literature-motivated coefficients, and no validation-tuned relaxation strength.

2026-06-16T14:16:35Z - Keep in `staging` after Iteration 8 re-triage against
`dinosaur_dfi` at `cfdc344723cee1f267b892ddd924fc5d07b89f2d`.

Rank this second behind `near-surface-anomaly-diagnostics`. The broad
missing-tendency hypothesis remains plausible, and local Held-Suarez forcing
hooks are present. Reputable references continue to support the description of
Held-Suarez as Newtonian temperature relaxation plus lower-boundary linear drag
for idealized dynamical-core testing.

Do not move to `ready` now. The recent terrain-aware rejection showed that
aggregate primary-score improvement can hide unacceptable early Z500 and MSLP
RMSE regressions, so a throughout-rollout forcing that perturbs temperature,
mass evolution, and low-level winds is a higher guardrail risk than an
output-only near-surface diagnostic. The current proposal also still needs
revision for the accepted `dinosaur_dfi` incumbent, including a side-by-side
candidate name, preserved DFI, fixed literature-motivated coefficients, and
tracer-safe equation composition if humidity tracers are present.

2026-06-16T15:27:07Z - Keep in `staging` after Iteration 9 re-triage against
`dinosaur_dfi_surface_residual` at
`845de671268f42c6b44b0a60c287e043087364a1`.

Rank this behind `mass-diagnostic-analysis-residuals`. The new incumbent
already captures a large low-risk share of the near-surface diagnostic error by
using output-only residuals while leaving mass fields effectively unchanged.
That makes a narrow mass-diagnostic residual follow-up more directly connected
to the remaining fixed-score gap than an idealized prognostic Held-Suarez
forcing.

Keep staged rather than ready or scrap. The broad missing-tendency mechanism
could still be informative later, and local source hooks exist for composing
Held-Suarez forcing. However, it now has three unresolved issues before it
should be considered for implementation: the front matter still targets
canonical `dinosaur`, the proposal must be revised to preserve both DFI and the
accepted near-surface residual correction in a side-by-side
`dinosaur_dfi_surface_residual_*` candidate, and the lower-atmosphere Rayleigh
drag remains a direct risk to the sensitive early `10m_u_component_of_wind`
guardrail. The terrain-aware failure also raises caution for any throughout-
rollout tendency that can perturb early mass-field RMSE. Do not promote unless
the ready mass-residual experiment fails or new evidence supports fixed,
literature-motivated weak coefficients without validation tuning.

2026-06-16T16:25:41Z - Move to `scrap` after Iteration 10 re-triage against
`dinosaur_dfi_surface_residual` at
`845de671268f42c6b44b0a60c287e043087364a1`.

This staged proposal is now superseded by
`.logbook/research/ready/wind-sparing-held-suarez-relaxation.md`, which
keeps the useful Held-Suarez thermal-relaxation question but fixes the stale
proposal's blockers. The older file still targets canonical `dinosaur`, does
not explicitly preserve the accepted near-surface residual correction, and
includes lower-atmosphere Rayleigh drag that directly risks the sensitive early
`10m_u_component_of_wind` guardrail. Keeping both active would create duplicate
Held-Suarez branches with the weaker, outdated one competing against a more
incumbent-aware revision.

The scientific premise remains plausible enough for the revised proposal, but
this version should not be implemented as written. Scrapping it avoids selecting
an obsolete contract while retaining the notes that motivated the revised
wind-sparing candidate.
