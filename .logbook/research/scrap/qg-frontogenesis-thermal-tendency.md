---
schema_version: 1
slug: qg-frontogenesis-thermal-tendency
title: QG Frontogenesis Thermal Tendency for Extratropical Omega Forcing
status: scrap
created_at: 2026-06-25T01:38:28Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# QG Frontogenesis Thermal Tendency for Extratropical Omega Forcing

## Hypothesis

The incumbent dry primitive-equation rollout has resolved wind and temperature
gradients, but it has no parameterized representation of unresolved
frontogenetic secondary circulations. A bounded quasi-geostrophic Q-vector
thermal tendency can add the missing sign and phase of extratropical vertical
motion forcing while leaving log-pressure continuity and momentum untouched.
This should mainly affect synoptic thickness evolution, where the current
mass-DSE transport may still miss baroclinic heating and cooling tied to
frontogenesis.

## Mechanism

Add one side-by-side candidate, for example `dino_hsl2_mass_dse_qg_omega`.
During positive-time rollout, form a low-mode extratropical diagnostic from the
forecast state:

- reconstruct horizontal wind and temperature on sigma levels from the current
  state;
- estimate geostrophic wind with a conservative `f` floor and a latitude taper
  that is exactly zero in the tropics;
- compute the Q-vector proxy from geostrophic wind deformation acting on the
  horizontal temperature gradient;
- use low-mode `-div(Q)` with a fixed vertical envelope over the lower and
  middle free troposphere to define a bounded adiabatic temperature tendency;
- remove any layerwise global mean and cap the per-step temperature increment.

This is a reduced forcing proxy rather than a full elliptic omega solve. It
does not import same-time analysis omega, alter `sigma_dot`, change the
log-surface-pressure tendency, or modify horizontal/vertical scalar transport.
If the geostrophic diagnostic, Q-vector, static-stability proxy, or tendency is
nonfinite, the candidate must use the incumbent tendency.

## Implementation Scope

- Expected files: add a guarded Q-vector helper and opt-in selector in
  `primitive_equations.py` or as an adapter step filter; add a side-by-side
  factory and registry entry; add focused tests.
- Registry changes: add `dino_hsl2_mass_dse_qg_omega`.
- API changes: none to forecast inputs, outputs, evaluated variables, lead
  handling, or eval protocols.
- Tests to update: registry creation; disabled-flag incumbent equivalence;
  finite no-JIT smoke forecast; no-op in the tropical taper; no-op for uniform
  temperature; bounded finite response for an idealized baroclinic wave;
  fallback on small `f`, invalid static stability, or nonfinite diagnostics.

## Expected Metric Movement

- Expected improvements: `geopotential_500` at days 3-15 if baroclinic
  thickness phase is limited by missing frontogenetic vertical-motion heating;
  secondary `mean_sea_level_pressure` improvement through better synoptic mass
  distribution.
- Expected neutral metrics: `2m_temperature` and `10m_u_component_of_wind`
  should be mostly neutral because the operator is free-tropospheric,
  extratropical, and thermodynamic only.
- Possible regressions: broad thermal forcing can disturb the accepted
  mass-DSE balance, especially if the Q-vector proxy overreacts near jets or
  fronts; early `mean_sea_level_pressure` guardrails need close attention.

## Risks

- Numerical stability: moderate; Q-vector diagnostics involve horizontal
  derivatives and division by `f`, so masks and caps are mandatory.
- Compute cost: moderate; adds several low-mode gradient products per step but
  no iterative solve.
- Data leakage: none; uses only the forecast state and fixed masks/constants.
- Physical plausibility: moderate; QG omega forcing is standard for midlatitude
  vertical motion diagnosis, while the proposed tendency is a simplified
  bounded surrogate.
- Rollback complexity: low to moderate; the feature can be isolated behind one
  selector and one registry entry.

## Evaluation Plan

- Fast gate: run fixed fast for `dino_hsl2_mass_dse_qg_omega`; reject on any
  nonfinite diagnostic or early mass-field warning.
- Iteration gate: run fixed iteration with normal worker count and require
  `+0.002` primary-score improvement over cached `dino_hsl2_mass_dse`.
- Validation gate: run fixed validation only after iteration promotion and
  require `+0.001` improvement with clean guardrails.
- Outcome that would falsify the hypothesis: clean near-zero or negative
  iteration movement would show that QG frontogenetic thermal forcing is not a
  material remaining error source; any early MSLP/Z500 guardrail failure would
  show the reduced thermal tendency is too unbalanced.

## Citations

- Hoskins, B. J., I. Draghici, and H. C. Davies, 1978: A new look at the
  omega-equation. Quarterly Journal of the Royal Meteorological Society, 104,
  31-38. https://doi.org/10.1002/qj.49710443903
- Davies, H. C., 2015: The Quasigeostrophic Omega Equation: Reappraisal,
  Refinements, and Relevance. Monthly Weather Review, 143, 3-25.
  https://doi.org/10.1175/MWR-D-14-00098.1
- Keyser, D., M. J. Reeder, and R. J. Reed, 1988: A generalization of
  Petterssen's frontogenesis function and its relation to the forcing for
  vertical motion. Monthly Weather Review, 116, 762-780.
  https://doi.org/10.1175/1520-0493(1988)116%3C0762:AGOPFF%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of active `theta-omega-spinup` or
`analysis-omega-vertical-motion-spinup`: those ideas import analyzed omega as a
transient initialization/spinup source, while this candidate diagnoses a
forecast-state QG forcing during the rollout and never changes the forecast
contract. It is also distinct from `log-sigma-adiabatic-temperature-tendency`
and `energy-conserving-omega-alpha-coupling`, which edit existing sigma-omega
quadrature or pressure-work energetics. Here the incumbent sigma-dot and
pressure tendencies remain unchanged.

The mechanism is deliberately extratropical and thermal, making it decorrelated
from the tropical WTG proposal and from the Rossby-wave-source vorticity
proposal. The implementation should be kept bounded and low-mode; a full
elliptic omega solve would be too broad and expensive for one candidate.

## Evaluator Notes

### 2026-06-25T01:43:53Z

Decision: move to `scrap`; ranked 2 of 3 current proposals, behind tropical
WTG and ahead of the RWS vorticity correction only because it is thermodynamic
rather than a direct vorticity edit.

The cited QG literature supports Q-vectors and the omega equation as
diagnostics for midlatitude vertical motion, ageostrophic circulation, and
frontogenesis. It does not support the proposed reduced `-div(Q)` field as a
standalone prognostic heating term in this primitive-equation model. A proper
QG response would require a balanced omega solve and consistent thermodynamic
and mass-continuity coupling. This proposal explicitly avoids that solve and
instead adds a capped thermal tendency while leaving `sigma_dot`,
`log_surface_pressure`, divergence, pressure-gradient coupling, and the
accepted mass-DSE transport unchanged.

Local history further lowers the priority. The active staging queue already has
more coherent omega/pressure-work ideas: same-time analysis omega spinup,
theta-only omega spinup, log-sigma adiabatic quadrature, and discrete
omega-alpha/geopotential coupling. Several recent pressure, sigma, and thermal
forcing follow-ups were clean but negative or subthreshold, and direct pressure
forcing damaged MSLP/Z500 guardrails. Compared with those staged alternatives,
this proposal is a broader diagnostic-to-forcing shortcut with high risk of
double-counting frontogenetic vertical-motion effects already represented by
the primitive equations.

Do not keep this in the active queue without a prior read-only diagnostic
showing a systematic extratropical Q-vector/omega phase error that the existing
staged omega or pressure-work proposals cannot test.
