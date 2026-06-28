---
schema_version: 1
slug: exner-balanced-pressure-gradient-split
title: Exner Balanced Pressure Gradient Split
status: staging
created_at: 2026-06-21T04:30:49Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Exner Balanced Pressure Gradient Split

## Hypothesis

The incumbent now uses a potential-temperature thermodynamic tendency, but the
explicit pressure-gradient coupling still follows the existing temperature
variation and log-surface-pressure product form. In hydrostatic pressure or
sigma-coordinate primitive equations, the pressure-gradient and thermodynamic
conversion terms are most naturally paired through Exner pressure and potential
temperature. A narrow Exner-balanced split for the explicit pressure-gradient
product should reduce spurious divergence and thermal conversion errors without
changing the semi-implicit operator or the fixed evaluation contract.

## Mechanism

Add a model option for a `theta_exner` pressure-gradient product when the
potential-temperature tendency is active. The candidate should keep the
incumbent implicit terms, hydrostatic geopotential calculation, time step,
offcentering, DFI, and residual corrections unchanged. Only the explicit
thermodynamic pressure-gradient product in the vorticity-divergence tendency
should be reformulated.

The bounded implementation target is to replace the `R * T' * grad(log p_s)`
style explicit product with an equivalent Exner-pressure split using the local
potential-temperature anomaly around the same reference state. The reference
part should remain handled by the incumbent implicit gravity-wave operator, so
this experiment tests thermodynamic consistency rather than a full pressure
gradient or vertical discretization rewrite.

## Implementation Scope

- Expected files: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  for the optional pressure-gradient product, and `adapter.py` for wiring the
  option into an incumbent-derived factory.
- Registry changes: add one model factory with a suffix such as
  `_theta_exner_pg_split`.
- API changes: no external forecast API changes; one internal option on the
  Dinosaur primitive-equation configuration is sufficient.
- Tests to update: add a unit-level construction or tendency-shape test that
  exercises the new option and confirms finite tendencies for a representative
  state.

## Expected Metric Movement

- Expected improvements: `geopotential_500` and `mean_sea_level_pressure`,
  especially at medium leads where balanced pressure-gradient errors project
  onto gravity-wave and column-mass errors.
- Expected neutral metrics: `10m_u_component_of_wind`, because the surface wind
  diagnostic and residual model are not altered.
- Possible regressions: `2m_temperature` if the current temperature-product
  form is compensating a lower-column thermal bias.

## Risks

- Numerical stability: moderate; pressure-gradient changes can excite fast
  modes if the explicit split is inconsistent with the incumbent implicit
  reference operator.
- Compute cost: negligible to low; the reformulation reuses existing sigma-level
  fields and spectral derivatives.
- Data leakage: none; no target data or future lead information is introduced.
- Physical plausibility: high if the split is algebraically tied to potential
  temperature and Exner pressure, but low if implemented as an unrelated tuning
  term.
- Rollback complexity: low; the incumbent product remains the default for all
  existing registered models.

## Evaluation Plan

- Fast gate: require finite outputs on the fixed `fast` protocol with no new
  diagnostics or target variables.
- Iteration gate: run the fixed `iteration` protocol with the normal worker
  policy and compare the primary score and variable guardrails to the incumbent.
- Validation gate: run fixed `validation` only after an iteration gain or a
  clearly neutral aggregate with strong Z500/MSLP improvement.
- Outcome that would falsify the hypothesis: fast-mode instability, nonfinite
  tendencies, or iteration regressions concentrated in Z500/MSLP.

## Citations

- Laprise, R., 1992: The Euler equations of motion with hydrostatic pressure as
  an independent variable. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1992)120%3C0197:TEEOMW%3E2.0.CO;2
- Simmons, A. J., and D. M. Burridge, 1981: An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2

## Researcher Notes

This is not the rejected well-balanced sigma pressure-gradient idea and not the
staged pressure-gradient product dealiasing or Simmons-Burridge vertical
operator proposal. It does not add terrain, change the vertical finite
difference, alter filters, or initialize a different state. It tests a narrow
thermodynamic consistency change made relevant by the accepted theta-tendency
incumbent.

## Evaluator Notes

### 2026-06-21T04:35:33Z

Decision: move to `staging`; ranked second of the three new proposals.

The mechanism is scientifically plausible and distinct from the active
pressure-gradient product dealiasing and Simmons-Burridge vertical-operator
proposals. It also differs from the scrapped well-balanced sigma
pressure-gradient split because it aims at the theta/Exner form of the
explicit product rather than moving layer-mean temperature anomalies into the
linear reference operator.

Do not promote it ahead of the fixed-pressure HS proposal. Recent operator
history is cautionary: the theta-consistent implicit gravity operator was
finite but strongly negative with MSLP and wind guardrail failures, direct
surface-pressure continuity correction was clean but negative, and the
well-balanced pressure-gradient split was already scrapped as a broad runtime
operator change. This proposal is narrower than those, but it still touches a
core vorticity-divergence pressure-gradient source every tendency evaluation
and could disrupt the semi-implicit balance that the incumbent now relies on.
Keep staged for a later pressure-gradient experiment only after lower-risk
thermal-equilibrium and diagnostic candidates are exhausted.
