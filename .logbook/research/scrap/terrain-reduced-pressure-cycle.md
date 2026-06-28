---
schema_version: 1
slug: terrain-reduced-pressure-cycle
title: Use a Terrain-Aware Surface-to-Sea-Level Pressure Cycle Without Prognostic Orography
status: scrap
created_at: 2026-06-18T06:01:43Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
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

# Use a Terrain-Aware Surface-to-Sea-Level Pressure Cycle Without Prognostic Orography

## Hypothesis

The incumbent still treats `mean_sea_level_pressure` as model surface pressure
when a true `surface_pressure` channel is absent, and then emits the model
surface pressure back under the MSLP channel. Prior terrain-aware orography had
a large aggregate signal but failed mass-field guardrails because it changed
the prognostic lower boundary and geopotential datum too broadly.

A narrower pressure-reduction cycle can preserve the accepted flat, Strang
rollout while using static surface geopotential only to convert between MSLP
and surface pressure at initialization and output time. This targets the
surface-pressure/MSLP mismatch without adding orographic pressure-gradient
forcing, changing Z500 diagnostics, or applying an analysis residual.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_terrain_pressure`.
Preserve the accepted DFI, weak-HS forcing, hydrostatic layer initialization,
near-surface residuals, and symmetric exact Coriolis rollout.

Add an optional pressure-cycle path:

- load or inject grid-aligned static surface geopotential and convert it to
  height with the standard gravity constant, with a zero-height fallback;
- when `surface_pressure` is absent but `mean_sea_level_pressure` is present,
  derive a bounded surface-pressure estimate from MSLP, terrain height, and a
  lower-column virtual temperature diagnosed from the accepted initialized
  sigma state after log-pressure and hydrostatic layer initialization;
- initialize `log_surface_pressure` from that derived surface pressure;
- keep modal orography zero in the primitive equations and keep geopotential
  output on the incumbent path;
- at output time, diagnose `mean_sea_level_pressure` from forecast surface
  pressure using the inverse bounded hypsometric reduction and the forecast
  lowest-sigma-layer virtual temperature;
- leave `geopotential_*`, pressure-level temperature and winds, 2 m
  temperature, and 10 m wind diagnostics on the incumbent path.

This tests whether the damaging part of the older terrain experiment was the
prognostic orographic forcing/geopotential datum, while retaining a physically
necessary distinction between surface pressure and MSLP.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Static surface geopotential should be a private constructor/provider
    detail with a deterministic zero fallback.
- Tests to update:
  - Verify zero terrain reproduces the incumbent pressure fallback and MSLP
    output to roundoff.
  - Unit-test the pressure reduction and inverse reduction on an isothermal
    column with known height.
  - Verify only `log_surface_pressure` initialization and MSLP output change
    when terrain pressure cycling is enabled.
  - Verify the candidate preserves the accepted Strang Coriolis flags.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at early and medium leads if the current MSLP as
    surface-pressure fallback is a remaining deterministic diagnostic error.
  - `geopotential_500` may improve indirectly if the initialized mass column is
    less over-deep over high terrain, though Z500 output itself is unchanged.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should retain the accepted
    near-surface residual behavior.
- Possible regressions:
  - A simple pressure reduction may introduce terrain-correlated MSLP artifacts
    over very high topography.
  - Changing initialized `log_surface_pressure` without adding orographic
    forcing may alter mass/wind adjustment enough to hurt Z500 or low-level wind
    guardrails.

## Risks

- Numerical stability:
  - Moderate. The rollout remains flat and accepted, but the initialized mass
    field changes over terrain.
- Compute cost:
  - Low. The extra work is static-field loading and columnwise hypsometric
    arithmetic.
- Data leakage:
  - Low if only forecast-time initial state and static surface geopotential are
    used. Do not use positive-lead truth, validation scores, or fitted
    coefficients.
- Physical plausibility:
  - Moderate to high. MSLP and surface pressure are distinct fields, and
    hydrostatic pressure reduction is standard, but reduction over high terrain
    is known to be uncertain.
- Rollback complexity:
  - Low. Remove one option, one factory/export, one registry entry, and focused
    tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_terrain_pressure`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_terrain_pressure --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    mainly from MSLP, with no early Z500, MSLP, or 10 m wind guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_terrain_pressure --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A guardrail failure resembling the older terrain/orography experiment, or a
    clean near-zero MSLP movement, would show that this pressure-cycle subset is
    either harmful or too weak under the fixed protocol.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  uses `mean_sea_level_pressure` as a surface-pressure fallback and emits the
  same forecast surface-pressure field for both surface pressure and MSLP.
- History: `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography/decision.md`
  rejected full terrain/orography because mass-field guardrails failed despite
  a large aggregate signal.
- History: `.logbook/history/2026-06-16_15-28-07_mass-diagnostic-analysis-residuals/decision.md`
  rejected decaying mass residuals as sub-threshold, so this proposal uses a
  physical pressure reduction rather than an analysis residual.
- ECMWF Open Data parameter documentation lists `sp` surface pressure and `msl`
  mean sea level pressure as distinct fields.
  https://www.ecmwf.int/en/forecasts/datasets/open-data
- ECMWF ERA5 model-level documentation describes surface pressure,
  geopotential at the surface, and conversion of surface geopotential to height.
  https://confluence.ecmwf.int/plugins/viewsource/viewpagesrc.action?pageId=158636068
- Pauley, P. M. 1998. An Example of Uncertainty in Sea Level Pressure
  Reduction. Weather and Forecasting.
  https://doi.org/10.1175/1520-0434(1998)013%3C0833:AEOUIS%3E2.0.CO;2
- Mohr, M. 2004. Problems with the Mean Sea Level Pressure Field over the
  Western United States. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2004)132%3C1952:PWTMSL%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of `terrain-aware-surface-pressure-orography`: it keeps
prognostic orography at zero, does not alter sigma geopotential output, and does
not feed surface height into pressure-gradient tendencies. It is also not a
mass-residual revival because it does not add a decaying analysis-minus-model
correction. The proposal explicitly preserves the accepted Strang incumbent and
isolates only the pressure-coordinate/MSLP conversion question.

## Evaluator Notes

### 2026-06-18T06:07:51Z

Decision: move to `scrap`.

The physical distinction between surface pressure and MSLP is real, and source
inspection confirms the incumbent currently uses `mean_sea_level_pressure` as a
surface-pressure fallback and then emits forecast surface pressure for both
`surface_pressure` and `mean_sea_level_pressure`. However, this proposal is not
ready for the current loop because the required static surface geopotential is
not available through `ForecastInput` or the dycore registry factory. The data
layer can read constants, but the model API currently passes only dynamic state
channels, coordinates, and timing. A zero-terrain fallback would make the
candidate essentially incumbent-equivalent, while hard-coding a dataset path or
changing evaluation plumbing would exceed a single model-selection proposal.

Prior terrain and pressure evidence also argues against spending a run here.
The full terrain/orography candidate had a huge aggregate primary gain but
failed early Z500 and MSLP RMSE guardrails catastrophically; pressure-aware
vertical coordinates and pressure anchoring were rejected; mass diagnostic
residuals were safe but sub-threshold; and output-remap experiments showed that
metric-facing pressure diagnostics can redistribute RMSE badly. This narrower
cycle is not a byte-for-byte duplicate, but it inherits enough implementation
and guardrail risk that it should be scrapped until a separate infrastructure
change exposes static constants cleanly to dycores.
