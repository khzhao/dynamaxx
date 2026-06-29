---
schema_version: 1
slug: ekman-pressure-work-thermal-coupling
title: Ekman Pressure-Work Thermal Coupling
status: ready
created_at: 2026-06-29T12:56:30Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
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

# Ekman Pressure-Work Thermal Coupling

## Hypothesis

The incumbent accepted a coupled Ekman lower-boundary closure that changes
low-level wind and applies a small mass-neutral `log_surface_pressure`
increment. That pressure increment is currently not paired with any local dry
adiabatic temperature response. Adding a tightly capped, area-neutral thermal
pressure-work response to the already accepted pressure increment should improve
`mean_sea_level_pressure`, `geopotential_500`, and possibly `2m_temperature`
without changing the stress, pumping, wind diagnostic, evaluation contract, or
available fields.

## Mechanism

Add one opt-in descendant of `dino_ri2m_ekman_coupled`, for example
`dino_ri2m_ekman_pwork`.

For the candidate only:

- reuse the accepted `_ekman_coupled_surface_step_filter` unchanged through its
  stress, wind-increment, Ekman-transport, and `log_pressure_increment`
  calculation;
- after the accepted pressure increment is finalized, compute a dry adiabatic
  temperature increment proportional to local `kappa * T * delta_log_p`;
- apply the increment only through the existing lower-layer Ekman vertical
  taper, with zero layer mean removed using quadrature weights;
- cap the per-step temperature increment to a small fixed value, such as
  `0.02 K`, before adding it to `temperature_variation`;
- fall back exactly to the incumbent if pressure, temperature, taper, cap, or
  corrected state diagnostics are nonfinite;
- leave vorticity, divergence, `log_surface_pressure`, tracers, residual memory,
  Richardson 2 m temperature, Richardson 10 m wind, target variables, splits,
  lead times, and metrics unchanged.

This is not a retune of coupled Ekman stress-pumping: the accepted wind stress
and pressure pumping are fixed. The only new mechanism is thermodynamic
consistency for the incumbent pressure increment.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model derived from `ekman_coupled_dinosaur_dycore_model()`.
- API changes:
  - None.
- Tests to update:
  - Verify zero pressure increment gives exact incumbent thermal state.
  - Verify positive and negative pressure increments produce bounded opposite
    thermal responses.
  - Verify layer mean removal, cap behavior, finite fallback, and registry flags.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium leads if the
    accepted pressure pumping is slightly thermodynamically inconsistent.
  - `2m_temperature` if lower-column compression/expansion errors leak into the
    screen diagnostic.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because wind stress and the 10 m diagnostic are
    unchanged.
- Possible regressions:
  - Early MSLP or Z500 can regress if the accepted pressure increment benefited
    from being dynamically cold-neutral.

## Risks

- Numerical stability:
  - Low to moderate; the increment is local, capped, and has exact fallback.
- Compute cost:
  - Negligible relative to the incumbent Ekman filter.
- Data leakage:
  - None. It uses only current forecast temperature, pressure increment, sigma
    geometry, and fixed constants.
- Physical plausibility:
  - Moderate to high as a reduced dry pressure-work correction, but it is not a
    complete boundary-layer thermodynamic scheme.
- Rollback complexity:
  - Low.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_ekman_pwork`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_pwork --workers <worker_count>`.
  - Support requires at least `+0.002` primary-score delta against cached
    `dino_ri2m_ekman_coupled`, clean diagnostics, and no fixed RMSE guardrail
    failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_ekman_pwork --workers <worker_count>`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, or any short-lead mass-field
    guardrail regression, would show the added pressure-work response is not a
    useful remaining error source.

## Citations

- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press.
- Dynamaxx history:
  `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/decision.md`.

## Researcher Notes

Negative evidence from `stability-veered-10m-wind-diagnostic` is treated as
wind-output evidence only; this proposal does not rotate or otherwise alter
10 m wind output. It also avoids absent soil moisture, broad PV balancing, and
Z500-only output diagnostics.

## Evaluator Notes

### 2026-06-29T13:00:56Z

Decision: move to `ready`; ready rank `1 of 1`; ranked `1 of 2` in this triage
pass.

This is the best next experiment among the two reviewed proposals. It is a
small, falsifiable extension of the accepted `dino_ri2m_ekman_coupled`
mechanism: keep the stress, Ekman transport, pressure increment, wind
diagnostic, output variables, and evaluation contract fixed, and test only
whether the accepted lower-boundary `log_surface_pressure` increment needs a
matching dry adiabatic thermal response. The implementation surface is
localized to the existing Ekman step-filter path plus a side-by-side factory,
registry entry, and focused tests.

Duplicate risk is acceptable. This is not a rerun of the accepted coupled Ekman
closure because it leaves the accepted momentum and pressure increments fixed.
It is also narrower than staged `bounded-pressure-work-thermal-tendency` and
`energy-conserving-omega-alpha-coupling`: those touch broad thermodynamic
pressure-work/operator paths, while this proposal couples temperature only to
the already accepted, capped, area-neutral Ekman pressure increment. The staged
mass-only `ekman-pumping-logp-tendency` and stress-only
`bulk-aerodynamic-surface-stress` concerns were resolved by the now-accepted
coupled incumbent; this proposal tests a remaining thermodynamic consistency
hole rather than another boundary-layer drag or pumping retune.

Pressure-work history is the main caution. `hydrostatic-balanced-theta-pressure-work`
had large aggregate iteration signal but failed short-lead MSLP/Z500 guardrails,
and the ramped/column-neutral pressure-work follow-up was clean but neutral.
That argues for strict bounds, layer-mean removal, exact finite fallback, and no
validation unless the fixed iteration gate promotes. The proposal already
includes those safeguards and should be implemented as a single predeclared
candidate, not as an amplitude sweep.
