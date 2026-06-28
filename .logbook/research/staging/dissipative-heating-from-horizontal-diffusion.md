---
schema_version: 1
slug: dissipative-heating-from-horizontal-diffusion
title: Convert Horizontal Diffusion Kinetic-Energy Loss into Heat
status: staging
created_at: 2026-06-18T11:44:45Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
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

# Convert Horizontal Diffusion Kinetic-Energy Loss into Heat

## Hypothesis

The incumbent still has a persistent cold `2m_temperature` bias at medium and
long leads while using a horizontal diffusion filter that damps resolved wind
modes without returning any lost kinetic energy to the thermodynamic state. In a
dry primitive-equation model, unresolved frictional dissipation should appear as
heat rather than disappear from the total energy budget. A small local
dissipative-heating correction tied to the already accepted diffusion operator
may reduce cold thermal drift without changing wind initialization, pressure
initialization, Coriolis splitting, output residuals, or the fixed forecast
contract.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_diffusion_heating`.
Preserve all incumbent settings except the positive-time horizontal diffusion
filter.

Replace the rollout diffusion filter with an opt-in combined filter that:

- applies the same horizontal diffusion operator and coefficients as the
  incumbent to the candidate next state;
- diagnoses nodal wind before and after that diffusion using
  `spherical_harmonic.vor_div_to_uv_nodal`;
- computes nonnegative per-layer kinetic-energy loss from the wind difference,
  area-local and sigma-local, with a conservative bound on maximum heating per
  inner step;
- converts the bounded energy loss into a dry-temperature increment using the
  model heat capacity from `physics_specs`;
- adds the increment to `temperature_variation` after subtracting the
  `reference_temperature` convention and transforming back to modal space;
- leaves vorticity and divergence equal to the normally diffused values;
- leaves `log_surface_pressure`, passive tracers, `sim_time`, lead selection,
  and near-surface residual correction unchanged;
- keeps DFI on the incumbent diffusion path, without irreversible heating, so
  the time-reversed initialization remains a balance filter rather than a
  frictional-physics loop.

This is not a new diffusion strength, top sponge, wind residual, or
Held-Suarez tuning experiment. It uses the same dissipation already present in
the incumbent and only changes the thermodynamic accounting for kinetic energy
removed by that dissipation.

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
    metrics, and protocols remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every Strang incumbent flag except
    the new diffusion-heating option.
  - Unit-test the combined filter with a synthetic state where diffusion reduces
    wind amplitude and temperature increases by a finite bounded amount.
  - Verify zero kinetic-energy loss produces exactly the incumbent diffused
    state.
  - Verify `log_surface_pressure`, tracers, and `sim_time` are unchanged.
  - Verify the DFI filter list remains the incumbent list while the rollout
    filter uses the heating wrapper.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` from days 5 to 15 if part of the incumbent cold drift is
    unresolved kinetic-energy loss rather than missing radiative forcing.
  - `geopotential_500` may improve if column temperature thickness is too cold
    after repeated filtered rollout steps.
- Expected neutral metrics:
  - Day-1 fields should remain close to the incumbent because heating per inner
    step is bounded and no initialization fields are changed.
  - `10m_u_component_of_wind` should be near neutral because the wind after
    diffusion is the same as the incumbent diffusion path.
- Possible regressions:
  - `mean_sea_level_pressure` and `geopotential_500` already develop positive
    long-lead biases; extra heating could worsen thickness or mass-field RMSE.
  - If cold `2m_temperature` error is dominated by missing surface physics
    rather than numerical energy loss, the score movement may be small.

## Risks

- Numerical stability:
  - Moderate. The heating is positive definite and bounded, but it changes the
    thermodynamic state every inner step and must pass the fixed fast gate.
- Compute cost:
  - Low to moderate. The filter adds wind transforms and local reductions per
    inner step but does not change grid size, lead count, or worker count.
- Data leakage:
  - None. The correction uses only forecast states, fixed physical constants,
    and the incumbent diffusion operator.
- Physical plausibility:
  - Moderate to high. Frictional and numerical kinetic-energy dissipation should
    heat the resolved thermodynamic reservoir, but this implementation is a
    simplified dry conversion rather than a full turbulent boundary-layer
    parameterization.
- Rollback complexity:
  - Low. Remove one filter option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_diffusion_heating`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_diffusion_heating --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    diagnostics clean, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_diffusion_heating --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show diffusion energy
    loss is not a material remaining error source. Any early MSLP, Z500, or
    wind guardrail failure would show the heating disrupts the accepted balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds the
  current horizontal diffusion step filter in `_horizontal_diffusion_step_filter`
  and applies it through `time_integration.step_with_filters`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py`
  provides wind transforms needed to diagnose kinetic-energy loss from the
  filtered vorticity-divergence state.
- History: `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected changing diffusion shape after a large negative iteration delta, so
  this proposal keeps the accepted diffusion strength and converts its energy
  loss instead of adding damping.
- History: `.logbook/history/2026-06-17_23-29-54_mass-neutral-weak-hs-forcing/decision.md`
  rejected a broad thermal-forcing change; this proposal ties heating to local
  resolved kinetic-energy dissipation rather than to a prescribed thermal
  relaxation increment.
- Becker, E. 2003. Frictional Heating in Global Climate Models. Monthly Weather
  Review. https://doi.org/10.1175/1520-0493(2003)131%3C0508:FHIGCM%3E2.0.CO;2
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
  Atmospheric Models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241

## Researcher Notes

This is not a duplicate of staged `symmetric-horizontal-diffusion-split`, which
changes filter placement around the step. This candidate keeps the accepted
rollout diffusion effect on wind and tests whether the lost kinetic energy
should be thermodynamically accounted for.

It is also distinct from scrapped `upper-sigma-rayleigh-sponge`, rejected
hyperdiffusion, rejected divergence damping, and rejected weak-HS thermal
forcing variants. Those add or relocate dissipation or relaxation. This
proposal converts already-applied diffusion loss into heat and is aimed at the
observed cold thermal drift while avoiding new wind-output residuals.

## Evaluator Notes

### 2026-06-18T11:49:28Z

Decision: move to `staging`, staged fallback rank 3.

The idea is physically plausible and distinct from rejected diffusion-strength
or weak-HS thermal-forcing experiments because it preserves the incumbent wind
diffusion path and asks whether numerically removed kinetic energy should heat
the dry thermodynamic reservoir. It has low leakage risk and could improve
`2m_temperature` and hydrostatic thickness if the remaining cold drift is tied
to unaccounted diffusion loss.

Keep it staged rather than ready because the implementation surface and
validation burden are larger than the top candidates. Diagnosing local kinetic
energy loss before and after a modal diffusion filter, bounding heating every
inner step, and converting it into `temperature_variation` creates a
hard-to-validate energy budget. Prior diffusion and forcing history is also
cautionary: scale-selective hyperdiffusion was strongly negative, and
mass-neutral weak-HS forcing badly regressed `2m_temperature`. Select this only
after lower-risk continuity, diagnostic, and split-order candidates are scored.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 3.

This remains below hypsometric Z and omega spinup because it adds an inferred
energy-budget correction every inner step. It stays above the anti-aliasing and
vertical-operator candidates because it preserves the incumbent diffusion path
and tests a physically interpretable sink-to-heat mechanism rather than
changing transport or pressure-gradient operators. The current ready diffusion
split should be scored before this heating variant because it isolates
placement without adding thermodynamic feedback.

### 2026-06-18T17:21:29Z

Decision: keep in `staging`, ranked behind the ready Richardson wind diagnostic
and the omega-spinup fallback.

The idea remains physically grounded and distinct from diffusion-strength
experiments because it preserves the incumbent wind diffusion path and accounts
for kinetic-energy loss thermodynamically. It should not be the next run after
the accepted near-surface residual improvement because it adds an inferred
positive heating term every inner step, which can perturb thickness, MSLP, and
Z500. Keep it as a medium-priority fallback if lower-surface diagnostic and
transient spinup experiments fail cleanly.
