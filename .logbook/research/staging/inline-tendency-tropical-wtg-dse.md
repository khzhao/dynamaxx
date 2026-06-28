---
schema_version: 1
slug: inline-tendency-tropical-wtg-dse
title: Inline Tropical WTG Mass-DSE Thermodynamic Tendency
status: staging
rank: 3
priority: medium-low
created_at: 2026-06-25T12:21:45Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg
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

# Inline Tropical WTG Mass-DSE Thermodynamic Tendency

## Hypothesis

The accepted WTG mechanism is currently implemented as a post-step temperature
filter. That is safe, but it means the semi-implicit primitive-equation step
does not see the WTG thermal tendency while forming the same-step pressure,
divergence, and hydrostatic response. The latest failed WTG variants were clean
but too small because they only adjusted support and neutrality. A larger,
bounded mechanism is to keep the accepted WTG physics but insert it as an
explicit thermodynamic tendency inside the primitive-equation tendency
evaluation, so the IMEX Runge-Kutta stages can couple it more directly to the
forecast dynamics.

## Mechanism

Add one side-by-side model, for example `dino_hsl2_mass_dse_wtg_inline`,
derived from `dino_hsl2_mass_dse_wtg`. Disable the post-step WTG filter for
this candidate and instead add an opt-in WTG temperature tendency to
`PrimitiveEquationsSigma.temperature_tendency_potential_temperature_form`.

The tendency should use the accepted ingredients:

- dry static energy anomaly and sigma-layer pressure thickness;
- fixed tropical latitude and free-tropospheric sigma envelopes;
- fixed low-mode mass-DSE projection;
- accepted multi-day relaxation timescale;
- the same Kelvin-per-inner-step cap expressed as a tendency cap;
- layer-neutral temperature tendency offset and finite fallback.

The WTG term is added only to the rollout equation, not to the time-reversed DFI
equation. The candidate leaves HSL transport, vertical advection, adiabatic
pressure work, vorticity, divergence, log surface pressure, tracers, forcing
constants, output variables, and fixed evaluation protocols unchanged except
for the thermodynamic tendency placement.

## Implementation Scope

- Expected files: add one opt-in WTG tendency helper in
  `primitive_equations.py`, thread a selector from `adapter.py`, expose a
  factory through `__init__.py`, register one model key, and add focused tests.
- Registry changes: add `dino_hsl2_mass_dse_wtg_inline`; keep the accepted
  `dino_hsl2_mass_dse_wtg` post-step filter path unchanged.
- API changes: none.
- Tests to update: disabled-path incumbent equivalence; finite tendency on
  synthetic tropical DSE anomalies; no-op outside the WTG mask; cap and
  layer-neutrality checks; proof that the DFI equation does not receive the
  inline WTG selector; registry and finite non-JIT smoke coverage.

## Expected Metric Movement

- Expected improvements: `mean_sea_level_pressure`, `geopotential_500`, and
  `10m_u_component_of_wind` if the accepted WTG thermal correction is currently
  phase-lagged relative to mass and wind adjustment.
- Expected neutral metrics: `2m_temperature` should remain close where the
  accepted WTG mask is zero because all surface residual and lower-boundary
  paths are preserved.
- Possible regressions: moving WTG into the equation can couple the thermal
  relaxation more strongly to pressure and divergence, so early MSLP and Z500
  guardrails are the key risk.

## Risks

- Numerical stability: moderate; the WTG term remains capped but now enters
  every explicit tendency evaluation rather than only a completed step.
- Compute cost: moderate; WTG diagnostics may run at multiple IMEX stages,
  increasing cost relative to the post-step filter.
- Data leakage: none; it uses only forecast state and fixed constants.
- Physical plausibility: moderate to high; WTG is a recognized tropical balance,
  and tendency-form forcing is a standard way to couple parameterized physics to
  a dynamical core.
- Rollback complexity: moderate; it touches the primitive-equation tendency
  path plus the adapter/factory/registry, but remains side-by-side.

## Evaluation Plan

- Fast gate: run `uv run pytest` and `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_inline`; require clean diagnostics.
- Iteration gate: compare fixed iteration against cached
  `dino_hsl2_mass_dse_wtg` incumbent metrics from `.logbook/leaderboard.json`;
  cached metrics are authoritative if compatible.
- Validation gate: run fixed validation only after iteration promotion.
- Outcome that would falsify the hypothesis: a clean subthreshold or negative
  iteration delta would show that WTG's current post-step placement is not a
  material remaining error source; any early MSLP/Z500 guardrail failure would
  show inline coupling is too aggressive.

## Citations

- Sobel, A. H. and Bretherton, C. S. 2000. Modeling Tropical Precipitation in a
  Single Column. Journal of Climate.
  https://doi.org/10.1175/1520-0442(2000)013%3C4378:MTPIAS%3E2.0.CO;2
- Sobel, A. H., Nilsson, J., and Polvani, L. M. 2001. The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences. https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Whitaker, J. S. and Kar, S. K. 2013. Implicit-Explicit Runge-Kutta Methods
  for Fast-Slow Wave Problems. Monthly Weather Review.
  https://doi.org/10.1175/MWR-D-13-00132.1
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements the IMEX SIL3 step, while
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently applies WTG as a
  positive-time post-step filter.

## Researcher Notes

This is related to, but materially different from, staged
`time-centered-tropical-wtg-mass-dse`. The staged idea still treats WTG as a
state transform around a completed dynamics step. This proposal tests a
different failure mode: whether the WTG thermal correction needs to be visible
inside explicit tendency evaluations so the semi-implicit step couples it to
mass and wind evolution immediately.

## Evaluator Notes

### 2026-06-25T12:26:00Z

Decision: move to `staging`; ranked 3 of 3 new proposals.

The mechanism is scientifically coherent: WTG is a recognized tropical balance
approximation, and a tendency-form parameterized thermal relaxation could couple
more directly to pressure and divergence than the current post-step filter. The
proposal is side-by-side, leaves the forecast and evaluation contracts
unchanged, and includes appropriate tests for disabled-path equivalence,
masking, capping, layer neutrality, finite fallback, and DFI exclusion.

It is not ready because its implementation and scoring cost are materially
higher than the other two candidates. Moving WTG inside
`temperature_tendency_potential_temperature_form` touches the core
primitive-equation tendency path, needs careful separation from time-reversed
DFI, and may apply the WTG diagnostics at multiple IMEX stages per inner step.
That is a larger blast radius after two clean WTG post-step refinements already
failed to beat the incumbent. The stronger same-step coupling may also expose
the exact early MSLP/Z500 guardrail risk that the accepted post-step filter has
avoided.

Keep staged for a later WTG operator-placement pass if cheaper WTG variants and
the guarded vertical-DSE ramp fail. It should not enter `ready` until there is
more evidence that post-step WTG placement, rather than the relaxed anomaly
target or vertical-DSE transport, is the limiting error.
