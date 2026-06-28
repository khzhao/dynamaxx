---
schema_version: 1
slug: vorticity-sparing-horizontal-diffusion
title: Spare Rotational Flow in the Horizontal Diffusion Filter
status: staging
created_at: 2026-06-19T21:03:11Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/filtering.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Spare Rotational Flow in the Horizontal Diffusion Filter

## Hypothesis

The incumbent applies the same spectral horizontal diffusion filter to every
modal state leaf with a compatible shape. That keeps the model stable, but it
also damps rotational vorticity and divergent gravity-wave structure equally.
After the accepted off-centered SIL3 change, fast divergent modes already have
a strong damping path, while the remaining `10m_u_component_of_wind` and Z500
errors may be sensitive to excessive damping of balanced rotational flow.

Reducing only the vorticity diffusion strength while leaving divergence,
temperature, log-surface-pressure, tracers, off-centering, and the high-mode
stabilization path otherwise intact should preserve more geostrophic wind and
planetary-wave amplitude without reopening the mass-field instability that
uniform diffusion prevents.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_vort_sparing_diffusion`.
Preserve the incumbent DFI, weak-HS forcing, log-pressure and hydrostatic layer
initialization, symmetric exact Coriolis split, theta tendency, theta mean
recentering, semi-implicit off-centering, stability-aware residual decay,
Richardson 10 m wind diagnostic, output variables, lead schedule, and fixed
evaluation protocols.

For this candidate only:

- replace the tree-wide horizontal diffusion step filter with a state-aware
  filter for Dinosaur primitive-equation states;
- apply the incumbent diffusion scaling unchanged to `divergence`,
  `temperature_variation`, `log_surface_pressure`, and tracers;
- apply a fixed weaker diffusion scale to `vorticity`, for example 50 percent
  of the incumbent scale, with the same order and modal shape;
- preserve the global and very-low-mode behavior of the incumbent filter, and
  do not change spectral truncation, diffusion order, time step, DFI span, or
  off-centering strength;
- use the same variable-selective filter in DFI and positive-time rollout so
  the initialization and forecast discretizations remain consistent;
- fall back to the incumbent uniform filter if the state-aware filter sees an
  unsupported state type or produces nonfinite leaves.

This changes component selectivity, not spectral selectivity. It is not a
diffusion-order sweep, not low-mode planetary-wave masking, not sigma-tapered
diffusion, and not a state-dependent Leith viscosity.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, target variables, lead times, and metrics
    remain unchanged.
- Tests to update:
  - Unit-test that the default filter is exactly incumbent-equivalent.
  - Unit-test that the candidate damps vorticity less than divergence at a
    high total wavenumber while preserving all non-vorticity scaling.
  - Verify finite fallback to the uniform filter for unsupported or nonfinite
    state leaves.
  - Verify the candidate factory preserves every incumbent setting except the
    vorticity-sparing diffusion selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at days 4 to 15 if excessive rotational damping
    contributes to the persistent negative wind skill.
  - `geopotential_500` at medium leads if balanced rotational amplitude is
    better preserved while the divergent fast-mode damping remains strong.
- Expected neutral metrics:
  - `mean_sea_level_pressure` should remain close to incumbent because
    divergence, log-surface-pressure, and temperature diffusion are unchanged.
  - `2m_temperature` should remain close to incumbent because residual
    correction and weak-HS forcing are unchanged.
- Possible regressions:
  - Vorticity high modes may become too energetic and feed back into wind or
    mass fields.
  - The prior diffusion family has weak local evidence, so the signal may be
    clean but sub-threshold or negative.

## Risks

- Numerical stability:
  - Low to moderate. The stabilizing diffusion on divergent and thermodynamic
    fields remains incumbent-strength, but reduced vorticity damping could
    preserve noisy rotational modes.
- Compute cost:
  - Negligible. This changes filter coefficients on existing modal leaves and
    adds no transforms, lead times, or resolution.
- Data leakage:
  - None. The filter uses only fixed spectral geometry and model state.
- Physical plausibility:
  - Moderate. Vorticity-divergence dynamical cores often treat rotational and
    divergent components separately, and the accepted off-centering makes the
    divergent component less dependent on uniform diffusion for stability.
- Rollback complexity:
  - Low. Restore the current tree-wide filter and remove one factory/export,
    registry entry, selector, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_vort_sparing_diffusion`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_vort_sparing_diffusion --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure,
    and no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_vort_sparing_diffusion --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that uniform
    vorticity damping is not a material remaining error source. Any early 10 m
    wind, Z500, or MSLP guardrail failure would show the rotational high modes
    need incumbent-strength damping.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  applies horizontal diffusion as a post-step filter, and
  `src/dynamaxx/dycore/models/dinosaur/filtering.py` currently builds a
  shape-based tree filter.
- Dynamaxx history:
  `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md`
  accepted off-centered SIL3 with a large mass-field gain, reducing the need
  for uniform diffusion to carry all fast-mode control.
- Dynamaxx history:
  `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected a broad diffusion-order change, so this proposal keeps the order and
  high-wavenumber law fixed.
- NOAA/GFDL, The Spectral Dynamical Core, documents horizontal diffusion of
  vorticity, divergence, and temperature in spectral primitive-equation models.
  https://www.gfdl.noaa.gov/wp-content/uploads/files/user_files/pjp/spectral_core.pdf
- Jablonowski, C. and Williamson, D. L. 2011. The Pros and Cons of Diffusion,
  Filters and Fixers in Atmospheric General Circulation Models. In Numerical
  Techniques for Global Atmospheric Models. Springer.
  https://opensky.ucar.edu/islandora/object/books%3A271
- Gelb, A. and Gleeson, J. P. 2001. Spectral Viscosity for Shallow Water
  Equations in Spherical Geometry. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2001)129%3C2346:SVFSWE%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of staged `planetary-wave-preserving-horizontal-diffusion`,
which changes the spectral mask for all variables. It is not staged
`sigma-tapered-horizontal-diffusion`, which changes vertical dependence. It is
not `leith-nonlinear-eddy-viscosity`, which makes the coefficient
state-dependent. This proposal keeps the incumbent spectral law and vertical
profile and changes only the relative damping applied to vorticity versus the
gravity-wave and thermodynamic variables.

The recent theta-consistent implicit gravity operator rejection is negative
evidence against another coupled pressure/gravity matrix change. This proposal
does not touch the implicit operator or inverse. The recent Ekman diagnostic
rejection was clean but sub-threshold; this proposal changes the prognostic
rotational amplitude that feeds 10 m wind rather than another output-direction
diagnostic.

## Evaluator Notes

### 2026-06-19T21:10:25Z

Decision: move to `staging`; ranked 2 of 3 fresh proposals.

The proposal is implementable and not a duplicate of active diffusion ideas.
Source inspection confirms the incumbent builds one shape-based horizontal
diffusion filter and applies it through the step-filter path, so a
primitive-equation-state-aware filter could preserve the incumbent scaling for
divergence, temperature variation, log-surface pressure, and tracers while
weakening only vorticity. The NOAA/GFDL spectral-core documentation supports
the general physical framing by documenting horizontal diffusion of vorticity,
divergence, and temperature with spectral Laplacian powers in primitive-equation
models; Jablonowski and Williamson remain useful cautionary background on the
tradeoffs of filters and fixers.

Keep staged rather than ready because the local diffusion family evidence is
weak. `scale-selective-hyperdiffusion` regressed primary score by
`-0.05124210065383061` and failed the early 10 m wind guardrail, while several
active staged proposals already test spectral, vertical, and state-dependent
diffusion variants. This candidate is narrower than those because it preserves
the horizontal spectral law and does not weaken mass or thermodynamic damping,
but it still changes the prognostic trajectory and could preserve noisy
rotational high modes that later contaminate 10 m wind, Z500, or MSLP.

If promoted later, use a conservative fixed vorticity multiplier, apply the
same selector in DFI and positive-time rollout, and require tests that
non-vorticity leaves are incumbent-equivalent and unsupported states fall back
to the uniform filter.
