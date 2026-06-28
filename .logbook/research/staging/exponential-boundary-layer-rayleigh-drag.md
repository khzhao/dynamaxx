---
schema_version: 1
slug: exponential-boundary-layer-rayleigh-drag
title: Add Weak Exact Boundary-Layer Rayleigh Drag
status: staging
created_at: 2026-06-18T15:50:23Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add Weak Exact Boundary-Layer Rayleigh Drag

## Hypothesis

The incumbent includes the accepted wind-sparing weak Held-Suarez thermal
relaxation but still sets the Held-Suarez Rayleigh drag coefficient to zero.
That choice protected the early `10m_u_component_of_wind` guardrail when the
thermal forcing was first introduced, but it also leaves the dry flat dycore
without any boundary-layer momentum sink. A weak, low-sigma, exactly integrated
Rayleigh drag may reduce accumulated low-level wind drift and improve MSLP/Z500
through better large-scale momentum balance while avoiding the broad damping
failures seen in diffusion and divergence experiments.

## Mechanism

Register a side-by-side model named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_boundary_drag`.
Preserve the incumbent initialization, DFI path, weak-HS thermal relaxation,
near-surface residuals, log-pressure remap, hydrostatic layer initialization,
horizontal diffusion, symmetric exact-Coriolis split, output variables, and
fixed protocols.

Add only a positive-time step filter after the non-Coriolis dynamics step and
before or inside the existing symmetric Coriolis wrapper:

- transform modal vorticity/divergence to nodal winds;
- apply an exact exponential damping to `u` and `v` with a fixed smooth vertical
  taper that is zero above about `sigma = 0.70` and largest at the lowest sigma
  layer;
- use a weak predeclared surface e-folding time, for example 20 days, not a
  sweep or validation-tuned parameter;
- transform the damped winds back to modal vorticity/divergence;
- leave temperature, `log_surface_pressure`, tracers, residual correction,
  pressure-level output interpolation, and DFI filters unchanged.

This is a lower-boundary momentum source, not another global hyperdiffusion,
divergence damping, timestep, or wind-output residual rotation.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input channels, output channels, leads, and
    fixed evaluation protocols remain unchanged.
- Tests to update:
  - Unit-test the vertical drag weight: exactly zero above the cutoff, monotone
    into the lowest layer, finite, and shape-compatible with sigma levels.
  - Unit-test the exact drag filter on synthetic winds and verify that only
    vorticity/divergence change.
  - Verify the candidate factory preserves all incumbent flags except the new
    boundary-layer drag option.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and long leads if the incumbent low-level
    flow has too little frictional spin-down.
  - `mean_sea_level_pressure` and `geopotential_500` if lower-level momentum
    drift is feeding back onto balanced mass fields.
- Expected neutral metrics:
  - `2m_temperature` should remain close to incumbent because thermal forcing and
    near-surface temperature residuals are unchanged.
  - Day-1 fields should move little because the drag is weak and exactly
    integrated.
- Possible regressions:
  - Early `10m_u_component_of_wind` may regress if the incumbent already needs
    the undamped low-level wind amplitude.
  - The Coriolis/pressure-gradient balance can shift when low-level momentum is
    damped, producing MSLP or Z500 regressions.

## Risks

- Numerical stability:
  - Low to moderate. Linear drag is stabilizing, but it changes prognostic wind
    every inner step.
- Compute cost:
  - Low. It adds two existing wind transforms and local multiplications per
    inner step.
- Data leakage:
  - None. The filter uses only forecast state, sigma geometry, and fixed
    coefficients.
- Physical plausibility:
  - Moderate to high. Idealized dycore benchmarks commonly use lower-boundary
    Rayleigh drag as a boundary-layer friction surrogate.
- Rollback complexity:
  - Low. Remove one option, one filter, one factory/export, one registry entry,
    and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_boundary_drag`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_boundary_drag --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed early or variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_boundary_drag --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show missing low-level
    drag is not a material remaining error source. Any early 10 m wind guardrail
    failure would show the momentum sink is too intrusive.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` sets
    `DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY = 0.0`, so the accepted weak-HS path is
    thermal-only.
  - History: `.logbook/history/2026-06-16_16-27-03_wind-sparing-held-suarez-relaxation/decision.md`
    accepted thermal weak-HS and noted long-lead 10 m wind as the largest cost.
  - History: `.logbook/history/2026-06-18_08-58-52_coriolis-rotated-surface-wind-residual/decision.md`
    rejected rotating the output wind residual after a day-1 wind guardrail
    failure; this proposal changes prognostic low-level momentum weakly rather
    than rotating diagnostics.
  - Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of
    dynamical cores of atmospheric general circulation models. Bulletin of the
    American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
  - ECMWF OpenIFS documentation describes Held-Suarez forcing as Newtonian
    cooling plus low-level Rayleigh wind damping for dycore tests.
    https://confluence.ecmwf.int/plugins/viewsource/viewpagesrc.action?pageId=56660076
  - CESM Held-Suarez documentation describes linear drag at the lower boundary
    in the CAM spectral-transform dycore benchmark.
    https://www.cesm.ucar.edu/models/simple/held-suarez

## Researcher Notes

This is not a duplicate of accepted `wind-sparing-held-suarez-relaxation`: that
candidate deliberately removed Rayleigh drag and added only weak thermal
relaxation. It is also not a repeat of `scale-selective-hyperdiffusion`,
`symmetric-horizontal-diffusion-split`, or `divergence-selective-gravity-wave-damping`
because it is vertically confined to the lower boundary and damps physical
momentum rather than globally damping spectral modes or divergence.

It differs from active staged ideas: it does not alter vertical advection,
scalar advection, momentum advection form, diffusion heating, IMEX order,
dealiasing, omega spinup, hydrostatic theta initialization, or the Simmons-
Burridge geopotential operator. The proposal spends wind guardrail margin, so
it should be evaluated conservatively, but the mechanism is distinct from the
recent failed output-wind and diffusion families.

## Evaluator Notes

### 2026-06-18T15:55:59Z

Decision: move to `staging`, not `ready`.

The proposal is scientifically plausible: Held-Suarez-style lower-boundary
Rayleigh damping is a standard idealized dycore forcing component, and the
incumbent currently retains the accepted weak thermal relaxation while leaving
`DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY = 0.0`. The implementation is also
reasonably local if expressed as an opt-in exact low-level momentum filter with
fixed coefficients and a side-by-side registry entry.

Do not promote it as the next run. The current incumbent already carries a
documented long-lead `10m_u_component_of_wind` cost from weak-HS thermal
relaxation, and the recent `coriolis-rotated-surface-wind-residual` experiment
failed the day-1 wind guardrail with a `+12.310765318969419%` wind RMSE
regression. This proposal is more physical than that rejected output rotation,
but it still changes prognostic low-level momentum every inner step and can
shift geostrophic and pressure-gradient balance. That is a higher-risk next
experiment than the ready stability-aware residual decay, which keeps the
trajectory and mass fields unchanged.

Keep it staged as a fallback if output-diagnostic residual improvements are
exhausted or if future diagnostics identify low-level wind spin-down as the
dominant remaining error source. It is not a duplicate of the accepted
wind-sparing weak-HS relaxation because that candidate explicitly omitted
Rayleigh drag, and it is not a duplicate of rejected diffusion/sponge ideas
because this damping is vertically confined boundary-layer momentum damping.
