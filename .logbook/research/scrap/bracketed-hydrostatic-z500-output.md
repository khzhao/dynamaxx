---
schema_version: 1
slug: bracketed-hydrostatic-z500-output
title: Bracketed Hydrostatic Z500 Output Diagnostic
status: scrap
created_at: 2026-06-30T09:33:49Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Bracketed Hydrostatic Z500 Output Diagnostic

## Hypothesis

The incumbent computes hydrostatic sigma geopotential from forecast temperature
and then linearly interpolates sigma geopotential to pressure levels for
`geopotential_500`. Prior output-only Z500 replacements were too broad and
regressed early Z500, but the current incumbent has since changed materially:
mass-DSE HSL, vertical-DSE, RI2m T2m, and coupled Ekman stress-pumping all
shifted the balance state. A stricter diagnostic may still help if only a small
subset of columns have a local interpolation inconsistency around 500 hPa.

The testable mechanism is not to replace the Z500 diagnostic everywhere.
Instead, compute an independent local hydrostatic thickness estimate only when
the forecast sigma layers cleanly bracket 500 hPa, use it as a small correction
to the incumbent interpolated Z500, and fall back to the incumbent output for
out-of-column, noisy, or large-amplitude cases.

## Mechanism

Register one side-by-side candidate, for example `dino_ri2m_bracket_z500`,
derived from `ekman_coupled_dinosaur_dycore_model()`.

For the candidate only, change output packing for
`geopotential_500` and leave the trajectory unchanged:

- compute the incumbent sigma-layer temperature, optional humidity,
  geopotential, sigma pressure, and incumbent pressure-level output exactly as
  in `dinosaur_state_to_weather_state`;
- for the 500 hPa target only, identify the adjacent sigma layers whose local
  pressures bracket 500 hPa at each lead and grid point;
- estimate the 500 hPa geopotential by integrating the dry or bounded virtual
  hypsometric thickness from the closer bracketing sigma geopotential to
  500 hPa;
- form only a residual correction to the incumbent linearly interpolated Z500,
  not a full replacement;
- apply the residual only if both bracket layers are finite, pressure is
  strictly monotone around the target, humidity is finite or absent, the
  correction is below a fixed small cap, and the corrected value stays between
  loose neighboring geopotential bounds;
- use a smooth low-amplitude blend, for example no more than `25%` of the
  bracketed residual and no more than a fixed geopotential cap in SI units;
- leave all other geopotential levels, pressure-level temperature, winds,
  humidity, MSLP, surface pressure, T2m, U10, residual memory, and positive-time
  dynamics unchanged;
- fall back exactly to incumbent `geopotential_500` wherever any diagnostic is
  invalid.

This is an output diagnostic, not a forecast-contract change. It differs from
earlier hypsometric Z500 replacements by making the incumbent interpolation the
base answer, applying only a capped local residual, and restricting activation
to clean in-column brackets.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py` only if a
    reusable bracketing helper is cleaner than adapter-local code
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model key such as `dino_ri2m_bracket_z500`.
- API changes:
  - None. The same `geopotential_500` channel is returned under the same fixed
    protocols.
- Tests to update:
  - Verify all non-Z500 output channels are unchanged.
  - Verify out-of-column 500 hPa targets reproduce incumbent interpolation.
  - Verify nonmonotone pressure, nonfinite humidity/temperature/geopotential,
    and excessive residual corrections fall back to incumbent Z500.
  - Verify a synthetic hydrostatic column with a small interpolation residual
    receives a bounded correction.
  - Verify candidate factory parity with `dino_ri2m_ekman_coupled` except for
    the new output selector and name.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500`, especially days 1-10, if local sigma-to-pressure
    interpolation around 500 hPa still contributes to height RMSE.
  - Primary score could improve with minimal cross-channel risk because only
    the emitted Z500 diagnostic changes.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, and
    `10m_u_component_of_wind` should be unchanged except for metric aggregation
    bookkeeping.
- Possible regressions:
  - Earlier hypsometric Z500 output replacements regressed early Z500; the
    capped residual design may still activate in columns where incumbent linear
    interpolation is empirically better.
  - Virtual-temperature use can import passive humidity noise; dry fallback and
    humidity bounds are required.

## Risks

- Numerical stability:
  - Very low for rollout because this is output-only. Risk is diagnostic RMSE,
    not model blow-up.
- Compute cost:
  - Low. It adds local vertical bracketing and algebra at output time.
- Data leakage:
  - None. It uses only same-lead forecast sigma fields and fixed pressure
    coordinates.
- Physical plausibility:
  - Moderate to high. The hypsometric relation is physically grounded, but this
    proposal deliberately treats it as a small local correction rather than a
    universal replacement.
- Rollback complexity:
  - Low. Remove one output helper/selector, one factory/export, one registry
    key, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_bracket_z500`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_bracket_z500 --workers 4`.
  - Compare against cached `dino_ri2m_ekman_coupled` metrics when valid.
    Support requires primary delta at least `+0.002`, clean diagnostics, no
    early day-1-through-day-5 Z500 guardrail failure, and no variable-by-lead
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_bracket_z500 --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` with clean diagnostics and
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show local bracketed
    Z500 interpolation residuals are not a material remaining score source.
    Any early Z500 guardrail regression would show even capped hypsometric
    residual correction is noisier than incumbent interpolation.

## Citations

- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
  Survey, second edition. Academic Press. Hydrostatic and hypsometric pressure
  thickness relationships.
- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press. Hydrostatic balance and thickness diagnostics.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- ECMWF IFS Documentation, Part III: Dynamics and Numerical Procedures,
  documents hydrostatic primitive-equation and pressure-coordinate diagnostic
  context. https://www.ecmwf.int/en/publications/ifs-documentation
- Local negative evidence:
  `.logbook/research/scrap/pressure-level-hypsometric-z500-diagnostic.md`
  records that a broader pressure-level hypsometric Z500 diagnostic was a
  duplicate of a previously scored replacement and regressed early Z500. This
  proposal responds by keeping incumbent interpolation as the base path and
  applying only a small, bracket-valid residual.
- Local source reference:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` already computes sigma
  geopotential and pressure-level output fields in `dinosaur_state_to_weather_state`.

## Researcher Notes

This proposal is deliberately output-only and narrow. It is decorrelated from
Ekman coefficient/depth/timing/projection variants, broad state trust regions,
and pressure-thickness/mass-DSE denominator variants. It also differs from the
staged `hydrostatic-pressure-increment-consistency-filter`, which would alter
prognostic `log_surface_pressure` increments during every positive-time step.

The main local warning is strong: earlier full hypsometric Z500 replacement
ideas were not useful. This proposal should therefore be evaluated as a strict
fallback-gated residual test, not as a family of interpolation retunes. If the
fast or iteration artifact shows almost no activation, or if Z500 moves
negative at early leads, the idea should be scrapped rather than tuned.

## Evaluator Notes

### 2026-06-30T09:37:05Z

Decision: move to `scrap`; ranked 2 of 2 in this triage batch.

The physical ingredients are standard, but the proposal is not materially
different enough from prior output-only Z500 diagnostic failures to justify
another model-selection run. The scrapped
`pressure-level-hypsometric-z500-diagnostic` already tested a local
hypsometric pressure-level geopotential diagnostic with incumbent fallback and
failed promotion, including an early Z500 regression. Earlier output-only
geopotential/datum ideas also showed that clean diagnostic isolation can still
fail variable-lead guardrails or become too directly metric-facing.

The bracketed residual and 25% blend reduce amplitude, but they do not change
the core mechanism: edit only the emitted `geopotential_500` field using a
hypsometric residual around the scored pressure surface while leaving the
trajectory unchanged. That makes the likely upside small and mostly confined to
one scored channel, while the protocol risk remains high because the experiment
could improve or degrade the metric without improving the dycore state. The
incumbent has changed since the older hypsometric run, but there is no new
read-only evidence that current 500 hPa errors are caused by local vertical
interpolation rather than dynamical phase or mass/thickness evolution.

Do not revive this family unless diagnostics show a persistent, lead-stable,
in-column interpolation residual at 500 hPa that is separable from forecast
state error and that explains Z500 RMSE without harming early leads. Even then,
it should remain behind state or initialization mechanisms because it is an
output-only correction to a fixed target variable.
