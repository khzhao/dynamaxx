---
schema_version: 1
slug: flux-form-surface-pressure-continuity
title: Use Flux-Form Surface-Pressure Continuity Correction
status: ready
created_at: 2026-06-18T11:44:45Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Flux-Form Surface-Pressure Continuity Correction

## Hypothesis

The incumbent prognoses `log_surface_pressure` with a split product-form
continuity tendency: the vertically integrated divergence is in the implicit
operator, while the horizontal advection of `log_surface_pressure` is explicit.
This split is stable, but it does not force the discrete total tendency to be
equivalent to a conservative flux-form surface-pressure equation. The incumbent
shows growing long-lead MSLP and Z500 drift, so a local product-rule correction
to the surface-pressure continuity equation may improve mass-field evolution
without anchoring global pressure, changing pressure initialization, or using
truth residuals.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_flux_form_logp`.
Preserve the incumbent initialization, DFI, weak Held-Suarez forcing, residual
correction, horizontal diffusion, vertical advection, exact Coriolis Strang
split, output variables, and fixed protocols.

Add an opt-in primitive-equation wrapper for the sigma-coordinate equation:

- compute the incumbent explicit terms and implicit terms exactly as before;
- inside the explicit term wrapper, recompute the diagnostic state for the same
  input state;
- form the product-form full continuity tendency in nodal space as
  `-sigma_integral(divergence + u_dot_grad_log_surface_pressure)`;
- form a flux-form full tendency from the divergence of the vertically
  integrated surface-pressure-weighted horizontal mass flux,
  `-(1 / surface_pressure) * div(int(surface_pressure * wind d_sigma))`, using
  the same spherical-harmonic derivative operators already used by the dycore;
- add only the modal difference
  `flux_form_full_tendency - product_form_full_tendency` to the incumbent
  explicit `log_surface_pressure` tendency;
- leave the implicit inverse unchanged, so the sum of incumbent implicit
  divergence tendency plus corrected explicit tendency approximates the
  flux-form surface-pressure equation;
- leave vorticity, divergence, temperature, tracers, Coriolis rotation, DFI
  state merging, and output packing unchanged.

This is a rollout continuity discretization change, not a surface-pressure
initialization change and not a global pressure anchor.

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
  - None. The forecast input and output contract stays unchanged.
- Tests to update:
  - Unit-test the flux-form correction on a constant surface-pressure state and
    verify it is zero to roundoff.
  - Unit-test that the area-weighted integral of `surface_pressure` is better
    conserved by one corrected tendency step on a synthetic divergent wind
    field.
  - Verify vorticity, divergence, temperature variation, tracers, and
    `sim_time` are unchanged by the wrapper except through normal integration.
  - Verify the candidate factory preserves every Strang incumbent option except
    the new continuity-correction option.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 3 to 15 if product-rule inconsistency in
    `log_surface_pressure` evolution contributes to growing mass-field drift.
  - `geopotential_500` at medium and long leads if improved column mass
    evolution reduces balanced thickness and pressure-gradient errors.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` at day 1 should be close to
    the incumbent because initialization, Coriolis treatment, wind fields, and
    near-surface residuals are unchanged.
- Possible regressions:
  - Changing surface-pressure tendency can feed back through the pressure
    gradient and hydrostatic output, so early MSLP or Z500 guardrails may fail
    if the correction is too strong.
  - If the mass drift is dominated by missing physics or MSLP-as-surface-pressure
    diagnostics, the correction may be clean but subthreshold.

## Risks

- Numerical stability:
  - Moderate. The correction touches a core prognostic mass variable every step,
    although it is a product-rule correction rather than an external forcing.
- Compute cost:
  - Low to moderate. It adds one diagnostic-state reuse or recomputation and a
    small number of horizontal derivative operations per explicit tendency.
- Data leakage:
  - None. The correction uses only the current forecast state and fixed grid
    geometry.
- Physical plausibility:
  - High as a finite-volume-inspired mass continuity correction; moderate in
    this spectral sigma implementation because it preserves the incumbent
    semi-implicit split rather than replacing the full mass coordinate.
- Rollback complexity:
  - Low. Remove one wrapper/flag, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_flux_form_logp`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_flux_form_logp --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    diagnostics clean, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_flux_form_logp --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the incumbent's
    mass drift is not materially controlled by this product-rule error. Any
    early MSLP or Z500 guardrail failure would show the correction disrupts the
    accepted pressure-gradient balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  computes explicit `log_surface_pressure` tendency from
  `u_dot_grad_log_sp` and computes the vertically integrated divergence
  contribution in `implicit_terms`.
- History: `.logbook/history/2026-06-16_17-43-05_global-mean-pressure-anchor/decision.md`
  rejected a global pressure anchor as neutral-negative; this proposal is local
  and flux-form, not a global mode constraint.
- History: `.logbook/history/2026-06-17_22-19-32_continuity-balanced-divergence-init/decision.md`
  rejected a one-time divergence initialization correction; this proposal leaves
  initial divergence untouched and changes only rollout continuity.
- History: `.logbook/history/2026-06-18_10-29-23_variable-selective-pressure-initialization/decision.md`
  rejected pressure-linear scalar initialization variants; this proposal does
  not change pressure-level-to-sigma initialization.
- Lin, S.-J. 2004. A Vertically Lagrangian Finite-Volume Dynamical Core for
  Global Models. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2004)132%3C2293:AVLFDC%3E2.0.CO;2
- NCAR CAM6 Scientific Guide, Dynamics chapter, describes HOMME's use of
  surface pressure rather than log pressure for mass and energy conservation.
  https://acomstaff.acom.ucar.edu/tilmes/CAM_docs/doc/build/html/cam6_scientific_guide/chapter3.html
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is not a duplicate of active staged `skew-symmetric-horizontal-scalar-advection`.
That proposal changes horizontal advection of temperature and tracers. This
proposal targets only the surface-pressure continuity product rule.

It is also distinct from global pressure anchoring, mass residual output
corrections, terrain-reduced pressure cycles, pressure-linear initialization,
and continuity-balanced divergence initialization. It does not edit initial
surface pressure, pressure-level scalar remaps, MSLP diagnostics, wind fields,
or the evaluation protocol.

## Evaluator Notes

### 2026-06-18T11:49:28Z

Decision: move to `ready`, ready rank 1.

This is the strongest next candidate because it is a causal mass-continuity
rollout change with a clear numerical mechanism and no forecast-contract or
metric changes. Source inspection confirms the incumbent separates explicit
`log_surface_pressure` advection from vertically integrated divergence in the
primitive-equation terms, so a side-by-side product-rule correction can be
implemented without changing initialization, output residuals, Coriolis
splitting, or the fixed protocols.

Recent negative pressure evidence does not directly falsify this idea. The
variable-selective pressure initialization failed broadly, the global pressure
anchor was effectively neutral, and continuity-balanced divergence
initialization was clean but negative; all were initialization or global-mode
tests. This proposal instead changes only positive-time local continuity. The
main risk is early MSLP/Z500 balance, so it should be implemented with a
constant-pressure zero-correction test, mass-integral tendency test, and strict
day-1-to-day-5 guardrail review.
