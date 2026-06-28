---
schema_version: 1
slug: passive-humidity-upwind-vertical-transport
title: Upwind Vertical Transport for Passive Humidity Only
status: staging
created_at: 2026-06-22T00:00:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Upwind Vertical Transport for Passive Humidity Only

## Hypothesis

The incumbent keeps humidity passive for dynamics, but humidity still enters the
diagnostic hydrostatic geopotential calculation when output fields are packed.
Centered vertical advection of passive humidity can create layer-to-layer
ringing or small negative overshoots that are dynamically harmless but can
contaminate virtual-temperature thickness and therefore `geopotential_500`.
Using first-order upwind vertical advection only for passive humidity should
make the diagnostic moisture column more monotone while preserving the accepted
dry thermodynamic, wind, pressure, DFI, and residual behavior.

## Mechanism

Add an opt-in primitive-equation option for tracer-only vertical advection:

- keep the incumbent centered vertical advection for vorticity, divergence,
  temperature, and any dry pressure-gradient terms;
- when computing tracer tendencies, use
  `sigma_coordinates.upwind_vertical_advection` only for
  `specific_humidity` vertical transport;
- keep the existing horizontal scalar advection for humidity unchanged;
- keep humidity dynamically passive by leaving `use_humidity_in_dynamics=False`
  in the candidate factory, so humidity still does not feed pressure-gradient
  tendencies or heating;
- apply the same tracer-only upwind path in DFI and positive-time rollout so the
  humidity tracer is initialized and advanced consistently;
- fall back to centered tracer vertical advection if the tracer key is absent or
  if finite diagnostics fail in focused tests.

The proposal changes a passive tracer transport stencil, not the forecast
contract, target variables, vertical coordinate, time step, or pressure-level
output interface.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` for an optional
    tracer vertical-advection callable on `PrimitiveEquationsSigma` and focused
    use inside tracer tendency construction.
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for a boolean selector,
    threading into `_primitive_equation`, and a side-by-side candidate factory
    based on the current incumbent.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` for the new factory export.
  - `src/dynamaxx/dycore/registry.py` for a registered candidate name such as
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_humidity_upwind_vadv`.
  - `tests/dycore/models/dinosaur/test_primitive_equations.py` for tracer-only
    stencil behavior.
  - `tests/dycore/test_registry.py` for registration coverage.
- Registry changes:
  - Add one side-by-side model entry; leave the incumbent and existing staged
    vertical-advection candidates untouched.
- API changes:
  - None. The `DycoreModel.forecast` signature, emitted variables, lead times,
    and fixed evaluation protocols remain unchanged.
- Tests to update:
  - Verify a synthetic state changes humidity tracer vertical tendency under the
    selector while temperature, vorticity, divergence, and log pressure tendencies
    remain equal to the incumbent.
  - Verify absent humidity gives incumbent-equivalent tendencies.
  - Verify candidate factory preserves `use_humidity_in_dynamics=False`,
    land-sea T2m residual memory, weak-HS analysis equilibrium, and all current
    initialization flags.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium and longer leads if passive humidity ringing is
    corrupting virtual-temperature thickness in the output diagnostic.
  - Possibly small `mean_sea_level_pressure` neutrality-to-improvement through
    reduced diagnostic inconsistency if packed pressure-level fields are more
    coherent.
- Expected neutral metrics:
  - `2m_temperature` should stay close to the accepted land-sea residual
    incumbent because dry temperature evolution and the output residual branch
    are unchanged.
  - `10m_u_component_of_wind` should stay close to incumbent because wind
    dynamics and the Richardson diagnostic are unchanged.
- Possible regressions:
  - Upwinding may over-diffuse vertical humidity gradients and worsen tropical
    or frontal `geopotential_500` where sharp moisture structure improves the
    virtual-temperature diagnostic.
  - If passive humidity phase error is not a meaningful score source, the change
    may be clean but subthreshold.

## Risks

- Numerical stability:
  - Low. Upwind transport is usually more stable for advected tracers than
    centered transport, and the change is confined to passive humidity.
- Compute cost:
  - Negligible. It reuses the existing upwind vertical-advection function and
    adds no rollout steps, workers, or output fields.
- Data leakage:
  - None. The mechanism uses only the same initialized humidity tracer and
    forecast state.
- Physical plausibility:
  - Moderate. Monotone/upwind transport is a standard tracer-stability tool, but
    first-order upwinding is diffusive and humidity is still a simplified passive
    tracer in this dry dycore.
- Rollback complexity:
  - Low to moderate. Remove one primitive-equation option, one adapter selector,
    one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_humidity_upwind_vadv`.
  - Require finite forecasts, zero diagnostic issues, and no broad Z500 or T2m
    degradation in fast diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_humidity_upwind_vadv --workers 4`.
  - Support requires the fixed `+0.002` primary-score improvement with clean
    guardrails, preferably with measurable `geopotential_500` improvement and
    neutral near-surface variables.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_humidity_upwind_vadv --workers 4` only if iteration promotes.
  - Validation should preserve the Z500 direction without triggering early
    `2m_temperature` or `10m_u_component_of_wind` guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, Z500 regression, or any
    near-surface guardrail failure would show passive-humidity vertical ringing
    is not a useful remaining error source under the fixed protocols.

## Citations

- Citation or source:
  - Local code: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
    computes tracer tendencies by combining horizontal scalar advection and the
    same vertical-advection callable used for dynamical fields.
  - Local code: `src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py`
    already provides both `centered_vertical_advection` and
    `upwind_vertical_advection`.
  - Local code: `src/dynamaxx/dycore/models/dinosaur/adapter.py` keeps humidity
    dynamically passive unless `use_humidity_in_dynamics=True`, but uses humidity
    in `dinosaur_state_to_weather_state` for diagnostic geopotential when the
    tracer exists.
  - Local history: `.logbook/history/2026-06-17_12-29-40_passive-humidity-dfi-bypass/decision.md`
    showed broad passive-humidity DFI bypass was not useful, motivating a
    narrower transport-stencil test rather than restoring unfiltered humidity.
  - LeVeque, R. J. 2002. `Finite Volume Methods for Hyperbolic Problems`.
    Cambridge University Press. Describes upwind discretizations for stable
    transport of advected quantities.
  - Durran, D. R. 2010. `Numerical Methods for Fluid Dynamics: With Applications
    to Geophysics`, second edition. Springer. Covers advection discretization
    tradeoffs and numerical diffusion in geophysical fluid models.

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is not the staged full upwind vertical-advection idea because it preserves
centered vertical advection for temperature and momentum and changes only the
passive humidity tracer. It is not the rejected passive-humidity DFI bypass,
which restored an unfiltered tracer after balance initialization; this proposal
keeps DFI consistency and only changes the vertical transport stencil. It also
avoids active moist dynamics, virtual-temperature pressure-gradient feedback,
or humidity-weighted forcing, all of which would move beyond the current
forecast contract and the accepted dry-dynamics incumbent.

## Evaluator Notes

### 2026-06-22T01:42:36Z

Decision: move to `staging`; plausible but not a ready model-selection
experiment.

The proposal is scientifically coherent and does not change the public forecast
contract or evaluation support. Humidity remains passive in the dynamics while
continuing to feed the virtual-temperature geopotential diagnostic, which is
consistent with the rejected `dry-consistent-geopotential-diagnostic` result:
removing passive humidity from geopotential caused a day-1 Z500 guardrail
failure. Upwind transport is also a standard monotone tracer-stability idea,
and the existing `sigma_coordinates.upwind_vertical_advection` callable gives
the implementation a credible starting point.

Keep it out of `ready` for now because the expected primary-score leverage is
weaker than the land-sea wind residual proposal and the implementation surface
is broader. Source inspection shows tracer vertical tendencies are currently
computed through a generic tree map over all tracers inside
`PrimitiveEquationsSigma`; changing only `specific_humidity` requires a new
tracer-specific internal path rather than a simple factory flag. That is still
compatible with the API, but it is less isolated than an output-only residual
decay branch.

Prior humidity-only evidence also argues for staging. The passive-humidity DFI
bypass was clean but slightly negative (`-1.9179700339044814e-07` iteration
delta), and the passive-humidity positivity limiter was clean but slightly
negative (`-0.0000019440828125105725`). This new transport-stencil mechanism is
different enough to retain, especially because it targets Z500 through virtual
temperature rather than forecast humidity as a scored variable, but it should
wait behind the lower-surface, output-only wind residual experiment. If later
promoted, require tests proving temperature, vorticity, divergence, log
pressure, dry-dynamics humidity coupling, and the accepted surface residual
branches remain incumbent-equivalent.
