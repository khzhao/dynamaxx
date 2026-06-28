---
schema_version: 1
slug: polar-absolute-vorticity-guard
title: Add a Bounded Polar Absolute-Vorticity Guard
status: scrap
created_at: 2026-06-19T11:47:54Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
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

# Add a Bounded Polar Absolute-Vorticity Guard

## Hypothesis

The incumbent uses exact Coriolis splitting and off-centered gravity-wave
treatment, but high-latitude vorticity remains sensitive to spectral ringing,
coordinate singularity, and repeated nonlinear transforms. Rare polar grid cells
where absolute vorticity `zeta + f` flips sign relative to the planetary
vorticity or develops extreme local Rossby number can seed unrealistic polar
height and pressure errors. A bounded, polar-confined absolute-vorticity guard
should remove only those outliers while leaving midlatitude synoptic evolution
and near-surface diagnostics effectively unchanged.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_polar_vort_guard`.
Preserve the incumbent initialization, DFI, weak Held-Suarez forcing, exact
symmetric Coriolis split, theta tendency, theta mean recentering, fixed
off-centering, horizontal diffusion, near-surface residuals, Richardson 10 m
wind diagnostic, output variables, and fixed protocols.

Add an opt-in step filter after the incumbent dynamics and horizontal diffusion,
but before or alongside theta recentering:

- convert only relative vorticity to nodal space;
- compute the planetary vorticity `f = 2 Omega sin(latitude)` on the same grid;
- apply a smooth latitude taper that is exactly zero equatorward of a fixed
  polar threshold, for example 70 degrees, and reaches one near the final
  latitude rows;
- where the taper is active, constrain the nodal relative vorticity so absolute
  vorticity has the same sign as `f` and the local magnitude `abs(zeta / f)` is
  below a fixed broad cap;
- blend the constrained and original vorticity by the taper, transform back to
  modal space, and clip with existing spectral truncation;
- leave divergence, temperature variation, log surface pressure, tracers,
  `sim_time`, surface residuals, and all output diagnostics unchanged;
- use finite guards and return the incumbent state if the constrained vorticity
  is nonfinite.

This is a dynamical polar outlier guard. It is not an exact-pole wind-row
initialization cleanup, not a global zero-mean vorticity projection, not a
barotropic angular-momentum fixer, and not another broad horizontal diffusion
change.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` only if the
    Coriolis/absolute-vorticity helper is cleaner there
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, outputs, shapes, lead times, target variables, and
    fixed protocols remain unchanged.
- Tests to update:
  - Unit-test that midlatitude vorticity is unchanged when the latitude taper is
    zero.
  - Unit-test that synthetic polar sign flips in absolute vorticity are bounded
    and finite.
  - Verify divergence, temperature, log surface pressure, tracers, and
    `sim_time` are unchanged by the filter.
  - Verify the candidate factory preserves all incumbent flags except the polar
    vorticity guard selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and long leads if
    polar vorticity outliers are feeding large-scale height and pressure errors.
  - Guardrail behavior should stay clean because the guard is polar-confined and
    does not directly alter 2 m or 10 m diagnostics.
- Expected neutral metrics:
  - `2m_temperature` should be mostly neutral because thermal fields and
    near-surface residuals are unchanged.
  - `10m_u_component_of_wind` should be neutral outside polar taper regions.
- Possible regressions:
  - Strong polar cyclones and stratospheric vortices can have large relative
    vorticity for physically valid reasons; over-bounding them may degrade
    high-latitude Z500 or MSLP.
  - Vorticity-only edits can create slight imbalance with divergence and mass
    fields, so fast diagnostics and early Z500 guardrails are important.

## Risks

- Numerical stability:
  - Moderate. The filter removes vorticity outliers but can introduce imbalance
    if it activates often or too sharply.
- Compute cost:
  - Low. It adds one vorticity nodal transform and one modal transform per inner
    step.
- Data leakage:
  - None. It uses only the current forecast state, latitude, and fixed physical
    constants.
- Physical plausibility:
  - Moderate. Absolute-vorticity sign and Rossby-number bounds are meaningful
    large-scale-flow checks, but the atmosphere can produce intense polar
    vortices that should not be overconstrained.
- Rollback complexity:
  - Low. The change is a side-by-side step filter and registry entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failures, and
    at least `+0.002` primary-score improvement.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4` only
    if iteration promotes.
  - Support requires clean diagnostics, no guardrail failures, and at least
    `+0.001` validation primary-score improvement.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta would show polar vorticity outliers are not
    material for the fixed global WeatherBench2 score.
  - Any early wind or Z500 guardrail failure would show that vorticity-only
    bounding damages balanced flow more than it helps polar stability.

## Citations

- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics, second edition,
  discussion of vorticity-divergence primitive equations and balanced
  large-scale flow.
- Jablonowski, C. and Williamson, D. L. 2006. A baroclinic instability test case
  for atmospheric model dynamical cores. Quarterly Journal of the Royal
  Meteorological Society.
- Source reference:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`, where
  `curl_and_div_tendencies` uses absolute vorticity `aux_state.vorticity +
  coriolis_parameter`.
- Source history: `.logbook/history/2026-06-17_14-44-29_polar-vector-wind-initialization-taper/decision.md`
  showed exact-pole wind-row initialization cleanup was stable but
  roundoff-scale, so this proposal targets rollout polar vorticity outliers
  rather than input row regularization.

## Researcher Notes

This proposal is intentionally distinct from active diffusion ideas such as
`leith-nonlinear-eddy-viscosity` and `planetary-wave-preserving-horizontal-diffusion`.
It does not change the diffusion operator or damp all high modes. It also
differs from scrapped `zero-mean-vorticity-mode-projection` and
`barotropic-angular-momentum-fixer` because it is local, polar-confined, and
only activates on absolute-vorticity/Rossby-number outliers. The expected signal
is lower than the accepted off-centered solver change, but the implementation
surface is modest and decorrelated from recent pressure, humidity, vertical
advection, and surface-diagnostic failures.

## Evaluator Notes

### 2026-06-19T11:53:51Z

Decision: move to `scrap`; ranked 3 of 3 new proposals.

The proposal is too speculative for a fixed-gate iteration. It introduces a
vorticity-only limiter after dynamics and diffusion, which can create imbalance
with divergence, temperature, and pressure fields. The physical argument also
needs diagnostic evidence that polar absolute-vorticity sign flips or extreme
local Rossby numbers are occurring often enough to affect the global
WeatherBench2 score. Without that evidence, the mechanism risks clipping real
polar cyclone or vortex structure.

History argues against spending an evaluation on this now. Exact-pole wind-row
cleanup was clean but numerical-noise scale with iteration delta
`+1.444147295082132e-07`; preserving pre-DFI vorticity was clean but negative
at `-0.002335598569885189`; the zero-mean vorticity projection was already
scrapped as likely no-op/roundoff cleanup; and broad barotropic wind correction
was scrapped for balance risk. This guard is more active than those cleanup
ideas but not better evidenced, so its cost-risk tradeoff is unfavorable.
