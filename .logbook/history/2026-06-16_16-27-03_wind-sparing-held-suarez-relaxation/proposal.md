---
schema_version: 1
slug: wind-sparing-held-suarez-relaxation
title: Add Wind-Sparing Weak Held-Suarez Thermal Relaxation
status: ready
created_at: 2026-06-16T16:23:40Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual
expected_code_paths:
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

# Add Wind-Sparing Weak Held-Suarez Thermal Relaxation

## Hypothesis

The accepted incumbent `dinosaur_dfi_surface_residual` preserves the useful
digital-filter initialization and output-only near-surface residual correction,
but it is still a dry, mostly adiabatic primitive-equation free rollout. Existing
incumbent artifacts show negative validation mean skill versus persistence for
all four fixed target channels, with day-15 validation skill of about `-2.555`
for `2m_temperature`, `-1.886` for `mean_sea_level_pressure`, `-0.871` for
`geopotential_500`, and `-1.718` for `10m_u_component_of_wind`.

A very weak Held-Suarez-style Newtonian relaxation of temperature toward the
standard zonally symmetric equilibrium should reduce the largest thermal and
hydrostatic drift over days 5-15 without replacing the accepted initialization or
surface diagnostic corrections. To address the early `10m_u_component_of_wind`
guardrail risk, the first model-selection candidate should disable direct
Rayleigh momentum drag and apply only a predeclared, weak thermal relaxation.

## Mechanism

Add an adapter option that composes the existing primitive-equation object with
`held_suarez.HeldSuarezForcingSigma` through
`time_integration.compose_equations`, but expose a side-by-side registered
candidate named `dinosaur_dfi_surface_residual_weak_hs` that keeps:

- `apply_digital_filter_initialization=True`;
- `apply_near_surface_residual_correction=True`;
- the incumbent pressure-level input conversion and finite pressure-level output
  extrapolation;
- the incumbent equidistant sigma grid, spectral truncation, horizontal
  diffusion filter, variables, lead times, and fixed evaluation protocols.

The candidate should set the Held-Suarez friction coefficient to zero
(`kf = 0 / day`) and weaken the standard thermal relaxation rates by a fixed
factor of four before any model-selection evaluation (`ka = 1 / 160 days`,
`ks = 1 / 16 days`). This is deliberately a single prespecified candidate, not a
coefficient search. The forcing should return zero tracer tendencies matching
any tracers carried in the state so composition preserves the current WeatherState
contract when humidity channels are present but not active in the dry dynamics.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only a side-by-side factory for
    `dinosaur_dfi_surface_residual_weak_hs`; do not change the existing
    `dinosaur`, `dinosaur_dfi`, or `dinosaur_dfi_surface_residual` entries.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` and all fixed target
    variables, leads, splits, and metrics remain unchanged.
- Tests to update:
  - Add a factory/registry test confirming the candidate preserves DFI and the
    near-surface residual correction.
  - Add a deterministic `jit_forecast=False` forecast test showing the forced
    path returns finite requested outputs with the same variables and shapes.
  - Add a composition test confirming exactly one primitive-equation object is
    combined with one explicit weak Held-Suarez thermal forcing and that the
    candidate uses `kf=0`, `ka=1/160 day`, and `ks=1/16 day`.
  - Add a tracer-shape test or explicit wrapper check showing humidity tracers,
    when carried through the state, receive zero forcing tendencies rather than
    being dropped from the pytree.

## Expected Metric Movement

- Expected improvements:
  - Medium- and long-lead `2m_temperature`, where the incumbent has large cold
    drift by day 15 (`validation bias ~= -8.632 K`).
  - Medium- and long-lead `mean_sea_level_pressure` and `geopotential_500` if
    weaker temperature drift improves hydrostatic thickness and mass-field
    evolution without the terrain/MSLP guardrail failure seen previously.
  - Aggregate primary score if the broad long-lead skill losses are partly
    caused by missing weak thermal damping rather than only missing moist or
    terrain processes.
- Expected neutral metrics:
  - Early day-1 mass fields should remain close to the incumbent because the
    relaxation time scales are 16-160 days and DFI is unchanged.
  - Near-surface residual improvements in `2m_temperature` and
    `10m_u_component_of_wind` should be retained because the accepted output-only
    correction is still applied after the trajectory is converted to
    WeatherState outputs.
- Possible regressions:
  - `10m_u_component_of_wind` can still regress indirectly through changed
    pressure gradients, even with `kf=0`. This must be treated as a hard
    iteration guardrail, not something to tune against validation.
  - A zonally symmetric equilibrium temperature can damp useful regional or
    seasonal anomalies if the weak relaxation is still too strong for
    deterministic 1-15 day hindcasts.

## Risks

- Numerical stability:
  - Low to moderate. The forcing object exists in the vendored Dinosaur code,
    but the composed equation must be checked for finite fast diagnostics and
    matching tracer pytrees.
- Compute cost:
  - Low. The candidate adds explicit thermal tendencies inside the existing
    stepper; it does not increase resolution, output volume, lead count, or
    worker count.
- Data leakage:
  - Low. The Held-Suarez equilibrium and the fixed weakening factor are analytic
    and prespecified. Do not estimate coefficients from iteration or validation
    truth.
- Physical plausibility:
  - Moderate. Held-Suarez forcing is an idealized dycore benchmark rather than a
    real NWP physics suite. The proposal is justified as a weak missing thermal
    relaxation test, not as calibrated radiation or boundary-layer physics.
- Rollback complexity:
  - Low. The change can be isolated behind an adapter option and one side-by-side
    factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs`.
  - Require finite forecasts, zero diagnostic issues, preserved output variables,
    and no WeatherState contract changes.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs --workers 4`.
  - Support for the hypothesis requires at least the fixed `+0.002` primary-score
    promotion threshold versus `dinosaur_dfi_surface_residual` and clean
    diagnostics.
  - Reject before validation if early lead-days 1-5 mean RMSE regresses by more
    than the fixed 2% guardrail for `10m_u_component_of_wind`, or if any fixed
    variable/lead RMSE regression exceeds the 10% guardrail.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs --workers 4`
    only after iteration promotion.
  - Do not change `kf`, `ka`, `ks`, decay hours, DFI settings, metrics, target
    variables, leads, or splits after seeing validation results.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with a sub-threshold or negative primary
    delta would show that weak analytic thermal relaxation does not move the
    fixed WeatherBench2 score enough beyond the accepted DFI plus surface
    residual incumbent.
  - Any early `10m_u_component_of_wind`, `mean_sea_level_pressure`, or
    `geopotential_500` guardrail failure would show that even the wind-sparing
    weak forcing is too intrusive for the fixed model-selection contract.

## Citations

- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society, 75, 1825-1830.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- GFDL-hosted Held and Suarez paper PDF describes the benchmark as evaluating
  dycores independently of full physical parameterizations.
  https://www.gfdl.noaa.gov/bibliography/related_files/ih9401.pdf
- CESM Held-Suarez documentation describes replacing full physics with
  temperature relaxation toward a zonally symmetric equilibrium and lower
  boundary linear drag for spectral-transform dycore tests.
  https://www.cesm.ucar.edu/models/simple/held-suarez
- OpenIFS documentation describes the Held-Suarez case as a flat-earth dycore
  benchmark with Newtonian temperature relaxation and low-level Rayleigh damping.
  https://confluence.ecmwf.int/plugins/viewsource/viewpagesrc.action?pageId=56660076
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
  implements `HeldSuarezForcingSigma`; `time_integration.py` implements
  `compose_equations`; `adapter.py` currently exposes DFI and near-surface
  residual options for side-by-side factories.
- Prior accepted history:
  `.logbook/history/2026-06-16_09-54-58_balanced-digital-filter-initialization`
  and
  `.logbook/history/2026-06-16_14-27-30_near-surface-anomaly-diagnostics`.

## Researcher Notes

This is a revised version of the staged Held-Suarez line, not an edit to the
staged proposal. The important differences are that it targets the current
`dinosaur_dfi_surface_residual` incumbent, explicitly preserves both accepted
mechanisms, uses a side-by-side candidate, and removes direct Rayleigh momentum
drag in the first candidate to reduce the early `10m_u_component_of_wind`
guardrail risk.

This is not a near-duplicate of rejected hyperdiffusion because it changes
thermal forcing rather than the spectral damping curve. It is not a near-duplicate
of rejected terrain, pressure-grid, standard-atmosphere, mass-residual, or moist
virtual-temperature experiments because it does not alter orography/MSLP
diagnosis, vertical coordinates, the semi-implicit reference profile, output-only
mass residuals, or humidity dynamics. The rejected mass-residual result also
argues against another output correction proposal: the remaining plausible
research question is whether a weak prognostic thermal tendency can move the
long-lead drift while retaining the incumbent's accepted output corrections.

## Evaluator Notes

2026-06-16T16:25:41Z - Move to `ready` for Iteration 10 ranking against
`dinosaur_dfi_surface_residual` at
`845de671268f42c6b44b0a60c287e043087364a1`.

This is the strongest active proposal after the mass-diagnostic residual
rejection. It is a revised Held-Suarez experiment that fixes the staged
version's main blockers: it targets the current incumbent, preserves both
accepted mechanisms (DFI and near-surface residual diagnostics), uses a
side-by-side candidate, makes no forecast-contract or fixed-protocol change,
and removes direct Rayleigh momentum drag by setting `kf = 0`. The code surface
is still local to the Dinosaur adapter, candidate export/registration, and
focused tests.

Literature/source check supports only the broad mechanism, not a guarantee of
WeatherBench2 skill: Held and Suarez proposed an idealized dycore benchmark for
evaluating dynamical cores independently of full physics
(https://www.gfdl.noaa.gov/bibliography/related_files/ih9401.pdf), and CESM and
OpenIFS documentation describe the standard case as Newtonian temperature
relaxation toward a zonally symmetric equilibrium with lower-boundary linear
drag (https://www.cesm.ucar.edu/models/simple/held-suarez,
https://confluence.ecmwf.int/plugins/viewsource/viewpagesrc.action?pageId=56660076).
That makes the proposal physically interpretable but still idealized weather
forcing; the weakened thermal-only variant is a risk-control adaptation for
this fixed short-range evaluation, not a literature-standard configuration.

Promote as the only ready proposal because it has a clear, predeclared,
low-leakage mechanism with useful failure information: if weak thermal
relaxation does not move long-lead thermal/mass drift, the loop should pivot
away from simple analytic forcing. Main risks remain indirect early
`10m_u_component_of_wind`, `mean_sea_level_pressure`, or `geopotential_500`
guardrail regressions because the tendency acts throughout the rollout. The
Orchestrator should select or defer; Evaluator is not making an implementation
or acceptance decision.
