---
schema_version: 1
slug: dfi-theta-mean-recenter
title: Apply Theta Mean Recentering During Digital Filter Initialization
status: ready
created_at: 2026-06-19T11:47:54Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
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

# Apply Theta Mean Recentering During Digital Filter Initialization

## Hypothesis

The incumbent applies layerwise dry-potential-temperature mean recentering only
during positive-time rollout. Digital filter initialization still builds its
filtered initial state with the pre-recenter filter set, so the state handed to
the accepted off-centered rollout can carry a small layer-mean theta offset
created by the backward/forward DFI averaging. Applying the same accepted theta
mean constraint inside DFI should reduce thermal spinup without changing the
forecast contract, DFI span, off-centering amount, or output diagnostics.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_dfi_theta`.
Preserve the incumbent primitive equation, weak Held-Suarez forcing, log-pressure
and hydrostatic layer initialization, symmetric exact Coriolis split,
stability-aware near-surface residuals, Richardson 10 m wind diagnostic, theta
tendency, positive-time theta recentering, fixed SIL3 off-centering, output
variables, and lead schedule.

For this candidate only, include `_theta_layer_mean_recenter_step_filter` in the
`dfi_filters` list whenever `apply_theta_layer_mean_recentering` is enabled. Use
the same helper, reference temperature, pressure conversion, finite guard, and
layerwise area-mean formula as the positive-time incumbent path. Do not change
the DFI Lanczos weights, cutoff period, time span, solver selection, or the
off-centered rollout table. If the recentering diagnostics are nonfinite, keep
the helper's incumbent no-op fallback.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, lead times,
    target variables, and fixed protocols remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent flag except the new
    DFI theta-recenter selector.
  - Unit-test that DFI filter construction includes the theta recenter filter
    only when the opt-in flag is set.
  - Verify a synthetic DFI step preserves layerwise area-mean dry theta when the
    new filter is present.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 1 to 5 if DFI thermal-mean drift is a remaining
    source of lower-column spinup after the accepted positive-time theta
    recentering.
  - `geopotential_500` at early and medium leads if better layerwise theta
    consistency reduces hydrostatic thickness drift.
- Expected neutral metrics:
  - `10m_u_component_of_wind` and `mean_sea_level_pressure` should be close to
    neutral because winds, log surface pressure, off-centering, and surface
    residual decay are unchanged.
- Possible regressions:
  - DFI filtering intentionally removes high-frequency imbalance; adding a
    nonlinear thermal constraint during the filter may preserve a small balanced
    thermal bias that the incumbent DFI was removing.
  - The effect size may be below the iteration threshold, as several DFI-routing
    followups have been clean but weak.

## Risks

- Numerical stability:
  - Low to moderate. The helper already has finite guards, but applying it in
    signed DFI trajectories makes the DFI path less linear.
- Compute cost:
  - Low. It adds the same nodal pressure and theta reductions already used by
    positive-time recentering to DFI steps.
- Data leakage:
  - None. The filter uses only the evolving forecast state and fixed grid
    geometry.
- Physical plausibility:
  - Moderate. Layerwise dry theta conservation is consistent with adiabatic dry
    dynamics, but DFI is a balance filter rather than a physical time step.
- Rollback complexity:
  - Low. The change is side-by-side factory plumbing plus one DFI filter
    inclusion.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failures, and
    at least `+0.002` primary-score improvement over the incumbent.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4` only
    if iteration promotes.
  - Support requires clean diagnostics, no guardrail failures, and at least
    `+0.001` validation primary-score improvement.
- Outcome that would falsify the hypothesis:
  - A clean but sub-threshold iteration delta would show that DFI theta-mean
    drift is not material for the current off-centered incumbent.
  - Any early `10m_u_component_of_wind` or `2m_temperature` guardrail failure
    would indicate the DFI constraint is disrupting useful filtered balance.

## Citations

- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
  digital filter. Monthly Weather Review.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics, second edition,
  sections on hydrostatic primitive equations and sigma-coordinate energetics.
- Source history: `.logbook/history/2026-06-19_00-02-28_theta-zero-mode-thermal-recentering/decision.md`
  accepted positive-time theta mean recentering with validation delta
  `+0.005185083087329123`.
- Source history: `.logbook/history/2026-06-19_10-17-34_centered-dfi-offcenter-rollout/decision.md`
  rejected DFI solver routing alone as clean but neutral.

## Researcher Notes

This is not a duplicate of `mass-weighted-theta-recentering`, which changes the
recenter weighting formula, or `zonal-mean-theta-recentering`, which imposed a
much stronger zonal/latitudinal constraint and produced nonfinite forecasts. It
also differs from the rejected centered DFI/offcenter rollout candidate because
it leaves the solver routing and off-centering untouched and instead makes DFI
respect the accepted rollout-only theta mean invariant.

## Evaluator Notes

### 2026-06-19T11:53:51Z

Decision: move to `ready`; ranked 1 of 3 new proposals and the sole ready
recommendation.

This is the strongest next experiment because it is a narrow extension of a
measured accepted mechanism. The accepted theta zero-mode recentering improved
iteration by `+0.003997358805283291` and validation by
`+0.005185083087329123` with clean diagnostics. Source inspection confirms the
current adapter builds `dfi_filters` before appending
`_theta_layer_mean_recenter_step_filter` to positive-time rollout filters, so
the proposal targets a real remaining asymmetry rather than inventing a new
operator family.

The main negative evidence is the recent centered-DFI/offcenter-rollout result,
which was clean but neutral at only `+0.000005771767184858945` iteration delta.
That does not duplicate this proposal: solver routing left the filtered-state
thermal invariant unchanged, while this candidate applies the already accepted
layerwise theta constraint inside DFI. The implementation surface is small,
side-by-side, and easy to revert. The finite-guarded no-op fallback keeps the
numerical risk acceptable, though the Scorer should watch for DFI balance
disruption and late-wind tradeoffs.
