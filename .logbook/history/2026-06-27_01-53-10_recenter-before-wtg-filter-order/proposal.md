---
schema_version: 1
slug: recenter-before-wtg-filter-order
title: Recenter Before WTG Filter Ordering
status: ready
created_at: 2026-06-27T01:48:57Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Recenter Before WTG Filter Ordering

## Hypothesis

The current incumbent applies the tropical WTG mass-DSE relaxation filter and
then the theta layer-mean recentering filter during positive-time rollout. Both
filters are individually heat/balance motivated, but their order matters because
the recentering filter adds a uniform layer temperature correction after WTG has
already relaxed tropical low-mode mass-DSE anomalies. Applying theta recentering
before WTG would let the WTG filter be the final thermal balance adjustment in
the tropics, potentially preserving the accepted WTG signal while avoiding a
small global layer correction that can partially undo it.

## Mechanism

Register a side-by-side candidate named
`dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg`. Preserve all incumbent
physics, selectors, constants, and masks, but change the positive-time filter
order when both `apply_tropical_wtg_mass_dse_relaxation` and
`apply_theta_layer_mean_recentering` are enabled:

1. apply theta layer-mean recentering;
2. apply tropical WTG mass-DSE relaxation;
3. continue with the existing symmetric Coriolis split and trajectory wrapper.

The candidate should not alter DFI filters, evaluation protocols, target
variables, lead times, WTG support, vertical-DSE ramping, temperature caps,
surface residuals, or output diagnostics.

This is distinct from the rejected WTG support taper and moisture-convergence
gate. It does not change where or how strongly WTG acts; it changes the ordering
of two accepted rollout-only thermal filters.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg`.
- API changes:
  - None.
- Tests to update:
  - Factory parity with the incumbent except the filter-order selector and name.
  - Unit test confirming rollout filter order is theta recentering before WTG
    for the candidate and incumbent order remains unchanged.
  - Unit test confirming DFI filters remain unchanged and exclude both
    rollout-only filters as before.
  - Registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - Tropical-sensitive `2m_temperature`, `mean_sea_level_pressure`, and
    `geopotential_500` if post-WTG theta recentering is diluting a useful WTG
    correction.
- Expected neutral metrics:
  - Most short-lead metrics if the two small corrections nearly commute.
  - `10m_u_component_of_wind`, except through indirect pressure/thermal changes.
- Possible regressions:
  - The accepted order may be stabilizing because the final theta recentering
    removes global thermal drift after WTG. Reversing it could increase drift or
    damage early T2m.
  - If the filters commute numerically, the result will be near neutral and not
    worth further work.

## Risks

- Numerical stability:
  - Low. Both filters are already accepted and finite-guarded.
- Compute cost:
  - None beyond the incumbent.
- Data leakage:
  - None.
- Physical plausibility:
  - Moderate. Operator ordering is a numerical splitting choice; putting the
    regionally targeted WTG correction last may better enforce the intended
    tropical balance, but this is a splitting experiment rather than a new
    physical process.
- Rollback complexity:
  - Low.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg`
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero result would show the filters effectively commute under
    the current step size and caps. A negative result would show the accepted
    final recentering is more useful than final WTG enforcement.

## Citations

- Sobel, A. H., Nilsson, J., and Polvani, L. M. 2001. The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences, 58, 3650-3665.
  https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Strang, G. 1968. On the construction and comparison of difference schemes.
  SIAM Journal on Numerical Analysis, 5, 506-517.
  https://doi.org/10.1137/0705041
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This proposal is intentionally cheap and diagnostic. If it is neutral, future
WTG work should focus on physical content rather than filter ordering. If it is
negative, it supports the current design in which theta recentering is the final
thermal cleanup. If it is positive, it gives a low-risk way to improve the
accepted WTG/vertical-DSE combination without altering fixed evaluation
protocols.

## Evaluator Notes

### 2026-06-27T01:52:04Z

Decision: move to `ready`; ranked 1 of 3 new proposals.

This is the strongest proposal in the batch because it tests a concrete
operator-order interaction between two already accepted rollout-only thermal
filters while preserving the WTG mask, vertical envelope, relaxation strength,
temperature cap, ramped vertical-DSE path, forecast API, and fixed evaluation
protocols. Source inspection confirms the current rollout path appends WTG
before theta recentering, while DFI receives only the earlier shared filters,
so the proposed side-by-side selector is real and low surface area.

Recent WTG support variants are negative evidence for changing where WTG acts,
and the rejected pressure-thickness WTG closure argues against another small
neutrality refinement. This proposal avoids both patterns. It is also cheaper
and narrower than staged WTG timing ideas such as half-step centered WTG or
inline WTG tendency coupling. The expected score movement may still be small,
but it is a clean diagnostic of whether final theta recentering is diluting the
accepted WTG correction under the current `dino_hsl2_mass_dse_wtg_vdse_ramp`
incumbent. Keep `ready` small by making this the only ready item from this
batch.
