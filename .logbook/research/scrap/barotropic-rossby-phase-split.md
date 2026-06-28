---
schema_version: 1
slug: barotropic-rossby-phase-split
title: Add a Low-Mode Barotropic Rossby Phase Split
status: scrap
created_at: 2026-06-19T23:12:17Z
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

# Add a Low-Mode Barotropic Rossby Phase Split

## Hypothesis

The accepted exact Coriolis and Strang split results show that isolating a
linear rotational process can improve this spectral primitive-equation rollout.
The current incumbent still loses medium-range skill in `geopotential_500` and
MSLP as synoptic and planetary waves drift. A small residual source of error may
be phase error in the low-mode barotropic Rossby component, which strongly
controls large-scale pressure and height patterns.

A phase-only low-mode barotropic vorticity split can test this mechanism without
adding diffusion, changing amplitudes, anchoring to the initial analysis, or
altering near-surface residual diagnostics.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_rossby_phase`.
Preserve all incumbent physics, initialization, DFI, Coriolis Strang rotation,
theta tendency, theta recentering, semi-implicit off-centering, output residuals,
and fixed evaluation protocols.

Add an opt-in step filter during positive-time rollout only:

- compute the pressure- or sigma-thickness-weighted vertical mean of modal
  vorticity after each inner step;
- select only very low total wavenumbers, for example `2 <= n <= 10`, tapering
  to zero by `n = 14`, and exclude zonal-mean `m = 0` coefficients;
- rotate each selected complex spherical-harmonic coefficient by a small
  analytic barotropic Rossby phase over the step, using the spherical
  nondivergent mode estimate `omega = -2 * Omega * m / (n * (n + 1))`;
- apply only a fixed fraction of that phase update, for example `0.25`, so the
  candidate supplements rather than replaces the full primitive-equation
  vorticity tendency;
- add the resulting barotropic vorticity increment back uniformly across sigma
  layers or with sigma-thickness weights;
- preserve modal amplitude exactly for the corrected barotropic component;
- leave divergence, temperature, `log_surface_pressure`, tracers, Coriolis
  rotation, DFI, output packing, and residual corrections unchanged;
- skip the correction for modes whose modal layout cannot expose total
  wavenumber and zonal wavenumber safely.

This is not another diffusion or damping proposal. It is also not an initial
planetary-wave anchor because it does not use analysis residuals after
initialization; it applies a deterministic phase split to the forecast's own
current low-mode barotropic vorticity.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py` only if a small
    helper is needed to expose modal wavenumber indices cleanly
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory with the `_rossby_phase` suffix.
- API changes:
  - None. Forecast input, output variables, target variables, and metrics remain
    unchanged.
- Tests to update:
  - Unit-test the modal mask and phase angles for known `(n, m)` coefficients.
  - Verify amplitude preservation for a synthetic complex modal coefficient.
  - Verify the filter changes only vorticity and leaves divergence,
    temperature variation, log pressure, tracers, and `sim_time` unchanged.
  - Verify the candidate does not apply the filter during DFI.
  - Add factory, registry, and finite non-JIT smoke coverage.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 3 to 15 if
    low-mode planetary/synoptic phase error is a remaining large-scale source of
    error.
  - Some secondary 10 m wind improvement through improved barotropic steering,
    without changing the accepted Richardson diagnostic.
- Expected neutral metrics:
  - `2m_temperature` should remain dominated by the accepted scale-separated
    residual path.
- Possible regressions:
  - The analytic nondivergent Rossby phase estimate is only approximate for a
    stratified primitive-equation state with divergence and thermal coupling.
  - Phase-only vorticity updates can still alter pressure gradients indirectly
    and may hurt early Z500 or MSLP if applied too strongly.

## Risks

- Numerical stability:
  - Low to moderate. The update preserves selected modal amplitudes, but it
    changes a prognostic vorticity component each step.
- Compute cost:
  - Low. The filter is modal arithmetic on a small subset of coefficients.
- Data leakage:
  - None. It uses only the forecast state, fixed grid metadata, and physical
    rotation rate.
- Physical plausibility:
  - Moderate. Barotropic Rossby phase speeds are a standard spherical wave
    reference, but this is an approximate split inside a baroclinic primitive
    equation model.
- Rollback complexity:
  - Low. Remove one filter/flag, optional helper, one factory/export, one
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_rossby_phase`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_rossby_phase --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail violation.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_rossby_phase --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001`.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, an early Z500 guardrail
    failure, or broad MSLP regression would show that approximate Rossby phase
    splitting is not a useful remaining error correction for this incumbent.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-18_03-03-20_exact-coriolis-rotation-split/decision.md`
  and `.logbook/history/2026-06-18_04-38-06_symmetric-coriolis-rotation-split/decision.md`
  accepted exact linear Coriolis splitting, motivating a separate low-mode
  linear wave split rather than another damping proposal.
- Williamson, D. L., Drake, J. B., Hack, J. J., Jakob, R., and Swarztrauber,
  P. N. 1992. "A standard test set for numerical approximations to the shallow
  water equations in spherical geometry." Journal of Computational Physics.
  https://doi.org/10.1016/S0021-9991(05)80016-6
- Bourke, W. 1974. "A Multi-Level Spectral Model. I. Formulation and
  Hemispheric Integrations." Monthly Weather Review.
  https://journals.ametsoc.org/view/journals/mwre/102/10/1520-0493_1974_102_0687_amlsmi_2_0_co_2.xml
- Held, I. M., and Suarez, M. J. 1994. "A Proposal for the Intercomparison of
  the Dynamical Cores of Atmospheric General Circulation Models." Bulletin of
  the American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Dinosaur upstream documentation describes its spectral JAX atmospheric
  dynamical core: https://github.com/neuralgcm/dinosaur

## Researcher Notes

This is not a duplicate of `decaying-planetary-wave-initial-anchor`, which was
scrapped because it blended forecast state back toward initial analysis modes.
This proposal is phase-only, amplitude-preserving, and uses no analysis target
after the initial forecast state is created. It is also distinct from staged
diffusion, vorticity-sparing diffusion, and Leith-viscosity ideas because it
does not damp or strengthen any mode.

## Evaluator Notes

### 2026-06-19T23:16:12Z

Decision: move to `scrap`.

The proposal is scientifically interesting but too speculative for the current
queue. The Rossby-Haurwitz/barotropic frequency formula is a real shallow-water
or nondivergent reference, but applying a fractional analytic phase rotation to
the vertically averaged vorticity inside a dry, stratified primitive-equation
rollout is not the same kind of isolated linear split as the accepted Coriolis
rotation. The cited Williamson et al. shallow-water test-set paper supports
Rossby-Haurwitz waves as idealized spherical shallow-water structure, not as a
guarantee that this phase-only correction will improve MSLP/Z500 in the current
baroclinic model. See Williamson et al. 1992, Journal of Computational Physics,
https://doi.org/10.1016/S0021-9991(05)80016-6.

The idea is also dominated by existing research state. The staged
`planetary-wave-preserving-horizontal-diffusion` tests low-mode wave-amplitude
handling without imposing a new analytic phase tendency, and the scrapped
`decaying-planetary-wave-initial-anchor` documents why repeated low-mode edits
to balanced prognostic state are risky. This proposal avoids analysis anchoring
and preserves modal amplitude, but it still edits prognostic vorticity every
inner step and can indirectly perturb pressure gradients, Z500, MSLP, and wind
phase. That is a worse cost-risk tradeoff than the ready mass residual and the
staged thermal IAU.

Rank: 3 of 3 fresh proposals. Scrap rather than keep another low-mode
prognostic wave modifier in staging.
