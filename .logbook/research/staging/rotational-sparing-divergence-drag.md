---
schema_version: 1
slug: rotational-sparing-divergence-drag
title: Rotational-Sparing Lower-Boundary Divergence Drag
status: staging
created_at: 2026-06-21T23:28:24Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
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

# Rotational-Sparing Lower-Boundary Divergence Drag

## Hypothesis

The incumbent has useful low-level wind diagnostics, scale-separated
near-surface residual memory, and an analysis-offset thermal equilibrium, but
the positive-time dry rollout still lacks a boundary-layer sink for unresolved
ageostrophic convergence. The cached incumbent iteration metrics show
`mean_sea_level_pressure` skill becomes negative after day 3 and
`10m_u_component_of_wind` skill becomes negative after day 3, while recent
output-only residual variants were clean but too small to clear the primary
gate. A weak, lower-sigma damping of the divergent wind component should reduce
spurious near-surface convergence and gravity-wave adjustment without damping
balanced rotational jets, changing surface-temperature diagnostics, or
modifying the analysis-HS equilibrium.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_rot_sparing_div_drag`.
Preserve the full incumbent initialization, DFI, weak Held-Suarez thermal
forcing, analysis-HS offset, Coriolis Strang split, theta tendency/recentering,
semi-implicit off-centering, pressure-level diagnostics, 10 m wind diagnostic,
near-surface residual correction, output variables, lead schedule, and fixed
evaluation protocols.

For the candidate only, add a positive-time step filter after the existing
rollout dynamics and horizontal diffusion filters, but keep it out of the
time-reversed DFI initializer:

- leave vorticity unchanged so the rotational component of horizontal wind and
  large-scale jets are not directly damped;
- multiply modal divergence by an exact exponential damping factor with a
  smooth vertical taper that is largest in the lowest sigma layer and zero above
  about `sigma = 0.70`;
- use one fixed conservative lowest-layer e-folding time, for example
  `5` to `8` days, and do not tune it against iteration or validation scores;
- leave temperature variation, `log_surface_pressure`, tracers, `sim_time`,
  analysis-HS forcing, and output diagnostics unchanged;
- guard the filter so nonfinite factors or incompatible shapes fall back to the
  incumbent next state.

This is not a full Rayleigh drag, not an ageostrophic wind estimate, and not a
near-surface residual gate. It damps only the divergent modal component in the
lower boundary layer, which is the component most directly tied to spurious
mass convergence and fast gravity adjustment.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model factory and registry key with the
    `_rot_sparing_div_drag` suffix.
- API changes:
  - None. `DycoreModel.forecast`, forecast inputs, outputs, target variables,
    splits, and deterministic gates remain unchanged.
- Tests to update:
  - Unit-test the sigma taper: finite, monotone toward the surface, zero above
    the cutoff, and shape-compatible with the model vertical grid.
  - Unit-test the step filter on synthetic states: divergence damps by the
    expected exact factor, while vorticity, temperature variation,
    `log_surface_pressure`, tracers, and `sim_time` are unchanged.
  - Verify the filter is added only to positive-time rollout filters, not to DFI
    filters.
  - Verify the candidate factory preserves every incumbent option except the new
    divergence-drag selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 3 to 15 if low-level divergent noise is
    feeding mass-field drift.
  - `10m_u_component_of_wind` at medium leads if unresolved boundary-layer
    convergence is contributing to the persistent zonal-wind error.
  - `geopotential_500` may improve modestly if reduced mass adjustment improves
    large-scale balance.
- Expected neutral metrics:
  - `2m_temperature` should remain close to incumbent because screen-temperature
    diagnostics, surface residuals, and thermal forcing are unchanged.
  - Rotational wind-dominated synoptic jets should move less than in full
    Rayleigh or deformation-rate damping experiments.
- Possible regressions:
  - Real cyclone and frontal convergence can be physically important; damping it
    can worsen MSLP evolution.
  - If the remaining wind error is rotational or diagnostic rather than
    divergent, primary movement may be near zero.

## Risks

- Numerical stability:
  - Low to moderate. Exact damping is stable, but any positive-time divergence
    filter changes mass-wind adjustment and must be guarded by the fixed early
    RMSE checks.
- Compute cost:
  - Negligible to low. The simplest implementation multiplies existing modal
    divergence by a layerwise factor and adds no output volume or extra leads.
- Data leakage:
  - None. The filter uses only the forecast state, sigma geometry, fixed
    constants, and no future targets, validation statistics, or golden data.
- Physical plausibility:
  - Moderate. Boundary-layer friction primarily acts on ageostrophic flow, and
    low-level convergence is tightly coupled to pressure tendency. This proposal
    is a reduced numerical surrogate, not a full turbulent closure.
- Rollback complexity:
  - Low. Remove one adapter flag/helper, one factory/export, one registry entry,
    and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_rot_sparing_div_drag`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_rot_sparing_div_drag --workers 4`.
  - Compare against the valid cached incumbent artifacts. Support requires
    primary-score delta at least `+0.002`, clean diagnostics, no early day 1-5
    mean RMSE regression over `2%`, and no variable-lead RMSE regression over
    `10%`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_rot_sparing_div_drag --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show lower-boundary
    divergent damping is not a material remaining error source. Any early MSLP,
    Z500, or wind guardrail failure would show the filter is too intrusive.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` sets
    `DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY = 0.0` and assembles positive-time
    filters separately from DFI filters, which provides a local hook for an
    opt-in rollout-only divergence filter.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
    represents the state directly in modal `vorticity` and `divergence`, making
    a rotational-sparing divergence filter implementable without changing the
    forecast contract.
  - Dynamaxx history:
    `.logbook/history/2026-06-21_21-39-17_coherent-u-residual-gate/decision.md`
    found a one-channel residual gate clean but far below the primary-score
    threshold, motivating a forecast-internal low-level balance mechanism.
  - Dynamaxx history:
    `.logbook/history/2026-06-21_10-27-50_first-step-divergence-balance-filter/decision.md`
    showed that broad first-step divergence edits can violate early MSLP
    guardrails; this proposal is weaker, lower-boundary-tapered, and applied as
    exact positive-time damping rather than an initialization balance rewrite.
  - Dynamaxx research:
    `.logbook/research/staging/geostrophic-sparing-boundary-layer-drag.md`
    and `.logbook/research/staging/exponential-boundary-layer-rayleigh-drag.md`
    cover full or ageostrophic wind damping; this proposal preserves vorticity
    exactly and damps only modal divergence.
  - Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of
    dynamical cores of atmospheric general circulation models. Bulletin of the
    American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2

## Researcher Notes

This proposal is intentionally decorrelated from the active
`land-sea-contrast-surface-temperature` and
`orographic-lapse-screen-temperature` proposals: it does not touch
`2m_temperature`, static land/ocean masks, or orography-based screen-temperature
diagnostics. It is also not another analysis-HS offset source, residual-memory
gate, or pressure-level output reconstruction. The recent negative evidence
argues against tiny output-side residual tweaks and near-no-op HS variants; this
tests a separate low-level mass-wind balance mechanism while preserving the
fixed forecast contract and evaluation protocol.

## Evaluator Notes

### 2026-06-21T23:30:36Z

Decision: move to `staging`; ranked 3 of 3 current proposals.

The mechanism is not a duplicate of the existing full Rayleigh or
geostrophic-sparing drag proposals: damping modal divergence while preserving
vorticity is a cleaner rotational-sparing test, and it does not require any
forecast-time static WeatherBench2 constants. It is implementable without
changing the forecast contract or fixed evaluation protocols.

Do not promote it to ready in this batch. It changes positive-time mass-wind
adjustment directly, overlaps a crowded staged family of boundary-layer,
diffusion, and divergence filters, and history gives weak or negative evidence
for nearby mechanisms. The previous first-step divergence balance filter was
clean but slightly negative, and broader balance/operator changes have often
spent MSLP/Z500 guardrail margin. Keep this staged as a later fallback if the
lower-risk surface-temperature diagnostic ideas are exhausted, with a single
fixed conservative damping timescale and tests proving DFI exclusion,
vorticity preservation, and exact no-op fallback on incompatible states.
