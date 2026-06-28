---
schema_version: 1
slug: layer-mean-thermal-recentering
title: Recenter Layer-Mean Temperature During Forward Rollout
status: ready
created_at: 2026-06-17T03:07:20Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Recenter Layer-Mean Temperature During Forward Rollout

## Hypothesis

The incumbent still develops a persistent cold `2m_temperature` bias and
increasing mass-field error over days 5-15, even after accepted DFI,
near-surface residual diagnostics, weak wind-sparing Held-Suarez thermal
relaxation, and log-pressure initialization. The validation artifact for the
incumbent shows `2m_temperature` bias near `-4.3 K` by day 15 and steadily
worsening `mean_sea_level_pressure` and `geopotential_500` skill with lead.

In a dry hydrostatic primitive-equation forecast without full radiation,
convection, surface fluxes, or resolved topography, unconstrained drift of the
global layer-mean thermal state can contaminate both near-surface temperature
and hydrostatic thickness. A conservative step filter that preserves the
post-DFI area-mean temperature variation in each sigma layer during the forward
rollout should remove only the global thermal drift mode while leaving spatial
temperature anomalies, winds, pressure anomalies, DFI, and accepted residual
diagnostics intact.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter`. Preserve the
incumbent DFI path exactly. During the positive-time forecast rollout only, add
a step filter after the normal IMEX step and existing horizontal diffusion that
copies the previous state's spectral zero-wavenumber coefficient of
`temperature_variation` for each sigma layer into the next state.

The filter should:

- affect only the layerwise global-mean modal coefficient of
  `temperature_variation`
- leave nonzero temperature modes, vorticity, divergence, log surface pressure,
  passive tracers, and `sim_time` unchanged
- run only in the scored forward trajectory, not inside the time-reversed DFI
  integration
- preserve weak Held-Suarez thermal relaxation for spatial modes while
  preventing net global layer-mean thermal drift after initialization
- preserve the fixed `ForecastInput -> WeatherState` contract, target
  variables, lead times, metrics, and evaluation splits

This is a state constraint, not a coefficient search: the first candidate should
have no tunable relaxation strength.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter`.
- API changes:
  - None. Preserve deterministic `forecast(ForecastInput) -> WeatherState`.
- Tests to update:
  - Unit-test the filter on a small `primitive_equations.State` to confirm only
    layerwise zero-wavenumber `temperature_variation` coefficients are copied
    from the previous state.
  - Verify vorticity, divergence, log surface pressure, tracers, and nonzero
    temperature modes are unchanged by the filter.
  - Verify the candidate preserves incumbent DFI, near-surface residuals, weak
    Held-Suarez relaxation, log-pressure initialization, step size, and spectral
    truncation.
  - Add a non-JIT finite smoke forecast test for the side-by-side candidate.

## Expected Metric Movement

- Expected improvements:
  - Medium- and long-lead `2m_temperature` if the remaining cold drift has a
    substantial global or zonal-mean component.
  - `geopotential_500` and `mean_sea_level_pressure` may improve through reduced
    hydrostatic-thickness drift.
  - Aggregate primary score should improve most at days 7-15 if the mechanism is
    correct.
- Expected neutral metrics:
  - Early day-1 fields should remain close to the incumbent because DFI and the
    initialized state are unchanged.
  - `10m_u_component_of_wind` should be mostly neutral because the filter does
    not directly damp momentum or alter vorticity/divergence.
- Possible regressions:
  - The accepted weak Held-Suarez relaxation may rely partly on changing the
    layer-mean temperature; freezing that mode could remove some of its benefit.
  - Weather-scale global-mean thermal evolution over 15 days is not exactly
    zero, so an overly strict recentering constraint could worsen seasonal or
    hemispheric temperature evolution.
  - Hydrostatic mass fields can regress if current thermal drift compensates a
    pressure or wind bias.

## Risks

- Numerical stability:
  - Low. The filter edits a bounded modal coefficient and does not add divisions,
    new variables, or longer trajectories.
- Compute cost:
  - Negligible relative to the incumbent. The filter is one modal array update
    per inner step and does not change output volume or worker count.
- Data leakage:
  - Low. The preserved value is carried from the model state after accepted DFI;
    it does not use future truth, validation statistics, or target-specific
    fitting.
- Physical plausibility:
  - Moderate. Global integral fixers are common in atmospheric models, but this
    proposal uses layerwise temperature variation as a dry static-energy proxy
    rather than enforcing a complete total-energy budget.
- Rollback complexity:
  - Low. The mechanism can be isolated behind one adapter flag and one
    side-by-side factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter --workers 4`.
  - Compare against exact incumbent records for
    `dinosaur_dfi_surface_residual_weak_hs_logp_init`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure, ideally led by long-lead
    `2m_temperature`, `geopotential_500`, or `mean_sea_level_pressure`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean but sub-threshold iteration delta, early `2m_temperature` guardrail
    failure, or mass-field guardrail failure would show that layer-mean thermal
    drift is not a useful remaining correction axis for this incumbent.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` constructs
    the accepted incumbent with DFI, weak Held-Suarez relaxation, near-surface
    residual correction, log-pressure initialization, and step filters.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
    exposes step-filter composition suitable for a side-by-side modal
    recentering constraint.
  - Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP
    and climate models. Journal of Computational Physics.
    https://doi.org/10.1016/j.jcp.2006.08.016
  - Williamson, D. L. and Olson, J. G. 1994. Climate simulations with a
    semi-Lagrangian version of the NCAR Community Climate Model. Monthly Weather
    Review. Conservation fixers in later CAM documentation follow this family
    of global integral corrections.
    https://doi.org/10.1175/1520-0493(1994)122%3C1594:CSWASL%3E2.0.CO;2
  - ECMWF IFS documentation and technical memoranda describe global fixers as a
    practical method for restoring conserved integral quantities after
    numerical transport steps.
    https://www.ecmwf.int/en/elibrary/74226-global-mass-fixer-algorithms-conservative-tracer-transport-ecmwf-model
  - ECMWF IFS Documentation Part III describes the hydrostatic relation linking
    temperature, pressure thickness, and geopotential in the dynamical core.
    https://www.ecmwf.int/sites/default/files/elibrary/112024/81625-ifs-documentation-cy49r1-part-iii-dynamics-and-numerical-procedures.pdf

## Researcher Notes

This proposal is not a pure Held-Suarez coefficient tune. It preserves the
accepted weak Held-Suarez forcing and adds a no-parameter global thermal
constraint during the forward rollout. It is also not a duplicate of rejected
`calendar-aware-solar-relaxation`, which changed the thermal-equilibrium
geometry and produced large `2m_temperature` regressions. Here the equilibrium
geometry is unchanged and only the globally averaged layerwise drift mode is
removed.

The rejected `global-mean-pressure-anchor` is relevant negative evidence but not
a duplicate: that candidate fixed one log-surface-pressure mode and had too
small an effect. This proposal targets the measured long-lead cold thermal bias
and hydrostatic thickness error by constraining temperature zero modes across
all sigma layers. The rejected divergence damping, 600 s time step,
hyperdiffusion, vertical-advection suppression, and T120 experiments argue
against broad stability or damping changes; this candidate is a narrow modal
constraint with negligible compute cost and no forecast-contract change.

## Evaluator Notes

2026-06-17T03:11:14Z - Move to `ready`; rank 2 of 4 active ideas, but not the recommended next implementation target.

This proposal is implementable and potentially high-signal, so it belongs in
`ready`, but it should rank behind Helmholtz wind initialization because it
modifies the forward trajectory at every inner step rather than only the initial
state. Source inspection confirms `temperature_variation` is a modal state leaf,
the adapter already composes forward step filters, and weak Held-Suarez forcing
is composed as an explicit thermal tendency. The requested filter can therefore
be isolated without new data, dependencies, target variables, or forecast API
changes.

The empirical premise is supported by the incumbent artifacts when filtering to
the incumbent model rows. In
`outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`,
`2m_temperature` bias is about `-4.287846045298119 K` at 360 h and RMSE is about
`10.37768330203996 K`; the iteration split shows the same long-lead cold bias
pattern. That gives this proposal a clearer metric-facing target than many
prior conservation-style ideas.

Scientific support is mixed but sufficient for a ready side-by-side experiment.
The cited conservation literature and ECMWF mass-fixer documentation support
using global integral fixers as practical numerical corrections, especially for
transport errors. However, freezing layerwise zero-wavenumber
`temperature_variation` is not the same as enforcing total dry energy, moist
energy, or mass conservation. It may also remove part of the accepted weak
Held-Suarez benefit if that benefit depends on changing the global layer-mean
thermal state. This is why the proposal is ready but not ranked first.

Relevant history raises both upside and caution. The rejected global mean
pressure anchor was clean but effect-free, showing that one zero-mode pressure
constraint can be too weak. This proposal touches all thermal layers and targets
a measured long-lead temperature drift, so it is not a duplicate. The rejected
calendar-aware solar relaxation shows that changing thermal forcing geometry can
badly regress `2m_temperature`; this proposal is narrower because it preserves
the accepted equilibrium shape and constrains only the global layer means. If
implemented, require a no-tunable-strength version, no validation tuning, and
close inspection of long-lead `2m_temperature` improvement together with
`geopotential_500`, `mean_sea_level_pressure`, and `10m_u_component_of_wind`
guardrails before validation.
