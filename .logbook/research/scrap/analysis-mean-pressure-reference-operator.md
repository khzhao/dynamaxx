---
schema_version: 1
slug: analysis-mean-pressure-reference-operator
title: Use Analysis-Mean Surface Pressure Only to Condition the Implicit Operator
status: scrap
created_at: 2026-06-21T08:05:17Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Analysis-Mean Surface Pressure Only to Condition the Implicit Operator

## Hypothesis

The semi-implicit gravity-wave solve is linearized around reference thermodynamic
state assumptions. The incumbent improves the analyzed state with log-pressure,
hydrostatic, theta, and analysis-HS corrections, but the implicit solve still
uses a fixed reference pressure scale. A trajectory whose global mean surface
pressure differs slightly from that scale can have a small stiffness mismatch in
the coupled divergence, temperature, and log-surface-pressure block. Using the
analysis-time area-mean surface pressure only as an operator reference may
improve conditioning without anchoring or modifying the prognostic pressure
field.

## Mechanism

Register one side-by-side candidate that computes an area-weighted global mean
surface pressure from the initialized dinosaur state after DFI setup inputs are
available. Pass that scalar into a candidate-only primitive-equation/operator
path as the reference pressure used by the implicit gravity-wave inverse, while
leaving the actual `log_surface_pressure` state untouched. Use the same fixed
scalar for the candidate's DFI and positive-time rollout for a given initial
condition.

This is not a global pressure anchor: no pressure modal coefficient is replaced,
recentered, clipped, or corrected in the forecast state or output. It is an
operator-conditioning candidate only. If the computed reference pressure is
nonfinite or outside a conservative Earthlike range, fall back to the incumbent
operator reference.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model with an `_analysis_ps_ref` suffix.
- API changes:
  - None. Forecast inputs, output variables, lead times, metrics, and splits
    remain unchanged.
- Tests to update:
  - Verify the candidate computes a finite area-weighted mean pressure from the
    initialized state and does not modify `log_surface_pressure`.
  - Verify a reference pressure equal to the incumbent scale reproduces the
    incumbent operator path.
  - Verify out-of-range or nonfinite reference pressure falls back to incumbent.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium leads if a small
    implicit gravity-wave conditioning mismatch remains after accepted
    off-centering.
  - Early leads if the operator better matches the initialized analysis column
    mass.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should stay close to the
    incumbent because diagnostics, residual corrections, and forcing are
    unchanged.
- Possible regressions:
  - If the fixed reference scale was already empirically optimal, changing it
    per forecast can perturb the accepted off-centered balance.
  - A per-initial-condition operator may increase compilation or tracing cost
    if not passed as an array value cleanly.

## Risks

- Numerical stability:
  - Moderate. The implicit gravity-wave inverse is a central stability path, so
    bounds and incumbent fallback are required.
- Compute cost:
  - Low at runtime, but implementation could add JIT specialization cost if the
    scalar is treated as static.
- Data leakage:
  - None. The scalar comes only from the forecast initial state.
- Physical plausibility:
  - Moderate to high. Semi-implicit primitive-equation solvers commonly depend
    on a reference state; matching its pressure scale to the initialized column
    mass is a plausible conditioning adjustment.
- Rollback complexity:
  - Medium. The primitive-equation operator hook must be isolated from the
    incumbent path.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Reuse compatible cached incumbent artifacts.
  - Require primary-score delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4` only
    after iteration promotion.
  - Require validation primary-score delta at least `+0.001` and the same
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that implicit
    reference pressure conditioning is not a material remaining error source.
    Any MSLP or Z500 guardrail breach would show the accepted fixed reference is
    safer.

## Citations

- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` implements the
  implicit primitive-equation gravity-wave solve.
- Dynamaxx history:
  global pressure anchoring experiments were rejected or staged as state/output
  corrections; this proposal does not alter the pressure state and should be
  evaluated as an operator-conditioning experiment.

## Researcher Notes

This proposal is decorrelated from the rejected mass-weighted theta recentering
candidate because it does not recenter temperature or pressure fields. It is
also narrower than broad implicit-matrix rewrites: a single scalar reference
pressure is changed for the candidate operator, and the incumbent path remains
the default.

## Evaluator Notes

### 2026-06-21T08:09:05Z

Decision: move to `scrap`.

The broad reference-state idea is physically plausible, but this proposal is a
poor implementation target for the current incumbent. Source inspection shows
the active adapter builds the pure-sigma primitive-equation path, whose
implicit matrix is driven by the reference-temperature profile and sigma
vertical weights; the scalar `reference_surface_pressure` hook appears in the
hybrid-coordinate path, not in the incumbent path. As written, the proposal
therefore risks either being a no-op for the active model or requiring a larger
primitive-equation operator rewrite than the mechanism describes.

Recent scored evidence also argues against spending an iteration here.
`.logbook/history/2026-06-19_14-58-18_theta-consistent-implicit-gravity-operator/decision.md`
changed the implicit gravity block and regressed iteration primary by
`-0.10312119608544257` with MSLP and wind guardrail failures.
`.logbook/history/2026-06-21_04-36-53_fixed-pressure-analysis-hs-equilibrium/decision.md`
was clean but regressed primary by `-0.0040528596151061524`, and the earlier
analysis-mean reference-temperature split was scrapped because adaptive
per-initial-condition reference states require awkward trajectory/JIT plumbing
without strong measured signal. This is not rejected because reference-state
operators are unscientific; it is rejected because the current code path,
duplicate pressure/operator staging, and negative local history make the
cost-risk tradeoff unfavorable. A future version would need a precise source
hook in the incumbent sigma operator and read-only diagnostics showing that
reference pressure conditioning is an actual limiting error.
