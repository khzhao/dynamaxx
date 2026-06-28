---
schema_version: 1
slug: deterministic-ke-backscatter
title: Reinject a Bounded Fraction of Diffused Kinetic Energy
status: scrap
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

# Reinject a Bounded Fraction of Diffused Kinetic Energy

## Hypothesis

The incumbent uses horizontal diffusion and off-centered semi-implicit damping
that stabilize the rollout, but both can remove kinetic energy from synoptic
scales. Recent narrow dealiasing was stable but too weak, while changing the
solver family without the accepted off-centering was strongly harmful. A
deterministic kinetic-energy backscatter filter can keep the accepted damping
and solver path, but return a small, capped fraction of diagnosed diffusion loss
to rotational flow at retained synoptic wavenumbers.

This should help if the remaining late-lead MSLP/Z500 and wind errors include
over-damped eddies rather than only thermal-equilibrium bias.

## Mechanism

Replace the candidate's horizontal diffusion filter with a budgeted wrapper:

- apply the incumbent horizontal diffusion exactly as today;
- compute area-weighted layer kinetic energy from vorticity/divergence-derived
  nodal winds before and after that diffusion filter;
- estimate the nonnegative kinetic-energy loss per layer, ignoring nonfinite or
  energy-increasing cases;
- form a rotational-only modal increment aligned with the current low-order
  vorticity anomaly or recent vorticity tendency, using a smooth total-wavenumber
  band that avoids the truncation edge;
- scale that increment to return only a small fixed fraction of the diagnosed
  lost kinetic energy, with a hard cap on wind-speed change per inner step;
- leave divergence, temperature, log surface pressure, tracers, residual memory,
  weak-HS forcing, and the accepted Coriolis split otherwise unchanged.

This is deterministic, so it does not introduce ensemble spread or a stochastic
forecast contract. The proposal tests whether a controlled upscale energy return
is more useful than additional diffusion tuning or output-only residuals.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for an opt-in
    `use_deterministic_ke_backscatter` flag and a diffusion-filter wrapper.
  - `src/dynamaxx/dycore/registry.py` for a side-by-side candidate factory.
  - `tests/dycore/test_registry.py` plus focused tests for zero-loss no-op,
    positive-loss cap enforcement, and finite fallback.
- Registry changes:
  - Add a model named
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_ke_backscatter`.
- API changes:
  - None. The output is the same single `WeatherState` forecast trajectory.
- Tests to update:
  - Registration/dependency tests.
  - Adapter unit tests verifying that the wrapper preserves state tree shape and
    cannot create nonfinite vorticity/divergence from finite inputs.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 5-15 if synoptic
    eddy amplitude is currently too damped.
  - `10m_u_component_of_wind` at medium leads if rotational wind variance is
    under-retained after diffusion and off-centering.
- Expected neutral metrics:
  - `2m_temperature` should be close to neutral because no thermal or
    near-surface residual correction is changed.
  - Early lead fields should remain close to incumbent under the per-step wind
    cap.
- Possible regressions:
  - Backscatter can amplify noisy vorticity modes or worsen phase errors.
  - Wind improvement may be offset by MSLP/Z500 degradation if energy is returned
    into the wrong scales.

## Risks

- Numerical stability:
  - Moderate. Any negative-viscosity-like mechanism can destabilize rollouts if
    caps or masks are too loose. The first candidate should return a very small
    fraction of loss and skip nonfinite diagnostics.
- Compute cost:
  - Low to moderate. Additional wind transforms and global reductions per inner
    step are manageable on the reported 48 CPU / 4 L4 GPU machine with 4 eval
    workers.
- Data leakage:
  - Low. The backscatter amplitude is computed from the model step itself, not
    from future truth or evaluation statistics.
- Physical plausibility:
  - Moderate. Operational backscatter schemes are usually stochastic and tied to
    parameterized physics; this is a deterministic dycore surrogate.
- Rollback complexity:
  - Low. It is a side-by-side opt-in wrapper around the existing diffusion
    filter.

## Evaluation Plan

- Fast gate:
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_ke_backscatter`.
  - Require clean diagnostics and no nonfinite rows.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_ke_backscatter --workers 4`.
  - Support requires primary-score delta at least `+0.002`, no fixed guardrail
    failures, and no broad late-lead wind degradation.
- Validation gate:
  - Run validation with `--workers 4` only after iteration promotion; require
    primary-score delta at least `+0.001`.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold delta would indicate that the incumbent is not limited
    by over-damped kinetic energy. Any nonfinite run or wind guardrail issue
    would reject this mechanism as too aggressive.

## Citations

- Shutts, G. J. 2005. "A kinetic energy backscatter algorithm for use in
  ensemble prediction systems." Quarterly Journal of the Royal Meteorological
  Society. https://doi.org/10.1256/qj.04.106
- Berner, J., Shutts, G. J., Leutbecher, M., and Palmer, T. N. 2009. "A
  spectral stochastic kinetic energy backscatter scheme and its impact on
  flow-dependent predictability in the ECMWF ensemble prediction system."
  Journal of the Atmospheric Sciences. https://doi.org/10.1175/2008JAS2677.1
- Jablonowski, C. and Williamson, D. L. 2011. "The pros and cons of diffusion,
  filters and fixers in atmospheric general circulation models." In Numerical
  Techniques for Global Atmospheric Models. https://doi.org/10.1007/978-3-642-11640-7_13

## Researcher Notes

This is not another diffusion-strength retune, Leith eddy viscosity,
planetary-wave-preserving diffusion, or dissipative-heating proposal. It keeps
the incumbent diffusion and asks whether a small part of the diagnosed kinetic
energy loss should return to resolved rotational flow. It also avoids the recent
CN-RK3 failure by preserving the accepted off-centered SIL3 positive-time
rollout.

## Evaluator Notes

### 2026-06-20T12:56:24Z

Decision: move to `scrap`.

The proposal preserves the fixed forecast contract and has reputable
backscatter motivation, but it is not a good next model-selection candidate for
this incumbent. It would add a deterministic negative-damping-like increment to
rotational flow every diffusion step, with extra global energy accounting,
mode-shape choices, and wind caps. That implementation surface is broader and
less directly constrained than the accepted theta post-step filters.

Local evidence and active research state argue against promoting another
diffusion/energy-return variant now. The recent absolute-vorticity flux
dealiasing experiment was clean but effectively neutral at only
`+0.00017069712459116815`, far below the `+0.002` iteration gate. Broader
diffusion-family ideas are already staged, including
`planetary-wave-preserving-horizontal-diffusion`,
`leith-nonlinear-eddy-viscosity`,
`theta-diffusion-dissipative-heating`, and
`kinetic-energy-skew-momentum-advection`; those cover lower-risk or more
mechanistic ways to test over-damping, energy accounting, and nonlinear energy
transfer.

Scrapping this file keeps the ready queue focused and avoids spending an
iteration on a high-risk backscatter surrogate whose amplitude, modal pattern,
and cap choices could easily amplify phase error or near-truncation noise. If
future diagnostics conclusively show under-retained kinetic energy after the
staged diffusion and dissipative-heating ideas are exhausted, a narrower
proposal should be rewritten with one predeclared modal pattern and stronger
offline energy tests rather than revived directly from this broad wrapper.
