---
schema_version: 1
slug: exact-coriolis-rotation-split
title: Split the Planetary Coriolis Term as an Exact Rotation
status: ready
created_at: 2026-06-18T01:51:56Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Split the Planetary Coriolis Term as an Exact Rotation

## Hypothesis

The incumbent's low-level zonal-wind skill remains poor, while prior wind
initialization, pole-row cleanup, angular-momentum fixing, diffusion, and
damping variants were either harmful, negligible, or too broad. A different
wind mechanism is the time discretization of the linear planetary Coriolis
operator. The Coriolis term is skew-symmetric and should rotate horizontal wind
without changing kinetic energy; explicit treatment can accumulate inertial
phase error over many 900 s steps.

Splitting only the planetary Coriolis contribution into an exact latitude-local
rotation should reduce inertial wind phase error without adding drag, changing
initial winds, forcing angular momentum, or altering scored wind outputs. If the
remaining `10m_u_component_of_wind` loss is partly phase error rather than
amplitude bias, this can improve wind skill while preserving the accepted mass
and thermal mechanisms.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split`.
Preserve incumbent initialization, DFI output state, weak-HS thermal forcing,
near-surface residuals, log-pressure and hydrostatic layer-mean initialization,
vertical advection, diffusion, sigma grid, output variables, target variables,
and evaluation protocols.

Change only the positive-time rollout's planetary Coriolis treatment:

- keep the incumbent DFI initializer unchanged with the normal primitive
  equation, so the accepted balanced initialization path is preserved;
- build the scored forward primitive-equation step with the same physical
  constants except `angular_velocity=0.0`, removing the linear planetary
  Coriolis contribution from `coriolis_parameter`;
- after each dynamics plus horizontal-diffusion step, convert candidate
  vorticity/divergence to nodal winds with the existing spherical-harmonic
  helpers;
- apply the exact local rotation over the step, using the original
  `f(latitude) = 2 * angular_velocity * sin(latitude)` and the nondimensional
  step length:
  `u_rot = u * cos(f * dt) + v * sin(f * dt)` and
  `v_rot = v * cos(f * dt) - u * sin(f * dt)`, with sign verified against the
  existing tendency convention in tests;
- convert the rotated winds back to modal vorticity/divergence and leave
  temperature, pressure, humidity tracers, `sim_time`, and output diagnostics
  unchanged.

The first implementation should not add Rayleigh drag, angular-momentum
projection, polar tapers, wind residuals, or target-variable feedback.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split`.
- API changes:
  - None. The deterministic forecast contract and requested WeatherState
    variables are unchanged.
- Tests to update:
  - Unit-test the exact rotation filter on a constant-latitude synthetic wind
    state and verify kinetic-energy preservation to roundoff.
  - Verify a one-step small-`dt` rotation agrees with the sign and first-order
    tendency of the existing Coriolis term.
  - Verify the candidate factory preserves incumbent options except for the
    exact-Coriolis split flag.
  - Verify temperature, `log_surface_pressure`, tracers, and output variable
    ordering are unchanged by the rotation filter.
  - Add a non-JIT finite smoke forecast and registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at early to medium leads if inertial phase error is
    a material part of the current wind loss.
  - `mean_sea_level_pressure` and `geopotential_500` may improve slightly if
    geostrophic adjustment is less phase-lagged.
- Expected neutral metrics:
  - `2m_temperature` should remain close to neutral because thermal forcing,
    temperature initialization, and near-surface residuals are unchanged.
- Possible regressions:
  - Projection between modal vorticity/divergence and nodal winds after every
    step may introduce aliasing or effective filtering.
  - Removing Coriolis from the base equation and applying it after the step is a
    split approximation; interactions with pressure gradients and advection may
    worsen balanced wave propagation.

## Risks

- Numerical stability:
  - Moderate. The isolated rotation is norm-preserving, but its split coupling
    with pressure-gradient and advection terms is unscored in this adapter.
- Compute cost:
  - Moderate. Each inner step adds wind transforms and one rotation, but it does
    not change grid size, lead count, or worker count.
- Data leakage:
  - None. The split uses only analytic Coriolis geometry and current model state.
- Physical plausibility:
  - High for the isolated term. The planetary Coriolis acceleration is a local
    rotation of horizontal wind on an f-plane; the approximation is the operator
    split on the sphere.
- Rollback complexity:
  - Low to moderate. Remove one physics-spec branch, one step filter, one
    factory, one registry entry, and tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the incumbent, clean diagnostics, no early day 1-5 RMSE guardrail failure,
    and no variable+lead RMSE guardrail failure, with special scrutiny of
    `10m_u_component_of_wind`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show planetary Coriolis
    time-discretization is not a material remaining wind-error source. Any early
    wind or mass-field guardrail failure would show the split disrupts balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  defines `PrimitiveEquationsBase.coriolis_parameter` and adds it to relative
  vorticity in `curl_and_div_tendencies`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds the
  current positive-time rollout with `time_integration.imex_rk_sil3` and
  spherical-harmonic wind/vorticity conversions.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py`
  provides `vor_div_to_uv_nodal` and `uv_nodal_to_vor_div_modal`, which are the
  natural conversion points for a wind-space rotation filter.
- History: `.logbook/history/2026-06-17_03-22-44_helmholtz-wind-initialization/decision.md`
  rejected broad wind initialization with iteration delta
  `-0.34423230670441374`; this proposal changes no initialized wind.
- History: `.logbook/history/2026-06-17_14-44-29_polar-vector-wind-initialization-taper/decision.md`
  found pole-only wind cleanup was numerical-noise scale, and
  `.logbook/research/scrap/barotropic-angular-momentum-fixer.md` was scrapped
  as too broad without drift diagnostics. This proposal is neither pole-only nor
  an angular-momentum projection.
- Williamson, D. L., Drake, J. B., Hack, J. J., Jakob, R., and Swarztrauber,
  P. N. 1992. A standard test set for numerical approximations to the shallow
  water equations in spherical geometry. Journal of Computational Physics.
  https://doi.org/10.1016/S0021-9991(05)80016-6
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of `helmholtz-wind-initialization`,
`polar-vector-wind-initialization-taper`, `barotropic-angular-momentum-fixer`, or
`vorticity-preserving-dfi-increment`. It does not alter initial winds, merge only
part of the DFI state, regularize pole rows, enforce angular momentum, damp wind,
or touch scored wind outputs.

It is also distinct from the staged `fourth-order-imex-rk-rollout`: that proposal
changes the entire IMEX time-stepper, while this one keeps the incumbent stepper
for all other terms and tests a single physically skew-symmetric linear operator
split.

## Evaluator Notes

### 2026-06-18T01:56:57Z

Decision: move to `staging`.

Source inspection supports feasibility: `PrimitiveEquationsBase` exposes the
planetary `coriolis_parameter`, and the spherical-harmonic module has the
needed `vor_div_to_uv_nodal` and `uv_nodal_to_vor_div_modal` conversions. The
mechanism is also scientifically coherent for the isolated linear Coriolis
operator.

Hold it behind the exact weak-HS source split because implementation risk is
higher. Removing planetary rotation from the base equation and reapplying it as
a wind-space filter adds modal/nodal wind transforms every inner step and may
change balanced pressure-gradient coupling or introduce aliasing. The recent
vorticity-preserving DFI increment was a clean negative result, and older broad
wind-initialization attempts were harmful, so another wind-specific candidate
needs stronger caution. Keep this as the top staged fallback if the ready item
fails cleanly or if wind diagnostics remain the dominant target.

### 2026-06-18T03:02:30Z

Decision: move to `ready`.

The exact weak-HS thermal-source split, which was previously ahead of this
idea, has now failed cleanly with only a `+0.000047270501076557` iteration
primary delta. That removes the immediate source-formulation blocker without
adding evidence against this proposal: the failed candidate targeted weak-HS
thermal forcing, while this one targets inertial wind phase error from the
planetary Coriolis operator.

Promote this as the single next implementable candidate because it is now the
strongest staged fallback, has a clear skew-symmetric mechanism, uses existing
`angular_velocity` and spherical-harmonic wind conversion hooks, and avoids
the temperature-forcing changes that recently caused large 2 m temperature
guardrail failures. Retain the known caution that the wind-space split adds
per-step transforms and can alter geostrophic coupling; those risks are
acceptable for one side-by-side implementation under the fixed gates.
