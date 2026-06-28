---
schema_version: 1
slug: full-state-theta-thermodynamic-tendency
title: Transport Full-State Potential Temperature in the Theta Tendency
status: staging
created_at: 2026-06-18T22:22:10Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Transport Full-State Potential Temperature in the Theta Tendency

## Hypothesis

The accepted theta tendency improved the current incumbent, but its localized
implementation computes potential temperature from `temperature_variation` and
then adds the existing adiabatic temperature tendency. Continuous dry
thermodynamics treats potential temperature of the full temperature field as
the materially conserved variable. A side-by-side formulation that transports a
full-state theta anomaly, including a fixed reference theta profile, may reduce
remaining cancellation error in lower- and middle-tropospheric thermal
evolution and improve `2m_temperature`, `geopotential_500`, and
`mean_sea_level_pressure` without changing accepted wind diagnostics.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_total_theta`.
Preserve the incumbent initialization, DFI span, weak Held-Suarez forcing,
log-pressure initialization, hydrostatic layer initialization, symmetric
exact-Coriolis split, stability-aware residual correction, Richardson 10 m wind
diagnostic, vertical coordinate, horizontal diffusion, output variables, and
fixed evaluation protocols.

Add a second opt-in theta tendency formulation for sigma coordinates:

- diagnose nodal full temperature as `T_ref + temperature_variation`;
- diagnose nodal pressure as `sigma * surface_pressure`;
- compute full dry potential temperature from full temperature and local
  pressure;
- subtract a fixed horizontally uniform reference theta profile derived from
  `T_ref`, sigma centers, and a reference surface pressure, so the transported
  scalar is a theta anomaly with a physically meaningful vertical reference;
- advect the full-state theta anomaly with the incumbent horizontal and
  vertical transport operators, including the reference-theta vertical
  stratification term when vertical motion crosses sigma layers;
- convert the transported theta tendency back to a temperature tendency with
  the local Exner factor and keep the existing pressure-work coupling from the
  incumbent adiabatic helper;
- leave vorticity, divergence, `log_surface_pressure`, tracers, Coriolis,
  residual correction, 10 m wind diagnostic, and pressure-level output packing
  unchanged;
- use the same formulation in DFI and positive-time rollout;
- fall back to the accepted theta-anomaly formulation if pressure, reference
  theta, or converted tendencies are nonfinite.

This is a thermodynamic-variable consistency candidate. It does not change
scalar advection symmetry, vertical-advection scheme, initialization, weak-HS
forcing, diffusion, or the forecast contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, inputs, outputs, lead times, metrics, splits,
    and deterministic gates remain unchanged.
- Tests to update:
  - Unit-test full-temperature theta conversion and reference-theta anomaly
    construction for finite pressure.
  - Verify the default accepted theta formulation remains unchanged.
  - Verify the full-state theta option changes only
    `temperature_variation` tendency from `explicit_terms`; vorticity,
    divergence, `log_surface_pressure`, tracers, and implicit terms remain
    shape-compatible and finite.
  - Verify a horizontally uniform full-state theta anomaly has no horizontal
    advective tendency under zero flow and that nonfinite diagnostics fall back
    to the accepted theta path.
  - Verify the candidate factory preserves all incumbent flags except the new
    full-state theta tendency selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium leads if the accepted theta gain was limited by
    omitting the reference thermal state from theta transport.
  - `geopotential_500` and `mean_sea_level_pressure` if the full-state theta
    anomaly yields cleaner hydrostatic thickness and pressure-gradient balance.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to the incumbent because wind
    initialization, Coriolis splitting, and the Richardson 10 m wind diagnostic
    are unchanged.
- Possible regressions:
  - The accepted anomaly-only theta formulation may already be empirically
    better matched to the semi-implicit split, and adding reference-theta
    vertical transport can overcorrect thermal stratification.
  - Keeping the existing pressure-work helper while changing theta transport
    must avoid double counting reference-state adiabatic effects.

## Risks

- Numerical stability:
  - Moderate. The change touches every thermodynamic tendency evaluation in DFI
    and rollout, though only through a side-by-side option.
- Compute cost:
  - Low to moderate. It adds pressure/theta conversions and reference-profile
    algebra but no extra rollout steps or resolution.
- Data leakage:
  - None. The mechanism uses only forecast state, fixed sigma geometry, and
    physical constants.
- Physical plausibility:
  - High for full potential temperature as the dry thermodynamic variable;
    moderate for the discrete reference-anomaly treatment because it must match
    the existing sigma-coordinate continuity and semi-implicit partition.
- Rollback complexity:
  - Low. Remove one formulation selector/helper, one factory/export, one
    registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_total_theta`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_total_theta --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_total_theta --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the accepted
    anomaly-only theta tendency is already the better discrete balance. Any
    early MSLP, Z500, or 10 m wind guardrail failure would show that the
    full-state theta reference treatment disrupts incumbent balance.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
    implements the accepted `TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE`
    path and computes theta from `temperature_variation`.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md`
    accepted theta-form thermal tendency with strong iteration and validation
    gains but small early MSLP/geopotential costs.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_20-37-51_theta-skew-symmetric-scalar-advection/scoring_notes.md`
    found the scalar split-form follow-up nearly neutral but slightly harmful,
    so this proposal changes the thermodynamic variable content rather than the
    advection operator.
  - Polichtchouk, I., Malardel, S., and Diamantakis, M. 2020. Potential
    temperature as a prognostic variable in hydrostatic semi-implicit
    semi-Lagrangian IFS. ECMWF Technical Memorandum 869.
    https://www.ecmwf.int/en/elibrary/81180-potential-temperature-prognostic-variable-hydrostatic-semi-implicit-semi
  - Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
    conserving vertical finite-difference scheme and hybrid vertical
    coordinates. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
    to Geophysics, second edition. Springer.
    https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is a direct current-incumbent follow-up to the accepted theta tendency, but
it is not a duplicate. The accepted candidate changed the transported
thermodynamic variable using `temperature_variation`; this candidate tests
whether the full thermal state and reference theta profile should participate
in the theta anomaly that is transported. It is not the rejected
`theta-skew-symmetric-scalar-advection` idea because it keeps the advection
operator unchanged. It is not active staged `theta-upwind-vertical-advection`
because it does not change vertical advection, and it is not active staged
`theta-diffusion-dissipative-heating` because it adds no positive heating
source.

It also avoids the older negative initialization family. Initial Dinosaur state,
DFI span, log-pressure remap, hydrostatic layer initialization, and pressure-
level output interpolation stay on the incumbent path. The only scientific
question is whether the accepted theta thermodynamic tendency should transport
anomaly theta of the full state rather than anomaly temperature converted to
theta.

## Evaluator Notes

### 2026-06-18T22:26:00Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

This is scientifically coherent and more physically fundamental than an
output-only diagnostic: the accepted theta candidate currently computes theta
from `temperature_variation`, while dry thermodynamics naturally points to the
potential temperature of the full state. The idea is not a duplicate of the
freshly rejected skew scalar advection candidate because it leaves the
horizontal scalar-advection operator unchanged, and it is not a duplicate of
the staged theta upwind or diffusion-heating ideas.

Keep it staged rather than ready because the implementation risk is materially
higher than the theta-consistent weak-HS proposal. The proposal would touch the
primitive-equation thermodynamic tendency used in both DFI and rollout, and the
reference-state treatment must avoid double-counting vertical reference-theta
transport or pressure-work terms already handled by the incumbent sigma
equations. A small mismatch could disrupt the semi-implicit balance that the
accepted theta candidate preserved, especially given the current incumbent's
repeatable day-1 MSLP and Z500 sensitivity.

This should remain a strong fallback if the lower-risk forcing-consistency
experiment is rejected cleanly. If promoted, the implementation should be kept
narrowly side-by-side, preserve the accepted theta path as fallback, and add
tests that isolate `temperature_variation` tendency changes from vorticity,
divergence, log-surface-pressure, tracer, implicit-term, and output-packing
behavior.
