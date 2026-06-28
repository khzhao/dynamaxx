---
schema_version: 1
slug: surface-drag-theta-dissipation
title: Return Boundary-Layer Momentum Drag as Theta Heating
status: staging
created_at: 2026-06-19T03:26:40Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
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

# Return Boundary-Layer Momentum Drag as Theta Heating

## Hypothesis

The incumbent retains weak Held-Suarez thermal relaxation but no explicit
low-level Rayleigh drag. A staged drag-only proposal is physically plausible,
but damping momentum without returning the lost kinetic energy to the thermal
reservoir can introduce a dry energy sink. A boundary-layer drag filter that
exactly diagnoses its kinetic-energy loss and converts that loss into a
theta-compatible heating increment may improve late low-level wind and
near-surface thermal evolution while preserving the forecast contract.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_drag_theta_heating`.
Preserve incumbent initialization, DFI, weak-HS thermal forcing, horizontal
diffusion, exact symmetric Coriolis split, Richardson 10 m wind diagnostic,
stability-aware residual correction, theta tendency, theta mean recentering,
output variables, WeatherBench2 splits, lead times, metrics, and deterministic
gates.

For the candidate only, add a positive-time low-level drag-and-heating filter:

- transform modal vorticity and divergence to nodal wind;
- apply a fixed weak exact Rayleigh damping to `u` and `v` in the lower sigma
  layers with a smooth taper that is zero above about `sigma = 0.70` and
  largest in the lowest layer;
- compute local nonnegative kinetic-energy loss from the pre-drag and post-drag
  wind speed in each affected layer;
- convert the lost kinetic energy to a dry temperature source using `cp`, then
  to a potential-temperature increment using the local Exner factor from the
  current sigma-layer pressure;
- add the equivalent local temperature increment to `temperature_variation` so
  the incumbent theta-form thermodynamic path sees a theta-compatible heating
  source;
- cap the heating per inner step and fall back to the drag-only or fully
  incumbent state if wind, pressure, Exner factor, or corrected temperature is
  nonfinite;
- leave `log_surface_pressure`, tracers, `sim_time`, output packing, residual
  correction, and pressure-level interpolation unchanged;
- keep the filter outside DFI because frictional heating is irreversible and
  should not be time-reversed during initialization.

This is not the existing staged drag-only idea and not the staged horizontal
diffusion-heating idea. The energy source is tied to low-level physical
momentum drag rather than to the existing spectral diffusion filter.

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
  - None. `DycoreModel.forecast`, input variables, output variables, target
    variables, lead times, splits, metrics, and deterministic gates stay
    unchanged.
- Tests to update:
  - Unit-test the vertical drag taper and exact damping factor.
  - Unit-test that kinetic-energy loss is nonnegative and zero when drag is
    zero.
  - Unit-test Exner-weighted theta heating on a synthetic pressure field and
    verify the fixed per-step heating cap.
  - Verify `log_surface_pressure`, tracers, and output variables are unchanged
    by the filter.
  - Verify DFI filters stay on the incumbent path while positive-time rollout
    uses the drag-heating filter.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and long leads if missing boundary-layer
    friction contributes to low-level wind drift.
  - `2m_temperature` at medium leads if energy-consistent drag heating offsets
    a small cold drift without output residual tuning.
  - `geopotential_500` and `mean_sea_level_pressure` may improve if low-level
    momentum and thermal energy budgets become more balanced.
- Expected neutral metrics:
  - Day-1 aggregate RMSE should remain near incumbent because drag and heating
    are weak, tapered, capped, and excluded from DFI.
- Possible regressions:
  - Low-level drag can degrade 10 m wind amplitude immediately if the incumbent
    already needs stronger winds.
  - Positive lower-column heating can alter thickness and pressure gradients,
    causing MSLP or Z500 regressions even when total energy accounting is more
    physical.

## Risks

- Numerical stability:
  - Moderate. Drag is stabilizing, but the coupled heating changes thermal
    state every positive-time inner step.
- Compute cost:
  - Low to moderate. It adds existing wind transforms and local pressure/Exner
    algebra without changing resolution, lead count, output volume, or worker
    count.
- Data leakage:
  - None. The filter uses only forecast state, fixed constants, sigma geometry,
    and predeclared coefficients.
- Physical plausibility:
  - Moderate to high. Boundary-layer drag and frictional heating are physically
    linked; this simplified dry conversion omits full turbulent mixing and
    surface physics.
- Rollback complexity:
  - Low. Remove one filter option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_drag_theta_heating`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_drag_theta_heating --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_drag_theta_heating --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that
    energy-consistent boundary-layer drag is not a material remaining error
    source. Any early 10 m wind, MSLP, or Z500 guardrail failure would show that
    the drag-heating coupling is too intrusive.

## Citations

- Citation or source:
  - Dynamaxx research:
    `.logbook/research/staging/exponential-boundary-layer-rayleigh-drag.md`
    records a drag-only lower-boundary momentum proposal; this proposal adds
    explicit theta-compatible heating for the diagnosed drag energy loss.
  - Dynamaxx research:
    `.logbook/research/staging/theta-diffusion-dissipative-heating.md` ties
    heating to horizontal diffusion loss; this proposal ties heating to
    physical low-level drag instead.
  - Dynamaxx source:
    `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently sets the weak
    Held-Suarez Rayleigh coefficient to zero while using theta-form
    thermodynamics in the incumbent.
  - Becker, E. 2003. Frictional Heating in Global Climate Models. Monthly
    Weather Review.
    https://doi.org/10.1175/1520-0493(2003)131%3C0508:FHIGCM%3E2.0.CO;2
  - Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of
    dynamical cores of atmospheric general circulation models. Bulletin of the
    American Meteorological Society.
    https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
  - Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP
    and climate models. Journal of Computational Physics.
    https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This proposal satisfies the theta-space thermodynamic-energy diversity request.
It is a stronger and more physically constrained mechanism than a wind-output
cap: the prognostic wind is damped only through a lower-boundary drag surrogate,
and the diagnosed kinetic-energy loss is returned as local theta-compatible
heat. It is not a duplicate of diffusion-heating because the energy source is
not numerical horizontal diffusion, and it is not a duplicate of drag-only
staging because thermal energy accounting is the central hypothesis.

## Evaluator Notes

### 2026-06-19T03:31:24Z

Decision: `staging`.

The mechanism is physically defensible, but it is too broad for the immediate
next experiment against the theta-recenter incumbent. It changes prognostic
momentum and adds irreversible lower-column heating every positive-time step,
which risks spending the remaining late `10m_u_component_of_wind` guardrail and
perturbing MSLP/Z500 through thickness changes. It also overlaps with existing
staged drag-only and dissipative-heating proposals, so it should wait until a
narrower pressure/mass experiment is tried or until scorer evidence indicates
low-level momentum/energy accounting is the dominant remaining error.

If revisited, keep the drag coefficient, vertical taper, Exner conversion, and
per-step heating cap fixed in the proposal before implementation. Do not tune
the drag or heating constants against iteration or validation results.
