---
schema_version: 1
slug: theta-consistent-held-suarez-forcing
title: Relax Weak Held-Suarez Forcing in Potential Temperature Space
status: ready
created_at: 2026-06-18T22:22:10Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
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

# Relax Weak Held-Suarez Forcing in Potential Temperature Space

## Hypothesis

The incumbent now uses a potential-temperature form for the dry thermodynamic
tendency, but the accepted weak Held-Suarez forcing still relaxes temperature
directly toward the analytic equilibrium temperature. In a dry hydrostatic
system, potential temperature is the materially conserved variable away from
sources and sinks. Applying the existing weak relaxation in potential
temperature space may make the added thermal source more consistent with the
accepted theta tendency and reduce the small early `mean_sea_level_pressure`
and `geopotential_500` side effects measured after the theta candidate was
accepted.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_hs`.
Preserve the incumbent DFI, weak-HS coefficient values, equilibrium
temperature formula, log-pressure initialization, hydrostatic layer
initialization, symmetric exact-Coriolis split, stability-aware residual
correction, Richardson 10 m wind diagnostic, horizontal diffusion, vertical
coordinate, output variables, and fixed evaluation protocols.

Add an opt-in Held-Suarez forcing path:

- diagnose nodal sigma pressure as `sigma * surface_pressure` inside the
  tracer-safe weak-HS forcing wrapper;
- convert current nodal temperature and Held-Suarez equilibrium temperature to
  dry potential temperature using the same reference pressure and kappa as the
  accepted theta tendency;
- relax `theta_current` toward `theta_equilibrium` with the existing
  temperature-relaxation coefficient `kt()`, without changing its timescale or
  adding a parameter sweep;
- convert the resulting theta tendency back to a temperature tendency with the
  local Exner factor;
- leave vorticity, divergence, `log_surface_pressure`, humidity tracers,
  Coriolis splitting, residual correction, Richardson 10 m wind packing, and
  pressure-level interpolation unchanged;
- use the same forcing formulation in DFI and positive-time rollout so this is
  a forcing-variable test, not a DFI merge variant;
- fall back to the incumbent temperature-space forcing if pressure, theta, or
  converted tendency diagnostics are nonfinite.

This candidate does not add new radiation, solar phase, humidity coupling,
Rayleigh drag, or tuned relaxation amplitudes. It only changes the variable in
which the already accepted weak thermal relaxation is applied.

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
  - None. `DycoreModel.forecast`, input channels, output channels, lead times,
    metrics, splits, and deterministic gates remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent flag except the new
    theta-space weak-HS forcing selector.
  - Unit-test that theta-space forcing is finite for positive pressure and is an
    exact no-op relative to incumbent when current temperature equals the
    equilibrium temperature.
  - Verify the forcing changes only `temperature_variation` tendency and leaves
    vorticity, divergence, `log_surface_pressure`, and tracers unchanged.
  - Verify the finite fallback returns the incumbent temperature-space tendency
    for nonfinite pressure diagnostics.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 1 to 7 if part of
    the accepted theta candidate's pressure/thickness side effect comes from a
    temperature-space weak thermal source.
  - `2m_temperature` at medium leads if the theta-consistent source preserves
    the accepted thermal gain while reducing lower-column imbalance.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain near the incumbent because
    prognostic wind equations, Coriolis splitting, residual correction, and the
    Richardson 10 m diagnostic are unchanged.
- Possible regressions:
  - The Held-Suarez equilibrium was designed as a temperature relaxation target,
    so transforming it to theta space may weaken or vertically redistribute a
    useful empirical correction.
  - Any thermal-source change can indirectly perturb pressure gradients and
    regress early MSLP or Z500 despite leaving mass continuity unchanged.

## Risks

- Numerical stability:
  - Low to moderate. The forcing is bounded by the existing weak-HS timescales,
    but it is applied every DFI and rollout step.
- Compute cost:
  - Low. It adds local pressure/theta conversions inside an existing forcing
    wrapper and does not change grid size, lead count, or worker count.
- Data leakage:
  - None. The mechanism uses only forecast state, fixed constants, and the
    already accepted analytic Held-Suarez equilibrium.
- Physical plausibility:
  - Moderate to high. Potential temperature is the dry adiabatic thermodynamic
    invariant, but Held-Suarez forcing itself is idealized rather than real
    weather physics.
- Rollback complexity:
  - Low. Remove one forcing selector/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_hs`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_hs --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_hs --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the accepted
    temperature-space weak-HS source is already better matched to the fixed
    WeatherBench2 scores. Any early MSLP, Z500, or wind guardrail failure would
    show that theta-space forcing disrupts the accepted balance.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` composes
    the accepted weak Held-Suarez thermal forcing through
    `_TracerSafeHeldSuarezForcingSigma` and currently computes a direct
    temperature relaxation tendency.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md`
    accepted the theta-form thermodynamic tendency and recorded small early
    MSLP/geopotential costs within guardrails.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_20-37-51_theta-skew-symmetric-scalar-advection/scoring_notes.md`
    rejected the scalar split-form follow-up as slightly negative, so this
    proposal targets thermal forcing consistency rather than advection symmetry.
  - Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of
    dynamical cores of atmospheric general circulation models. Bulletin of the
    American Meteorological Society.
    https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
  - Polichtchouk, I., Malardel, S., and Diamantakis, M. 2020. Potential
    temperature as a prognostic variable in hydrostatic semi-implicit
    semi-Lagrangian IFS. ECMWF Technical Memorandum 869.
    https://www.ecmwf.int/en/elibrary/81180-potential-temperature-prognostic-variable-hydrostatic-semi-implicit-semi
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
    to Geophysics, second edition. Springer.
    https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is not a duplicate of accepted `potential-temperature-thermodynamic-tendency`
because it leaves the primitive-equation thermodynamic transport path intact and
changes only the already accepted weak-HS forcing variable. It is not a repeat
of rejected or scrapped Held-Suarez amplitude, mass-neutral weak-HS, solar, or
humidity-radiative proposals because it does not add a new thermal source,
remove the accepted global source, introduce solar phase, or couple to passive
humidity. It also avoids the freshly rejected scalar split-form idea: the
advection operator and scalar transport remain incumbent.

The proposal directly learns from the accepted theta result: the measured
primary gain was strong, but the remaining guardrail-relevant cost was small
early MSLP/geopotential movement. A theta-consistent weak thermal source is a
bounded current-incumbent follow-up that could reduce that side effect while
preserving the accepted Richardson 10 m wind behavior.

## Evaluator Notes

### 2026-06-18T22:26:00Z

Decision: move to `ready`; ranked 1 of 3 new proposals.

This is the best next model-selection target. It is a direct follow-up to the
accepted theta thermodynamic tendency and tests whether the remaining weak
Held-Suarez source should use the same dry thermodynamic variable. The source
inspection supports the proposal premise: the current weak-HS wrapper still
relaxes nodal temperature directly, while the incumbent primitive-equation
thermal tendency now transports potential temperature. The implementation
surface is small, side-by-side, and compatible with the fixed forecast API,
output variables, splits, metrics, DFI span, residual correction, Richardson
10 m wind diagnostic, and deterministic gates.

This is not an output-only metric-targeting change and is not a duplicate of
the freshly rejected scalar split-form experiment. It should give a clean
answer about the accepted theta candidate's small day-1 MSLP/geopotential
side effect without changing advection symmetry, diffusion placement, or
initialization.

Concerns to carry into implementation: Held-Suarez was originally formulated
as a temperature relaxation, so converting the equilibrium target into theta
space may weaken a useful empirical thermal source. The Implementer should not
tune relaxation coefficients, should use the same forcing path in DFI and
positive-time rollout, and should keep a finite fallback to the incumbent
temperature-space forcing. The Scorer should watch early MSLP and Z500
carefully because the theta incumbent already showed small but repeatable
pressure/geopotential sensitivity.
