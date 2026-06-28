---
schema_version: 1
slug: energy-conserving-omega-alpha-coupling
title: Discrete Energy-Conserving Omega-Alpha / Geopotential Coupling
status: staging
created_at: 2026-06-23T02:31:00Z
author_role: Researcher
target_model: dino_hsl2_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py
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

# Discrete Energy-Conserving Omega-Alpha / Geopotential Coupling

## Hypothesis

The physical content of Simmons & Burridge (1981) is a **discrete identity**
linking the hydrostatic geopotential weights to the omega-alpha (pressure-work)
term so that the discrete kinetic <-> internal energy conversion `-integral(omega
dPhi/dp)` is exactly antisymmetric -- no spurious per-step energy source or sink.
In this core the geopotential `G` matrix (`get_geopotential_weights_sigma`) and the
pressure-work quadrature (`_t_omega_over_sigma_sp`, Durran-style midpoint rule) are
constructed **independently**, so the discrete conversion is only approximately
energy-neutral. The residual is a small per-step thermal/mass source that
accumulates over 1-15 day rollouts and projects onto `mean_sea_level_pressure`,
`geopotential_500`, and lower-tropospheric temperature. Deriving the two operators
from a common set of layer coefficients so they satisfy the S&B energy-conversion
constraint should remove that accumulated bias.

## Mechanism

Register a side-by-side candidate named `dino_hsl2_theta_eomega`. Preserve every
incumbent setting; change only how the omega-alpha layer weights are derived.

- In `primitive_equations.py`, derive the omega-alpha weights used in
  `_t_omega_over_sigma_sp` from the **same** alpha/beta layer coefficients as
  `get_geopotential_weights_sigma`, so the discrete pairing satisfies the S&B
  energy-conversion constraint, rather than from the independent
  `cumulative_sigma_integral` midpoint quadrature;
- keep the semi-implicit `H`/`G` matrices, the reference temperature `T_ref`, the
  thermodynamic variable (theta), and all other operators on the incumbent path;
- gate behind one adapter flag; finite-fallback to the incumbent quadrature.

## Implementation Scope

- Expected files: `primitive_equations.py` (omega-alpha weight derivation +
  branch), `sigma_coordinates.py` (shared coefficient helper if needed),
  `adapter.py` (flag), `__init__.py`, `registry.py`, tests.
- Registry changes: add only the side-by-side candidate.
- API changes: none.
- Tests to update: an energy-identity unit test verifying the column-integrated
  discrete conversion `sum_k omega_k alpha_k dsigma_k` matches `-sum_k Phi_k
  d(sigma_dot)` to machine precision for a test state; a **materiality** check that
  the derived weights differ measurably from the incumbent (guarding against a
  no-op); nonfinite fallback reproduces the incumbent; registry coverage and a
  finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements: `mean_sea_level_pressure` and `geopotential_500` (reduced
  accumulated mass/energy bias at medium-to-long lead); `2m_temperature` modest.
- Expected neutral metrics: `10m_u_component_of_wind`.
- Possible regressions: if the constraint is near-satisfied already the change is a
  near-no-op; touching the energetically sensitive thermodynamic tendency could mildly
  shift early-lead balance.

## Risks

- Numerical stability: moderate -- modifies an energetically sensitive term; the
  energy-identity test and early-lead guardrail are the safeguards.
- Compute cost: negligible (a weight-derivation change).
- Data leakage: none.
- Physical plausibility: high -- this is the conservation property S&B 1981 was
  designed around.
- Rollback complexity: low.

## Evaluation Plan

- Fast gate: `uv run pytest`; `uv run dynamaxx-eval fast --model dino_hsl2_theta_eomega`;
  finite forecasts, zero diagnostic issues.
- Iteration gate: `uv run dynamaxx-eval iteration --model dino_hsl2_theta_eomega --workers 4`;
  support is primary delta >= +0.002, clean diagnostics, no guardrail failure.
- Validation gate: `uv run dynamaxx-eval validation --model dino_hsl2_theta_eomega --workers 4`
  only after iteration promotion; require validation delta >= +0.001.
- Falsification: a clean near-zero delta would show the incumbent omega-alpha /
  geopotential pairing is already energy-neutral enough that the accumulated bias
  is not a material error source.

## Citations

- Citation or source:
  - Dynamaxx source: `primitive_equations.py` `_t_omega_over_sigma_sp` (independent
    midpoint pressure-work quadrature) and `get_geopotential_weights_sigma`
    (separately constructed geopotential weights).
  - Simmons, A. J. & Burridge, D. M. 1981. An energy and angular-momentum
    conserving vertical finite-difference scheme and hybrid vertical coordinates.
    Mon. Wea. Rev. 109(4), 758-766.
    https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
  - Arakawa, A. & Suarez, M. J. 1983. Vertical differencing of the primitive
    equations in sigma coordinates. Mon. Wea. Rev. 111(1), 34-45.
    https://doi.org/10.1175/1520-0493(1983)111%3C0034:VDOTPE%3E2.0.CO;2
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics, 2nd ed., Sec. 8.6.
    Springer. https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-23 from the
vertical-structure research pass, paired with `charney-phillips-interface-theta-advection`
but mechanistically distinct (energy-conversion identity vs thermodynamic
staggering) and targeting MSLP/Z500 rather than T2m. Distinct from the staged
`simmons-burridge-sigma-geopotential-operator` (which swaps only the hydrostatic
geopotential weights -- one side of the pairing), `log-sigma-adiabatic-temperature-tendency`
(changes only the omega/p quadrature rule, no coupling constraint), and
`bounded-pressure-work-thermal-tendency` (clips the term). This is the only idea
enforcing the energy-conversion identity *between* the two operators. Honest
success probability ~15-20% (higher no-op risk than the Charney-Phillips idea); the
mandatory materiality check decides up front whether it is worth a full run.

## Evaluator Notes

### 2026-06-23T03:03:08Z

Decision: move to `staging`; ranked 2 of 4 current proposals.

The physical motivation is legitimate, but this should not be the next
model-selection experiment. It overlaps the staged pressure-work and vertical
operator neighborhood, especially `simmons-burridge-sigma-geopotential-operator`,
`log-sigma-adiabatic-temperature-tendency`, and
`bounded-pressure-work-thermal-tendency`. This proposal is more coherent than a
simple cap because it couples the pressure-work and geopotential weights, but it
also touches a sensitive matched sigma-coordinate energy/implicit-balance path
where prior pressure, continuity, and hydrostatic refinements have been fragile
or cleanly negative.

Keep staged as a later pressure-work discretization candidate if diagnostics or
source inspection first show the incumbent pairing is materially inconsistent.
Before promotion, require the proposed materiality check to prove the derived
weights differ meaningfully from the incumbent and a discrete energy-identity
unit test that does not require changing the forecast contract or evaluation
protocols. Do not run it ahead of the Charney-Phillips theta-interface idea
because the no-op risk is higher and expected primary-score leverage is less
direct.
