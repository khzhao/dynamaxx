---
schema_version: 1
slug: passive-humidity-positivity-limiter
title: Floor Passive Humidity Before Geopotential Diagnostics
status: ready
created_at: 2026-06-16T21:09:23Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs
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

# Floor Passive Humidity Before Geopotential Diagnostics

## Hypothesis

The incumbent keeps `use_humidity_in_dynamics=False`, but when specific-humidity
pressure-level channels are present it still carries humidity as a passive tracer
and uses that tracer in hydrostatic geopotential diagnostics through virtual
temperature. Spectral tracer transport can create undershoots around sharp moist
gradients. Negative specific humidity is nonphysical, and even small negative
values can bias virtual temperature and therefore `geopotential_500` without
improving the dry dynamics.

A diagnostic-time nonnegative floor on passive humidity should reduce this
unphysical hydrostatic diagnostic pathway while leaving vorticity, divergence,
temperature, surface pressure, DFI, weak thermal Held-Suarez relaxation, and
near-surface residual correction unchanged.

## Mechanism

Add an optional adapter flag such as
`apply_passive_humidity_positivity_limiter`. When enabled and the Dinosaur
trajectory contains `specific_humidity` as a tracer, convert only that tracer to
nodal values during `dinosaur_state_to_weather_state`, apply `jnp.maximum(q,
0.0)` before calling `primitive_equations.get_geopotential_on_sigma` and before
including humidity in sigma-to-pressure diagnostic interpolation, and leave the
stored prognostic trajectory untouched.

The candidate should be a side-by-side model named
`dinosaur_dfi_surface_residual_weak_hs_qpos`. It must preserve
`use_humidity_in_dynamics=False`; this proposal is not a revival of moist virtual
temperature dynamics.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for
    `dinosaur_dfi_surface_residual_weak_hs_qpos`.
- API changes:
  - None. Forecast shape, variables, leads, deterministic behavior, and metrics
    remain unchanged.
- Tests to update:
  - Unit-test the helper that floors negative humidity and leaves positive and
    missing humidity unchanged.
  - Test that the candidate factory preserves incumbent DFI, weak Held-Suarez,
    near-surface residual correction, and `use_humidity_in_dynamics=False`.
  - Add registry/dependency smoke coverage for the new model name.
  - Add a small finite forecast test with a humidity channel if existing fixtures
    make that cheap.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium and long leads if passive humidity spectral
    undershoots are contaminating virtual-temperature hydrostatic reconstruction.
  - Small indirect primary-score improvement if corrected Z500 diagnostics also
    reduce pressure-level interpolation artifacts.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and most `mean_sea_level_pressure`
    behavior should stay near incumbent because prognostic dry dynamics and the
    accepted near-surface residual correction are unchanged.
- Possible regressions:
  - If negative passive humidity happens to compensate a dry-temperature
    diagnostic bias, flooring it could worsen Z500.
  - A local floor is not mass conserving. Because the limiter is diagnostic-time
    only and humidity is not an evaluated output target, this is less invasive
    than a prognostic moisture transport limiter but should still be tracked in
    scoring notes.

## Risks

- Numerical stability:
  - Low. The limiter is applied after trajectory generation and cannot destabilize
    the time integrator.
- Compute cost:
  - Low. It adds one elementwise operation to the existing output conversion when
    humidity is present.
- Data leakage:
  - Low. The floor uses only physical bounds and the candidate forecast state; it
    does not use target residuals, future truth, validation statistics, or new
    metrics.
- Physical plausibility:
  - Moderate. Positive-definite moisture transport is physically motivated, but
    this proposal uses a diagnostic-time floor rather than a conservative
    transport scheme. That choice is deliberate to keep the candidate bounded and
    separate from the rejected moist-dynamics experiment.
- Rollback complexity:
  - Low. The change is isolated behind one adapter flag and a side-by-side
    registry entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_qpos`.
  - Require finite outputs and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_qpos --workers 4`.
  - Support for the hypothesis requires at least `+0.002` primary-score
    improvement over `dinosaur_dfi_surface_residual_weak_hs`, clean diagnostics,
    and no fixed RMSE guardrail failures.
- Validation gate:
  - Run validation only after iteration promotion:
    `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_qpos --workers 4`.
  - Accept only with at least `+0.001` validation primary improvement and clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean iteration run with near-zero or negative Z500 movement, or a primary
    delta below `+0.002`, would show that passive humidity negativity is not a
    meaningful remaining error source for the current incumbent.

## Citations

- Local source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` includes
  specific humidity in the Dinosaur state when pressure-level humidity channels
  are available, while the incumbent keeps `use_humidity_in_dynamics=False`.
- Local source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` passes trajectory
  humidity into `primitive_equations.get_geopotential_on_sigma` during output
  conversion.
- Local source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  computes hydrostatic geopotential with virtual temperature when specific
  humidity is provided.
- Lin, S.-J. and Rood, R. B. 1996. "Multidimensional Flux-Form Semi-Lagrangian
  Transport Schemes." Monthly Weather Review, 124, 2046-2070.
  https://doi.org/10.1175/1520-0493(1996)124<2046:MFFSLT>2.0.CO;2
- Williamson, D. L. and Rasch, P. J. 1989. "Two-Dimensional Semi-Lagrangian
  Transport with Shape-Preserving Interpolation." Monthly Weather Review, 117,
  102-129.
  https://doi.org/10.1175/1520-0493(1989)117<0102:TDSLTW>2.0.CO;2
- Skamarock, W. C. 2006. "Positive-Definite and Monotonic Limiters for
  Unrestricted-Time-Step Transport Schemes." Monthly Weather Review, 134,
  2241-2250. https://doi.org/10.1175/MWR3170.1

## Researcher Notes

This is not a duplicate of the rejected `moist-virtual-temperature-dynamics`
candidate because it does not feed moisture back into vorticity, divergence, or
temperature tendencies. It is also not an output residual correction: it applies
a physical nonnegativity bound to a passive tracer before a hydrostatic
diagnostic, without using analysis-minus-forecast residuals, lead-dependent
decays, target-specific constants, or validation tuning.

This proposal is intentionally weaker and lower risk than a full conservative
positive-definite tracer transport rewrite. If this diagnostic-time floor has no
measurable signal, a broader prognostic moisture-transport limiter should not be
promoted without additional evidence because it would be a larger implementation
surface and could interact with the already rejected moist-dynamics path.

## Evaluator Notes

2026-06-16T21:12:45Z - Move to `ready` for Iteration 15 ranking against
`dinosaur_dfi_surface_residual_weak_hs` at
`4756cc9a4b69c41eec60e2177fb03a73974f0e2d`.

Promote this as the only ready proposal. The mechanism is narrow and
implementable without changing the forecast contract or fixed evaluation
protocol: keep `use_humidity_in_dynamics=False`, leave the prognostic trajectory
untouched, and apply a physical nonnegative bound only when passive humidity is
used in output-time hydrostatic diagnostics. Local source inspection confirms
that the adapter already carries humidity tracers when complete pressure-level
humidity stacks are present and passes them into
`primitive_equations.get_geopotential_on_sigma`, where humidity modifies virtual
temperature for geopotential reconstruction.

This is not a duplicate of the rejected moist-virtual-temperature dynamics
candidate. That candidate enabled humidity feedbacks during rollout and failed
the fast diagnostic gate with nonfinite forecasts; this proposal is
post-trajectory and should not destabilize the time integrator. It is also not a
target-residual correction: the floor uses only a state-local physical bound and
does not inspect validation truth, lead-specific residuals, or future target
data. The main weakness is expected signal size, because the change is likely to
touch primarily `geopotential_500`, so the iteration gate may falsify it with a
clean but sub-threshold delta.

Ranked recommendation: 1. implement
`passive-humidity-positivity-limiter` next as
`dinosaur_dfi_surface_residual_weak_hs_qpos`; 2. keep
`full-grid-spectral-truncation` staged as a broader but more expensive
resolution experiment if the humidity diagnostic limiter fails cleanly.
