---
schema_version: 1
slug: geopotential-datum-output-correction
title: Add a Column Geopotential Datum Output Correction
status: scrap
created_at: 2026-06-17T06:38:45Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Add a Column Geopotential Datum Output Correction

## Hypothesis

The adapter runs the Dinosaur primitive equations with zero orography and then
reconstructs pressure-level geopotential hydrostatically from the model sigma
state. The rejected terrain-aware orography experiment showed that inserting
spatial orography into the prognostic dynamics can improve aggregate primary
score while badly failing early Z500/MSLP guardrails. The rejected mass
diagnostic residual showed that a broad decaying residual for both MSLP and
geopotential was safe but too small after near-surface residuals.

A narrower output-only geopotential datum correction may recover part of the
zero-orography vertical-reference mismatch without changing prognostic pressure
gradients, MSLP, or any wind/temperature output. Geopotential is defined
relative to a reference datum, so a columnwise offset diagnosed at initialization
is physically different from changing the evolving mass field.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_geopotential_datum`.
Preserve incumbent trajectory construction, DFI, weak Held-Suarez relaxation,
near-surface residual diagnostics, log-pressure and layer-mean hydrostatic initialization,
zero prognostic orography, finite output interpolation, spectral resolution, and
inner step.

Add a guarded output option for geopotential pressure-level channels only:

- after converting the raw trajectory to a `WeatherState`, compute the lead-zero
  raw diagnostic for each output `geopotential_<pressure_level>` channel;
- when the same analyzed geopotential channel is present in the initial state,
  compute a column offset `initial_geopotential - raw_lead_zero_geopotential`;
- apply a vertically and temporally constant column datum offset to requested
  geopotential pressure-level outputs only;
- do not alter `mean_sea_level_pressure`, `surface_pressure`,
  `2m_temperature`, winds, temperature pressure-level channels, humidity,
  prognostic state variables, or evaluation metrics.

The proposal intentionally does not use a decaying mass residual and does not
apply any correction to MSLP.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_geopotential_datum`.
- API changes:
  - None. The model emits the same requested `WeatherState` channels.
- Tests to update:
  - Unit-test that a geopotential datum correction changes only
    `geopotential_*` channels and leaves MSLP, surface pressure, near-surface
    channels, winds, temperature, and humidity unchanged.
  - Verify lead-zero geopotential equals the initial analyzed geopotential when
    the channel is available.
  - Verify the candidate preserves all incumbent flags and the registry model
    name.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` RMSE and skill, especially at early and medium leads, if
    a persistent datum offset from zero-orography reconstruction remains after
    hydrostatic initialization.
  - Primary score may improve modestly without perturbing the accepted
    near-surface and pressure-mass behavior.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and
    `mean_sea_level_pressure` should be exactly neutral apart from roundoff
    because their output channels and the forecast trajectory are unchanged.
- Possible regressions:
  - A time-constant datum offset could become stale for pressure-level
    geopotential at long leads, especially in rapidly developing systems.
  - If the current Z500 error is mostly dynamical rather than a vertical datum
    mismatch, the primary-score movement may be too small to clear promotion.

## Risks

- Numerical stability:
  - Low. This is output-only and does not feed back into the trajectory.
- Compute cost:
  - Low. It adds one lead-zero residual calculation and channel update for
    geopotential outputs.
- Data leakage:
  - Low to moderate. The correction uses only same-time initial analysis fields,
    like the accepted near-surface residual correction, but it should be
    scrutinized because it is an output diagnostic correction.
- Physical plausibility:
  - Moderate. A geopotential datum offset is physically interpretable under the
    zero-orography adapter, but a constant offset is a simplified proxy rather
    than a full terrain-following pressure reduction.
- Rollback complexity:
  - Low. It can be removed as one guarded option and one side-by-side factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_geopotential_datum`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_geopotential_datum --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`, clean
    diagnostics, no fixed RMSE guardrail failure, and no material regression in
    non-geopotential target variables.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_geopotential_datum --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean but sub-threshold iteration delta would show that the remaining Z500
    error is not a simple datum mismatch. Any Z500 guardrail failure or
    unexpected movement in MSLP, 2 m temperature, or 10 m wind would argue
    against this output correction.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` reconstructs
  pressure-level geopotential from the sigma-coordinate state using zero
  orography in `dinosaur_state_to_weather_state`.
- History: `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography/decision.md`
  rejected prognostic terrain-aware orography because it failed early Z500 and
  MSLP RMSE guardrails despite a large aggregate primary gain.
- History: `.logbook/history/2026-06-16_15-28-07_mass-diagnostic-analysis-residuals/decision.md`
  rejected broad mass diagnostic residuals because the safe primary-score gain
  was only `+0.00042505322207886387`, below promotion.
- ECMWF Parameter Database entry 156 defines geopotential height as height
  relative to potential energy, calculated by dividing geopotential by standard
  gravity. https://codes.ecmwf.int/grib/param-db/156
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- ECMWF IFS Documentation Part III describes hydrostatic geopotential
  reconstruction and terrain-following vertical-coordinate treatment in the
  dynamical core.

## Researcher Notes

This is intentionally narrower than both prior failed mass-field ideas. It is
not the terrain-aware surface-pressure/orography candidate because it does not
insert orography into the prognostic pressure-gradient force or alter surface
pressure. It is not the mass diagnostic residual candidate because it does not
touch MSLP, does not use an exponential decay, and only addresses the
geopotential reference datum.

The idea should be ranked behind initialization refinements if the Evaluator
wants mechanisms with less output-correction risk. It is included because the
current incumbent still has large absolute Z500 RMSE at long leads, while prior
history says prognostic orography is too disruptive and broad mass residuals are
too weak.

## Evaluator Notes

2026-06-17T06:41:34Z - Move to `staging`; rank 3 of 4 active ideas.

This is plausible but should not be the next implementation target because it
is an output-only correction aimed directly at a scored target channel. The
mechanism is narrower than rejected terrain-aware orography: it would not feed
orography into prognostic pressure gradients, would not alter MSLP, and would
leave the forecast trajectory unchanged. It is also narrower than the rejected
mass diagnostic residual, which safely moved scores by only
`+0.00042505322207886387` after near-surface residuals. That narrower scope is
enough to keep the idea staged rather than scrapped.

The risk is protocol and guardrail relevance. Terrain-aware orography improved
aggregate primary by `+0.19845155161644534` but failed early `geopotential_500`
and `mean_sea_level_pressure` RMSE guardrails by about 36% and 32% on
iteration, respectively. The rejected log-pressure output interpolation also
shows that output-path changes can be clean diagnostically yet badly
redistribute variable-lead RMSE, with 54 guardrail failures. A constant
lead-zero geopotential datum offset could similarly improve one aggregate
component while becoming stale at longer leads or masking a dynamical error.

Stage this behind initialization refinements. If later promoted, the
implementation should be strictly side-by-side, limited to `geopotential_*`
pressure-level outputs, leave MSLP/surface pressure/winds/temperature/humidity
bitwise unchanged apart from roundoff, and include tests proving the correction
uses only same-time initial analysis fields. Any fast or iteration evidence of
unexpected movement in non-geopotential target variables should stop the idea.

2026-06-17T08:00:01Z - Keep in `staging`; retargeted to current incumbent and
rank 3 of 5 active ideas.

I updated the front matter, candidate model name, evaluation commands, and
comparison baseline to target
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
Prior notes remain above as historical context.

The idea remains plausible but below initialization remap work. The source path
still reconstructs pressure-level geopotential from zero-orography sigma
fields, and terrain-aware orography history shows there is signal in vertical
datum or terrain handling. But that same history is the warning: the terrain
candidate improved aggregate iteration primary by `+0.19845155161644534` while
failing early Z500 and MSLP RMSE guardrails badly, and log-pressure output
interpolation produced 54 variable+lead guardrail failures. The safer mass
diagnostic residual moved primary only `+0.00042505322207886387`, below
promotion.

Keep staged only as a tightly guarded output-diagnostic fallback. It should not
displace conservative initialization remapping or bounded initialization
extrapolation because it directly edits a scored output channel and could mask
a dynamical error. If promoted later, non-geopotential channels should be
verified unchanged apart from roundoff before any iteration run.

2026-06-17T09:09:07Z - Move to `scrap`; no longer recommended after latest
output-path and remap evidence.

This idea is now weaker than the new dry-consistent geopotential diagnostic and
should leave the active queue. It directly adds a lead-zero-derived residual to
a scored geopotential channel, while the dry-geopotential proposal tests a
cleaner same-trajectory diagnostic consistency question without using an
analysis-minus-model residual. Both target Z500, so keeping both active would
duplicate the next search direction while favoring the more protocol-sensitive
mechanism.

Prior history also argues against spending another full iteration on this
datum correction. Terrain-aware orography produced a large aggregate primary
gain but failed early Z500 and MSLP guardrails badly; the broad mass diagnostic
residual was safe but improved primary by only `+0.00042505322207886387`; and
log-pressure output interpolation produced 54 variable-lead RMSE guardrail
failures despite being output-only and diagnostic-clean. The latest
conservative pressure-thickness initialization remap was stable and
guardrail-clean but still regressed primary by `-0.006775878375613553`, with the
largest RMSE increases in Z500 and MSLP around days 4-8. A constant
geopotential datum offset is therefore too likely to be stale, too directly
metric-facing, or too small to clear the fixed gates.

Do not revive this unless a future diagnostic shows a persistent columnwise
Z500 offset that is separable from humidity diagnostics, pressure interpolation,
and mass-field phase errors, and unless the implementation includes strict
same-time-only provenance plus invariance tests for every non-geopotential
channel.
