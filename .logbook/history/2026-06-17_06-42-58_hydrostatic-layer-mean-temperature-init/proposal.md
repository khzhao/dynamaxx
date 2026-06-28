---
schema_version: 1
slug: hydrostatic-layer-mean-temperature-init
title: Use Layer-Mean Hypsometric Temperature Initialization
status: ready
created_at: 2026-06-17T06:38:45Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init
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

# Use Layer-Mean Hypsometric Temperature Initialization

## Hypothesis

The current incumbent's largest accepted gain came from replacing analyzed
pressure-level temperature with a dry temperature diagnosed from same-time
geopotential thickness before the accepted log-pressure sigma remap. That
confirmed hydrostatic consistency is a high-signal initialization axis for this
adapter. The implementation currently estimates a level-centered temperature
from one-sided or centered finite differences of geopotential in log pressure.
Those point derivatives can amplify level noise, especially at the top and
bottom pressure levels.

A layer-mean hypsometric reconstruction should preserve the same physical
constraint while using the hydrostatic quantity that pressure-level thickness
directly defines: mean virtual temperature between pressure interfaces. This may
retain the accepted mass-field improvement while reducing the short-lead
`2m_temperature` regressions introduced by the incumbent hydrostatic
initialization.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
Preserve incumbent DFI, weak Held-Suarez thermal relaxation, near-surface
residual diagnostics, log-pressure pressure-to-sigma remapping, T80 truncation,
900 s inner step, finite output extrapolation, and zero orography.

Add a guarded initialization option that replaces
`_hydrostatic_temperature_from_geopotential_thickness` with a layer-mean method:

- compute hypsometric dry layer-mean temperature between adjacent analyzed
  pressure levels from `-(Phi_{k+1} - Phi_k) / (R_d * ln(p_{k+1} / p_k))`,
  including the existing humidity virtual-temperature conversion when humidity
  is present;
- assign each pressure level a bounded average of adjacent layer means, using
  the single adjacent layer at top and bottom boundaries;
- fall back to analyzed temperature at points where the reconstructed
  temperature is nonfinite or nonpositive;
- pass the resulting pressure-level temperature through the incumbent
  log-pressure pressure-to-sigma interpolation.

This is not a tunable blend: it changes the hydrostatic estimator from a
pointwise derivative to a finite-layer hypsometric average.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` and fixed target variables
    remain unchanged.
- Tests to update:
  - Unit-test the layer-mean helper on an analytic hydrostatic column where the
    reconstructed temperature matches known layer means.
  - Verify fallback to analyzed temperature for nonfinite or nonpositive
    reconstructions.
  - Verify the factory preserves incumbent DFI, weak Held-Suarez relaxation,
    near-surface residuals, log-pressure initialization, spectral resolution,
    and inner step.
  - Verify the new registry entry constructs and has the expected model name.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` should retain most of the
    incumbent hydrostatic-initialization gain if layer-mean thickness is the
    better-balanced thermal input.
  - Short-lead `2m_temperature` may improve relative to the incumbent because
    layer-endpoint derivative noise is reduced before near-surface residuals are
    applied.
  - Primary score may improve modestly at days 1-7 if the initialization is less
    noisy but still hydrostatically balanced.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be nearly neutral because wind
    initialization, DFI, weak thermal relaxation, and near-surface wind residuals
    are unchanged.
- Possible regressions:
  - Z500 and MSLP could regress if the accepted point-derivative hydrostatic
    projection was beneficial because it sharpened vertical structure rather
    than because it reduced imbalance.
  - 2 m temperature can still regress if the analyzed pressure-level thermal
    field carries useful near-surface structure that any hydrostatic
    reconstruction smooths away.

## Risks

- Numerical stability:
  - Low to moderate. This changes only initialization, but the accepted
    hydrostatic initialization showed short-lead `2m_temperature` sensitivity.
- Compute cost:
  - Low. The method adds one vertical pass per initial state and no rollout cost.
- Data leakage:
  - Low. It uses only same-time pressure-level geopotential, temperature,
    humidity when already present, and pressure coordinates.
- Physical plausibility:
  - High. The hypsometric equation relates layer thickness and layer-mean
    virtual temperature under hydrostatic balance.
- Rollback complexity:
  - Low. The candidate can be isolated behind one adapter flag and one
    side-by-side factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean but sub-threshold iteration delta, early `2m_temperature` guardrail
    failure, or mass-field RMSE regression would show that the incumbent
    point-derivative hydrostatic estimator is already the better choice.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  the accepted log-pressure and hydrostatic-thickness initialization path in
  `weather_state_to_dinosaur_state` and
  `_hydrostatic_temperature_from_geopotential_thickness`.
- History: `.logbook/history/2026-06-17_05-33-37_hydrostatic-thickness-initialization/decision.md`
  accepted the current incumbent with iteration primary delta
  `+0.0668578150568` and validation primary delta
  `+0.06740481815858179`, while noting short-lead `2m_temperature` as the main
  sensitive regression channel.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- ECMWF IFS Documentation Part III describes hydrostatic primitive-equation
  vertical discretization and the relation between pressure thickness,
  temperature, and geopotential in the dynamical core.
- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press. The hypsometric equation is the standard
  hydrostatic relationship between pressure thickness and layer-mean virtual
  temperature.

## Researcher Notes

This is a direct follow-up to an accepted mechanism, but it is not a duplicate:
the incumbent diagnoses level-centered temperature with finite differences,
while this proposal diagnoses layer-mean hypsometric temperature and maps those
layer means back to levels. It does not change surface pressure, orography,
sigma grid placement, output interpolation, DFI settings, Held-Suarez geometry,
wind control variables, metrics, target variables, or evaluation protocols.

Negative evidence from `standard-atmosphere-reference-profile`,
`pressure-aware-sigma-layer-grid`, and `helmholtz-wind-initialization` argues
against broader balance-partition or coordinate changes. This proposal stays on
the narrow initialization axis that has repeatedly produced measurable gains:
DFI, log-pressure initialization, and hydrostatic-thickness initialization.

## Evaluator Notes

2026-06-17T06:41:34Z - Move to `ready`; rank 1 of 4 active ideas for the next
dycore iteration.

This is the strongest next experiment because it directly refines the current
incumbent's largest accepted mechanism. The incumbent
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init` improved
iteration primary by `+0.0668578150568` and validation primary by
`+0.06740481815858179` by replacing analyzed pressure-level temperature with a
hydrostatic-thickness reconstruction before the already accepted log-pressure
sigma remap. The accepted scoring notes also identify short-lead
`2m_temperature` as the main remaining sensitive regression channel, with the
largest accepted variable-lead RMSE regression at 24 h. A layer-mean
hypsometric estimator is a credible, non-tunable way to keep the hydrostatic
constraint while reducing one-sided/centered derivative noise at pressure-level
endpoints.

Prior history supports this narrow scope. Accepted DFI, weak Held-Suarez,
log-pressure initialization, and hydrostatic-thickness initialization all
improved fixed scores when they preserved the forecast API and changed only
well-defined initialization or weak thermal-balance behavior. In contrast,
pressure-aware sigma grid placement regressed iteration primary by
`-0.10322710509965427`, Helmholtz wind initialization regressed by
`-0.34423230670441374`, and terrain-aware orography failed early Z500/MSLP
guardrails despite a large aggregate primary gain. This proposal avoids those
broader coordinate, wind-control, and terrain/mass changes.

The main risk is that it is adjacent to two thermal ideas with guardrail
sensitivity. The accepted hydrostatic incumbent has small short-lead
`2m_temperature` regressions, and rejected layer-mean thermal recentering
improved primary but failed the early `10m_u_component_of_wind` RMSE guardrail
by just over 2%. This proposal is still preferable because it is
initialization-only, does not recenter the forecast thermal field, and leaves
DFI, weak Held-Suarez, near-surface residuals, output interpolation, sigma grid,
vertical advection, and scoring protocols unchanged. The Implementer should add
focused tests for analytic hypsometric columns, humidity conversion, invalid
fallbacks, and exact preservation of all incumbent flags.
