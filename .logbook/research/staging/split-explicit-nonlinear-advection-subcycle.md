---
schema_version: 1
slug: split-explicit-nonlinear-advection-subcycle
title: Subcycle Only Nonlinear Advective Tendencies Inside the Accepted Step
status: staging
created_at: 2026-06-21T00:30:15Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Subcycle Only Nonlinear Advective Tendencies Inside the Accepted Step

## Hypothesis

The accepted off-centered semi-implicit step controls fast gravity-wave
oscillations, while exact Coriolis splitting and analysis-offset weak-HS forcing
handle other large accepted error sources. A rejected `600 s` inner step showed
that uniformly shortening the whole timestep is not useful, and a rejected
Williamson CN-RK3 rollout showed that replacing the accepted off-centered
mechanism is harmful. The remaining error may instead come from sampling
nonlinear horizontal and vertical advection too coarsely at the `900 s` inner
step while the linear fast-mode treatment is already adequate.

Subcycling only the explicit nonlinear advective part should reduce aliasing
and phase error in baroclinic transport without changing the accepted
semi-implicit gravity-wave damping, exact Coriolis Strang split, weak-HS
equilibrium offset, residual correction, output contract, or fixed WB2
evaluation.

## Mechanism

Add a side-by-side candidate with a suffix such as
`nonlinear_advect_subcycle`. Preserve every incumbent option and register one
new opt-in rollout wrapper.

For the candidate only:

- keep the same `900 s` public inner step, lead schedule, DFI span, and output
  packing;
- within each positive-time inner step, split the tendency into the existing
  semi-implicit linear operator plus explicit nonlinear advection and forcing;
- evaluate the nonlinear advective tendency twice with `450 s` substeps while
  applying the accepted semi-implicit solve, exact Coriolis Strang rotation,
  weak-HS forcing, theta mean recentering, diffusion, and residual correction
  on the incumbent outer-step cadence;
- preserve the accepted off-centering value and do not change vertical
  coordinate, spectral truncation, target variables, leads, metrics, or splits;
- keep the first implementation positive-time only unless the Implementer can
  show the signed DFI forward/backward path remains symmetric and finite;
- no-op back to incumbent stepping on unexpected state shapes or nonfinite
  substep diagnostics.

This is not a timestep sweep: it tests one fixed split-explicit structure with
unchanged outer cadence and no validation-guided parameter search.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` if a reusable
    wrapper is cleaner than adapter-local logic
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory extending the incumbent model name with
    `_nonlinear_advect_subcycle`.
- API changes:
  - None. `DycoreModel.forecast`, state variables, outputs, lead times, metrics,
    and evaluation protocols remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves all incumbent flags except the new
    nonlinear-advection subcycle selector.
  - Unit-test that zero-flow or zero-tendency states are identical to incumbent
    stepping.
  - Unit-test that the subcycled path takes two explicit advective updates per
    accepted outer step while keeping the same lead indexing.
  - Verify DFI is either explicitly unchanged or covered by a finite symmetric
    subcycled path.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `10m_u_component_of_wind` at medium leads if coarse
    nonlinear transport is a remaining source of phase error.
  - `mean_sea_level_pressure` if reduced advective imbalance improves surface
    pressure evolution without touching the pressure-gradient operator.
- Expected neutral metrics:
  - `2m_temperature` should stay close to incumbent because the accepted
    near-surface residual and analysis-HS equilibrium are preserved.
- Possible regressions:
  - If the accepted time discretization is empirically tuned as a whole, changing
    only nonlinear advection can disrupt balance with the semi-implicit solve.
  - Extra explicit substeps can sharpen gradients and expose existing diffusion
    or vertical-advection weaknesses.

## Risks

- Numerical stability:
  - Moderate. The candidate changes positive-time integration, but keeps the
    accepted fast-mode implicit operator and uses finite fallback.
- Compute cost:
  - Moderate. Nonlinear tendency evaluation is roughly doubled per outer step,
    but should remain practical with `--workers 4` on the reported machine.
- Data leakage:
  - None. The mechanism uses only current forecast state and fixed constants.
- Physical plausibility:
  - High. Split-explicit and subcycled treatments are standard for separating
    fast linear waves from slower nonlinear advection.
- Rollback complexity:
  - Low to moderate. Remove one selector/wrapper, one factory/export, one
    registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that nonlinear
    advective subcycling is not a material remaining bottleneck. Any early wind
    or mass-field guardrail failure would show the split disrupts incumbent
    balance.

## Citations

- Wicker, L. J. and Skamarock, W. C. 2002. Time-splitting methods for elastic
  models using forward time schemes. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2002)130%3C2088:TSMFEM%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Satoh, M. 2002. Conservative scheme for the compressible nonhydrostatic
  models with the horizontally explicit and vertically implicit time
  integration scheme. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2002)130%3C1227:CSFTCN%3E2.0.CO;2
- Dynamaxx history:
  `.logbook/history/2026-06-16_18-41-23_six-hundred-second-inner-step/decision.md`
  rejected a uniform timestep reduction, so this proposal does not shorten the
  whole model step.
- Dynamaxx history:
  `.logbook/history/2026-06-20_07-31-40_williamson-cn-rk3-rollout/decision.md`
  rejected replacing the accepted off-centered SIL3 structure, so this proposal
  keeps that accepted fast-mode treatment.

## Researcher Notes

This is decorrelated from the weak analysis-HS follow-ups because it does not
change thermal equilibrium offsets, rates, projections, or lead timing. It is
also not another broad damping/filter proposal: it changes the temporal
sampling of nonlinear advection while preserving the accepted implicit damping
and all output diagnostics.

## Evaluator Notes

### 2026-06-21T00:35:34Z

Decision: move to `staging`; ranked first among this batch but not ready.

The proposal is the strongest of the three because it preserves the accepted
off-centered SIL3 fast-mode treatment, exact Coriolis split, analysis-offset
HS equilibrium, residual correction, lead schedule, and output contract. It is
also materially different from the rejected whole-step `600 s` experiment: the
outer cadence remains `900 s`, and only explicit nonlinear advective sampling
is changed. The cited split-explicit literature supports the general numerical
mechanism, and prior nonlinear-tendency dealiasing was clean and slightly
positive, so nonlinear transport remains a plausible research family.

Do not promote to `ready` under the current evidence. The implementation would
still change positive-time integration inside every accepted step, likely
roughly double nonlinear tendency work, and create DFI symmetry/fallback
complexity. Recent integration evidence raises the bar: the `600 s` whole
inner-step candidate was clean but slightly negative, and the Williamson
CN-RK3 rollout was strongly negative despite clean diagnostics. Active staging
already contains lower-cost nonlinear/advection representatives such as
`two-thirds-explicit-tendency-dealiasing`,
`kinetic-energy-skew-momentum-advection`, and
`vertical-courant-limited-advection`. Keep this as a later staged experiment
only if cheaper nonlinear-transport tests fail to explain the remaining error.
