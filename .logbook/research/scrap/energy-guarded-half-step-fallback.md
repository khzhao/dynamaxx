---
schema_version: 1
slug: energy-guarded-half-step-fallback
title: Total-Energy Guarded Half-Step Fallback
status: scrap
created_at: 2026-06-20T17:06:07Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
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

# Total-Energy Guarded Half-Step Fallback

## Hypothesis

The incumbent has accumulated several successful balance and stability devices:
DFI, exact Coriolis splitting, theta recentering, semi-implicit offcentering, and
analysis-offset weak-HS equilibrium. The remaining negative late-lead Z500,
MSLP, wind, and 2 m temperature scores may partly come from intermittent
high-energy numerical excursions rather than a uniform bias that should be
corrected every step. Prior CN-RK3 and broad rollout changes were harmful or
subthreshold, so replacing the whole time integrator is not attractive.

A rare-trigger fallback can target only suspicious steps. If a full step causes
an excessive increase in a simple dry total-energy norm or creates nonfinite
values, recomputing that same interval as two half steps should reduce local
truncation error and stabilize the outlier without changing the normal
trajectory when the incumbent step is already well behaved.

## Mechanism

Register a side-by-side candidate with a suffix such as `_energy_guarded_substep`.
Wrap the positive-time rollout step after the accepted DFI initialization. For
each step:

- compute the incumbent one-step update exactly as today;
- compute a column-mass-weighted dry total-energy diagnostic before and after
  the proposed update, using kinetic energy plus a temperature/geopotential
  proxy available from the Dinosaur state;
- accept the incumbent full step when the relative energy growth is finite and
  below a fixed conservative threshold;
- otherwise recompute the same interval as two half steps with the same
  tendencies, filters, Coriolis split, theta recentering, weak-HS forcing, and
  surface residual logic evaluated at half-step cadence;
- after the fallback, apply the same finite checks and use a bounded repair only
  for nonfinite diagnostic scalars, not for forecast target variables.

The fallback must be deterministic and JAX-compatible, for example through
`jax.lax.cond`. It should not change output lead times, metrics, target
variables, the number of returned trajectories, or the fixed evaluation
protocols.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add a single opt-in model entry whose name appends
    `_energy_guarded_substep` to the current incumbent.
- API changes:
  - None. The candidate still returns exactly one forecast trajectory as a
    standard `WeatherState`.
- Tests to update:
  - Unit-test that the guard does not trigger for a benign state, triggers for a
    manufactured high-energy step, preserves output shape/tree structure, and
    remains deterministic under JIT.
  - Add a registry test for the side-by-side candidate.

## Expected Metric Movement

- Expected improvements:
  - Most likely gains are late-lead `geopotential_500`,
    `mean_sea_level_pressure`, and `10m_u_component_of_wind` if rare energetic
    outliers currently contaminate synoptic balance.
  - A smaller 2 m temperature gain is possible if stabilized mass and height
    evolution reduces the incumbent's late cold drift.
- Expected neutral metrics:
  - Day-1 and day-2 metrics should be nearly unchanged when the guard rarely
    triggers.
- Possible regressions:
  - Frequent fallback could overdamp fast waves by effectively reducing the time
    step too often, increasing cost and changing the incumbent's calibrated
    balance. The trigger rate should be logged during development and kept low.

## Risks

- Numerical stability:
  - Moderate. Half-step recomputation is stabilizing in principle, but a poorly
    chosen energy norm could trigger on physically meaningful baroclinic growth.
    The guard must be based on extreme local growth and finite checks, not on
    ordinary synoptic amplification.
- Compute cost:
  - Moderate. In compiled JAX control flow, branch compilation cost is one-time,
    but runtime cost rises when fallback triggers. The proposal is realistic
    under the reported 48 CPUs, 4 L4 GPUs, and 4 eval workers only if triggers
    are rare.
- Data leakage:
  - None. The decision uses only the current forecast state and candidate next
    state.
- Physical plausibility:
  - Moderate. Adaptive substepping is a numerical robustness device, not a new
    physical parameterization. It is justified only if it improves fixed
    protocol metrics without broad damping.
- Rollback complexity:
  - Low to moderate. The wrapper should be isolated behind a model flag; however,
    integrator plumbing must be kept simple enough that removing the flag
    restores the incumbent exactly.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
  - Require finite outputs, no shape/API changes, and wall-clock cost close
    enough to the incumbent to keep full iteration feasible.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Support the hypothesis if late-lead Z500/MSLP/wind improve and the aggregate
    primary score beats the incumbent without day-1/day-2 degradation.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4`.
  - Require validation primary improvement or a clear late-lead stability gain
    that does not trade away the incumbent's accepted 2 m temperature progress.
- Outcome that would falsify the hypothesis:
  - A near-zero trigger rate with neutral scores means rare energetic steps are
    not the limiting error. A high trigger rate with worse scores means the
    guard is acting as an uncalibrated global time-step change and should be
    rejected.

## Citations

- Durran, D. R. (2010). "Numerical Methods for Fluid Dynamics: With
  Applications to Geophysics", 2nd edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Soederlind, G. (2002). "Automatic Control and Adaptive Time-Stepping."
  Numerical Algorithms, 31, 281-310. https://doi.org/10.1023/A:1021160023092
- Jablonowski, C., and Williamson, D. L. (2006). "A baroclinic instability test
  case for atmospheric model dynamical cores." Quarterly Journal of the Royal
  Meteorological Society, 132, 2943-2975. https://doi.org/10.1256/qj.06.12

## Researcher Notes

This is not a CN-RK3 or RK replacement proposal. The incumbent full step remains
the default path, and the half-step path is only a deterministic fallback for
extreme energy growth or nonfinite states. It also differs from staged bounded
log-pressure or pressure-work limiters because the guard observes a whole-state
energy norm and changes time resolution for one interval, rather than clipping a
single prognostic variable. The fixed evaluation protocols, target variables,
lead times, and single-trajectory forecast contract remain unchanged.

## Evaluator Notes

### 2026-06-20T17:10:51Z

Decision: move to `scrap`.

The proposal is deterministic and does not intentionally change the forecast
contract, but it is too broad and weakly evidenced for the next loop. The
current incumbent's fast, iteration, and validation diagnostics are clean, so
there is no observed nonfinite or energetic-outlier failure mode for an
adaptive substep guard to fix. Recent rollout evidence is unfavorable:
`williamson-cn-rk3-rollout` was clean but severely negative, and even narrower
DFI/rollout refinements such as the DFI-balanced analysis-HS equilibrium and
theta-variance guard were clean but slightly negative.

Implementation would touch the core positive-time stepper, duplicate full-step
and half-step paths through filters, Coriolis split, theta recentering,
weak-HS forcing, and residual logic, and introduce a new dry total-energy norm
whose threshold would be hard to justify without tuning. That combination makes
it a broad numerical-control bundle rather than a focused implementable idea
under the fixed evaluation gates. Future rollout work should stay in narrower
staged families that preserve the accepted offcentered SIL3 mechanism.
