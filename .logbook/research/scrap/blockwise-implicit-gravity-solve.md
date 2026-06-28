---
schema_version: 1
slug: blockwise-implicit-gravity-solve
title: Use the Blockwise Semi-Implicit Gravity-Wave Inverse
status: scrap
created_at: 2026-06-20T14:53:43Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
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

# Use the Blockwise Semi-Implicit Gravity-Wave Inverse

## Hypothesis

The current incumbent uses the default `split` implicit inverse for the
semi-implicit gravity-wave block. Dinosaur already contains a `blockwise`
inverse path for the same sigma-coordinate implicit operator. The blockwise
form applies the coupled divergence, temperature, and log-surface-pressure solve
through block matrix identities and sparse vertical geopotential/temperature
operators. It is intended to reduce vertical matrix-vector work and may also
reduce accumulated roundoff or operator inconsistency in the mass/thermal
gravity-wave response.

This is a solver-internal numerical experiment, not a new time integrator. It
avoids the rejected CN-RK3 rollout family, does not change off-centering
strength, and does not modify the theta implicit gravity operator that recently
regressed. If the blockwise inverse is algebraically equivalent in practice, the
candidate should be neutral and cheap to reject; if the current split path is a
small source of mass-field numerical error, MSLP and Z500 may improve.

## Mechanism

Register a side-by-side candidate that exposes `implicit_inverse_method` through
the Dinosaur adapter and sets it to `blockwise` for both the DFI equation and
the positive-time rollout equation.

The candidate should:

- add an adapter field for the primitive-equation implicit inverse method;
- pass the selected method through `_primitive_equation` into
  `PrimitiveEquations` and `PrimitiveEquationsSigma`;
- keep the accepted SIL3 tableau, off-centering value, exact Coriolis Strang
  split, theta tendency, theta mean recentering, weak-HS forcing,
  analysis-offset HS equilibrium, surface residuals, spectral truncation, and
  horizontal diffusion unchanged;
- use the existing `blockwise` branch in
  `PrimitiveEquationsSigma.implicit_inverse` without introducing new matrix
  coefficients;
- finite-guard the candidate at the step level using the same nonfinite
  fallback style already used for off-centered SIL3 where practical;
- include a unit-level split-versus-blockwise comparison on small synthetic
  states so the Implementer and Evaluator can see whether this is numerically
  distinct or near-identical.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` only if tests
    expose a bug in the existing blockwise path
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory with a suffix such as `_blockwise_si`.
- API changes:
  - None. Forecast input/output shapes, target variables, lead times, metrics,
    and protocols remain fixed.
- Tests to update:
  - Unit-test that the adapter routes `implicit_inverse_method="blockwise"` to
    the primitive equation.
  - Compare split and blockwise inverse outputs on deterministic finite states
    and record an expected tolerance rather than requiring bitwise equality.
  - Verify the candidate factory preserves all incumbent options except the
    inverse selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - Small `mean_sea_level_pressure` and `geopotential_500` improvements at
    medium leads if the split inverse introduces avoidable vertical-coupling
    roundoff or mass/thermal imbalance under the accepted off-centered SIL3
    scheme.
  - Possible small runtime or memory improvement during evaluation if fewer
    vertical matrix-vector products dominate.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should remain close because
    surface residual correction and wind diagnostics are unchanged.
  - If split and blockwise are numerically indistinguishable, all metrics should
    be near incumbent.
- Possible regressions:
  - The blockwise path may be less exercised and could have numerical or shape
    bugs under the current unsharded CPU/GPU evaluation path.
  - Sparse vertical operator accumulation can differ from the dense split
    inverse enough to alter pressure-gradient balance adversely.

## Risks

- Numerical stability:
  - Low to moderate. The equation and time integrator are unchanged, but the
    implicit inverse implementation touches the gravity-wave mass/thermal block.
- Compute cost:
  - Low. No extra forecast steps or transforms are added. Runtime could improve
    or regress depending on JAX compilation and hardware.
- Data leakage:
  - None. The method uses only current forecast state and fixed model matrices.
- Physical plausibility:
  - Moderate. This is primarily a numerical linear-solve formulation, but it
    targets the physically important coupled divergence, temperature, and
    surface-pressure gravity-wave block.
- Rollback complexity:
  - Low. Remove one selector, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_name> --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta would show the existing split inverse is
    not a material score bottleneck. Any fast diagnostic failure or broad MSLP,
    Z500, or wind regression would show the less-used blockwise path is not
    suitable for this incumbent.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` documents
  `implicit_inverse_method` values `split`, `stacked`, and `blockwise`, and
  implements the blockwise matrix inverse for the sigma-coordinate gravity-wave
  block.
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently builds primitive
  equations without exposing `implicit_inverse_method`, so all incumbent models
  use the default `split` path.
- Dynamaxx history:
  `.logbook/history/2026-06-20_07-31-40_williamson-cn-rk3-rollout/decision.md`
  rejected a different positive-time time integrator; this proposal keeps SIL3
  and changes only the existing implicit inverse implementation.
- Dynamaxx history:
  `.logbook/history/2026-06-19_14-58-18_theta-consistent-implicit-gravity-operator/decision.md`
  rejected changing the implicit gravity operator itself; this proposal keeps
  the operator coefficients fixed.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Simmons, A. J. and Temperton, C. 1997. Stability of a two-time-level
  semi-implicit integration scheme for gravity-wave motion. Monthly Weather
  Review.
  https://doi.org/10.1175/1520-0493(1997)125%3C0600:SOATTL%3E2.0.CO;2
- Robert, A. 1981. A stable numerical integration scheme for the primitive
  meteorological equations. Atmosphere-Ocean.
  https://doi.org/10.1080/07055900.1981.9649098

## Researcher Notes

This proposal is intentionally decorrelated from the recent rejected families:
it is not CN-RK3, not a new off-centering strength, not a theta implicit
operator, not vorticity-flux dealiasing, not weak-HS retuning, and not surface
residual memory. It uses an existing but currently unexposed solver path.

The expected score movement is smaller than the accepted analysis-offset or
surface-diagnostic wins. The reason to keep it as a proposal is that it is
localized, reversible, and tests whether an unused numerical option in the
vendored dycore improves the accepted off-centered mass/thermal solve under the
current fixed evaluation.

## Evaluator Notes

### 2026-06-20T14:57:48Z

Decision: move to `scrap`.

The proposal is localized and source-supported, but it is unlikely to beat the
current incumbent under the fixed primary score. Source inspection confirms
`PrimitiveEquationsSigma.implicit_inverse` already implements `split`,
`stacked`, and `blockwise`, and the adapter could expose the selector. The same
source comments also state that `split` is the fastest unsharded method, while
`blockwise` is mainly intended to reduce matrix-vector work when vertical
sharding makes those products expensive. The current model-selection evidence
does not indicate that linear-solve roundoff or vertical sharding cost is the
remaining score bottleneck.

As a metric experiment, the expected signal is too weak: if blockwise is
algebraically equivalent, the candidate should be neutral and fail the
`+0.002` iteration promotion threshold; if it is not equivalent, the less-used
sparse block path can perturb the gravity-wave mass/thermal solve in a family
where recent broader implicit-operator changes were harmful. The rejected
theta-consistent implicit gravity operator regressed iteration primary by
`-0.10312119608544257` with pressure and wind guardrail failures, while the
recent CN-RK3 rollout rejection cautions against spending another run on a
solver-internal numerical variant with no direct physical correction. Scrap
rather than stage a likely-neutral implementation cycle.
