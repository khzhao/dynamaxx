---
schema_version: 1
slug: theta-diffusion-dissipative-heating
title: Convert Horizontal Diffusion Kinetic-Energy Loss into Theta-Compatible Heating
status: staging
created_at: 2026-06-18T20:33:04Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
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

# Convert Horizontal Diffusion Kinetic-Energy Loss into Theta-Compatible Heating

## Hypothesis

The incumbent uses a horizontal diffusion filter that damps resolved wind modes
after each step. That kinetic-energy loss is not returned to the thermodynamic
state. In a dry primitive-equation model, dissipated kinetic energy should
become internal energy; otherwise repeated diffusion can contribute to thermal
and thickness drift. A small, bounded heating correction tied to the kinetic
energy already removed by the accepted diffusion path may improve
`2m_temperature`, `geopotential_500`, and `mean_sea_level_pressure` while
leaving the accepted wind diffusion, Richardson 10 m wind diagnostic, residual
correction, Coriolis split, initialization, and evaluation contract unchanged.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_diffusion_heating`.
Preserve every incumbent setting except the positive-time horizontal diffusion
step filter.

Add an opt-in combined filter for rollout only:

- apply the same horizontal diffusion operator and coefficients as the
  incumbent to produce the filtered next state;
- diagnose nodal wind before and after diffusion using existing
  vorticity/divergence to wind transforms;
- compute nonnegative local kinetic-energy loss from the wind difference, with
  per-layer and per-step heating caps;
- convert bounded energy loss to a dry-temperature increment using the model
  heat capacity and add it to `temperature_variation`;
- because the incumbent thermodynamic transport is theta-form, keep the heating
  physically as an additive temperature source after the diffusion filter rather
  than modifying the theta-advection tendency itself;
- leave vorticity and divergence equal to the normally diffused values;
- leave `log_surface_pressure`, passive tracers, `sim_time`, output packing,
  Richardson 10 m wind diagnostic, and near-surface residual correction
  unchanged;
- keep DFI on the incumbent diffusion path without irreversible heating, so the
  time-reversed initialization remains a balance filter rather than a frictional
  physics loop.

This is not a diffusion-strength sweep, a new damping curve, a weak-HS forcing
change, or a wind residual. It tests thermodynamic accounting for kinetic
energy already removed by the accepted filter.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, lead times,
    metrics, and fixed protocols remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent flag except the new
    diffusion-heating option and model name.
  - Unit-test the combined filter with a synthetic state where diffusion reduces
    wind amplitude and temperature increases by a finite bounded amount.
  - Verify zero kinetic-energy loss returns exactly the incumbent diffused
    state.
  - Verify `log_surface_pressure`, tracers, `sim_time`, output variables, and
    DFI filter selection are unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and long leads if unaccounted diffusion energy
    loss contributes to cold thermal drift after residual correction decays.
  - `geopotential_500` if warmer column thickness offsets remaining thermal
    underprediction without disturbing winds.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to the incumbent because the
    filtered wind state is unchanged and the accepted Richardson diagnostic is
    preserved.
  - Day-1 fields should remain close to the incumbent because heating is bounded
    and is not applied during DFI.
- Possible regressions:
  - Extra heating can worsen long-lead thickness, MSLP, or Z500 if the remaining
    thermal error is not caused by diffusion energy loss.
  - Local heating after filtering may create pressure-gradient changes that
    indirectly affect wind phase at later leads.

## Risks

- Numerical stability:
  - Moderate. Heating is nonnegative and bounded, but it changes the thermal
    state every positive-time inner step.
- Compute cost:
  - Low to moderate. The filter adds wind transforms and local algebra per step,
    but does not change resolution, lead count, output volume, or worker count.
- Data leakage:
  - None. The correction uses only forecast states, fixed physical constants,
    and the incumbent diffusion operator.
- Physical plausibility:
  - Moderate to high. Frictional and numerical kinetic-energy dissipation should
    be thermodynamically accounted for, but this dry local conversion is simpler
    than a full turbulent boundary-layer parameterization.
- Rollback complexity:
  - Low. Remove one filter option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_diffusion_heating`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_diffusion_heating --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_diffusion_heating --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show diffusion energy
    loss is not a material remaining thermal/pressure error source. Any early
    MSLP, Z500, or wind guardrail failure would show the heating disrupts
    accepted balance.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds the
    current horizontal diffusion step filter and applies it through
    `time_integration.step_with_filters`.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py`
    provides the vorticity/divergence to nodal-wind transforms needed to
    diagnose kinetic-energy loss from filtering.
  - History: `.logbook/history/2026-06-18_13-26-11_symmetric-horizontal-diffusion-split/decision.md`
    rejected pure diffusion placement with numerical-scale movement; this
    proposal keeps placement and strength unchanged and tests energy accounting.
  - History: `.logbook/history/2026-06-17_23-29-54_mass-neutral-weak-hs-forcing/decision.md`
    rejected removing the accepted weak-HS global thermal mean, so this proposal
    does not change weak-HS forcing and uses diffusion-local heating instead.
  - Becker, E. 2003. Frictional Heating in Global Climate Models. Monthly
    Weather Review. https://doi.org/10.1175/1520-0493(2003)131%3C0508:FHIGCM%3E2.0.CO;2
  - Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP
    and climate models. Journal of Computational Physics.
    https://doi.org/10.1016/j.jcp.2006.08.016
  - Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
    Atmospheric Models. Journal of the Meteorological Society of Japan.
    https://doi.org/10.2151/jmsj.85B.241

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is not a near-duplicate of the accepted Richardson 10 m wind diagnostic:
the raw and diagnosed 10 m wind paths remain unchanged, and the proposed
heating is tied to diffusion energy loss rather than surface-layer stability
scaling. It is not a near-duplicate of the accepted theta tendency because the
theta-form thermodynamic equation stays intact; the added term is a separate
positive-time dissipative-heating source after the diffusion filter.

It is not a repeat of rejected diffusion-strength, diffusion-ordering,
Held-Suarez, or mass-neutral forcing experiments. Those changed damping,
placement, or prescribed thermal forcing. This candidate preserves the
incumbent diffusion effect on wind and the accepted weak-HS source, then tests
whether the already removed kinetic energy should be returned as heat. A
related older-target staged diffusion-heating note exists, but this proposal is
rewritten for the current theta/Richardson/stability-aware incumbent and should
not move or consume the staged file.

## Evaluator Notes

### 2026-06-18T20:36:37Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

The mechanism is scientifically plausible and distinct from rejected diffusion
placement or strength changes. It preserves the incumbent wind diffusion path
and asks whether kinetic energy already removed by the fixed horizontal
diffusion filter should be returned as dry heating. It is also not a duplicate
of the accepted theta tendency because the theta transport equation remains
unchanged and the proposed source is applied after the rollout diffusion
filter.

Keep it staged rather than ready because the accepted theta candidate already
introduced a small early pressure/geopotential cost: iteration day-1
`mean_sea_level_pressure` regressed by `+1.7579965544157576%`, and validation
day-1 `mean_sea_level_pressure` regressed by `+1.6361908236509046%`, both
within guardrails but relevant. A positive definite heating source every
positive-time inner step could improve medium-lead `2m_temperature`, but it
could also worsen thickness, MSLP, or Z500 enough to miss the `+0.002`
iteration threshold or trip guardrails.

A related older staged file,
`.logbook/research/staging/dissipative-heating-from-horizontal-diffusion.md`,
records the same energy-accounting concept for a previous incumbent. This
current proposal is the more relevant artifact after the Richardson wind and
theta acceptances. It should remain a medium-priority fallback if the ready
scalar-transport experiment fails cleanly or if diagnostics show persistent
cold thermal drift tied to diffusion loss.
