---
schema_version: 1
slug: pressure-level-hypsometric-mslp-diagnostic
title: Diagnose MSLP from Low Pressure-Level Height and Thickness
status: staging
created_at: 2026-06-27T23:17:41Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m
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

# Diagnose MSLP from Low Pressure-Level Height and Thickness

## Hypothesis

The incumbent still emits `mean_sea_level_pressure` from the raw modeled
surface-pressure path, and validation MSLP mean skill is negative after the
first few days. The ready `persistent-mslp-reduction-offset` tests a static
initial MSLP/surface-pressure reduction factor. A different failure mode is
possible: the modeled surface pressure may carry useful synoptic evolution, but
the output operator lacks a pressure-level thickness reduction that uses the
forecast low-level height and temperature structure at each lead.

A bounded MSLP diagnostic derived from a low isobaric surface, such as 925 hPa
or 850 hPa where in-column, can use the forecast hydrostatic height and
lower-tropospheric temperature to infer sea-level pressure without persisting
the initial surface-pressure ratio. This tests whether a pressure-level
hypsometric reduction better matches the WeatherBench2 MSLP target while
leaving the trajectory and non-MSLP variables unchanged.

## Mechanism

Register one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_plmslp` or a short alias
`dino_ri2m_plmslp`. Preserve the incumbent trajectory, initialization, DFI,
weak-HS forcing, HSL/DSE transport, WTG, vertical-DSE ramp, T2m residual memory,
bulk-Richardson T2m, 10 m wind diagnostic, Z500 path, and fixed protocols.

For `mean_sea_level_pressure` only:

- keep the raw incumbent surface-pressure-as-MSLP field available as fallback;
- compute forecast temperature and geopotential on low pressure levels already
  available in the adapter output conversion, preferring 925 hPa where the
  pressure surface is safely inside the model column and falling back to 850 hPa
  where 925 hPa is below the local surface or nonfinite;
- convert pressure-level geopotential to height and estimate a bounded mean
  virtual temperature for the layer between sea level and the selected pressure
  surface using the selected pressure-level temperature plus the lower-level
  forecast temperature when available;
- solve the dry hypsometric relation for sea-level pressure implied by the
  selected pressure surface height and mean virtual temperature;
- blend only a fixed, capped increment from the raw incumbent MSLP toward this
  pressure-level hypsometric MSLP, with no lead-zero discontinuity and a smooth
  activation that protects the incumbent's positive short-lead MSLP skill;
- cap the final correction in pressure units, for example at a few hPa, and
  reject corrections from high terrain, out-of-column pressure levels,
  nonpositive temperatures, nonfinite heights, or implausible sea-level
  pressures;
- leave `surface_pressure`, `geopotential_500`, `2m_temperature`,
  `10m_u_component_of_wind`, pressure-level temperatures, pressure-level winds,
  humidity, and the prognostic Dinosaur state unchanged.

This is not the ready persistent MSLP offset, because it does not multiply by a
lead-zero MSLP/surface-pressure ratio. It is also not the staged dynamic
hypsometric MSLP reduction, because it does not infer an effective terrain
height from the initial MSLP/surface-pressure mismatch or reduce from modeled
surface pressure. It derives the diagnostic from forecast isobaric height and
lower-tropospheric thickness.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused adapter tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model derived from
    `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`.
- API changes:
  - None. Forecast inputs, requested variables, output schema, target variables,
    lead schedule, and fixed evaluation protocols remain unchanged.
- Tests to update:
  - Verify zero correction and invalid diagnostics reproduce incumbent MSLP.
  - Verify a synthetic hydrostatic column maps a pressure-level height and
    mean temperature to the expected sea-level pressure.
  - Verify the helper selects 925 hPa before 850 hPa when both are valid and
    falls back when the selected level is out-of-column.
  - Verify only `mean_sea_level_pressure` changes; `surface_pressure` and all
    other target channels remain unchanged.
  - Verify lead-zero and early-lead activation are no-op or near-no-op as
    documented, and pressure correction caps are enforced.
  - Verify the candidate factory preserves every incumbent selector except the
    pressure-level MSLP diagnostic flag and model name.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 4-15 if the raw surface-pressure output
    has useful evolution but a poor sea-level reduction diagnostic.
  - Primary score may improve with low blast radius because the change is
    MSLP-only and final-output-only.
- Expected neutral metrics:
  - `2m_temperature`, `geopotential_500`, and `10m_u_component_of_wind` should
    be unchanged except for metric aggregation noise.
- Possible regressions:
  - Forecast pressure-level geopotential is itself a model diagnostic; using it
    to reconstruct MSLP may amplify Z/temperature errors into the pressure
    channel.
  - A low pressure-level reduction can be unreliable over high terrain or
    strong inversions, so fallback and clipping are essential.

## Risks

- Numerical stability:
  - Very low. The change cannot feed back into the rollout.
- Compute cost:
  - Low. It uses pressure-level temperature/geopotential diagnostics already
    produced during output conversion and adds local hypsometric algebra.
- Data leakage:
  - Low. It uses only forecast-state fields at the same lead, fixed pressure
    levels, fixed constants, and same-time initialization for lead activation.
    It must not use future truth or validation statistics.
- Physical plausibility:
  - Moderate. Hypsometric sea-level pressure reduction is standard, and using
    low isobaric height/thickness is a recognized way to connect pressure and
    mass fields. The reduction is still simplified and should be capped.
- Rollback complexity:
  - Low. Remove one diagnostic helper/selector, one factory/export, one
    registry key, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_plmslp` using the final
    registered candidate name.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_plmslp --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    incumbent, clean diagnostics, no early day-1-through-day-5 RMSE guardrail
    failure, and no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_plmslp --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that
    pressure-level hypsometric MSLP does not improve on the incumbent raw
    surface-pressure diagnostic. Any MSLP guardrail failure would show the
    pressure-level reduction is noisier or more terrain-sensitive than the raw
    path.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently emits both
  `surface_pressure` and `mean_sea_level_pressure` from the same modeled
  surface-pressure field.
- Dynamaxx research:
  `.logbook/research/ready/persistent-mslp-reduction-offset.md` proposes an
  MSLP-only persistent initial reduction factor; this proposal is a dynamic
  pressure-level reduction, not an initial-ratio offset.
- Dynamaxx research:
  `.logbook/research/staging/hypsometric-dynamic-mslp-reduction.md` proposes
  reducing modeled surface pressure through an inferred effective terrain
  height; this proposal instead reduces from forecast isobaric height and
  lower-tropospheric thickness.
- Mass, C. F., Ovens, D., Westrick, K., and Colle, B. A. 2004. Problems with
  the Mean Sea Level Pressure Field over the Western United States. *Monthly
  Weather Review*. The paper discusses converting a reduced 1000 hPa
  geopotential height into MSLP through the thickness equation.
  https://doi.org/10.1175/1520-0493(2004)132%3C1952:PWTMSL%3E2.0.CO;2
- Pauley, P. M. 1998. An Example of Uncertainty in Sea Level Pressure
  Reduction. *Weather and Forecasting*. The paper summarizes how the
  hypsometric equation underlies sea-level pressure reduction and why reduction
  choices can matter.
  https://doi.org/10.1175/1520-0434(1998)013%3C0833:AEOUIS%3E2.0.CO;2
- NOAA/AOML notes on the hydrostatic and hypsometric equations:
  https://www.aoml.noaa.gov/ftp/hrd/annane/prelim_notes/hypsometric_equation.pdf
- National Weather Service pressure definitions describe MSLP as pressure
  reduced to sea level using observed temperature-profile information:
  https://www.weather.gov/bou/pressure_definitions

## Researcher Notes

This is deliberately separated from the existing ready `persistent-mslp-
reduction-offset`: it does not persist the initial MSLP/surface-pressure
factor, so it can fail or succeed for a different reason. It is also separate
from the staged `coupled-lowmode-hydrostatic-mass-residual`: it does not carry
lead-zero residuals for either MSLP or Z500, and it leaves Z500 untouched.

The nearest negative history is pressure-level output reconstruction work:
`.logbook/history/2026-06-21_18-05-20_theta-hydrostatic-pressure-output-reconstruction/decision.md`
showed that broad pressure-level thermodynamic output reconstruction was clean
but harmful. This proposal narrows the scope to the still-negative MSLP channel
and uses strict fallback, late activation, and caps. If rejected, future MSLP
diagnostics should probably wait for read-only evidence rather than adding
more output reductions.

## Evaluator Notes

### 2026-06-27T23:22:43Z

Decision: move to `staging`.

The idea is physically recognizable and implementable: MSLP is a reduction
diagnostic, the current incumbent still has validation MSLP mean skill around
`-0.08385`, and the proposed pressure-level hypsometric path is output-only
with no trajectory feedback. Literature checks support hypsometric reduction as
the standard pressure-to-sea-level basis and also support caution: MSLP
reduction choices are uncertain, especially where fictitious below-ground
thermal columns or terrain-sensitive reductions matter.

Do not place this in `ready` now. The proposal overlaps strongly with the
existing MSLP diagnostic queue: `persistent-mslp-reduction-offset` is simpler,
and `hypsometric-dynamic-mslp-reduction` is already staged as the dynamic
follow-up. This pressure-level variant is a useful third path only if simpler
MSLP reduction ideas fail cleanly or read-only diagnostics show that forecast
925/850 hPa height and thickness carry a better MSLP signal than surface
pressure plus an initial reduction factor.

Rank it behind the ready T2m air-mass diagnostic and behind the simpler staged
persistent MSLP offset. The main risks are metric-facing one-channel
post-processing, amplification of pressure-level height/temperature errors into
MSLP, and terrain/out-of-column edge cases. If revisited, require strict
high-terrain fallback, a fixed correction cap chosen before scoring, no
lead-zero discontinuity, and tests proving every non-MSLP channel remains
incumbent-equivalent.

### 2026-06-28T07:01:40Z

Decision: keep in `staging`; rank 3 of 4.

The physical claim is still defensible, and the proposal is bounded to final
MSLP output, but it is a more formula-heavy diagnostic than the persistent
offset and a broader implementation than the staged dynamic hypsometric
surface-pressure reduction. It adds pressure-level selection, height/thickness
quality gates, activation timing, and capped blending around 925/850 hPa
fields that are themselves forecast diagnostics. That makes it useful as a
later discriminator if simpler MSLP reductions fail, but not the best ready
candidate now. Keep it staged, with the strict requirement that any future
implementation leave all non-MSLP target channels incumbent-equivalent and use
cached incumbent artifacts for comparison.
