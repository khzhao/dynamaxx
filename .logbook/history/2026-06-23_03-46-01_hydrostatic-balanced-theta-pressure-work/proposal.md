---
schema_version: 1
slug: hydrostatic-balanced-theta-pressure-work
title: Hydrostatic-Balanced Theta Pressure Work
status: ready
created_at: 2026-06-23T03:42:31Z
author_role: Researcher
target_model: dino_hsl2_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Hydrostatic-Balanced Theta Pressure Work

## Hypothesis

The incumbent `dino_hsl2_theta` improved the thermodynamic path by transporting
dry potential-temperature anomaly horizontally with a midpoint semi-Lagrangian
departure. The remaining thermodynamic conversion back to temperature still
adds the existing temperature-form adiabatic pressure-work tendency from
`nodal_temperature_adiabatic_tendency`. That term is numerically paired with the
temperature-form transport operator, not with the theta transport increment and
the local Exner-pressure tendency used to convert theta back to temperature.

A narrow theta/Exner pressure-work branch can reduce column-thickness and mass
imbalance without touching the accepted HSL departure geometry, vertical theta
stencil, residual corrections, or forecast contract. The expected benefit is
cleaner hydrostatic thickness feeding `geopotential_500` and
`mean_sea_level_pressure`, with less risk than another HSL remap or vertical
theta reconstruction.

## Mechanism

Add one side-by-side candidate, for example `dino_hsl2_theta_pw`. Preserve every
incumbent option except the thermodynamic pressure-work conversion inside
`PrimitiveEquationsSigma.temperature_tendency_potential_temperature_form`.

For the candidate only:

- compute the accepted horizontal HSL2 theta-anomaly tendency and incumbent
  centered vertical theta-anomaly tendency exactly as `dino_hsl2_theta` does;
- diagnose `dlog(p)/dt` on sigma centers from the existing
  `nodal_log_pressure_tendency`, `sigma_dot_full`, and local sigma pressure,
  using only same-step forecast state quantities;
- form the Exner conversion term as
  `kappa * full_temperature * dlog(p)/dt`, but use the same pressure and
  theta diagnostics already used by the theta path so the conversion is
  hydrostatically paired with the transported theta field;
- replace only the additive `nodal_temperature_adiabatic_tendency` contribution
  in the theta-form branch with this guarded theta/Exner pressure-work term;
- leave the temperature-form branch, momentum, divergence, log-surface-pressure
  tendency, passive tracers, HSL2 departure, DFI, weak-HS forcing, ocean bulk
  heat flux, residual correction, and pressure-level output interpolation
  unchanged;
- fall back to the incumbent `dino_hsl2_theta` temperature tendency if any
  pressure, Exner, or converted tendency diagnostic is nonfinite or if pressure
  is nonpositive.

This proposal changes the thermodynamic conversion term, not the scalar remap,
not the vertical transport operator, and not the forecast output schema.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model, preferably `dino_hsl2_theta_pw`.
- API changes:
  - None.
- Tests to update:
  - Verify a zero pressure-tendency state reproduces the incumbent theta
    transport tendency.
  - Verify positive finite sigma pressure is required and nonfinite diagnostics
    fall back to the incumbent tendency.
  - Verify the candidate factory preserves every `dino_hsl2_theta` option except
    the new pressure-work selector.
  - Add registry coverage and a finite non-JIT forecast smoke test.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if residual
    hydrostatic thickness error comes from a mismatch between theta transport
    and temperature pressure-work conversion.
  - `2m_temperature` may improve modestly after residual memory decays because
    lower-column thermal conversion is more internally consistent.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because momentum,
    Coriolis splitting, and the Richardson wind diagnostic are unchanged.
- Possible regressions:
  - If the existing temperature-form adiabatic term is empirically compensating
    other errors, a stricter theta/Exner conversion can degrade MSLP or Z500.
  - Pressure-work changes couple directly to the thermal column and could expose
    early mass-field guardrail regressions.

## Risks

- Numerical stability:
  - Moderate. The change touches the thermodynamic tendency every inner step,
    but it is algebraic, bounded by finite-pressure checks, and has an exact
    incumbent fallback.
- Compute cost:
  - Low. It reuses existing pressure and log-pressure diagnostics and adds only
    elementwise conversion work.
- Data leakage:
  - None. Uses only current forecast state, fixed grid geometry, and existing
    constants.
- Physical plausibility:
  - High. Potential temperature and Exner pressure are the standard variables
    for dry adiabatic thermodynamics in hydrostatic primitive-equation models.
- Rollback complexity:
  - Low. Remove one selector, one helper path, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_theta_pw`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_theta_pw --workers 4`.
  - Support requires clean diagnostics, fixed guardrails passing, and iteration
    primary delta at least `+0.002` against the cached `dino_hsl2_theta`
    incumbent score `-0.31282890543336245`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_theta_pw --workers 4`
    only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` against cached
    incumbent validation score `-0.3072374345999185`.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, or early MSLP/Z500 guardrail
    regression, would show the accepted pressure-work pairing is already better
    than the proposed theta/Exner conversion under this benchmark.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  contains `temperature_tendency_potential_temperature_form`,
  `nodal_pressure_sigma`, `nodal_log_pressure_tendency`, and
  `nodal_temperature_adiabatic_tendency`.
- History:
  `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
  accepted HSL theta transport with validation delta `+0.10295803136629866`.
- History:
  `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
  accepted midpoint HSL theta departure with validation delta
  `+0.007196436070573853`.
- Laprise, R. 1992. The Euler equations of motion with hydrostatic pressure as
  an independent variable. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C0197:TEEOMW%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2

## Researcher Notes

This deliberately avoids nearby failed HSL remap variants. It does not change
departure CFL blending, monotonic remapping, Picard trajectories, HSL mean
neutrality, or Charney-Phillips/interface vertical theta transport. Recent
negative evidence says the accepted HSL2 geometry is sensitive: CFL blending was
nonfinite, qmono remap regressed, Picard was neutral-slightly negative,
mean-neutral HSL was subthreshold, and CP/interface theta vertical transport
remained nonfinite after bounded repair. This proposal therefore leaves those
operators alone and tests a separate thermodynamic consistency mechanism.

## Evaluator Notes

### 2026-06-23T03:45:13Z

Decision: move to `ready`; ranked 1 of 2 current proposals.

This is the strongest next target because it is narrow, mechanistic, and avoids
the recently fragile HSL-theta operator neighborhood. The accepted
`dino_hsl2_theta` sequence shows horizontal theta transport and midpoint
departure were high-signal improvements, while subsequent HSL changes were
negative or subthreshold: CFL blending failed fast with nonfinite forecasts,
qmono remapping regressed strongly, Picard correction was slightly negative,
mean-neutral recentering was far below the promotion threshold, and
Charney-Phillips/interface theta vertical transport remained nonfinite after a
bounded repair. This proposal leaves the accepted HSL2 departure, remap,
vertical theta transport, residuals, DFI, weak-HS forcing, and output contract
unchanged.

The pressure-work/theta/omega queue is crowded, but this proposal is more
implementable as the immediate experiment than the staged broad cap,
full-state-theta, or energy-conserving omega-alpha coupling ideas. It tests one
specific mismatch: the theta-form thermodynamic branch still adds the existing
temperature-form adiabatic pressure-work tendency, while the accepted transport
path now evolves theta anomaly and converts through local pressure/Exner
diagnostics. That is a plausible hydrostatic thickness and MSLP/Z500 error
source, the code surface is localized, and the finite/nonpositive-pressure
fallback to the incumbent makes rollback and diagnosis clean.

Recommendation to Orchestrator: implement exactly this proposal next as
`dino_hsl2_theta_pw`, using the fixed gates only: `uv run pytest`,
`uv run dynamaxx-eval fast --model dino_hsl2_theta_pw`, then
`uv run dynamaxx-eval iteration --model dino_hsl2_theta_pw --workers 4`, and
validation with `--workers 4` only after iteration promotion. Reuse the cached
leaderboard incumbent metrics for `dino_hsl2_theta` unless concretely invalid;
do not rerun the incumbent just because candidate source edits exist. Golden is
prohibited.
