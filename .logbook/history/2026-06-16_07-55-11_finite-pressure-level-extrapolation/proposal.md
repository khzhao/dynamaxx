---
schema_version: 1
slug: finite-pressure-level-extrapolation
title: Make Dinosaur Pressure-Level Outputs Finite
status: ready
created_at: 2026-06-16T07:45:01Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Make Dinosaur Pressure-Level Outputs Finite

## Hypothesis

The current fixed fast gate cannot distinguish real model changes because the
incumbent `dinosaur` already fails the official full-forecast finite diagnostic.
The scored metric rows in `outputs/eval/fast_dinosaur.json` are finite, but the
full emitted forecast tensor contains 4,567,590 NaN or Inf values. The rejected
`dinosaur_moist` candidate showed the same failure mode with 4,713,420
non-finite values, so the issue is an adapter/evaluation-compatibility problem,
not unique to moisture.

The likely numerical cause is pressure-level output interpolation for levels
that fall outside the terrain-following sigma column, especially lower pressure
surfaces such as 925 hPa and 1000 hPa in high-terrain regions or after surface
pressure evolution. These levels are present in the WeatherBench2 initial state,
the adapter advertises them as supported outputs, and `evaluate_batch_totals`
diagnoses the full forecast tensor before selecting the four scored target
channels. A bounded finite extrapolation for out-of-column pressure-level
diagnostics should restore a valid incumbent gate without changing the forecast
contract, emitted channel set, metric definitions, or diagnostic rules.

## Mechanism

Keep the Dinosaur forecast API and evaluation diagnostics unchanged. Change only
the Dinosaur pressure-level packing path so every advertised pressure-level
diagnostic is finite even when the requested pressure level maps to a sigma value
outside the valid column.

The implementer should replace NaN-producing sigma-to-pressure output
interpolation with a bounded rule:

- use the existing linear interpolation where the requested pressure lies within
  the valid sigma range;
- for pressure levels above the top valid sigma center, use a finite top-layer
  extrapolation or nearest top-layer value;
- for pressure levels below the local surface, use a finite bottom-layer
  extrapolation or nearest bottom-layer value;
- apply the same finite rule to temperature, horizontal winds, geopotential, and
  passive humidity outputs so `WeatherState.values` is finite for the full
  default Dinosaur output set.

This is an infrastructure and adapter-compatibility proposal. It is not a
model-selection physics candidate and should not be judged by iteration skill
against the incumbent until it first establishes a finite, comparable incumbent
baseline under the fixed fast gate.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py` only if the
    finite extrapolation is implemented as a reusable interpolation helper.
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Registry changes:
  - None. The canonical `dinosaur` factory should continue to produce the
    default model name.
- API changes:
  - None. Do not add outputs, remove outputs, add constants to `ForecastInput`,
    or change `forecast(ForecastInput) -> WeatherState`.
- Tests to update:
  - Add a unit test where surface pressure is lower than one requested pressure
    level and `dinosaur_state_to_weather_state` still returns finite values for
    all emitted pressure-level fields.
  - Add a regression test that the four fixed target variables remain present
    and finite.
  - Preserve existing interpolation behavior for in-column pressure levels.

## Expected Metric Movement

- Expected improvements:
  - Fast diagnostic status should change from failed to passing for the
    incumbent if the non-finite values are caused by out-of-column
    pressure-level interpolation.
  - Primary score should become a finite value computed from existing metric
    rows, rather than `-inf` from diagnostic failure.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, `geopotential_500`, and
    `10m_u_component_of_wind` should be numerically unchanged except where a
    target pressure level is itself outside the sigma column.
- Possible regressions:
  - If 500 hPa is below ground in rare high-terrain columns, the finite fill rule
    may change `geopotential_500` there. The change is still preferable to NaN
    output, but the Scorer should record the magnitude.

## Risks

- Numerical stability:
  - Low. The change is in output diagnostics after the trajectory is computed;
    it does not feed back into the dycore state.
- Compute cost:
  - Negligible. It adds simple masking or bounded extrapolation during output
    packing.
- Data leakage:
  - Low. The rule uses only the model state and the current surface pressure, not
    future truth.
- Physical plausibility:
  - Moderate. Below-ground pressure-level values are diagnostic extrapolations,
    not physical atmospheric states. However ERA5 pressure-level products also
    contain interpolated or extrapolated values below terrain, and the fixed
    evaluation requires finite gridded arrays.
- Rollback complexity:
  - Low. The change can be isolated to the sigma-to-pressure output helper.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur`.
  - The support criterion is `diagnostics.failed=false` with finite metric
    records. The raw primary score can then be used as the comparable incumbent
    fast baseline.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur --workers 4` only after
    fast passes, to create the first finite incumbent iteration baseline if the
    Orchestrator treats this as infrastructure repair.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur --workers 4` only if
    the Orchestrator needs a finite validation baseline for subsequent
    model-selection decisions.
- Outcome that would falsify the hypothesis:
  - If full-output non-finite values remain after bounded pressure-level
    extrapolation, then the failure is not primarily from out-of-column
    sigma-to-pressure interpolation and the implementer should stop rather than
    alter fixed diagnostics inside this proposal.

## Citations

- Dynamaxx source: `src/dynamaxx/eval/runner.py` calls
  `diagnose_forecast(forecast.values)` before selecting target channels, so
  non-finite values in unscored emitted channels fail the fixed gate.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  uses `_linear_interp_with_safe_extrap`, which can return NaN outside its
  limited extrapolation range.
- Dynamaxx artifact: `outputs/eval/fast_dinosaur.json` reports
  `nonfinite_forecast` with value 4,567,590 for the incumbent while target metric
  rows are finite.
- ECMWF C3S forum documentation notes that ERA5 pressure-level variables at
  lower levels can be below model terrain because they are interpolated from
  model levels. https://forum.ecmwf.int/t/atmospheric-variables-below-model-terrain/1225
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Kochkov et al. 2024. Neural general circulation models for weather and
  climate. Nature. The Dinosaur-backed dycore uses hydrostatic primitive
  equations with vertical sigma coordinates and a horizontal pseudo-spectral
  discretization. https://www.nature.com/articles/s41586-024-07744-y

## Researcher Notes

This proposal explicitly incorporates the iteration-2 Orchestrator evidence that
the dry incumbent fast gate fails with the same diagnostic class as the rejected
moist candidate. It is distinct from the staged digital-filter and near-surface
diagnostic ideas because it does not change initialization balance or target
post-processing. It should be handled before further model-selection candidates,
because otherwise every candidate can be rejected for a pre-existing incumbent
adapter compatibility failure.

## Evaluator Notes

2026-06-16T07:47:01Z - Move to `ready`.

This is the only current proposal that directly addresses the gate-blocking
evidence. Source inspection confirms `evaluate_batch_totals` diagnoses
`forecast.values` before target-channel selection, so non-finite values in
unscored emitted channels fail `fast`. The Dinosaur adapter emits pressure-level
fields through `_interp_sigma_to_pressure_by_time`, which calls
`vertical_interpolation.interp_sigma_to_pressure`; the default bounded
`_linear_interp_with_safe_extrap` path returns NaN outside its extrapolation
range. That matches the incumbent and rejected moist-candidate failure mode
without requiring any change to diagnostics, target variables, splits, or
metrics.

Approve as an infrastructure-first repair, not as a skill-improving
model-selection candidate. Implementation should stay constrained to finite
pressure-level output packing, with regression tests that preserve in-column
interpolation and keep all advertised outputs finite. The canonical `dinosaur`
fast gate must pass before iteration/validation baselines or model-selection
candidates resume. If non-finite values remain after bounded pressure-level
output extrapolation, stop and return for diagnosis rather than masking fixed
diagnostics.
