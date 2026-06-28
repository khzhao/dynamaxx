---
schema_version: 1
slug: pressure-aware-sigma-layer-grid
title: Use a Pressure-Aware Sigma Layer Grid
status: ready
created_at: 2026-06-16T11:56:27Z
author_role: Researcher
target_model: dinosaur_dfi
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/coordinates.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use a Pressure-Aware Sigma Layer Grid

## Hypothesis

The incumbent `dinosaur_dfi` initializes a 13-layer sigma-coordinate dycore from
WeatherBench2 pressure-level analyses, but the adapter chooses equidistant sigma
layers solely from the number of available pressure levels. The processed ERA5
state uses uneven pressure levels at 50, 100, 150, 200, 250, 300, 400, 500, 600,
700, 850, 925, and 1000 hPa. An equidistant sigma grid therefore places many
prognostic layers away from the analyzed levels that define the initial
temperature, wind, humidity, and scored 500 hPa geopotential fields.

A deterministic sigma grid whose layer interfaces are derived from the available
pressure-level interfaces should reduce pressure-to-sigma remapping error and
vertical finite-difference mismatch without adding forcing, terrain constants,
target-specific output corrections, or fitted parameters. Preserving DFI on top
of this grid should keep the accepted spin-up benefit while improving the
vertical representation that DFI is filtering.

## Mechanism

Add an adapter option for a pressure-aware sigma grid. The side-by-side candidate
should keep `apply_digital_filter_initialization=True` and use a registered name
such as `dinosaur_dfi_pressure_grid`.

The candidate should construct sigma layer boundaries from the inferred
WeatherBench2 pressure levels:

- sort the pressure levels from top to bottom;
- use fixed pressure interfaces at 0 hPa, the midpoints between adjacent pressure
  levels, and 1000 hPa;
- divide those interfaces by 1000 hPa to obtain monotone sigma boundaries from
  0 to 1;
- build `sigma_coordinates.SigmaCoordinates` from those boundaries instead of
  `SigmaCoordinates.equidistant(layer_count)`;
- leave the horizontal grid, spectral truncation, DFI window, IMEX SIL3 stepper,
  horizontal diffusion order, pressure-level output extrapolation, output
  variables, and fixed evaluation protocols unchanged.

For the current 13-level processed ERA5 subset, the resulting reference
boundaries are approximately
`[0.0, 0.075, 0.125, 0.175, 0.225, 0.275, 0.35, 0.45, 0.55, 0.65, 0.775, 0.8875, 0.9625, 1.0]`.
This keeps the grid deterministic and pressure-level informed while preserving a
terrain-following sigma coordinate under the model's evolving surface pressure.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/coordinates.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add a side-by-side `dinosaur_dfi_pressure_grid` factory so the incumbent
    `dinosaur_dfi` remains comparable.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` remains unchanged.
- Tests to update:
  - Add a helper test proving the pressure-aware boundaries are monotone, start
    at 0, end at 1, and are reproducible from the inferred pressure levels.
  - Add a no-JIT forecast test showing the pressure-aware DFI candidate preserves
    requested output variables, shape, and finite values.
  - Add a registry test confirming `dinosaur_dfi_pressure_grid` is available and
    retains `apply_digital_filter_initialization=True`.
  - Preserve default tests showing canonical `dinosaur` and incumbent
    `dinosaur_dfi` still use the existing equidistant grid.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at early and medium leads because 500 hPa becomes a native
    layer-center pressure under the reference 1000 hPa surface pressure rather
    than only an output interpolation target.
  - `mean_sea_level_pressure` and mass-field skill if the pressure-aware layer
    thicknesses reduce hydrostatic and divergence adjustment from the initial
    pressure-level remap.
  - `2m_temperature` and `10m_u_component_of_wind` may improve at short leads
    because the lowest layer center moves closer to the 925-1000 hPa analyzed
    lower troposphere than the current uniform 13-layer grid.
- Expected neutral metrics:
  - Large-scale midlatitude flow should remain close to `dinosaur_dfi` because
    the horizontal discretization, DFI, filtering, and forecast contract are
    unchanged.
- Possible regressions:
  - The thinner lowest layer may make vertical advection more sensitive near the
    surface and could trigger the early `10m_u_component_of_wind` guardrail.
  - Coarser spacing between 700 and 850 hPa could degrade some lower-tropospheric
    thermal or wind structures.
  - If the equidistant grid is acting as useful smoothing of pressure-level
    analysis noise, a pressure-aware grid could reduce that smoothing and hurt
    primary score.

## Risks

- Numerical stability:
  - Moderate. Dinosaur supports nonuniform sigma coordinates, but the smallest
    pressure-aware layer thickness is smaller than the current uniform spacing.
    The candidate must pass the fixed fast gate before any iteration scoring.
- Compute cost:
  - Negligible. The layer count, horizontal resolution, forecast length, DFI
    window, and output size remain unchanged.
- Data leakage:
  - Low. The grid is derived only from forecast-time input channel metadata and a
    fixed 1000 hPa reference surface pressure, not from future truth,
    validation scores, or learned statistics.
- Physical plausibility:
  - Good. Atmospheric primitive-equation models depend sensitively on vertical
    coordinate and layer placement; matching the computational layer interfaces
    to the pressure levels used by the analyses is a transparent numerical
    choice.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter option and one
    side-by-side registry factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_pressure_grid`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_pressure_grid --workers 4`.
  - Support for the hypothesis is a primary-score improvement of at least the
    protocol promotion threshold over `dinosaur_dfi`, preferably led by
    `geopotential_500` or `mean_sea_level_pressure` without an early 10 m wind
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_pressure_grid --workers 4`
    only after iteration promotion.
  - Validation should preserve the mass-field or lower-tropospheric direction
    rather than depending on one split-specific lead.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with sub-threshold primary movement, broad
    Z500/MSLP regression, or an early `10m_u_component_of_wind` guardrail failure
    would show that pressure-aware layer placement is not beneficial under the
    fixed WeatherBench2 contract.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/coordinates.py` currently
  constructs `SigmaCoordinates.equidistant(layer_count)` regardless of the
  inferred pressure-level spacing.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` infers the
  pressure levels from input temperature, wind, and humidity channels, then uses
  that layer count for the sigma-coordinate dycore.
- Dynamaxx processed metadata:
  `/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative/metadata.json`
  records the fixed 13 pressure levels used by this evaluation dataset.
- ECMWF ERA5 model-level guidance describes pressure on model levels as the
  middle of layers defined by model half-level pressures, supporting explicit
  layer-interface reasoning. https://confluence.ecmwf.int/plugins/viewsource/viewpagesrc.action?pageId=158636068
- ECMWF IFS Documentation, Part III, describes the IFS hybrid vertical
  coordinate as a monotonic function of pressure and surface pressure, with
  vertical discretization as a core part of the dynamics. https://www.ecmwf.int/sites/default/files/elibrary/2014/9203-part-iii-dynamics-and-numerical-procedures.pdf
- Arakawa, A. and Suarez, M. J. 1983. Vertical Differencing of the Primitive
  Equations in Sigma Coordinates. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1983)111%3C0034:VDOTPE%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of accepted `finite-pressure-level-extrapolation`, which
only made pressure-level output packing finite after the trajectory. This
proposal changes the prognostic vertical grid before initialization, DFI, and the
main rollout.

It is not a duplicate of rejected `standard-atmosphere-reference-profile`, which
changed the semi-implicit reference temperature while leaving layer placement
unchanged and produced only a `+0.00023612927630622949` iteration delta. The new
mechanism changes the vertical coordinate and remapping geometry, so it should
affect the actual initialized sigma state and vertical finite-difference weights.

It is decorrelated from the current staged ideas: unlike
`terrain-aware-surface-pressure-orography`, it does not load static terrain or
alter surface pressure/orography; unlike `held-suarez-relaxation-forcing`, it
adds no thermal relaxation or Rayleigh drag; unlike
`near-surface-anomaly-diagnostics`, it is not output-only and does not persist
target residuals. The idea is worth triage because it is lower plumbing risk
than terrain, less physically idealized than Held-Suarez forcing, and broader
than a near-surface diagnostic correction while preserving the accepted DFI
incumbent path.

## Evaluator Notes

2026-06-16T12:04:45Z - Move to `ready`.

This is the strongest current next experiment against incumbent `dinosaur_dfi`
at `cfdc344723cee1f267b892ddd924fc5d07b89f2d`. Source inspection confirms the
coordinate builder still constructs `SigmaCoordinates.equidistant(layer_count)`,
while the adapter infers the same 13 pressure levels from pressure-level
temperature and wind channels and preserves DFI through the side-by-side
`dinosaur_dfi` factory. Processed dataset metadata confirms the fixed levels are
50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, and 1000 hPa.

The mechanism is distinct from both accepted finite pressure-level
extrapolation, which repaired post-trajectory output packing, and rejected
standard-atmosphere reference profile, which altered the semi-implicit
temperature split but barely moved iteration score. This proposal changes the
prognostic sigma grid before pressure-to-sigma initialization, DFI, vertical
finite differences, and pressure-level output interpolation. Reputable-source
checks support the general premise that vertical coordinates and layer
interfaces are core numerical choices: ECMWF IFS documentation derives model
level pressure from half-level definitions plus surface pressure, and Arakawa
and Suarez discuss vertical differencing choices for sigma-coordinate primitive
equation models. Those sources do not prove this exact WeatherBench2 grid will
improve skill, so the expected gain remains empirical.

Promote as the sole ready proposal because it has the best cost-risk tradeoff:
small implementation surface, no new static data loading, no learned or
validation-tuned parameter, no output-only target correction, and a plausible
path to affect multiple scored fields through the initialized mass and
hydrostatic structure. The main risks are thinner nonuniform layers and possible
early low-level wind sensitivity; implementation should stay side-by-side as
`dinosaur_dfi_pressure_grid`, preserve the current equidistant default, and add
tests for deterministic monotone boundaries, DFI retention, finite no-JIT
forecast output, and registry availability.
