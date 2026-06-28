---
schema_version: 1
slug: exact-weak-hs-thermal-split
title: Integrate Weak Held-Suarez Cooling With an Exact Thermal Split
status: ready
created_at: 2026-06-18T01:51:56Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Integrate Weak Held-Suarez Cooling With an Exact Thermal Split

## Hypothesis

The accepted weak Held-Suarez thermal relaxation is a large part of the current
incumbent. Recent negative evidence says not to remove its global-mean thermal
source, change its seasonal equilibrium, add Rayleigh drag, or make it
mass-neutral. A remaining, materially different question is whether the
accepted Newtonian relaxation is being integrated with avoidable explicit
time-discretization error.

The weak-HS temperature tendency is linear in temperature for fixed surface
pressure and equilibrium temperature. Applying that tendency as an exact
exponential split after each positive-time dynamics step should preserve the
accepted forcing amplitude and global thermal source while reducing 900 s
source-integration error. This may improve long-lead 2 m temperature and mass
drift without changing the forecast contract.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs`.
Preserve the incumbent DFI output state, near-surface residual correction,
log-pressure and hydrostatic layer-mean initialization, no-drag weak-HS
coefficients, horizontal diffusion, sigma grid, target variables, and lead
times.

Change only the positive-time rollout treatment of the accepted thermal
relaxation:

- keep the incumbent DFI initializer unchanged, including the current composed
  weak-HS equation, so this is not the rejected dry-DFI/weak-HS split;
- for the scored forward trajectory, build the primitive-equation step without
  composing `_TracerSafeHeldSuarezForcingSigma` into the explicit RHS;
- after each dynamics plus horizontal-diffusion step, apply a deterministic
  thermal step filter that converts temperature to nodal absolute temperature,
  diagnoses nodal surface pressure from `log_surface_pressure`, computes the
  same `kt()` and `equilibrium_temperature()` used by the incumbent weak-HS
  class, and updates
  `T_next = T_eq + (T_before - T_eq) * exp(-kt * dt)`;
- convert only the resulting temperature perturbation back to modal
  `temperature_variation`; leave vorticity, divergence, `log_surface_pressure`,
  tracers, output interpolation, residual corrections, and diagnostics
  unchanged.

The proposal intentionally does not tune `ka`, `ks`, `kf`, `sigma_b`, equilibrium
amplitudes, DFI length, diffusion, or any evaluation metric.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs`.
- API changes:
  - None. Preserve `forecast(ForecastInput) -> WeatherState` and fixed
    WeatherBench2 output variables.
- Tests to update:
  - Unit-test the exact weak-HS filter against the analytic solution of
    `dT/dt = -k(T - T_eq)` for a small synthetic state.
  - Verify the candidate preserves incumbent options and differs only in the new
    exact-HS forward-rollout flag.
  - Verify the filter modifies only `temperature_variation` and preserves all
    other state leaves exactly apart from dtype roundoff.
  - Add a non-JIT finite smoke forecast and registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and long leads if explicit weak-HS source
    integration contributes to the incumbent cold drift.
  - `mean_sea_level_pressure` and `geopotential_500` if cleaner thermal forcing
    reduces accumulated column-thickness and pressure bias.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because no drag,
    vorticity correction, wind output residual, or wind initialization changes
    are introduced.
- Possible regressions:
  - Operator splitting can change the phase relationship between thermal forcing
    and dynamics even when the source term is integrated more accurately.
  - Keeping DFI on the incumbent composed equation while the forward rollout uses
    an exact split may introduce a small initialization/forecast consistency
    mismatch.

## Risks

- Numerical stability:
  - Low. Exact exponential relaxation is bounded for positive `kt`, but it still
    changes the forward thermal trajectory.
- Compute cost:
  - Low. It adds one nodal temperature transform, surface-pressure diagnostic,
    and modal transform per inner step, with no grid-size or lead-count change.
- Data leakage:
  - None. The filter uses only current model state and fixed analytic weak-HS
    coefficients.
- Physical plausibility:
  - High for the source term. Newtonian relaxation has an analytic exponential
    solution over a fixed step.
- Rollback complexity:
  - Low. Remove one step filter, one flag, one factory, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the incumbent, clean diagnostics, no early day 1-5 RMSE guardrail failure,
    and no variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_exact_hs --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that explicit
    weak-HS source integration is not a material remaining error source. Any
    early 2 m temperature or MSLP guardrail failure would show the split harms
    balance or the accepted thermal correction.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` composes the
  accepted `_TracerSafeHeldSuarezForcingSigma` into the equation through
  `_compose_weak_held_suarez_equation`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
  implements `HeldSuarezForcingSigma.kt()` and `equilibrium_temperature()`,
  which define the same Newtonian relaxation this proposal would integrate
  exactly.
- History: `.logbook/history/2026-06-16_16-27-03_wind-sparing-held-suarez-relaxation/decision.md`
  accepted weak wind-sparing thermal Held-Suarez relaxation with validation
  delta `+0.062227260743318746`.
- History: `.logbook/history/2026-06-17_23-29-54_mass-neutral-weak-hs-forcing/decision.md`
  rejected removing the weak-HS global-mean thermal tendency with iteration
  delta `-0.05788584798245422`, so this proposal preserves that source.
- History: `.logbook/history/2026-06-16_23-51-06_calendar-aware-solar-relaxation/decision.md`
  rejected changing the weak-HS equilibrium geometry with iteration delta
  `-0.040271379533892704`; this proposal keeps the equilibrium unchanged.
- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- CESM Held-Suarez documentation describes replacing full physics with
  specified temperature relaxation and lower-boundary drag following
  Held-Suarez. https://www.cesm.ucar.edu/models/simple/held-suarez
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of `mass-neutral-weak-hs-forcing`: it does not subtract
the global thermal tendency or weaken the accepted global source. It is not a
calendar-aware, Rayleigh-drag, or coefficient-tuning proposal, and it does not
revive the obsolete scrapped Held-Suarez branch.

It is also distinct from `dry-dfi-weak-hs-split`: that candidate removed weak-HS
forcing from the DFI branch and produced a near-zero score movement. This
proposal keeps the accepted DFI branch unchanged and tests only whether the
positive-time accepted Newtonian cooling is better applied as an exact source
split.

## Evaluator Notes

### 2026-06-18T01:56:57Z

Decision: move to `ready`.

This is the best current implementation candidate. Source inspection confirms
the incumbent weak-HS path is an isolated thermal-only forcing in
`_TracerSafeHeldSuarezForcingSigma`, with the exact ingredients exposed through
`kt()` and `equilibrium_temperature()`. The adapter can keep DFI on the
incumbent composed equation while using a forward-rollout post-step filter for
the analytic thermal relaxation, so the change is side-by-side, reversible, and
does not require a protocol or API change.

The ranking is driven by scope and evidence. The accepted weak-HS mechanism had
large validation gain, while mass-neutral weak-HS forcing and calendar-shifted
equilibrium both failed badly, so preserving the accepted forcing amplitude and
equilibrium geometry is important. This proposal changes only source-term time
integration. The likely effect may be modest because the weak-HS rates are slow
relative to the 900 s inner step, but it is cheap, low-leakage, and gives a
clean test of whether source splitting matters without disturbing winds,
pressure initialization, or output residuals.
