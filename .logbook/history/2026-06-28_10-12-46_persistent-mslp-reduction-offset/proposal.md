---
schema_version: 1
slug: persistent-mslp-reduction-offset
title: Persist the Initial Sea-Level Pressure Reduction Offset
status: ready
created_at: 2026-06-18T23:56:34Z
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

# Persist the Initial Sea-Level Pressure Reduction Offset

## Hypothesis

The adapter currently emits `mean_sea_level_pressure` from the model surface
pressure field. That is a large representational simplification: sea-level
pressure is a diagnostic reduction intended to remove terrain pressure effects,
whereas the Dinosaur rollout uses zero orography and a sigma surface pressure.
An older mass-diagnostic residual correction was safe but too small because it
decayed both MSLP and geopotential residuals. A persistent, MSLP-only pressure
reduction factor inferred from the initial analysis should better represent the
static terrain-reduction offset while leaving the trajectory and Z500 path
untouched.

## Mechanism

Register a side-by-side candidate derived from the current incumbent, using a
short name such as `dino_ri2m_mslp_offset`. Preserve the incumbent trajectory,
initialization, DFI, weak Held-Suarez forcing, HSL/DSE transport, WTG,
vertical-DSE ramp, accepted T2m diagnostics, Richardson 10 m wind diagnostic,
pressure-level interpolation, output variables, and fixed protocols.

Add one opt-in output diagnostic after `dinosaur_state_to_weather_state` creates
the raw trajectory and before or alongside the existing residual correction:

- if both `surface_pressure` and `mean_sea_level_pressure` are present in the
  initial state and MSLP is requested in output, compute a same-time reduction
  factor `initial_mslp / initial_surface_pressure`;
- clip the factor to one fixed physically broad interval, for example
  `[0.75, 1.35]`, and fall back to `1.0` wherever inputs are missing or
  nonfinite;
- emit corrected MSLP as raw modeled surface pressure multiplied by that
  persistent reduction factor at every requested lead;
- leave `surface_pressure` output, `geopotential_500`, pressure-level fields,
  `2m_temperature`, 10 m winds, and the prognostic Dinosaur state unchanged;
- keep the accepted near-surface residual correction exactly as-is for
  `2m_temperature` and `10m_u_component_of_wind`.

This is not a decaying mass residual and not a terrain/orography rollout
experiment. It is a one-channel diagnostic pressure-reduction adapter that uses
only same-time initialization information.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, outputs, lead times, target variables, splits, and
    deterministic gates remain unchanged.
- Tests to update:
  - Unit-test finite MSLP reduction-factor computation, clipping, and no-op
    fallback when either initial pressure channel is absent.
  - Verify only the `mean_sea_level_pressure` channel changes; `surface_pressure`
    and all non-MSLP channels remain unchanged before accepted near-surface
    residual correction.
  - Verify lead-zero MSLP equals initial MSLP when both initial pressure fields
    are present and the factor is finite.
  - Verify the candidate factory preserves every incumbent option except the new
    MSLP-offset selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` across most leads if the fixed target includes a
    persistent terrain-reduction component that raw model surface pressure
    cannot represent.
  - Primary score may improve without pressure, height, temperature, or wind
    trajectory side effects because the change is MSLP-output-only.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and `geopotential_500` should
    remain unchanged except for metric aggregation noise.
- Possible regressions:
  - The initial MSLP/surface-pressure ratio may contain synoptic analysis
    increments in addition to static terrain reduction, so persisting it can
    overcorrect evolving cyclones or anticyclones.
  - If the fixed WeatherBench2 initial state lacks true `surface_pressure`, the
    candidate will correctly fall back and be nearly neutral.

## Risks

- Numerical stability:
  - Very low. The change is output-only and cannot feed back into rollout.
- Compute cost:
  - Negligible. It adds one channelwise factor and multiplication per initial
    state and lead.
- Data leakage:
  - Low. It uses only same-time initial analysis channels already available to
    the forecast, not future truth, validation statistics, or golden data.
- Physical plausibility:
  - Moderate. Sea-level pressure reduction is a diagnostic post-processing
    problem, and a persistent multiplicative factor is simpler than a full
    virtual-temperature reduction formula, but it captures the static part that
    the zero-orography dycore cannot represent.
- Rollback complexity:
  - Low. Remove one diagnostic helper/flag, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_mslp_offset` using the
    final registered candidate name.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_mslp_offset --workers 4`
    using the final registered candidate name.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_mslp_offset --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero delta would show that MSLP-as-surface-pressure is not a
    material remaining score bottleneck or that the fixed data lacks the needed
    surface-pressure channel. Any MSLP guardrail failure would show the
    persistent factor is too static for evolving weather systems.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
    emits `surface_pressure` and `mean_sea_level_pressure` from the same raw
    surface-pressure field.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_15-28-07_mass-diagnostic-analysis-residuals/decision.md`
    found decaying MSLP and geopotential residuals safe but below promotion.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography/decision.md`
    rejected changing terrain/orography and prognostic surface-pressure
    handling after severe early mass-field guardrail failures.
  - Pauley, P. M. 1998. An Example of Uncertainty in Sea Level Pressure
    Reduction. Weather and Forecasting.
    https://doi.org/10.1175/1520-0434(1998)013%3C0833:AEOUIS%3E2.0.CO;2
  - ECMWF IFS Documentation Part VI: Technical and Computational Procedures
    describes pressure and geopotential post-processing context in the IFS.
    https://www.ecmwf.int/sites/default/files/elibrary/2003/77032-ifs-documentation-cy23r4-part-vi-technical-and-computational-procedures_1.pdf
  - Stull, R. Practical Meteorology, Sea-Level Pressure Reduction, summarizes
    hypsometric sea-level pressure reduction.
    https://geo.libretexts.org/Bookshelves/Meteorology_and_Climate_Science/Practical_Meteorology_%28Stull%29/09%3A_Weather_Reports_and_Map_Analysis/9.00%3A_Sea-level_Pressure_Reduction

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is not a duplicate of `mass-diagnostic-analysis-residuals`: that rejected
candidate applied decaying analysis residuals to both MSLP and pressure-level
geopotential, and its signal was too small. This proposal applies a persistent
multiplicative MSLP reduction factor only, because the terrain pressure
reduction component should not decay like a transient analysis increment.

It is also not a terrain/orography retry. The raw surface-pressure trajectory,
zero-orography geopotential reconstruction, pressure-level interpolation, Z500,
and all dynamics remain on the incumbent path. If it fails, the result should
discourage further MSLP diagnostic adapters unless a separate infrastructure
proposal adds explicit terrain metadata support.

## Evaluator Notes

### 2026-06-19T00:01:16Z

Decision: `staging`.

The proposal is implementable under the fixed forecast and evaluation contract:
it uses only same-time initial fields, leaves the prognostic trajectory
unchanged, does not alter metrics or splits, and should be easy to roll back.
The sea-level-pressure reduction argument is physically plausible, and the
older terrain/orography history supports keeping this diagnostic isolated from
prognostic surface pressure and Z500.

Do not promote it as the next ready item yet. It is a one-channel output-only
metric adapter, so the evidentiary bar is higher than for a dycore trajectory
change. Prior `mass-diagnostic-analysis-residuals` was safe but subthreshold,
while `terrain-aware-surface-pressure-orography` showed that pressure-field
changes can create large early mass-field guardrail failures even when primary
score improves. Persisting the initial MSLP/surface-pressure ratio may also
carry same-time synoptic analysis increments, not only static terrain
reduction, so an MSLP-specific guardrail failure remains plausible.

Rank: 2 of 3. Keep staged for a later pass if trajectory-level theta proposals
do not promote, or if Researcher can add stronger evidence that the initial
ratio is dominated by stationary reduction rather than weather-dependent
analysis increments.

### 2026-06-27T19:07:18Z

Decision: promote to `ready`; ready rank 2.

The new incumbent still emits `mean_sea_level_pressure` from the same raw
surface-pressure path, and validation mean MSLP skill remains negative at about
`-0.08385`. This proposal is a justified one-channel diagnostic rather than an
unmotivated metric adapter: sea-level pressure is a reduction diagnostic, while
the zero-orography sigma dycore surface pressure is not itself MSLP.

Promote it behind the T2m diagnostic because the current primary-score
bottleneck is T2m, but keep it in the ready cap because the implementation
surface and rollback cost are very low and the non-MSLP channels should remain
identical. If selected, retarget the factory to derive from
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`, fix the clipping bounds before
scoring, and reject any implementation that changes surface pressure, Z500,
T2m, U10, or the forecast trajectory.

### 2026-06-27T23:22:43Z

Decision: demote to `staging`; MSLP follow-up rank 1.

The proposal remains feasible and scientifically plausible under the current
incumbent, and the recent bulk-Richardson acceptance record explicitly left it
as the remaining ready MSLP diagnostic. However, a new lower-tropospheric
air-mass T2m proposal now targets the dominant remaining validation weakness:
`2m_temperature` mean skill is about `-0.95734`, compared with MSLP mean skill
around `-0.08385`. Keeping both in `ready` would be allowed by the hard cap, but
the current queue has a clear best next experiment and the protocol prefers a
small ready set.

Move this back to `staging` without rejecting it. It should be the first MSLP
idea to promote if the air-mass T2m diagnostic fails cleanly, if the
Orchestrator explicitly chooses to diversify away from T2m output diagnostics,
or if a scorer pass shows the T2m path cannot clear guardrails. Prefer this
simple persistent offset before more complex hypsometric MSLP variants because
it has the smallest implementation surface and tests the zero-orography
surface-pressure-versus-MSLP mismatch directly.

### 2026-06-28T07:01:40Z

Decision: move to `ready`; rank 1 of 4.

The fresh re-triage now favors this proposal. The intervening lower-
tropospheric final-output T2m blend regressed T2m badly, and the momentum-only
vertical-advection experiment became nonfinite on the fixed iteration split.
Those results reinforce the current lesson: avoid another T2m blend or
vertical-transport family and use the accepted incumbent artifacts unchanged
while testing a low-blast-radius correction for the remaining negative MSLP
channel.

This is the best candidate because it is final-output-only, one-channel,
bounded, easy to roll back, and directly tests the raw surface-pressure-as-MSLP
diagnostic mismatch in the zero-orography Dinosaur adapter. It is also simpler
than the hypsometric variants, so it should run before any formula-heavy MSLP
reduction. I retargeted the front matter to the current incumbent
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`; the implementation should create
a short side-by-side current-incumbent factory, for example
`dino_ri2m_mslp_offset`, and must leave `surface_pressure`,
`geopotential_500`, `2m_temperature`, `10m_u_component_of_wind`, the forecast
trajectory, and fixed protocols unchanged. Scorer should reuse the cached
incumbent artifacts from commit `3992244f20b2a938fdd96f8904f3749f5505670d` and
must not run `golden`.
