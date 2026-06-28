---
schema_version: 1
slug: bounded-log-pressure-tendency-limiter
title: Bound Extreme Log-Surface-Pressure Step Increments
status: staging
created_at: 2026-06-20T10:45:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
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

# Bound Extreme Log-Surface-Pressure Step Increments

## Hypothesis

The incumbent's long-lead `mean_sea_level_pressure` skill degrades while the
accepted off-centered SIL3 step and scale-separated near-surface residuals keep
fast diagnostics clean. Prior mass-field experiments show that anchoring the
global pressure mode or rewriting continuity in flux form is either too weak or
harmful. A narrower stability mechanism is to limit only spatially extreme
one-step log-surface-pressure increments while preserving the step's global
mean increment.

This targets local continuity overshoots and sigma-coordinate pressure-gradient
noise without applying an analysis residual, changing the fixed score contract,
or weakening the accepted off-centered fast-mode damping.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_logp_limiter`.
Preserve all accepted incumbent options and add one positive-time step filter
after the accepted off-centered SIL3 step, exact Coriolis Strang wrapper, and
standard horizontal diffusion.

The filter should:

- convert `prev_state.log_surface_pressure` and `next_state.log_surface_pressure`
  to nodal fields;
- compute the one-step increment `delta_logp = next_logp - prev_logp`;
- compute an area-weighted mean increment and anomaly using the Dinosaur
  quadrature weights;
- bound only the anomaly with fixed values, for example the smaller of
  `3.0 * rms(delta_logp_anomaly)` and an absolute `0.02` log-pressure cap per
  900 s inner step;
- add the unmodified area-mean increment back, so the filter is not a global
  pressure anchor;
- convert the corrected log-pressure field back to modal space and leave
  vorticity, divergence, temperature, tracers, and `sim_time` unchanged;
- no-op on nonfinite diagnostics or unexpected shapes.

The same limiter may be included in DFI filters only if the implementation
proves the signed backward/forward path remains finite. The first implementation
should default to positive-time rollout only.

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
  - None. The forecast API, output variables, target variables, lead times,
    metrics, and protocols remain unchanged.
- Tests to update:
  - Unit-test that small increments pass through exactly.
  - Unit-test that extreme local increments are bounded while the area-mean
    increment is preserved.
  - Verify non-log-pressure state leaves are unchanged.
  - Verify nonfinite inputs fall back to the accepted unfiltered state.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at medium and long leads if local continuity
    overshoots are a remaining source of pressure drift.
  - `geopotential_500` if less noisy surface-pressure evolution improves
    hydrostatic thickness and pressure-gradient balance.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should be mostly neutral
    because near-surface residual correction and wind diagnostics are unchanged.
- Possible regressions:
  - Synoptic pressure deepening or filling can be physically rapid; too tight a
    cap may suppress real cyclogenesis and damage MSLP skill.
  - Any pressure-path filter can indirectly affect winds and heights through the
    sigma-coordinate pressure-gradient force.

## Risks

- Numerical stability:
  - Low to moderate. The filter is bounded and finite-guarded, but it modifies a
    prognostic mass field each inner step.
- Compute cost:
  - Low. It adds one nodal transform, one modal transform, and reductions over a
    single surface field per step.
- Data leakage:
  - None. The limiter uses only the previous and next forecast states and fixed
    constants.
- Physical plausibility:
  - Moderate. Conservative and monotone transport methods commonly control
    local tracer or mass overshoots; this is a simplified spectral-step analog
    for log surface pressure.
- Rollback complexity:
  - Low. Remove one filter flag, one helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_logp_limiter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_logp_limiter --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_logp_limiter --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta would show that local log-pressure
    increment overshoots are not a material remaining error source. Any MSLP,
    Z500, or 10 m wind guardrail failure would show the limiter is suppressing
    real balanced pressure evolution.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  computes sigma-coordinate log-surface-pressure tendency from
  `u_dot_grad_log_sp`, while `adapter.py` already hosts positive-time filters
  for accepted Coriolis rotation and theta recentering.
- History: `.logbook/history/2026-06-16_17-43-05_global-mean-pressure-anchor/decision.md`
  rejected direct global pressure anchoring as neutral-negative, so this
  proposal preserves the model's own area-mean pressure increment.
- History: `.logbook/history/2026-06-18_11-53-08_flux-form-surface-pressure-continuity/decision.md`
  rejected a broader continuity rewrite with iteration delta
  `-0.015126833559440334`; this proposal is a local increment limiter rather
  than a new continuity equation.
- History: `.logbook/history/2026-06-19_03-32-34_mass-conserving-logp-spectral-smoother/decision.md`
  found mass-conserving spectral smoothing effectively neutral, so this proposal
  limits only step increments rather than smoothing the accumulated field.
- Lin, S.-J. and Rood, R. B. 1996. Multidimensional flux-form semi-Lagrangian
  transport schemes. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Thuburn, J. 1996. Multidimensional flux-limited advection schemes. Journal of
  Computational Physics. https://doi.org/10.1006/jcph.1996.0215
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of rejected `global-mean-pressure-anchor`, because it
does not restore the initial mass or pressure mean. It preserves the model's
own step-mean pressure increment and only bounds local anomaly increments.

It is also distinct from rejected `flux-form-surface-pressure-continuity` and
`mass-conserving-logp-spectral-smoother`: it does not replace the continuity
tendency and does not smooth the accumulated log-pressure field by wavenumber.
The intended question is narrower: whether rare local log-pressure increments
are spending MSLP/Z500 skill after the accepted off-centered fast-mode control.

## Evaluator Notes

### 2026-06-20T10:48:47Z

Decision: move to `staging`; ranked 2 of 3 in this triage pass.

The proposal is distinct enough to preserve but not strong enough for the next
implementation. It is narrower than the rejected global mean pressure anchor,
the rejected flux-form surface-pressure continuity rewrite, and the neutral
mass-conserving log-pressure spectral smoother: it preserves the model's
area-mean step increment and bounds only local one-step anomaly increments after
the accepted off-centered rollout step.

Recent mass and log-pressure evidence keeps it out of `ready`. The direct
global pressure anchor was effectively neutral-negative, flux-form continuity
was clearly negative at `-0.015126833559440334`, and mass-conserving log-pressure
smoothing was clean but effectively zero at `+0.0000014025155478103457`. There
is also no scorer diagnostic showing that rare local log-pressure increments are
the current incumbent's limiting error, and a fixed cap can suppress physically
real synoptic pressure deepening or filling.

Keep this as a later pressure-path fallback if diagnostics or failed staged
mass-field ideas point specifically to local continuity overshoots. If promoted
later, the implementation should be positive-time only at first, preserve the
area-mean increment exactly, use a fixed broad cap, no-op on nonfinite or shape
mismatches, and include tests showing all non-log-pressure state leaves are
unchanged.
