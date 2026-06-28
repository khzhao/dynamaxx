---
schema_version: 1
slug: lead-ramped-semi-implicit-offcentering
title: Ramp Semi-Implicit Off-Centering Down After Startup
status: scrap
created_at: 2026-06-21T14:14:13Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Ramp Semi-Implicit Off-Centering Down After Startup

## Hypothesis

The accepted fixed semi-implicit off-centering is one of the incumbent's most
important mass-field stabilizers, but it applies the same damping strength from
the first inner step through day 15. Recent startup subcycling and first-step
divergence filtering were clean but negative, suggesting that a separate
startup repair is not enough. A different possibility is that the strongest
off-centering is needed mainly during the early gravity-wave adjustment, while
later balanced Rossby and baroclinic evolution would benefit from slightly less
implicit damping.

A smooth lead-time ramp from the accepted `0.05` off-centering toward a smaller
positive value after the first one to two forecast days may preserve the early
fast-mode control while reducing long-lead balanced-flow damping.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_si_ramp`.
Keep the accepted initialization, DFI, Coriolis Strang split, weak-HS
equilibrium, theta tendency and recentering, residual memory, diffusion, and
output diagnostics.

Replace the single fixed off-centered SIL3 stepper with a deterministic
piecewise rollout:

- use the incumbent `implicit_offcentering=0.05` for DFI and the first
  positive-time forecast day;
- ramp linearly or with a smooth cosine from `0.05` to a smaller floor such as
  `0.02` over the next day;
- keep the floor positive for the remainder of the rollout to avoid reopening
  the fast-mode instability that the accepted off-centering fixed;
- implement the ramp through prebuilt step functions or a small state-time
  branch that does not depend on validation data and does not alter saved lead
  times.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` if a helper is
    cleaner than adapter-level step selection
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate factory; do not change the incumbent name.
- API changes:
  - None. The forecast contract and fixed protocols remain unchanged.
- Tests to update:
  - Unit-test ramp weights at startup, transition, and long lead.
  - Verify floor/off-centering bounds and incumbent-equivalent behavior when
    ramp start and floor both equal `0.05`.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 4 to 15 if fixed
    off-centering is over-damping balanced mass and height evolution after
    startup.
  - `10m_u_component_of_wind` may improve at longer leads if rotational flow is
    less indirectly damped by the coupled gravity-wave block.
- Expected neutral metrics:
  - Early day-1 to day-2 mass diagnostics should remain close because the
    accepted off-centering is retained during startup.
- Possible regressions:
  - Late MSLP/Z500 can regress if the full `0.05` damping is still needed for
    all leads.
  - A ramp implemented with excessive recompilation or Python-side looping can
    raise runtime cost.

## Risks

- Numerical stability:
  - Moderate. The floor remains positive, but this deliberately weakens an
    accepted stabilizing mechanism after startup.
- Compute cost:
  - Low to moderate depending on implementation. Prebuilt step functions should
    avoid per-step recompilation.
- Data leakage:
  - Low. The schedule is fixed by lead time and uses no truth data.
- Physical plausibility:
  - Moderate. Off-centering is a numerical damping device for fast modes; using
    more damping during adjustment and less later is physically interpretable
    as startup damping rather than a new forcing.
- Rollback complexity:
  - Low. Remove one stepper option, one candidate factory, and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_si_ramp`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_si_ramp --workers 4`.
  - Support requires at least `+0.002` primary-score delta and no fixed
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_si_ramp --workers 4` only after iteration promotion.
  - Require at least `+0.001` validation delta with clean diagnostics.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that fixed
    off-centering is not materially over-damping late balanced modes, or that
    reducing it weakens needed fast-mode control.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements the row-sum-preserving `implicit_offcentering` modification used
  by the incumbent SIL3 stepper.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` sets
  `DEFAULT_SEMI_IMPLICIT_OFFCENTERING = 0.05` and composes the accepted
  off-centered solver through `_ode_solver`.
- History: `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md`
  accepted fixed off-centering as a major fast-mode and mass-field improvement.
- History: `.logbook/history/2026-06-21_08-11-13_startup-subcycled-first-day-rollout/decision.md`
  and `.logbook/history/2026-06-21_10-27-50_first-step-divergence-balance-filter/decision.md`
  rejected separate startup-only repairs, motivating a continuous damping
  schedule instead.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.

## Researcher Notes

This is not a duplicate of staged `divergence-selective-offcentering`, which
changes which variables receive off-centered damping. It is also not the recent
startup subcycling or first-step divergence-filter family, because the accepted
solver is retained and the damping schedule remains active after startup. The
proposal tests whether the time profile of the accepted damping is the remaining
error source.

## Evaluator Notes

### 2026-06-21T14:18:59Z

Decision: move to `scrap`; ranked 3 of 3 current proposals.

Reject this as a poor next model-selection candidate under the current
evidence. The accepted fixed semi-implicit off-centering was a very large,
validated mass-field improvement, and source inspection shows the incumbent
uses a single `DEFAULT_SEMI_IMPLICIT_OFFCENTERING = 0.05` in the SIL3 implicit
tableau. The proposal is implementable in principle, but it deliberately
weakens that accepted stabilizer after startup based on an unverified
over-damping hypothesis.

Recent history is specifically unfavorable. `startup-subcycled-first-day-rollout`
was clean but strongly negative with an early MSLP guardrail failure, and
`first-step-divergence-balance-filter` was clean but neutral-negative. The
nearby off-centering queue is also weak: `divergence-selective-offcentering`
is staged only because the literal formulation may be a no-op, while
`high-wavenumber-implicit-offcenter-filter` was scrapped for reintroducing
centered evolution and adding dual-step complexity. This ramp has the same
core risk of removing damping from a mechanism that currently anchors MSLP and
Z500 skill, but with a constant schedule that would be hard to distinguish from
tuning.

If future diagnostics show clear lead-dependent over-damping from the accepted
off-centering, a more precise proposal could be written. As submitted, the
expected benefit is speculative, the negative startup/off-centering history is
direct, and it should not remain in staging ahead of lower-risk initialization
or DFI-only candidates.
