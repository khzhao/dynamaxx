---
schema_version: 1
slug: time-centered-ekman-stress-pumping
title: Time-Centered Coupled Ekman Stress and Pumping
status: ready
created_at: 2026-06-30T13:38:54Z
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

# Time-Centered Coupled Ekman Stress and Pumping

## Hypothesis

The accepted `dino_ri2m_ekman_coupled` incumbent gained substantially from a
bounded lower-layer stress plus Ekman-pumping pressure closure. The current
adapter applies that closure as a positive-time step filter and explicitly
ignores `prev_state`, diagnosing stress, density, applied acceleration, and
pumping from the post-dynamics `next_state` only. That is an endpoint
quadrature of a strongly state-dependent source term.

A narrow time-centered version can reduce splitting and phase error in the
accepted stress-pumping closure without changing the drag coefficient, pressure
cap, equatorial taper, vertical taper, first-day activation, output variables,
or evaluation protocol. This is deliberately not another spinup ramp, exact
mass-neutral pressure projection, static roughness redistribution, pressure-work
heating, or DFI correction.

## Mechanism

Register one side-by-side candidate such as `dino_ri2m_ekman_tcenter`, derived
from `ekman_coupled_dinosaur_dycore_model()`.

For the candidate only, add an opt-in variant of `_ekman_coupled_surface_step_filter`
that uses both filter inputs:

- diagnose lowest-layer winds, lowest-layer temperature, and surface pressure
  from both `prev_state` and `next_state`;
- form a finite midpoint diagnostic state by averaging endpoint winds in nodal
  space and averaging positive endpoint temperature and surface pressure in
  physical space;
- compute density, bulk stress, lower-layer wind increments, same-stress Ekman
  transport divergence, and bounded `log_surface_pressure` increment from that
  midpoint diagnostic, while applying the increments to `next_state`;
- retain the incumbent drag coefficient, boundary-layer depth, second-layer
  vertical taper, equatorial pumping taper, wind-increment cap, pressure cap,
  pressure-per-wind ratio cap, modal projection safety checks, area-neutral
  pressure projection, and finite fallback;
- if any endpoint or midpoint diagnostic is nonfinite, nonpositive, or
  shape-incompatible, fall back exactly to the accepted incumbent
  `next_state`-diagnosed Ekman closure rather than disabling the closure;
- leave DFI, WTG, vertical-DSE, T2m memory, RI2m diagnostics, output conversion,
  target variables, lead days, and worker policy unchanged.

The first implementation should be one fixed numerical-quadrature candidate. It
should not sweep midpoint weights or tune drag, caps, activation windows, or
spatial masks.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key such as `dino_ri2m_ekman_tcenter`.
- API changes:
  - None. Forecast input, output variables, target variables, lead days, metric
    definitions, and fixed evaluation commands remain unchanged.
- Tests to update:
  - Verify identical `prev_state` and `next_state` reproduce the incumbent
    accepted closure exactly or to transform roundoff.
  - Verify invalid `prev_state` diagnostics fall back to the incumbent endpoint
    closure, not to a zero Ekman increment.
  - Verify the midpoint path preserves incumbent caps, lower-layer confinement,
    equatorial pumping taper, and pressure-per-wind cap.
  - Verify temperature, tracers, `sim_time`, residual-memory selectors, WTG, and
    vertical-DSE selectors are unchanged directly.
  - Verify candidate factory parity with `dino_ri2m_ekman_coupled` except for
    the new time-centered Ekman selector and model name.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `10m_u_component_of_wind` at days 2-15 if
    endpoint stress-pumping currently introduces a small source-splitting phase
    error.
  - `geopotential_500` may improve secondarily through better lower-boundary
    mass-wind balance.
- Expected neutral metrics:
  - `2m_temperature` should stay close because no thermal tendency, residual
    memory, or RI2m output path is changed.
  - Day-1 behavior should remain closer to the incumbent than the rejected
    spinup-ramp candidate because the full accepted Ekman closure is active
    immediately.
- Possible regressions:
  - Endpoint diagnosis may be empirically compensating another error in the
    accepted closure. Time centering could give back part of the Ekman gain.
  - If the midpoint pressure field damps useful first-step adjustment, early
    MSLP or U10 could regress even without a formal activation ramp.

## Risks

- Numerical stability:
  - Low to moderate. The candidate changes an accepted positive-time rollout
    filter, but all accepted caps and finite fallback remain active.
- Compute cost:
  - Low. It adds endpoint diagnostic transforms and local averaging inside an
    existing filter, with no new lead times or outputs.
- Data leakage:
  - None. The candidate uses only `prev_state`, `next_state`, fixed geometry,
    and fixed closure constants.
- Physical plausibility:
  - Moderate to high. Time-centered source evaluation is a standard way to
    reduce splitting error for state-dependent tendencies, and the underlying
    stress-pumping closure is already accepted.
- Rollback complexity:
  - Low. Remove one selector/helper path, one factory/export, one registry key,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_ekman_tcenter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_tcenter --workers 4`.
  - Compare against cached `dino_ri2m_ekman_coupled` incumbent artifacts when
    valid. Support requires primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_ekman_tcenter --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean diagnostics
    and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show endpoint
    quadrature in the accepted Ekman closure is not a material remaining error
    source. Any early U10, MSLP, or Z500 guardrail failure would show midpoint
    source placement disrupts accepted balance.

## Citations

- Local positive evidence:
  `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/decision.md`
  accepted `dino_ri2m_ekman_coupled` with iteration delta
  `+0.04799113626142959` and validation delta `+0.04683104652127085`.
- Local negative evidence:
  `.logbook/history/2026-06-30_05-41-41_ekman-balanced-spinup-ramp/decision.md`
  rejected an early Ekman activation ramp, so this proposal keeps full-strength
  positive-time Ekman forcing rather than weakening the first day.
- Local negative evidence:
  `.logbook/history/2026-06-30_01-49-51_exact-mass-neutral-ekman-pumping/decision.md`
  and `.logbook/history/2026-06-29_21-03-42_static-roughness-weighted-ekman-coupling/decision.md`
  show pressure invariant repair and static roughness redistribution are not
  leading remaining error sources.
- Local source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently deletes
  `prev_state` inside `_ekman_coupled_surface_step_filter` and diagnoses the
  accepted stress-pumping increment from `next_state` only.
- Ekman, V. W. 1905. "On the Influence of the Earth's Rotation on
  Ocean-Currents."
- Beljaars, A. C. M. 1995. "The parametrization of surface fluxes in
  large-scale models under free convection." Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1002/qj.49712152203
- Strang, G. 1968. "On the construction and comparison of difference schemes."
  SIAM Journal on Numerical Analysis. https://doi.org/10.1137/0705041

## Researcher Notes

This is a current-incumbent-specific numerical placement test for the accepted
Ekman closure. It is not the rejected spinup ramp because the closure reaches
full strength immediately; it is not the rejected mass fixer because the
pressure projection remains incumbent; it is not the rejected roughness variant
because the spatial stress coefficient remains uniform; and it avoids the
post-DFI low-mode thickness and vertical-momentum-advection neighborhoods.

## Evaluator Notes

### 2026-06-30T13:43:15Z

Decision: move to `ready`; ranked 1 of 2 new proposals.

This is the strongest current candidate because it is a narrow, reversible
numerical-placement test on the accepted high-signal
`dino_ri2m_ekman_coupled` closure. Source inspection confirms the incumbent
filter currently deletes `prev_state` and diagnoses the coupled stress-pumping
increment from `next_state` only, so the proposal targets a real endpoint
quadrature choice rather than an invented branch. It keeps the accepted drag
coefficient, caps, equatorial taper, area-neutral pressure projection,
first-day activation, RI2m diagnostics, target variables, lead range, and
fixed WeatherBench2 protocols unchanged.

The idea is not a duplicate of the rejected Ekman spinup ramp, exact
mass-neutral pumping repair, or static roughness redistribution. Those changed
activation, invariant repair, or spatial coefficient weighting and were
negative or effectively neutral. It is also distinct from staged
`coriolis-scaled-ekman-depth-coupling` and
`helmholtz-projected-ekman-coupling`, which change vertical projection geometry
or vector-component routing. This proposal changes only the source-state
quadrature while preserving the accepted closure structure.

Implementation should stay precise: register one side-by-side model such as
`dino_ri2m_ekman_tcenter`, use a fixed midpoint diagnostic from `prev_state`
and `next_state`, apply increments to `next_state`, and fall back exactly to the
incumbent endpoint closure on nonfinite, nonpositive, or incompatible midpoint
diagnostics. Do not sweep midpoint weights, drag constants, caps, activation
windows, masks, or fixed evaluation settings. Compare against the cached
`dino_ri2m_ekman_coupled` incumbent artifacts when protocol-compatible.
