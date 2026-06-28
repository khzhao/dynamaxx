---
schema_version: 1
slug: solar-weighted-thermal-tendency
title: Add a Weak Solar-Weighted Lower-Tropospheric Thermal Tendency
status: staging
created_at: 2026-06-18T17:18:05Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a Weak Solar-Weighted Lower-Tropospheric Thermal Tendency

## Hypothesis

The incumbent retains the accepted weak Held-Suarez thermal relaxation, but that
forcing is zonally symmetric and time independent. The rejected calendar-aware
candidate showed that displacing the Held-Suarez equilibrium seasonally was too
aggressive for 2 m temperature. A smaller positive-time tendency tied to local
top-of-atmosphere insolation can add a physically timed diurnal/seasonal thermal
signal while preserving the accepted Held-Suarez equilibrium geometry and
global-mean thermal source.

If part of the remaining 2 m temperature drift is due to missing local solar
phase rather than the residual decay itself, a bounded lower-tropospheric solar
tendency should improve `2m_temperature` after day 1 without changing wind
initialization, surface residual decay timescales, pressure initialization, or
fixed evaluation protocols.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_solar_thermal`.
Preserve the incumbent primitive equation, DFI, weak Held-Suarez forcing,
near-surface residual correction, log-pressure/hydrostatic initialization,
horizontal diffusion, exact Coriolis Strang split, output variables, and fixed
lead schedule.

Add an opt-in explicit equation wrapper after the primitive equation and before
or alongside weak Held-Suarez composition:

- use the existing `radiation.py` orbital-time utilities and the forecast
  initial timestamp to compute local normalized insolation as a function of
  model time, longitude, and latitude;
- project the tendency onto the lower troposphere, for example sigma centers
  greater than 0.7, with a smooth vertical taper;
- subtract the area-weighted horizontal mean of the solar anomaly at each layer
  so the candidate does not remove or replace the accepted global-mean weak-HS
  heating/cooling signal;
- apply a small fixed amplitude cap, such as no more than 0.25 K per day local
  equivalent heating before nondimensionalization;
- add the tendency only to `temperature_variation`; leave vorticity,
  divergence, `log_surface_pressure`, tracers, and diagnostics unchanged;
- use the same wrapper for DFI and positive-time rollout only if model time can
  be signed consistently. If signed time handling is not clean, keep DFI on the
  incumbent equation and apply the solar tendency only during positive-time
  rollout, recording that choice in implementation notes.

The proposal is a single fixed forcing candidate, not a sweep over amplitude,
vertical taper, or calendar phase.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/radiation.py` only if a small helper is
    needed for vectorized normalized flux
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. The forecast contract, inputs, outputs, target variables, leads, and
    protocols remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent option except the
    solar-thermal tendency flag.
  - Unit-test that the added tendency is finite, area-mean zero by layer, zero
    outside the lower-tropospheric taper, and bounded by the fixed amplitude.
  - Verify only `temperature_variation` receives a direct tendency.
  - Verify the tendency changes with longitude/local time and is deterministic
    for identical initial timestamps.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2 to 15 if missing local solar phase contributes to
    residual post-correction drift.
  - `geopotential_500` may improve slightly if lower-tropospheric thermal
    thickness drift is reduced without broad equilibrium shifts.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be less exposed than in thermal
    recentering experiments because this tendency is weak, local, and does not
    change initialized winds or surface residual decay.
  - `mean_sea_level_pressure` should remain close to incumbent if the
    layerwise area-mean tendency removal protects global mass-thickness balance.
- Possible regressions:
  - Even weak lower-tropospheric heating can perturb baroclinicity and degrade
    wind, MSLP, or Z500 phase.
  - If the accepted near-surface residual already captures the useful local
    surface signal, the added tendency may be redundant or harmful.

## Risks

- Numerical stability:
  - Low to moderate. The tendency is weak and bounded, but it adds persistent
    positive-time thermal forcing.
- Compute cost:
  - Low. The insolation calculation is local grid algebra and does not change
    resolution, lead count, or worker count.
- Data leakage:
  - Low. The mechanism uses only forecast initialization time, model time,
    longitude, latitude, and fixed astronomical constants. It must not use
    verification targets or validation-derived tuning.
- Physical plausibility:
  - Moderate. Insolation is a real thermal driver, and the repo already vendors
    TOA radiation utilities, but this is not a full radiation, cloud, land, or
    boundary-layer scheme.
- Rollback complexity:
  - Low. Remove one forcing wrapper/flag, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_solar_thermal`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_solar_thermal --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_solar_thermal --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that local
    solar-phase forcing is not a material remaining error source. Any early
    2 m temperature, MSLP, Z500, or 10 m wind guardrail failure would show that
    the simplified heating disrupts the accepted balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/radiation.py` already
  contains orbital-time and top-of-atmosphere radiation utilities with fixed
  solar constants.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py` defines
  the accepted Held-Suarez equilibrium and thermal relaxation structure used by
  the incumbent.
- History: `.logbook/history/2026-06-16_23-51-06_calendar-aware-solar-relaxation/decision.md`
  rejected seasonal displacement of the weak-HS equilibrium after 2 m
  temperature regressions; this proposal preserves that equilibrium and adds a
  much weaker bounded anomaly.
- History: `.logbook/history/2026-06-17_23-29-54_mass-neutral-weak-hs-forcing/decision.md`
  rejected removing the accepted global-mean weak-HS thermal tendency; this
  proposal keeps the accepted mean source and only makes the added solar anomaly
  layerwise area-mean zero.
- Held, I. M. and Suarez, M. J. 1994. A Proposal for the Intercomparison of the
  Dynamical Cores of Atmospheric General Circulation Models. Bulletin of the
  American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- NASA Earth Observatory, Climate and Earth's Energy Budget, summarizes solar
  energy as the driver of Earth's climate system:
  https://earthobservatory.nasa.gov/features/EnergyBalance
- NOAA NCEI Total Solar Irradiance Climate Data Record documents TSI as a
  measured climate data record:
  https://www.ncei.noaa.gov/products/climate-data-records/total-solar-irradiance

## Researcher Notes

This is not another residual-decay variant: it does not change residual
amplitude, residual variables, residual decay bounds, or residual physical
proxies. It adds a physically timed thermal tendency to the prognostic
temperature field.

It is distinct from active staged boundary-layer Rayleigh drag and dissipative
heating. It does not damp momentum and does not convert numerical wind-energy
loss into heat. It is also distinct from staged log-sigma adiabatic temperature
tendency because it is an external lower-tropospheric forcing, not a rewrite of
adiabatic thermodynamic transport.

## Evaluator Notes

### 2026-06-18T17:21:29Z

Decision: move to `staging`, not `ready`.

The proposal is physically motivated and implementable because the repository
already has radiation/orbital utilities and the suggested anomaly is bounded
and area-mean neutral by layer. It is distinct from the rejected
calendar-aware weak-Held-Suarez equilibrium shift because it preserves the
accepted equilibrium and adds a small local anomaly rather than moving the
background relaxation target.

Keep it staged because the direct family evidence is poor. Calendar-aware
solar relaxation regressed iteration by `-0.040271379533892704` with 2 m
temperature guardrail failures, and mass-neutral weak-Held-Suarez forcing
regressed by `-0.05788584798245422`, also through 2 m temperature. Even a weak
positive-time thermal tendency can perturb baroclinicity, MSLP, and Z500 after
the current incumbent already gained strongly from a safer output residual
mechanism. Rank it behind the ready Richardson wind diagnostic and behind the
best staged transient/energy-budget fallbacks until residual-output ideas are
exhausted or diagnostics point specifically to missing local solar phase.
