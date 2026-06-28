---
schema_version: 1
slug: smoothed-sigma-dot-vertical-advection
title: Smooth Diagnosed Sigma-Dot for Vertical Advection
status: staging
created_at: 2026-06-19T03:26:40Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Smooth Diagnosed Sigma-Dot for Vertical Advection

## Hypothesis

The incumbent keeps centered sigma-coordinate vertical advection, which is less
diffusive than first-order upwind transport but can pass layer-to-layer
diagnostic `sigma_dot` noise into momentum and thermodynamic tendencies. Prior
history shows that removing vertical advection is unstable and that first-order
upwind vertical advection is an active but more diffusive staged idea. A narrow
vertical numerical change that smooths only the diagnosed `sigma_dot` used by
vertical advection may reduce vertical grid-scale noise while preserving the
centered transport operator, continuity tendency, theta recentering, and output
contract.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_smoothed_sigma_dot_vadv`.
Preserve incumbent initialization, DFI, weak-HS forcing, horizontal diffusion,
exact symmetric Coriolis split, stability-aware residual decay, Richardson 10 m
wind diagnostic, potential-temperature tendency, theta mean recentering, output
variables, WeatherBench2 splits, lead times, metrics, and deterministic gates.

For the candidate only, add an opt-in sigma vertical-velocity smoother inside
`PrimitiveEquationsSigma`:

- keep the existing diagnosis of `sigma_dot_full` and `sigma_dot_explicit` from
  divergence and horizontal surface-pressure advection;
- before calling the vertical-advection operator for momentum, temperature,
  theta, and tracers, apply a fixed conservative three-point vertical smoother
  to the interior `sigma_dot` values;
- preserve top and bottom boundary zeros and subtract the layer-thickness
  weighted mean of the smoothing correction so no net column vertical mass flux
  is introduced into the advective velocity proxy;
- blend the smoothed velocity with the original velocity using a fixed small
  coefficient, for example `0.25`, rather than replacing it wholesale;
- do not smooth `sigma_dot` in the continuity calculation for
  `log_surface_pressure`, do not change horizontal divergence, and do not
  change pressure-gradient terms;
- use the same candidate equation for DFI and positive-time rollout because
  this is a reversible numerical discretization choice, not an irreversible
  spinup or output correction;
- fall back to the incumbent unsmoothed vertical velocity if smoothing produces
  nonfinite values or shape mismatches.

This is not scalar split-form advection, not upwind vertical advection, not
semi-Lagrangian transport, and not a wind-output cap. It changes only the
diagnosed vertical velocity supplied to the existing centered vertical
advection calls.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
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
  - Unit-test the vertical smoother on synthetic `sigma_dot` profiles,
    including boundary preservation and zero weighted-mean correction.
  - Verify the smoother leaves constant and linear profiles nearly unchanged
    while damping alternating layer noise.
  - Verify continuity and `log_surface_pressure` implicit terms still use the
    incumbent unsmoothed diagnostic path.
  - Verify candidate factory options preserve every incumbent setting except
    the sigma-dot vertical-advection smoother.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if
    vertical grid-scale sigma-dot noise is perturbing thickness and balanced
    pressure-gradient evolution.
  - `2m_temperature` may improve if lower-column theta transport becomes less
    noisy after the accepted theta recentering.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain near incumbent because horizontal
    wind state, Coriolis split, Richardson diagnostic, and residual correction
    are unchanged except through weaker downstream vertical-advection noise.
  - Early day-1 fields should move less than a full upwind or semi-Lagrangian
    vertical-transport replacement.
- Possible regressions:
  - Smoothing `sigma_dot` can break the exact consistency between diagnosed
    continuity and vertical advection, degrading pressure and geopotential.
  - If centered vertical advection already handles layer noise well, the change
    may be neutral or slightly diffusive.

## Risks

- Numerical stability:
  - Moderate. The smoother is bounded and conservative in the vertical velocity
    proxy, but it touches the vertical advection used by several prognostic
    fields.
- Compute cost:
  - Low. It adds a local vertical stencil and simple reductions without
    changing resolution, lead count, output volume, or worker count.
- Data leakage:
  - None. It uses only forecast diagnostic state, sigma geometry, and fixed
    constants.
- Physical plausibility:
  - Moderate. Vertical velocity filtering is a numerical stabilization of the
    advective velocity rather than a new physical parameterization; the
    hypothesis is that it damps vertical grid-scale noise while leaving large
    vertical motion mostly intact.
- Rollback complexity:
  - Low. Remove one equation option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_smoothed_sigma_dot_vadv`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_smoothed_sigma_dot_vadv --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_smoothed_sigma_dot_vadv --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that sigma-dot
    vertical noise is not a material remaining error source. Any early MSLP,
    Z500, or 10 m wind guardrail failure would show that smoothing disrupts
    vertical-continuity balance.

## Citations

- Citation or source:
  - Dynamaxx source:
    `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` diagnoses
    `sigma_dot_full` and `sigma_dot_explicit` in
    `compute_diagnostic_state_sigma` and uses them in centered vertical
    advection for momentum, temperature, theta, and tracers.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_20-56-11_vertical-advection-suppression/decision.md`
    showed disabling explicit vertical advection caused nonfinite fast
    forecasts, so this proposal preserves vertical advection.
  - Dynamaxx research:
    `.logbook/research/staging/theta-upwind-vertical-advection.md` records a
    stronger first-order upwind replacement; this proposal keeps centered
    advection and smooths only the advective sigma-dot input.
  - Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
    atmospheric models: a review. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
  - Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric
    transport schemes: desirable properties and a semi-Lagrangian view on
    finite-volume discretizations. In Numerical Techniques for Global
    Atmospheric Models.
    https://doi.org/10.1007/978-3-642-11640-7_8
  - Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
    conserving vertical finite-difference scheme and hybrid vertical
    coordinates. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2

## Researcher Notes

This proposal satisfies the vertical-numerics diversity request while avoiding
the rejected scalar split-form and wind-cap families. It is distinct from
`theta-omega-spinup`, which imports same-time analyzed omega as a transient
source, and from `upwind-vertical-advection-rollout`, which changes the
vertical transport operator itself. The negative evidence from vertical
advection suppression is used constructively: preserve the term, but reduce
small-scale noise in the diagnosed advective vertical velocity.

## Evaluator Notes

### 2026-06-19T03:31:24Z

Decision: `staging`.

This is plausible and more conservative than disabling or replacing vertical
advection, but it still touches a multi-field core tendency path and deliberately
decouples the smoothed advective `sigma_dot` from the unsmoothed continuity
diagnosis. That consistency risk is important given the nonfinite failure from
vertical-advection suppression and the already staged upwind vertical-advection
ideas. It is not the best immediate candidate against the current incumbent,
but it remains useful as a later vertical-numerics experiment if pressure/mass
and lower-column ideas stall.

Before implementation, the Orchestrator should require a precise proof/test of
top and bottom boundary preservation, weighted zero net correction, finite
fallback, and a factory check showing continuity still uses the incumbent
unsmoothed diagnostic path.
