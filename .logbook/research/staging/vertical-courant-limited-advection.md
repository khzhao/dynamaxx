---
schema_version: 1
slug: vertical-courant-limited-advection
title: Limit Sigma-Dot Courant Number in Centered Vertical Advection
status: staging
created_at: 2026-06-20T00:57:57Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Limit Sigma-Dot Courant Number in Centered Vertical Advection

## Hypothesis

The incumbent keeps centered sigma-coordinate vertical advection. Prior history
shows that removing vertical advection is nonfinite, and staged alternatives
such as upwind, semi-Lagrangian, and smoothed sigma-dot transport are broader
changes. A narrower failure mode remains: rare large diagnosed `sigma_dot`
values can locally violate the vertical Courant margin of the centered
advection stencil, injecting layer-to-layer temperature and momentum noise that
later appears as MSLP, Z500, 10 m wind, or 2 m temperature error.

A local Courant limiter on the advective sigma velocity should activate only in
outlier columns and preserve the centered operator for ordinary flow. This is a
more surgical vertical-numerics change than replacing the transport scheme or
smoothing all vertical velocities.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_vcourant`.
Preserve the incumbent initialization, DFI, weak-HS forcing, exact Coriolis
Strang split, theta tendency, theta mean recentering, semi-implicit
off-centering, horizontal diffusion, Richardson 10 m wind diagnostic, and
scale-separated surface residual correction.

For the candidate only:

- keep the existing diagnosis of `sigma_dot_full` and `sigma_dot_explicit` from
  divergence plus horizontal surface-pressure advection;
- before centered vertical advection is applied to vorticity, divergence,
  theta/temperature, and tracers, compute a local nondimensional vertical
  Courant proxy `abs(sigma_dot) * dt / delta_sigma`;
- where the proxy is below a fixed threshold such as `0.45`, leave the
  incumbent `sigma_dot` exactly unchanged;
- where the proxy exceeds the threshold, scale only the excess part toward the
  threshold with a smooth limiter, preserving sign and top/bottom zero flux;
- subtract a layer-thickness weighted correction from the interior limited
  sigma-dot profile so the limiter does not introduce a net vertical mass-flux
  bias in the column;
- do not alter the `log_surface_pressure` continuity tendency or the
  semi-implicit divergence solve, only the advective velocity passed to vertical
  transport;
- use the same limiter in DFI and positive-time rollout because it is a local
  stability condition of the centered vertical advection operator;
- fall back to the incumbent sigma-dot if the limiter produces nonfinite values
  or shape mismatches.

This is not `smoothed-sigma-dot-vertical-advection`: ordinary sigma-dot profiles
are bitwise unchanged, and only local Courant outliers are limited. It is not
upwind or semi-Lagrangian transport because the centered vertical-advection
stencil remains the operator.

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
  - Add one side-by-side factory with the `_vcourant` suffix.
- API changes:
  - None. Forecast contract, lead schedule, outputs, metrics, and protocols
    remain fixed.
- Tests to update:
  - Unit-test no-op behavior below the Courant threshold.
  - Unit-test sign preservation, threshold enforcement, top/bottom zero flux,
    and weighted zero-net correction on synthetic sigma-dot profiles.
  - Verify only vertical-advection tendencies change when the limiter activates;
    continuity and implicit terms remain incumbent-equivalent.
  - Verify candidate factory options preserve every incumbent setting except the
    vertical Courant limiter.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if rare
    vertical Courant outliers are feeding thickness and mass-field noise.
  - `2m_temperature` if lower-column vertical transport becomes less noisy
    without the diffusion of a full upwind replacement.
  - `10m_u_component_of_wind` if vertical momentum advection outliers contribute
    to late low-level wind phase error.
- Expected neutral metrics:
  - Day-1 fields should remain close to incumbent if the limiter is inactive in
    balanced initial columns.
- Possible regressions:
  - Limiting sigma-dot breaks exact consistency between vertical advection and
    unsmoothed continuity in active columns.
  - If large sigma-dot values represent real vertical motion rather than
    numerical outliers, the limiter can under-transport heat or momentum.

## Risks

- Numerical stability:
  - Low to moderate. The limiter is stabilizing for centered advection but
    touches multi-field vertical transport.
- Compute cost:
  - Low. Adds local vertical algebra and reductions only; no new transforms,
    resolution, lead, or worker changes.
- Data leakage:
  - None. Uses only forecast-state sigma-dot, sigma geometry, and fixed
    constants.
- Physical plausibility:
  - Moderate. Courant limiting is a numerical stability device, not a physical
    process, but it is targeted at known centered-advection stability behavior.
- Rollback complexity:
  - Low. Remove one limiter helper, one equation option, one factory/export, one
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_vcourant`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_vcourant --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_vcourant --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean diagnostics
    and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show vertical Courant
    outliers are not a material remaining error source. Early MSLP, Z500, or
    wind guardrail failures would show the limiter disrupts matched
    sigma-coordinate balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  diagnoses `sigma_dot_full` and uses centered vertical advection for multiple
  prognostic fields.
- Dynamaxx history:
  `.logbook/history/2026-06-16_20-56-11_vertical-advection-suppression/decision.md`
  showed that dropping vertical advection entirely causes nonfinite forecasts,
  so this proposal preserves vertical advection.
- Dynamaxx research:
  `.logbook/research/staging/smoothed-sigma-dot-vertical-advection.md` and
  `.logbook/research/staging/theta-upwind-vertical-advection.md` are broader
  vertical-transport alternatives; this proposal activates only on local
  Courant outliers.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. "Atmospheric
  transport schemes: desirable properties and a semi-Lagrangian view on
  finite-volume discretizations." In Numerical Techniques for Global
  Atmospheric Models. https://doi.org/10.1007/978-3-642-11640-7_8
- Staniforth, A. and Cote, J. 1991. "Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of staged `smoothed-sigma-dot-vertical-advection`,
which blends all vertical velocities with a smoothing stencil. It is not staged
`theta-upwind-vertical-advection` or scrapped `semi-lagrangian-vertical-transport`,
because it keeps the centered operator and limits only diagnosed Courant
outliers. It also avoids the latest DFI/theta and low-mode mass residual
negative evidence by changing neither DFI routing nor mass output residuals.

## Evaluator Notes

### 2026-06-20T01:00:53Z

Decision: move to `staging`; promising but not the best next experiment.

This is distinct from active staged vertical-transport ideas. It is narrower
than `smoothed-sigma-dot-vertical-advection` because ordinary sigma-dot profiles
would remain unchanged, narrower than `theta-upwind-vertical-advection` because
the centered operator remains in place, and much narrower than scrapped
`semi-lagrangian-vertical-transport` because there is no operator-split remap.
The numerical motivation is sound: Courant limits are a standard stability
constraint for advection, and a local limiter could be a useful diagnostic if
rare `sigma_dot` outliers are contaminating vertical transport.

Keep staged rather than ready because the proposal still touches all vertically
advected prognostic and tracer tendencies and intentionally decouples the
limited advective `sigma_dot` from the unsmoothed continuity tendency. The
nearest direct history is cautionary: removing vertical advection caused
nonfinite forecasts, and related vertical-transport replacements have been
kept as low-priority staging because they can disrupt mass/thickness balance or
add diffusion. Compared with the ready Lagrangian surface residual, this has a
larger implementation surface, higher guardrail risk, and less direct positive
incumbent evidence. It should remain available as the preferred vertical
numerics follow-up if output-only residual refinements stall.
