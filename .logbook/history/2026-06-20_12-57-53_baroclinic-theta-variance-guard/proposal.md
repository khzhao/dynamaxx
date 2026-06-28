---
schema_version: 1
slug: baroclinic-theta-variance-guard
title: Guard Layerwise Baroclinic Theta Variance During Rollout
status: ready
created_at: 2026-06-20T12:51:32Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Guard Layerwise Baroclinic Theta Variance During Rollout

## Hypothesis

The accepted theta mean-recentering filter preserves layerwise area-mean dry
potential temperature, but it does not constrain horizontal theta variance,
which is a simple proxy for dry baroclinic available potential energy. The
incumbent also applies weak-HS relaxation, horizontal diffusion, and off-centered
gravity-wave damping, all of which can damp thermal contrasts. A bounded
baroclinic theta-variance guard can preserve synoptic thermal-gradient amplitude
without changing the mean thermal state, the weak-HS equilibrium, or the
near-surface residual correction.

This should help if the remaining cold `2m_temperature` bias, negative
`geopotential_500` bias, and late MSLP errors partly reflect excessive loss of
baroclinic thermal structure rather than mean-temperature drift.

## Mechanism

Add an opt-in positive-time step filter after the accepted theta mean recenter:

- compute dry potential temperature from `temperature_variation`,
  `log_surface_pressure`, sigma centers, and the reference temperature for both
  the previous and candidate next state;
- remove each layer's area-weighted mean theta to isolate horizontal baroclinic
  anomalies;
- compute area-weighted theta variance per layer before and after the step;
- if candidate variance drops more than a small tolerance, rescale only a
  low-to-synoptic wavenumber band of the next theta anomaly toward the previous
  variance;
- convert the bounded theta increment back to `temperature_variation` at the
  next-state pressure, preserving the already-corrected layer mean;
- skip the correction wherever pressure, theta, variance, or the converted
  increment is nonfinite.

The first candidate should only prevent abrupt variance loss, not force exact
variance conservation. For example, cap the temperature increment per inner step
and allow natural growth or small damping.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for the opt-in guard and
    spectral variance-band helper.
  - `src/dynamaxx/dycore/registry.py` for the side-by-side candidate factory.
  - `tests/dycore/test_registry.py` plus focused finite/no-op tests.
- Registry changes:
  - Add a model named
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_var_guard`.
- API changes:
  - None. The forecast contract remains one `WeatherState` for the requested
    leads.
- Tests to update:
  - Confirm registration and default-false behavior.
  - Verify exact no-op when candidate variance is unchanged or larger.
  - Verify bounded finite increments when variance is artificially damped.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and MSLP at medium leads if thermal-gradient damping is
    flattening thickness fields.
  - `2m_temperature` after day 5 if preserved lower-tropospheric baroclinic
    variance reduces the incumbent cold drift without relying on residual
    memory.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain mostly on the accepted Richardson
    diagnostic and Coriolis paths, with only indirect thermal-wind effects.
- Possible regressions:
  - Preserving thermal variance can amplify phase errors in fronts and storms.
  - Low-level theta increments may interact with the accepted residual memory and
    worsen early `2m_temperature`.
  - The fixed weak-HS equilibrium may intentionally damp some thermal anomalies;
    the guard could fight useful damping.

## Risks

- Numerical stability:
  - Moderate. Variance rescaling can become unstable if applied to tiny
    variances, noisy high modes, or nonfinite pressure. Use variance floors,
    spectral tapering, and per-step caps.
- Compute cost:
  - Low to moderate. Additional theta conversions, area reductions, and one
    spectral taper per step are feasible under 4 eval workers.
- Data leakage:
  - Low. The guard uses only the previous and current model states during the
    rollout.
- Physical plausibility:
  - Moderate. It is a conservation-motivated numerical guard, not a full energy
    cycle or radiation scheme.
- Rollback complexity:
  - Low. The model is a side-by-side opt-in candidate.

## Evaluation Plan

- Fast gate:
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_var_guard`.
  - Require finite diagnostics and no issue count increase.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_var_guard --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean guardrails, and
    no early `2m_temperature` guardrail regression.
- Validation gate:
  - Run validation with `--workers 4` only after iteration promotion; require
    primary-score delta at least `+0.001`.
- Outcome that would falsify the hypothesis:
  - A negative or near-zero iteration delta with clean diagnostics would show
    that theta variance loss is not a material remaining error source. Any early
    T2m or Z500 guardrail regression would show the guard is preserving harmful
    thermal variance.

## Citations

- Lorenz, E. N. 1955. "Available potential energy and the maintenance of the
  general circulation." Tellus. https://doi.org/10.3402/tellusa.v7i2.8796
- Thuburn, J. 2008. "Some conservation issues for the dynamical cores of NWP and
  climate models." Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Arakawa, A. and Lamb, V. R. 1981. "A potential enstrophy and energy conserving
  scheme for the shallow water equations." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0018:APEAEC%3E2.0.CO;2

## Researcher Notes

This is distinct from accepted `theta-zero-mode-thermal-recentering` and staged
`mass-weighted-theta-recentering`: those constrain means, while this proposal
constrains horizontal baroclinic variance around the mean. It is also not the
same as staged skew-symmetric scalar advection, which changes the tendency form;
this proposal is a bounded post-step guard that preserves the incumbent
advection, weak-HS, DFI, off-centering, and residual-memory mechanisms.

## Evaluator Notes

### 2026-06-20T12:56:24Z

Decision: move to `ready`; ranked 1 of 3 in this triage pass.

This is the strongest proposal for immediate implementation. It is a narrow
rollout-only extension of the accepted theta mean-recentering path, uses only
previous and candidate model states, preserves the single-trajectory forecast
contract, and does not change fixed metrics, splits, target variables, or lead
times. Source inspection confirms `_theta_layer_mean_recenter_step_filter`
already provides the pressure/theta conversion and finite-fallback pattern that
the Implementer can extend without touching output diagnostics or residual
memory.

The local score history supports another carefully bounded theta-family test:
theta-form thermodynamics and theta zero-mode recentering were both accepted,
while DFI-only theta recentering was clean but neutral and the broad
theta-consistent implicit-gravity rewrite was strongly harmful. This proposal
stays closer to the accepted post-step filter than to the rejected implicit
operator rewrite, and it targets a different conserved moment from staged
`mass-weighted-theta-recentering`.

Main implementation constraints: apply the guard only after the accepted theta
mean recentering during positive-time rollout; preserve layer means; operate
only on a predeclared low-to-synoptic band; use variance floors, per-step
temperature caps, and finite no-op fallback; and do not tune the variance
tolerance or caps against iteration or validation results. The key risk is that
preserving thermal variance can preserve phase error or fight useful weak-HS
damping, so the Orchestrator should require clean early `2m_temperature`,
MSLP, and Z500 guardrails before validation.
