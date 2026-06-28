---
schema_version: 1
slug: symmetric-coriolis-rotation-split
title: Use a Symmetric Exact Coriolis Rotation Split
status: ready
created_at: 2026-06-18T04:29:16Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split
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

# Use a Symmetric Exact Coriolis Rotation Split

## Hypothesis

The accepted incumbent improves both iteration and validation by removing the
linear Coriolis rotation from the IMEX primitive-equation tendency and applying
the exact local wind rotation after each positive-time step. That implementation
is a first-order Lie split between Coriolis rotation and the remaining dynamics.

A symmetric half-step/full-step/half-step split should keep the accepted exact
rotation mechanism while reducing source-splitting phase error. The most likely
benefit is in wind phase and downstream mass-field evolution, without changing
DFI, hydrostatic initialization, weak Held-Suarez forcing, near-surface
residuals, output variables, or fixed evaluation protocols.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang`.
Preserve all incumbent settings except the positive-time Coriolis split order.

For the rollout only:

- build the primitive equation with `angular_velocity=0.0`, as in the accepted
  Coriolis split;
- build the non-Coriolis step with the existing IMEX SIL3 solver and existing
  horizontal diffusion filter;
- wrap that step as `rotate_half(non_coriolis_step(rotate_half(state)))`, where
  `rotate_half` converts modal vorticity/divergence to nodal winds, applies the
  exact Coriolis rotation for half the inner step at each latitude, and projects
  back to modal vorticity/divergence;
- preserve temperature variation, log surface pressure, tracers, and `sim_time`
  through each rotation;
- keep the DFI path on the incumbent unsplit dynamics, matching the accepted
  model and avoiding time-reversed split-filter complexity.

This is not a time-step sweep and not a new physical forcing. It only changes
operator ordering for the already accepted exact Coriolis source.

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
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang`.
- API changes:
  - None. `DycoreModel.forecast`, output variables, lead times, and fixed
    metrics remain unchanged.
- Tests to update:
  - Verify the candidate preserves every incumbent option except the symmetric
    Coriolis split flag.
  - Unit-test that two half rotations match the existing full-step rotation for
    a pure rotation state to numerical tolerance.
  - Unit-test that a half rotation leaves temperature, log surface pressure,
    tracers, and `sim_time` unchanged.
  - Verify the DFI initializer still uses the incumbent unsplit equation and
    incumbent DFI filters.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and long leads if part of the remaining
    wind error is Coriolis source-splitting phase error.
  - `mean_sea_level_pressure` and `geopotential_500` at medium leads if better
    wind phase reduces balanced mass-field drift.
- Expected neutral metrics:
  - `2m_temperature` should be close to neutral because thermal initialization,
    weak Held-Suarez relaxation, and near-surface residual correction are
    unchanged.
- Possible regressions:
  - The accepted post-step Lie split may be empirically better for this model's
    filter ordering.
  - The newest accepted candidate's largest remaining regression was day-1
    `geopotential_500`; changing split order could spend more of that guardrail
    margin.

## Risks

- Numerical stability:
  - Low to moderate. Each rotation is norm-preserving for nodal winds, but the
    non-Coriolis dynamics sees a half-rotated state and may shift fast-wave
    phase.
- Compute cost:
  - Low to moderate. It adds one extra wind transform pair per inner step
    relative to the accepted split. The reported 48 CPU, 174 GiB RAM, and four
    L4 GPUs are adequate for one side-by-side candidate at `--workers 4`.
- Data leakage:
  - None. The mechanism uses only forecast state and fixed physical constants.
- Physical plausibility:
  - High. Symmetric operator splitting is a standard way to reduce splitting
    error for separable evolution operators.
- Rollback complexity:
  - Low. Remove one split flag, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the incumbent, clean diagnostics, no early day 1-5 RMSE guardrail failure,
    and no variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that first-order
    Coriolis split error is not a material remaining source. Any early Z500 or
    10 m wind guardrail failure would show the symmetric ordering is too
    disruptive for the current incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  the accepted rollout-only exact Coriolis rotation filter and keeps DFI on the
  unsplit incumbent path.
- History: `.logbook/history/2026-06-18_03-03-20_exact-coriolis-rotation-split/decision.md`
  accepted the first exact Coriolis split with iteration delta
  `+0.016060659619097084` and validation delta `+0.014145578761930677`.
- Strang, G. 1968. On the Construction and Comparison of Difference Schemes.
  SIAM Journal on Numerical Analysis. https://doi.org/10.1137/0705041
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
  Atmospheric Models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241

## Researcher Notes

This is a close follow-up to the accepted Coriolis split, but it is not a
duplicate: the accepted model uses a post-step Lie split, while this proposal
uses a symmetric Strang split for the same source. It deliberately does not
change the DFI path, weak Held-Suarez source, horizontal diffusion strength,
inner step, target variables, or validation protocol.

It is decorrelated from the active staged `fourth-order-imex-rk-rollout`
proposal. RK4 changes the entire explicit quadrature and DFI solver hook; this
proposal keeps SIL3 and changes only the ordering of one accepted linear source
operator.

## Evaluator Notes

### 2026-06-18T04:36:51Z

Decision: move to `ready`.

This is the strongest next candidate. The latest accepted incumbent gained
`+0.016060659619097084` on iteration and `+0.014145578761930677` on validation
by separating the Coriolis source from the positive-time rollout, and source
inspection confirms the accepted implementation is a post-step exact rotation
filter applied after each non-Coriolis SIL3 step while DFI remains on the
unsplit equation. A symmetric half/full/half composition is therefore a real
operator-ordering variant rather than a duplicate. Literature checks against
Strang splitting references support the claim that symmetric splitting is a
standard route to reduce source-splitting error for separable operators.

Keep ready small and prefer this over output-only Z diagnostics and broader
time-integration changes. Implementation should preserve all incumbent options,
including rollout-only Coriolis splitting and unsplit DFI, and add only the
symmetric split mode plus focused tests. Main risks are the extra wind transform
pair per inner step, interaction with the horizontal-diffusion filter ordering,
and the accepted incumbent's existing day-1 `geopotential_500` regression of
about `+6.7%` against the prior incumbent.
