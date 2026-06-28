---
schema_version: 1
slug: enstrophy-conserving-vorticity-jacobian
title: Use an Enstrophy-Conserving Rotational Vorticity Jacobian
status: scrap
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

# Use an Enstrophy-Conserving Rotational Vorticity Jacobian

## Hypothesis

The incumbent still loses `10m_u_component_of_wind` skill after the first few
days, while broad damping, timestep, and flux-dealiasing variants have been
neutral or negative. A remaining path is not more damping, but a more balanced
horizontal rotational-vorticity discretization that reduces nonlinear cascade
error without suppressing resolved waves.

Classical atmospheric discretizations often separate rotational Jacobian
accuracy from divergent mass adjustment. Replacing only the nondivergent
rotational part of the absolute-vorticity tendency with an Arakawa-style
energy/enstrophy-conserving Jacobian should reduce rotational phase and cascade
error while preserving the accepted off-centered gravity-wave damping,
divergent flow, pressure-gradient, vertical-advection, weak-HS, and surface
residual mechanisms.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_vort_jacobian`.
Preserve all accepted incumbent options and add one opt-in vorticity tendency
formulation inside the sigma primitive equation.

In `PrimitiveEquationsSigma.curl_and_div_tendencies`, split the horizontal
absolute-vorticity transport into:

- a nondivergent rotational component based on the streamfunction
  `psi = inverse_laplacian(vorticity)`;
- a divergent component based on the velocity potential
  `chi = inverse_laplacian(divergence)`;
- the existing vertical-advection and pressure-gradient vector terms.

For the rotational component only, compute a finite-grid Arakawa-style Jacobian
for `-J(psi, zeta + f)` using existing spherical harmonic gradient transforms
and a symmetric average of advective, flux, and divergence forms. Keep the
incumbent operator for the divergent absolute-vorticity flux and for the
divergence tendency. Clip final modal tendencies with the existing
`coords.horizontal.clip_wavenumbers` path and fall back to the incumbent
tendency if any required field is nonfinite.

The implementer should start with the dry sigma equation used by the incumbent.
Humidity tendencies, pressure-gradient terms, DFI, off-centered SIL3, Coriolis
Strang splitting, and output diagnostics remain unchanged.

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
  - None. Forecast input/output shapes, target variables, metrics, and lead
    times remain unchanged.
- Tests to update:
  - Unit-test that solid-body rotation or zero-vorticity states remain finite
    and close to the incumbent tendency.
  - Unit-test that the new Jacobian returns zero for horizontally constant
    absolute vorticity.
  - Verify finite fallback to the incumbent tendency on nonfinite helper output.
  - Verify the candidate factory preserves all accepted incumbent flags except
    the new vorticity-formulation selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and long leads if rotational cascade or
    phase error is degrading large-scale wind evolution.
  - `geopotential_500` if more coherent rotational flow improves balanced height
    evolution without additional damping.
- Expected neutral metrics:
  - `2m_temperature` should remain close to incumbent because thermal tendency,
    weak-HS forcing, and near-surface residual memory are unchanged.
  - `mean_sea_level_pressure` should be less affected than in mass-continuity or
    pressure-gradient proposals because the divergence tendency is not replaced.
- Possible regressions:
  - The split between rotational and divergent flow may omit useful cancellation
    present in the incumbent vector-invariant flux form.
  - The Arakawa-style helper on a spherical spectral grid is an approximation;
    poor metric weighting could create polar or high-wavenumber noise.

## Risks

- Numerical stability:
  - Moderate. The change touches nonlinear momentum/vorticity tendencies, but
    final modal clipping and finite fallback are required.
- Compute cost:
  - Moderate. It adds inverse Laplacians, gradient transforms, and extra nodal
    products each explicit tendency evaluation. The reported 48 CPU, 153-173 GiB
    RAM, 4 L4 GPU resource envelope should still fit one side-by-side candidate
    under `--workers 4`, but fast runtime should be watched.
- Data leakage:
  - None. The tendency uses only forecast state and fixed grid/physics
    operators.
- Physical plausibility:
  - Moderate to high. Energy/enstrophy-conserving Jacobians are standard
    motivation for geophysical rotational flow discretization, though adapting
    them to this spectral sigma model is approximate.
- Rollback complexity:
  - Moderate. Remove one primitive-equation option/helper, one adapter flag, one
    factory/export, one registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_vort_jacobian`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_vort_jacobian --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_vort_jacobian --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta would show that rotational-vorticity
    cascade error is not a material remaining bottleneck. Any early wind, Z500,
    or MSLP guardrail failure would show the split disrupts balanced vector
    dynamics.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  currently computes vorticity and divergence tendencies through a single
  vector-invariant flux construction in `curl_and_div_tendencies`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py`
  provides `inverse_laplacian`, `cos_lat_grad`, `curl_cos_lat`, and
  `div_cos_lat`, which are sufficient to build a side-by-side rotational
  Jacobian helper.
- History: `.logbook/history/2026-06-20_05-39-53_absolute-vorticity-flux-dealiasing/decision.md`
  rejected product dealiasing as only `+0.00017069712459116815`; this proposal
  changes the rotational advective form rather than applying another spectral
  product mask.
- History: `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected stronger diffusion with wind guardrail regression, so this proposal
  avoids adding damping.
- Active research reference: `.logbook/research/staging/kinetic-energy-skew-momentum-advection.md`
  targets full horizontal momentum skew symmetry; this proposal is narrower and
  targets only the rotational vorticity Jacobian.
- Arakawa, A. 1966. Computational design for long-term numerical integration of
  the equations of fluid motion: Two-dimensional incompressible flow. Journal of
  Computational Physics. https://doi.org/10.1016/0021-9991(66)90015-5
- Arakawa, A. and Lamb, V. R. 1981. A potential enstrophy and energy conserving
  scheme for the shallow water equations. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0018:APEAEC%3E2.0.CO;2
- Salmon, R. 2004. Poisson-bracket approach to the construction of energy- and
  potential-enstrophy-conserving algorithms for the shallow-water equations.
  Journal of the Atmospheric Sciences.
  https://doi.org/10.1175/1520-0469(2004)061%3C2016:PATTCO%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of recent `absolute-vorticity-flux-dealiasing`, which
left the incumbent advective form intact and only dealiased products. The new
mechanism asks whether the rotational vorticity operator itself should be more
enstrophy-conserving.

It is also distinct from staged `kinetic-energy-skew-momentum-advection`,
`vorticity-sparing-horizontal-diffusion`, and scrapped
`pv-gradient-aware-vorticity-filter`: it does not rewrite the full momentum
advection, does not change horizontal diffusion, and does not add a PV or
vorticity filter. It keeps the accepted off-centered SIL3 damping because the
Williamson CN-RK3 rollout rejection showed that removing that positive-time
fast-mode damping is not viable.

## Evaluator Notes

### 2026-06-20T10:48:47Z

Decision: move to `scrap`; ranked 3 of 3 in this triage pass.

The conservation motivation is legitimate, but the proposal is not a good
candidate for this loop state. The closest recent nonlinear-vorticity evidence
is `absolute-vorticity-flux-dealiasing`, which was clean but only
`+0.00017069712459116815`, far below the `+0.002` promotion threshold. That
does not falsify every nonlinear operator idea, but it raises the bar for a
new vorticity-only refinement.

This candidate does not clear that bar. It would split the current
vector-invariant vorticity/divergence operator, introduce an approximate
Arakawa-style Jacobian on a spherical spectral grid, and rely on fallbacks around
core explicit tendencies. That is a broad, error-prone change with a meaningful
risk of disrupting cancellations between rotational, divergent, pressure-gradient
and vertical-advection terms.

It is also dominated by active staging. `kinetic-energy-skew-momentum-advection`
already preserves a broader and cleaner structure-preserving momentum-advection
test, while `two-thirds-explicit-tendency-dealiasing`,
`pressure-gradient-product-dealiasing`, `leith-nonlinear-eddy-viscosity`, and
related staged ideas cover
nonlinear-product or vorticity-cascade hypotheses with clearer implementation
boundaries. Do not keep this additional vorticity-Jacobian variant active unless
future diagnostics show a specific rotational-Jacobian error that those staged
ideas cannot test.
