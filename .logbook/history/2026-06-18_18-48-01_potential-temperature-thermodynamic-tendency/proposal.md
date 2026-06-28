---
schema_version: 1
slug: potential-temperature-thermodynamic-tendency
title: Use Potential Temperature for the Thermodynamic Tendency
status: ready
created_at: 2026-06-18T18:48:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind
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

# Use Potential Temperature for the Thermodynamic Tendency

## Hypothesis

The incumbent evolves temperature with separate horizontal advection, vertical
advection, and adiabatic pressure-work terms. In continuous dry adiabatic
motion, potential temperature is materially conserved, so computing the
thermodynamic tendency through potential temperature may reduce numerical
cancellation error between advective and compressional terms. This could improve
`2m_temperature`, `geopotential_500`, and `mean_sea_level_pressure` after the
accepted near-surface residuals decay, without changing wind initialization,
surface residual timescales, 10 m wind diagnostics, pressure remapping, or the
fixed evaluation contract.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency`.
Preserve the incumbent DFI, weak Held-Suarez forcing, log-pressure
initialization, hydrostatic layer initialization, symmetric exact-Coriolis
split, stability-aware near-surface residual correction, Richardson 10 m wind
diagnostic, horizontal diffusion, vertical coordinate, and output variables.

Add an opt-in thermodynamic equation path for sigma coordinates:

- diagnose nodal pressure as `p = sigma * surface_pressure` from the current
  state;
- compute dry potential temperature `theta = T * (p0 / p) ** kappa`, using the
  same `kappa` and pressure units as the primitive-equation physics specs;
- compute horizontal and vertical transport on a theta anomaly rather than on
  temperature variation;
- convert the resulting theta tendency back to a temperature tendency with the
  local Exner factor, adding the algebraically required pressure-work coupling
  from the model's existing `omega / p` diagnostic;
- leave vorticity, divergence, `log_surface_pressure`, humidity tracers,
  Coriolis splitting, DFI span, output interpolation, and near-surface
  diagnostics on the incumbent path;
- use the same candidate equation inside DFI and positive-time rollout so this
  is a thermodynamic-discretization test, not a DFI merge variant;
- fall back to the incumbent temperature tendency if any pressure or theta
  diagnostic is nonfinite.

This is not a potential-temperature initialization remap. The initial Dinosaur
state remains identical to the incumbent; only the positive-time and DFI
thermodynamic tendency formulation changes.

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
  - None. `DycoreModel.forecast`, inputs, outputs, lead times, and fixed
    protocols remain unchanged.
- Tests to update:
  - Unit-test theta conversion and inverse conversion for finite pressure.
  - Verify the option changes only the temperature tendency from
    `explicit_terms`; vorticity, divergence, `log_surface_pressure`, tracers,
    and implicit terms remain shape-compatible and finite.
  - Verify a uniform theta field has zero advective theta tendency under zero
    velocity.
  - Verify the candidate factory preserves all incumbent flags except the new
    thermodynamic-tendency selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3 to 15 if remaining thermal drift is partly
    caused by temperature-form pressure-work cancellation error.
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if cleaner
    temperature thickness evolution improves hydrostatic balance.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain near the accepted incumbent because
    wind state, Coriolis splitting, and the Richardson 10 m diagnostic are
    unchanged.
- Possible regressions:
  - The incumbent temperature-form discretization may be better matched to the
    existing semi-implicit linearization than a theta-form explicit tendency.
  - Thermal tendency changes can indirectly perturb pressure gradients and
    degrade early wind or Z500 guardrails even without direct wind changes.

## Risks

- Numerical stability:
  - Moderate. The tendency is algebraically motivated but touches every DFI and
    rollout step.
- Compute cost:
  - Low to moderate. It adds nodal pressure/theta conversions and reuses
    existing advection helpers.
- Data leakage:
  - None. The mechanism uses only forecast state variables and fixed constants.
- Physical plausibility:
  - High for the dry adiabatic invariant; moderate for the discrete conversion
    because it must stay consistent with the incumbent sigma continuity and
    semi-implicit split.
- Rollback complexity:
  - Low. Remove one equation option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the incumbent
    temperature tendency is not a material remaining error source. Any early
    `10m_u_component_of_wind`, Z500, or MSLP guardrail failure would show the
    theta tendency disrupts the accepted balance.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
    computes temperature horizontal advection, vertical advection, and
    adiabatic `omega / p` tendencies separately in `PrimitiveEquationsSigma`.
  - Dynamaxx history:
    `.logbook/history/2026-06-17_10-15-26_potential-temperature-logp-initialization/decision.md`
    rejected potential-temperature pressure-to-sigma initialization with
    iteration delta `-0.0009134462392161868`; this proposal keeps incumbent
    initialization and changes only the rollout thermodynamic tendency.
  - ECMWF Technical Memorandum 869, Polichtchouk, Malardel, and Diamantakis,
    "Potential temperature as a prognostic variable in hydrostatic
    semi-implicit semi-Lagrangian IFS", documents an IFS hydrostatic
    formulation using potential temperature and notes its dry adiabatic
    conservation property. https://www.ecmwf.int/en/elibrary/81180-potential-temperature-prognostic-variable-hydrostatic-semi-implicit-semi
  - NOAA/AOML potential temperature notes describe potential temperature as
    conserved for adiabatic parcel motion.
    https://www.aoml.noaa.gov/ftp/hrd/annane/prelim_notes/Potential_Temperature.pdf
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
    to Geophysics, second edition. Springer.
    https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of active staged
`log-sigma-adiabatic-temperature-tendency`, which changes a quadrature inside
the existing temperature-form `omega / p` helper. This proposal changes the
thermodynamic transported variable to potential temperature while preserving
the incumbent mass and wind equations.

It is also distinct from staged `skew-symmetric-horizontal-scalar-advection` and
`upwind-vertical-advection-rollout`, which change advection operators. This
candidate keeps those operators and changes the thermodynamic variable passed
through them. It explicitly incorporates negative evidence from rejected
temperature initialization and reference-profile experiments: the initial state
and reference profile remain incumbent-compatible, and the expected signal must
come from reduced rollout thermal cancellation error.

## Evaluator Notes

### 2026-06-18T18:47:01Z

Decision: move to `ready` as the single recommended next implementation target.

Ranking rationale: this is the strongest current candidate after reconsidering
the empty ready queue and the active staged backlog. It targets a remaining
non-wind error family after the accepted Richardson 10 m wind diagnostic
improved the primary score almost entirely through `10m_u_component_of_wind`
while leaving `2m_temperature`, `geopotential_500`, and
`mean_sea_level_pressure` effectively unchanged. The proposal is physically
grounded in dry potential-temperature conservation, uses only forecast-state
variables and fixed constants, preserves the accepted stability-aware surface
residual and Richardson 10 m wind diagnostic, and is already written against
the current incumbent name. Its implementation surface is moderate but
localized to the thermodynamic tendency path and side-by-side registry/tests.

It ranks ahead of the leading staged `analysis-omega-vertical-motion-spinup`
fallback because omega spinup requires new input-channel plumbing,
pressure-to-sigma remapping, a private anomaly or wrapper state, and careful
DFI/time-origin handling. It ranks ahead of staged diffusion-heating,
solar/humidity thermal forcing, boundary-layer drag, and nonlinear
anti-aliasing ideas because those either add empirical positive-time forcing,
spend wind guardrail margin, or have direct family evidence that is negative or
only subthreshold. It also ranks ahead of narrower staged
`log-sigma-adiabatic-temperature-tendency` because this proposal tests the
coherent materially conserved dry thermodynamic variable rather than swapping
one quadrature measure inside an otherwise matched sigma-coordinate
`omega / p` approximation.

Non-duplication checks: this is not a duplicate of accepted
`stability-aware-surface-residual-decay` or
`surface-layer-richardson-wind-diagnostic`, which are output/near-surface
diagnostic improvements and do not change prognostic thermodynamic transport.
It is not a duplicate of rejected
`potential-temperature-logp-initialization`, because that experiment changed
the initialization remap and scored a small negative iteration delta, while
this proposal keeps the incumbent initial state and changes only DFI/rollout
thermodynamic tendency formulation. It is not a duplicate of staged
`log-sigma-adiabatic-temperature-tendency`, which changes only the adiabatic
temperature quadrature helper; this proposal changes the transported
thermodynamic variable and then converts back consistently to temperature.
It is also not a duplicate of rejected or staged scalar-advection/dealiasing
candidates because their mechanism is the advection operator or modal support,
not the dry thermodynamic invariant.
