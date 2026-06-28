---
schema_version: 1
slug: kinetic-energy-skew-momentum-advection
title: Skew-Symmetrize Horizontal Momentum Advection
status: staging
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

# Skew-Symmetrize Horizontal Momentum Advection

## Hypothesis

The incumbent's explicit horizontal momentum nonlinearity is evaluated through a
vector-invariant vorticity flux plus kinetic-energy gradient pathway. That form
is physically meaningful, but pseudo-spectral products on a truncated grid can
still exchange kinetic energy with unresolved modes in a way that affects wind,
mass, and geopotential phase. Prior anti-aliasing evidence is mixed but not
exhausted: smooth explicit-tendency filtering was clean and slightly positive,
and active staged scalar-advection skew-symmetry targets temperature and
tracers rather than momentum.

A momentum-only skew-symmetric blend between vector-invariant and conservative
advective forms can reduce nonlinear kinetic-energy production without adding a
modal cutoff, changing diffusion, changing the time integrator, or touching
surface-wind residuals.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_skew_momentum`.
Preserve all incumbent options except an opt-in horizontal momentum-advection
form in the sigma primitive equation.

Refactor the horizontal momentum nonlinear tendency enough to isolate:

- the incumbent horizontal relative-vorticity flux and kinetic-energy-gradient
  contribution to vorticity and divergence;
- the planetary-Coriolis part, which remains handled by the accepted exact
  Coriolis Strang split and is not blended;
- vertical-advection and pressure-gradient contributions, which remain on the
  incumbent path.

For the candidate only:

- compute the incumbent vector-invariant horizontal momentum tendency;
- compute an advective-flux form for the nodal wind components using the same
  `div_sec_lat`, `curl_cos_lat`, and `div_cos_lat` operators already available
  in `primitive_equations.py`;
- transform the advective-form vector acceleration back to vorticity and
  divergence tendencies;
- use a fixed 0.5/0.5 skew-symmetric average of the vector-invariant and
  advective-form horizontal momentum tendencies;
- leave temperature, tracer, `log_surface_pressure`, weak-HS forcing,
  horizontal diffusion, DFI, and output packing unchanged.

The candidate should use the same skew momentum form in DFI and positive-time
rollout because this is an equation-discretization test, not a postprocessing
or DFI-merge variant.

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
  - None. Forecast inputs, outputs, target variables, lead times, and metrics
    remain fixed.
- Tests to update:
  - Unit-test that the incumbent default uses the existing vector-invariant
    momentum path.
  - Unit-test that the skew candidate averages the isolated horizontal momentum
    tendencies while preserving Coriolis, pressure-gradient, vertical-advection,
    temperature, tracer, and log-pressure tendencies.
  - Verify a resting atmosphere and solid-body rotation-like synthetic state do
    not produce spurious finite accelerations beyond transform roundoff.
  - Verify the candidate factory preserves all Strang incumbent flags except
    the momentum-advection selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium leads if nonlinear wind-energy transfer
    is feeding phase or amplitude error after the accepted Coriolis split.
  - `geopotential_500` and `mean_sea_level_pressure` if cleaner momentum
    evolution improves balanced mass-field adjustment.
- Expected neutral metrics:
  - Early `2m_temperature` should remain close to the incumbent because thermal
    initialization, weak-HS forcing, scalar advection, and near-surface
    residuals are unchanged.
- Possible regressions:
  - The blend may reduce useful resolved nonlinear transfer and behave like
    extra implicit damping even without a modal filter.
  - If momentum aliasing is not a material remaining source after the accepted
    exact Coriolis split, the iteration delta may be clean but subthreshold.

## Risks

- Numerical stability:
  - Moderate. Skew forms are generally stabilizing, but the refactor touches
    core vorticity and divergence tendencies.
- Compute cost:
  - Moderate. Computing both vector-invariant and advective-form tendencies adds
    transforms and derivative calls but keeps the same grid, leads, and worker
    policy.
- Data leakage:
  - None. The mechanism uses only the forecast state and fixed operators.
- Physical plausibility:
  - High as a discrete nonlinear-form test. It is less empirical than adding
    damping, but it is still an approximation to the fully conservative schemes
    used in production dynamical cores.
- Rollback complexity:
  - Moderate. The momentum tendency refactor should be isolated behind a
    selector, but it touches shared primitive-equation code and needs careful
    tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_skew_momentum`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_skew_momentum --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    diagnostics clean, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_skew_momentum --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that horizontal
    momentum skew-symmetry is not a material remaining error source. Any early
    `10m_u_component_of_wind`, MSLP, or Z500 guardrail failure would show the
    blend disrupts balanced nonlinear evolution.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  computes horizontal momentum tendencies through `curl_and_div_tendencies` and
  `kinetic_energy_tendency`.
- History: `.logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing/decision.md`
  found a clean but subthreshold positive signal from explicit-tendency
  anti-aliasing, motivating a stronger nonlinear-form change that does not add
  a modal cutoff.
- History: `.logbook/history/2026-06-18_08-58-52_coriolis-rotated-surface-wind-residual/decision.md`
  rejected a surface-wind residual variant with a day-1 10 m wind guardrail
  failure; this proposal changes prognostic momentum tendencies and does not
  postprocess 10 m wind.
- Arakawa, A. and Lamb, V. R. 1981. A Potential Enstrophy and Energy Conserving
  Scheme for the Shallow Water Equations. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0018:APEAEC%3E2.0.CO;2
- Morinishi, Y. 2010. Skew-symmetric form of convective terms and fully
  conservative finite difference schemes for variable density low-Mach number
  flows. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2009.09.031
- Eldred, C. and Randall, D. 2017. Total energy and potential enstrophy
  conserving schemes for the shallow water equations using Hamiltonian methods,
  Part 1. Geoscientific Model Development.
  https://doi.org/10.5194/gmd-10-791-2017
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is not a duplicate of active staged
`skew-symmetric-horizontal-scalar-advection`; that proposal changes scalar
transport for temperature and tracers. This proposal changes only the nonlinear
horizontal momentum form feeding vorticity and divergence.

It is also distinct from staged `two-thirds-explicit-tendency-dealiasing` and
the rejected smooth tendency filter because it does not mask or damp modal
tendencies. It is not a wind initialization, wind residual, angular-momentum
fixer, polar taper, or Coriolis variant. The expected implementation is broader
than the first two proposals in this pass, so the Evaluator should rank it below
lower-surface or single-equation corrections if cost-risk is the deciding
factor.

## Evaluator Notes

### 2026-06-18T11:49:28Z

Decision: move to `staging`, staged fallback rank 6.

The proposal has a defensible structure-preserving mechanism and is not a
duplicate of scalar skew advection, two-thirds tendency dealiasing, or the
failed surface-wind residual. Prior nonlinear-tendency dealiasing was clean and
slightly positive, so nonlinear form changes remain a legitimate research
family if lower-surface candidates fail.

Do not promote it now. The candidate would refactor core horizontal momentum
tendencies, compute two nonlinear forms, and transform the advective-form wind
acceleration back into vorticity/divergence tendencies. That is a broader and
more error-prone implementation than the flux-form continuity correction,
hypsometric diagnostic, diffusion split, or scalar-advection skew form. The
recent surface-wind residual guardrail failure also argues for caution around
early `10m_u_component_of_wind`, even though this proposal is prognostic rather
than output-only.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 7.

The mechanism remains physically motivated, but the implementation is broader
than scalar advection and likely more exposed to the early 10 m wind guardrail.
It now ranks below the new log-sigma adiabatic tendency because both are
dynamical operator changes, but log-sigma is more localized to one
thermodynamic helper. Keep this as a later momentum-form experiment only after
lower-risk diagnostics, split placement, and scalar/tendency tests are scored.
