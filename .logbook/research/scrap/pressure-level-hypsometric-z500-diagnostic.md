---
schema_version: 1
slug: pressure-level-hypsometric-z500-diagnostic
title: Diagnose Z500 by Local Hypsometric Pressure-Level Integration
status: scrap
created_at: 2026-06-23T11:17:35Z
author_role: Researcher
target_model: dino_hsl2_theta
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

# Diagnose Z500 by Local Hypsometric Pressure-Level Integration

## Hypothesis

The adapter currently computes geopotential on sigma layers from the forecast
temperature and humidity columns, then interpolates that sigma geopotential to
requested pressure levels. That is reasonable, but the scored `geopotential_500`
channel depends on a hydrostatic pressure-level integral. Interpolating a
precomputed sigma geopotential can introduce vertical phase error near layers
whose pressure surfaces move with forecast surface pressure.

A geopotential-only pressure-level diagnostic that integrates the hypsometric
thickness locally around the requested pressure surface may improve Z500
without changing the trajectory, pressure-level temperature interpolation,
MSLP, winds, HSL theta transport, or pressure-work terms.

## Mechanism

Register `dino_hsl2_theta_hypz` as an output-diagnostic side-by-side candidate.
Preserve the incumbent rollout and all non-geopotential output paths. For
`geopotential_<level>` outputs only:

- locate the sigma layers bracketing the requested pressure level at each grid
  point and lead;
- use forecast temperature and passive humidity to compute a bounded virtual
  temperature thickness between the bracketing sigma pressures and the target
  pressure;
- integrate hydrostatic thickness upward or downward from the nearest bracketing
  sigma geopotential rather than interpolating sigma geopotential directly;
- use incumbent interpolation as exact fallback for out-of-column levels,
  nonmonotone pressure, nonfinite humidity/temperature, or excessive local
  thickness correction;
- leave `mean_sea_level_pressure`, `surface_pressure`, `2m_temperature`,
  `10m_u_component_of_wind`, pressure-level wind, and pressure-level
  temperature unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py` only if a
    reusable helper is cleaner than adapter-local code
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused adapter/registry tests
- Registry changes:
  - Add one side-by-side model named `dino_hsl2_theta_hypz`.
- API changes:
  - None. The same `geopotential_500` channel is returned.
- Tests to update:
  - Verify zero correction for an isothermal hydrostatic column where direct
    sigma interpolation is analytically exact.
  - Verify finite fallback for target pressures outside the model column.
  - Verify only geopotential pressure-level channels change.
  - Verify humidity is kept in virtual-temperature thickness with bounded
    values, preserving the lesson from rejected dry-consistent geopotential.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500`, especially short-to-medium leads, if output vertical
    geopotential placement remains a measurable diagnostic error.
  - Primary score can improve with minimal risk to other scored variables
    because the rollout state is unchanged.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, and
    `10m_u_component_of_wind` should be unchanged except for metric bookkeeping.
- Possible regressions:
  - Direct sigma geopotential interpolation may already be the least noisy
    diagnostic; local hypsometric corrections could amplify column noise.

## Risks

- Numerical stability:
  - Very low for rollout; the change is output-only.
- Compute cost:
  - Low. It adds local vertical bracketing and thickness algebra at output time.
- Data leakage:
  - None. It uses only forecast temperature, humidity, sigma pressure, and
    geopotential at the same lead.
- Physical plausibility:
  - High. The hypsometric relation is the standard hydrostatic pressure-height
    relation, and this proposal keeps virtual-temperature humidity effects.
- Rollback complexity:
  - Low. Remove one diagnostic helper, flag/factory/export, registry entry, and
    tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_theta_hypz`
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_theta_hypz --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    early Z500 or cross-variable guardrail failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_theta_hypz --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero delta would show Z500 output vertical placement is not a
    material remaining error source. Any Z500 guardrail failure would show the
    hypsometric correction is noisier than incumbent interpolation.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` computes
  sigma geopotential with humidity and interpolates it to pressure levels in
  `dinosaur_state_to_weather_state`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  contains pressure/sigma interpolation utilities that can support bracketing
  pressure-level diagnostics.
- Dynamaxx history:
  `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
  rejected removing humidity from geopotential reconstruction, so this proposal
  preserves bounded virtual-temperature thickness.
- Dynamaxx history:
  `.logbook/history/2026-06-17_02-11-52_log-pressure-output-interpolation/decision.md`
  found output interpolation can matter but did not clear promotion; this
  proposal is narrower and geopotential-specific rather than a broad scalar
  interpolation swap.
- Wallace, J. M. and Hobbs, P. V. 2006. *Atmospheric Science: An Introductory
  Survey*, second edition, describes the hypsometric equation.
- Holton, J. R. and Hakim, G. J. 2012. *An Introduction to Dynamic
  Meteorology*, fifth edition, covers hydrostatic thickness and virtual
  temperature.
- ECMWF IFS Documentation CY48R1, Part III, Dynamics and Numerical Procedures,
  documents hydrostatic pressure/geopotential relationships in operational
  pressure-level diagnostics.

## Researcher Notes

This is not staged `hypsometric-dynamic-mslp-reduction`, which changes the
MSLP diagnostic from surface pressure. It is not `quasi-monotone-pressure-output-
interpolation` or `conservative-pressure-output-remap`, which target broad
vertical remapping behavior. It changes only geopotential pressure-level output,
preserves humidity in virtual-temperature thickness, and never feeds corrected
Z500 back into the dycore.

## Evaluator Notes

### 2026-06-23T11:21:12Z

Decision: move to `scrap`; ranked 3 of 3 new proposals.

This is a duplicate of a mechanism that has already been implemented and
scored. The prior `hypsometric-target-geopotential-diagnostic` candidate was an
output-only pressure-level geopotential diagnostic, passed tests, fast scoring,
iteration diagnostics, and formal RMSE guardrails, but failed promotion with
iteration delta `-0.00001598793092548894`. It also moved the target channel in
the wrong direction at early lead: day-1-to-5 `geopotential_500` mean RMSE
regressed by about `0.9814%`, and 24 h `geopotential_500` regressed by about
`7.3858%`.

The new proposal preserves humidity and frames the correction locally, but it
still changes only the reported pressure-level geopotential channel and does
not address the prior 24 h Z500 degradation mode. Recent pressure-level output
work is also negative: `theta-hydrostatic-pressure-output-reconstruction`
completed cleanly but regressed the primary score, and broad log-pressure
output interpolation previously produced many variable/lead guardrail
failures. Under the fixed dycore optimization protocol, this is too close to
metric-facing output remapping of one scored channel and is not a legitimate
next dycore-improvement candidate without separate read-only evidence showing a
new failure mode.
