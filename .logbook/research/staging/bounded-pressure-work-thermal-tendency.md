---
schema_version: 1
slug: bounded-pressure-work-thermal-tendency
title: Bound Local Pressure-Work Heating in the Theta Tendency
status: staging
created_at: 2026-06-20T04:46:29Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
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

# Bound Local Pressure-Work Heating in the Theta Tendency

## Hypothesis

The accepted theta tendency still adds the existing local pressure-work
temperature tendency from sigma-coordinate `omega / p` diagnostics. In a coarse
sigma model with zero orography and finite pressure-level initialization,
localized pressure-work spikes can create lower-column thermal drift that later
appears in `2m_temperature`, MSLP, and Z500. A conservative local cap on only
the pressure-work contribution should reduce rare thermodynamic outliers while
leaving theta transport, vertical advection, winds, surface pressure, and
residual memory on the incumbent path.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_pressure_work_cap`.
Preserve the full incumbent except for one opt-in bound inside the
thermodynamic pressure-work helper.

For this candidate only:

- add a selector in `PrimitiveEquationsSigma` for bounded pressure-work heating;
- compute the incumbent adiabatic pressure-work tendency exactly as today;
- clip only the local pressure-work contribution to a fixed physically broad
  tendency range, for example an equivalent `[-8 K/day, 8 K/day]` in SI units
  after nondimensional conversion;
- keep horizontal theta transport, vertical theta transport, scalar advection,
  momentum tendencies, `log_surface_pressure` tendency, weak-HS forcing,
  diffusion, DFI, and residual correction unchanged;
- use finite diagnostics so nonfinite pressure, `omega / p`, or converted
  tendency falls back to the incumbent uncapped pressure-work path;
- apply the same selector in DFI and positive-time rollout for thermodynamic
  consistency.

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
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead schedule, and
    metrics remain unchanged.
- Tests to update:
  - Unit-test cap conversion from K/day to model units.
  - Verify sub-cap pressure-work tendencies are unchanged.
  - Verify over-cap positive and negative tendencies are clipped and finite.
  - Verify horizontal/vertical theta transport and non-thermal state leaves are
    unchanged by the selector.
  - Verify the candidate factory preserves every incumbent option except the
    pressure-work cap selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and long leads if rare lower-column
    pressure-work spikes contribute to thermal drift after residual decay.
  - MSLP and `geopotential_500` if bounded thermal thickness evolution reduces
    pressure-gradient adjustment noise.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because wind
    control variables and surface wind diagnostics are unchanged.
- Possible regressions:
  - Pressure work is a real compressional heating/cooling term; clipping it can
    remove physically meaningful balanced thermodynamic evolution.
  - If spikes are not material under the accepted off-centered incumbent, the
    cap will be neutral or slightly harmful.

## Risks

- Numerical stability:
  - Low to moderate. The cap is stabilizing but changes thermal tendencies in
    DFI and rollout.
- Compute cost:
  - Low. It adds local clipping and unit conversion, with no extra transforms or
    rollout steps.
- Data leakage:
  - None. It uses only current forecast state and fixed physical constants.
- Physical plausibility:
  - Moderate. Bounded tendencies are common numerical safeguards, but the cap
    must be broad enough to avoid acting as a tuned thermal parameterization.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_pressure_work_cap`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_pressure_work_cap --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_pressure_work_cap --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show pressure-work
    outliers are not a material remaining error. Any early MSLP, Z500, or wind
    guardrail failure would show the cap damages balanced thermodynamics.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  computes `nodal_temperature_adiabatic_tendency` and the sigma-coordinate
  `T * omega / p` pressure-work helper used by the accepted theta tendency.
- Dynamaxx history:
  `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md`
  accepted the theta-form tendency but noted small pressure/geopotential costs,
  motivating a narrow pressure-work safeguard rather than another theta
  transport rewrite.
- Dynamaxx research:
  `.logbook/research/staging/log-sigma-adiabatic-temperature-tendency.md`
  changes the quadrature of the adiabatic term; this proposal keeps the
  quadrature and adds only a finite local bound.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Laprise, R. 1992. The Euler Equations of Motion with Hydrostatic Pressure as
  an Independent Variable. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C0197:TEEOMW%3E2.0.CO;2
- Polichtchouk, I., Malardel, S., and Diamantakis, M. 2020. Potential
  temperature as a prognostic variable in hydrostatic semi-implicit
  semi-Lagrangian IFS. ECMWF Technical Memorandum 869.
  https://www.ecmwf.int/en/elibrary/81180-potential-temperature-prognostic-variable-hydrostatic-semi-implicit-semi

## Researcher Notes

This is not a variant of divergence-zero-mode projection, passive humidity
routing, or near-surface residual memory. It also does not duplicate staged
`log-sigma-adiabatic-temperature-tendency`, `theta-upwind-vertical-advection`,
or `full-state-theta-thermodynamic-tendency`: those alter transport variables,
vertical advection, or adiabatic quadrature. This proposal keeps the accepted
theta transport formulation and only bounds the local pressure-work term that
can create extreme compressional heating or cooling.

## Evaluator Notes

### 2026-06-20T04:52:50Z

Decision: move to `staging`, not `ready`.

The hook is real and local: the accepted theta tendency still calls the
existing sigma-coordinate adiabatic pressure-work helper, and source inspection
confirms the pressure-work contribution can be isolated without changing
vorticity, divergence, `log_surface_pressure`, residual memory, or output
packing. Literature supports the underlying thermodynamics: pressure work is a
physical part of the heat equation, and potential-temperature formulations are
well motivated for adiabatic hydrostatic dynamics.

The proposal should not be the next implementation because the cap itself is
more of an empirical limiter than a supported discretization change. There is
no local diagnostic evidence here that rare pressure-work spikes are the
current incumbent's limiting error, and clipping compressional heating/cooling
can remove balanced adiabatic evolution. It also sits near several staged
theta/adiabatic-family fallbacks, including log-sigma adiabatic quadrature and
full-state theta transport, so it should wait until there is stronger evidence
that the remaining thermal drift is specifically an outlier problem rather than
a matched-coordinate or transport-form issue.

If selected later, keep the cap fixed and physically broad, apply it only to
the pressure-work contribution after computing the incumbent tendency, preserve
uncapped fallback on any nonfinite diagnostic, and require tests proving all
non-thermal state tendencies are unchanged.
