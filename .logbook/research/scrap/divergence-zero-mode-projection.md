---
schema_version: 1
slug: divergence-zero-mode-projection
title: Project Spurious Global-Mean Divergence Modes
status: scrap
created_at: 2026-06-20T04:32:18Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
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

# Project Spurious Global-Mean Divergence Modes

## Hypothesis

For any smooth horizontal vector field on a closed sphere, the area integral of
horizontal divergence is zero. The Dinosaur state carries divergence directly
in spherical-harmonic modal space, and the accepted incumbent repeatedly moves
that field through nonlinear products, semi-implicit solves, DFI, filters, and
exact Coriolis splitting. A tiny total-wavenumber-zero divergence component is
not a physical resolved flow mode; through the implicit log-surface-pressure
coupling it can behave like a global mass breathing mode and contaminate MSLP
or Z500 without representing balanced weather.

A narrow projection that removes only the modal global-mean divergence after
each positive-time step should enforce a geometric invariant while leaving
vorticity, temperature, log surface pressure, passive tracers, residual memory,
and all diagnostics unchanged.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_div0`.
Preserve the full incumbent trajectory, DFI, weak Held-Suarez forcing,
log-pressure and hydrostatic layer initialization, symmetric exact Coriolis
split, theta tendency, theta layer-mean recentering, off-centered SIL3 rollout,
Richardson 10 m wind diagnostic, and scale-separated near-surface residual.

For this candidate only:

- add an opt-in step filter after the raw positive-time step and before or
  alongside the existing theta-recentering/filter chain;
- identify the divergence modal coefficient corresponding to total wavenumber
  zero and set only that coefficient to zero for each vertical layer;
- do not alter vorticity zero modes, nonzero divergence modes, temperature,
  log_surface_pressure, tracers, or sim_time;
- keep DFI on the incumbent path unless a focused Implementer test shows the
  same projection is needed for finite DFI stability;
- guard the helper with shape tests so unsupported modal layouts fall back to
  the incumbent state rather than modifying the forecast;
- add tests proving that a synthetic nonzero global divergence mode is removed
  while all nonzero modes and all other state leaves are unchanged.

This is an invariant projection, not a pressure anchor. It does not add or
subtract global log surface pressure and does not smooth mass fields.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. Forecast input variables, output variables, lead times, target
    variables, metrics, and fixed protocols remain unchanged.
- Tests to update:
  - Unit-test exact removal of only the divergence total-wavenumber-zero mode.
  - Verify the projection is idempotent and finite.
  - Verify all non-divergence state leaves are bitwise unchanged.
  - Verify the candidate factory differs from the incumbent only by the new
    divergence-zero-mode selector and model name.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium and long leads if
    a small global divergence leak is feeding pressure/thickness drift.
  - Primary score may improve without spending near-surface guardrail margin
    because near-surface diagnostics and residual memory are unchanged.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should stay close to the
    incumbent except through downstream balanced mass-field changes.
- Possible regressions:
  - If the zero mode is already exactly zero in practice, the candidate will be
    clean but subthreshold.
  - If the semi-implicit solver uses a small numerical zero-mode divergence to
    balance another discretization error, removing it could slightly degrade
    pressure scores.

## Risks

- Numerical stability:
  - Low. The projection removes one nonphysical modal degree of freedom and is
    guarded by finite/shape checks.
- Compute cost:
  - Negligible. It is one modal assignment per step.
- Data leakage:
  - None. It uses only model state geometry and fixed modal indexing.
- Physical plausibility:
  - High. The global divergence integral vanishes on a closed sphere; the risk is
    that the effect is too small to move the fixed metrics.
- Rollback complexity:
  - Low. Remove one filter helper/flag, one factory/export, one registry entry,
    and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_div0`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_div0 --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_div0 --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean iteration delta below `+0.002` would show that global-mean divergence
    leakage is not a material remaining error source. Any MSLP or Z500 guardrail
    failure would show the projection disturbs a compensating numerical balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  stores divergence as a modal state component and couples it implicitly to
  `log_surface_pressure`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` composes
  positive-time step filters for the accepted incumbent and can host a guarded
  side-by-side invariant projection.
- Dynamaxx history:
  `.logbook/history/2026-06-16_17-43-05_global-mean-pressure-anchor/decision.md`
  rejected direct global pressure anchoring as neutral-negative, so this
  proposal avoids changing pressure and targets only the invariant-violating
  divergence mode.
- Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
  Atmospheric Models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241
- GFDL. Idealized Models with Spectral Dynamics. The documentation summarizes
  spectral atmospheric models and their conservation tradeoffs.
  https://www.gfdl.noaa.gov/idealized-models-with-spectral-dynamics/
- Taylor, M. A., and Fournier, A. 2010. A compatible and conservative spectral
  element method on unstructured grids. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2009.07.008

## Researcher Notes

This is not a duplicate of scrapped `zero-mean-vorticity-mode-projection`, which
targets relative-vorticity invariance and wind reconstruction. This proposal
targets only global-mean divergence, the component directly coupled to global
log-surface-pressure tendency.

It is also not the rejected `global-mean-pressure-anchor`: pressure is never
reset. Recent negative surface-residual evidence is not directly implicated
because the accepted residual memory path is preserved exactly.

## Evaluator Notes

### 2026-06-20T04:40:42Z

Decision: move to `scrap`.

The geometric invariant is valid, but source inspection makes this unlikely to
be a useful model-selection candidate for the current incumbent. Divergence is
initialized and repeatedly reconstructed from nodal winds through
`uv_nodal_to_vor_div_modal`/`div_cos_lat`, while explicit divergence tendencies
come from divergence or Laplacian operators whose total-wavenumber-zero
component should be derivative-null. The implicit gravity block can carry an
existing l=0 divergence into temperature/log-surface-pressure responses, but it
does not provide a clear source for creating that mode from mass fields.

For the accepted incumbent specifically, the symmetric exact Coriolis split
reconstructs vorticity and divergence from nodal winds at the positive-time
half-step boundary. Since `vor_div_to_uv_nodal` ignores the singular l=0
velocity-potential mode through the inverse Laplacian and the following
wind-to-divergence transform recomputes divergence from the velocity field, the
accepted path already removes any velocity-null divergence zero mode that might
survive the raw step. DFI remains a possible roundoff path, but there is no
evidence that it is score-relevant.

Prior loop evidence also argues against spending an iteration here:
global-mean pressure anchoring was clean but effectively neutral-negative,
divergence-selective gravity-wave damping was clean but negative, and the
continuity-balanced divergence initialization regressed primary score. This
proposal is narrower than those, but that mostly makes it more likely to be a
no-op/roundoff cleanup rather than a threshold-clearing improvement.
