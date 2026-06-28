---
schema_version: 1
slug: coupled-lowmode-hydrostatic-mass-residual
title: Coupled Low-Mode Hydrostatic MSLP-Z500 Residual
status: staging
created_at: 2026-06-26T00:10:51Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
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

# Coupled Low-Mode Hydrostatic MSLP-Z500 Residual

## Hypothesis

The current incumbent still has negative mean MSLP skill after the first few
days and only weak late Z500 skill, while `2m_temperature` is already covered
by staged surface-memory proposals. The earlier output-only
`low-mode-mass-diagnostic-residual-memory` experiment was clean and slightly
positive but subthreshold because it carried independent MSLP and Z500 residuals.
Independent residuals can over-persist weather-dependent analysis increments and
can also violate the dry hydrostatic relationship between sea-level pressure
and column thickness.

A stricter output-side correction that keeps only the common low-wavenumber
hydrostatic component shared by initial MSLP and Z500 residuals may capture a
stationary mass/thickness datum error without injecting two unrelated residual
patterns. This gives the mass diagnostics a physically coupled retest while
leaving the accepted trajectory untouched.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_hydro_resid`, derived from the current incumbent.

After the raw Dinosaur trajectory is converted to `WeatherState`, and before
returning requested outputs:

- compute lead-zero raw residuals for `mean_sea_level_pressure` and
  `geopotential_500` only when both channels are present in the initial state
  and requested outputs;
- project each residual to a fixed smooth low-mode spectral mask, for example
  full strength through total wavenumber 6 and tapered to zero by 12;
- convert the low-mode MSLP residual to an equivalent height residual using a
  fixed dry scale-height linearization of the hypsometric relation;
- retain only the sign-consistent common component between the equivalent MSLP
  height residual and the Z500 residual, for example a bounded weighted average
  with zero correction where the two imply opposite column-thickness errors;
- apply the common height residual to Z500 with a fixed decay, and invert the
  same common residual back to an MSLP correction with the same decay, so the
  two corrected channels remain hydrostatically coupled;
- cap each channel correction by a fixed fraction of its lead-zero low-mode
  residual norm and preserve lead-zero exactness;
- leave `2m_temperature`, `10m_u_component_of_wind`, pressure-level fields,
  surface pressure, humidity, prognostic state, WTG, vertical-DSE, and fixed
  protocols unchanged;
- fall back channel-by-channel to the incumbent output if transforms,
  scale-height algebra, common-mode diagnostics, or corrected fields are
  nonfinite or shape-incompatible.

This is an output diagnostic residual projection, not a pressure tendency
change, terrain-orography rollout, or forecast-contract change.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused adapter residual-correction tests under
    `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key such as
    `dino_hsl2_mass_dse_wtg_vdse_hydro_resid`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead schedule, metrics,
    and fixed protocols remain unchanged.
- Tests to update:
  - Verify no-op behavior when either mass channel is absent.
  - Verify low-mode mask shape, taper, and finite fallback.
  - Verify opposite-signed MSLP-equivalent and Z500 residuals produce zero or
    strongly damped common correction.
  - Verify sign-consistent synthetic residuals produce coupled MSLP and Z500
    corrections with the documented scale-height conversion.
  - Verify non-mass channels are unchanged.
  - Add factory, registry, and finite smoke-forecast coverage.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 2 to 15 if part of the current negative
    skill is a persistent large-scale pressure-reduction or mass-datum error.
  - `geopotential_500` at medium and late leads if a shared low-mode thickness
    residual remains after the accepted DSE and vertical-DSE improvements.
  - Primary score should improve modestly if the common residual captures both
    mass target channels without touching T2m or winds.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should remain identical or
    numerically equivalent because their output paths and trajectory are
    unchanged.
- Possible regressions:
  - A same-time initial residual may include real synoptic analysis increments
    that should decay faster than the fixed schedule.
  - The fixed scale-height linearization may reject useful MSLP or Z500
    residual components whose relationship is not captured by a dry
    hypsometric proxy.

## Risks

- Numerical stability:
  - Very low. This is output-only and cannot feed back into the integration.
- Compute cost:
  - Low. It adds a small number of spectral transforms and elementwise algebra
    per forecast, not per inner step.
- Data leakage:
  - Low. It uses only same-time initial-state channels and the model's own
    lead-zero diagnostic, matching accepted residual-correction patterns. It
    must not inspect future truth, validation errors, or leaderboard statistics.
- Physical plausibility:
  - Moderate. Low-mode separation and hypsometric pressure-thickness coupling
    are physically defensible, but this remains a reduced diagnostic correction
    rather than a terrain-aware pressure reduction scheme.
- Rollback complexity:
  - Low. Remove one output residual helper/selector, one factory/export, one
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_hydro_resid`.
  - Require finite outputs and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_hydro_resid --workers 4`.
  - Support requires primary delta at least `+0.002` against cached
    `dino_hsl2_mass_dse_wtg_vdse_ramp`, clean diagnostics, no early day-1-to-5
    mean RMSE guardrail failure, and no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_hydro_resid --workers 4`
    only after iteration promotion.
  - Support requires validation delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the remaining
    mass-channel errors are not a shared low-mode hydrostatic residual. Any
    early MSLP or Z500 guardrail failure would show the correction over-persists
    weather-dependent analysis structure.

## Citations

- Dynamaxx cached metrics:
  `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv` and
  `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv` show
  `mean_sea_level_pressure` has negative mean skill and `geopotential_500`
  skill decays toward small positive values at late leads.
- Dynamaxx history:
  `.logbook/history/2026-06-19_23-29-46_low-mode-mass-diagnostic-residual-memory`
  rejected independent low-mode MSLP/Z500 residual memory as clean but
  subthreshold, with iteration delta `+0.0007877795793892473`.
- Dynamaxx research:
  `.logbook/research/staging/persistent-mslp-reduction-offset.md` stages an
  MSLP-only persistent reduction factor; this proposal instead applies a
  coupled MSLP-Z500 common hydrostatic mode.
- von Storch, H., Langenberg, H., and Feser, F. 2000. A Spectral Nudging
  Technique for Dynamical Downscaling Purposes. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2000)128%3C3664:ASNTFD%3E2.0.CO;2
- Rasp, S. et al. 2024. WeatherBench 2: A benchmark for the next generation of
  data-driven global weather models. Journal of Advances in Modeling Earth
  Systems. https://doi.org/10.1029/2023MS004019
- Pauley, P. M. 1998. An Example of Uncertainty in Sea Level Pressure
  Reduction. Weather and Forecasting.
  https://doi.org/10.1175/1520-0434(1998)013%3C0833:AEOUIS%3E2.0.CO;2
- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press.

## Researcher Notes

This is not a duplicate of rejected `low-mode-mass-diagnostic-residual-memory`.
That candidate carried independent low-mode residuals for MSLP and Z500. This
proposal keeps only the common component that can be represented by one dry
hypsometric height/pressure residual, and discards sign-inconsistent channel
residuals instead of persisting them independently.

It is not a duplicate of staged `persistent-mslp-reduction-offset`, which is an
MSLP-only multiplicative output correction. It is not staged
`hypsometric-dynamic-mslp-reduction`, because it does not replace the lead-time
MSLP formula from current column state. It is not staged
`compensated-hydrostatic-dse-diagnostic`, because it does not alter the DSE or
geopotential diagnostic calculation; it is a same-time low-mode residual
projection on the two scored mass channels. It is also decorrelated from the
current vertical-DSE research thread because the prognostic trajectory is left
exactly incumbent.

## Evaluator Notes

### 2026-06-26T00:15:42Z

Decision: move to `staging`; ranked 2 of 2 reviewed proposals.

This is implementable under the current forecast contract and fixed evaluation
protocols. The proposal improves on the rejected independent low-mode
MSLP/Z500 residual memory by keeping only a sign-consistent common hydrostatic
component, so it is not a pure duplicate and should not be rejected merely for
using an established output-side residual pattern.

Stage rather than ready because the closest measured predecessor was clean but
only `+0.0007877795793892473` on iteration, well below the `+0.002` promotion
gate. This stricter common-mode version is more physically constrained, but it
is still output-only, metric-facing, and likely lower-signal than the
trajectory-level hydrostatic-work gate. It needs stronger evidence that the
remaining current-incumbent MSLP/Z500 error is a shared low-mode datum error
rather than weather-dependent analysis structure before becoming the next
implementation target.
