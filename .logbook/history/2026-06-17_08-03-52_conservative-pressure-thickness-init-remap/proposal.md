---
schema_version: 1
slug: conservative-pressure-thickness-init-remap
title: Conservative Pressure-Thickness Initialization Remap
status: ready
created_at: 2026-06-17T07:56:48Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Conservative Pressure-Thickness Initialization Remap

## Hypothesis

The accepted log-pressure, hydrostatic-thickness, and layer-mean hydrostatic
temperature initialization results show that initialization geometry is a
high-leverage axis for this incumbent. The current pressure-to-sigma
initialization still samples analyzed pressure-level fields at sigma-layer
centers. That pointwise remap can alias vertical shear and thermal gradients
when sigma layers represent finite pressure thicknesses, especially near the
lower troposphere where the fixed metrics are sensitive to `2m_temperature`,
`mean_sea_level_pressure`, and `10m_u_component_of_wind`.

A pressure-thickness conservative remap should better preserve column-integral
thermal and momentum structure when converting same-time analyses to the
Dinosaur sigma layers. It is materially distinct from the accepted layer-mean
hydrostatic temperature initialization because it changes how all initialized
three-dimensional fields are transferred onto sigma layers; it does not propose
another geopotential-thickness temperature derivative.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init`.
Preserve DFI, weak Held-Suarez thermal relaxation, near-surface residual
diagnostics, log-pressure initialization, layer-mean hydrostatic temperature
estimation, zero orography, the existing sigma grid, the output path, and the
forecast API.

Add an optional initialization remap that treats source pressure levels as
finite layers bounded by log-pressure midpoints and treats target sigma levels
as finite pressure layers bounded by `sigma_coords.boundaries * surface_pressure`.
For each column, compute overlap weights in pressure thickness or log-pressure
thickness and initialize temperature, horizontal winds, and passive humidity
from weighted layer averages instead of point interpolation at sigma centers.
Use bounded edge behavior for target layers extending above the top source layer
or below the bottom source layer; do not alter output interpolation.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_vertical_interpolation.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init`.
- API changes:
  - None. Forecast inputs, outputs, variables, lead times, and metrics remain
    unchanged.
- Tests to update:
  - Add a vertical-interpolation test for pressure-layer overlap weights,
    bounded edge behavior, and exact preservation of a column-constant field.
  - Add a column-integral preservation test for a simple linear profile where
    source and target layer boundaries differ.
  - Verify the candidate factory preserves all incumbent flags and changes only
    the initialization remap option.
  - Verify the candidate is registered and can produce a finite non-JIT smoke
    forecast with existing Dinosaur fixtures.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium and long leads if
    initialization currently aliases column thickness or pressure-gradient
    structure.
  - `2m_temperature` at early and medium leads if lower-layer thermal content is
    initialized more consistently than by center sampling.
  - `10m_u_component_of_wind` may improve if vertical wind shear is less noisy
    after pressure-to-sigma transfer.
- Expected neutral metrics:
  - Large-scale day-1 fields should remain close to the incumbent because this
    is an initialization-only remap and preserves the accepted forecast
    trajectory machinery.
- Possible regressions:
  - Layer averaging may smooth sharp jets or inversions and could spend some of
    the incumbent's small early 10 m wind guardrail margin.
  - If the source WeatherBench pressure-level channels are best interpreted as
    point values rather than layer means, conservative remapping could introduce
    a representation mismatch.

## Risks

- Numerical stability:
  - Low to moderate. The mechanism is bounded and initialization-only, but it
    changes all three-dimensional initialized fields.
- Compute cost:
  - Low. Overlap weights are computed only during initialization; evaluation
    should remain compatible with `--workers 4`.
- Data leakage:
  - Low. It uses only same-time input analysis fields already consumed by the
    incumbent.
- Physical plausibility:
  - Moderate to high. Finite-volume remapping is a standard way to preserve
    column-integrated quantities across vertical grids, but the pressure-level
    analysis semantics are approximate.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter flag, one remap helper,
    and one side-by-side factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean but sub-threshold iteration delta would show that center-sampled
    initialization is not a material remaining error source. Any early
    `10m_u_component_of_wind` guardrail failure would show that the added
    vertical averaging damages resolved shear too much.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  initializes pressure-level fields by calling
  `interp_pressure_to_sigma_log_pressure` before modal projection.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  already contains conservative regridding utilities and interpolation policies
  that can guide a pressure-layer overlap implementation.
- History:
  `.logbook/history/2026-06-17_00-55-17_log-pressure-sigma-initialization/decision.md`
  accepted log-pressure initialization with iteration delta
  `+0.006318821843572353` and validation delta `+0.007447672526236682`.
- History:
  `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted layer-mean hydrostatic temperature initialization with iteration
  delta `+0.004688970185515728` and validation delta
  `+0.005305927605172567`.
- Lin, S.-J. 2004. A Vertically Lagrangian Finite-Volume Dynamical Core for
  Global Models. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2004)132%3C2293:AVLFDC%3E2.0.CO;2
- Lin, S.-J. and Rood, R. B. 1996. Multidimensional Flux-Form
  Semi-Lagrangian Transport Schemes. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Lin, S.-J. 1997. A finite-volume integration method for computing pressure
  gradient force in general vertical coordinates. Quarterly Journal of the
  Royal Meteorological Society.

## Researcher Notes

This is not a duplicate of staged `bounded-log-pressure-init-extrapolation`.
That staged idea changes only edge extrapolation outside the analyzed pressure
stack; this proposal changes the interior remap from point sampling to finite
pressure-layer overlap while keeping bounded edge behavior as a safety detail.

It is also distinct from rejected `pressure-aware-sigma-layer-grid`, which
changed the model vertical grid and degraded primary score sharply. Here the
sigma grid, primitive equations, DFI, weak Held-Suarez forcing, near-surface
residual correction, and output contract are preserved. The proposal uses the
positive initialization history while avoiding another hydrostatic-temperature
derivative variant.

## Evaluator Notes

2026-06-17T08:00:01Z - Move to `ready`; rank 1 of 5 active ideas and sole
ready recommendation for the next iteration.

This is the strongest next experiment because it stays on the only recent
high-yield axis: same-time initialization geometry. The accepted log-pressure
initialization improved iteration by `+0.006318821843572353` and validation by
`+0.007447672526236682`; hydrostatic-thickness initialization improved
iteration by `+0.0668578150568` and validation by `+0.06740481815858179`; the
current layer-mean hydrostatic initialization then added
`+0.004688970185515728` iteration and `+0.005305927605172567` validation. This
proposal preserves those mechanisms, DFI, weak Held-Suarez relaxation,
near-surface residual correction, zero orography, vertical advection, output
packing, and the fixed forecast API while changing only pressure-to-sigma
initialization of three-dimensional fields.

It is not a duplicate of staged bounded edge extrapolation. Bounded
extrapolation changes only out-of-range edge behavior; this proposal changes
the interior pressure-to-sigma transfer from center sampling to finite
pressure-layer overlap, with bounded edges as a safety detail. Source
inspection confirms the relevant adapter hook is localized in
`weather_state_to_dinosaur_state`, and `vertical_interpolation.py` already has
conservative regrid weight utilities that reduce implementation risk. The
proposal is also narrower than rejected `pressure-aware-sigma-layer-grid`,
which changed the vertical grid and lost `-0.10322710509965427` iteration
primary, and avoids the rejected log-pressure output-remap path that produced
54 variable+lead RMSE guardrail failures.

The main caveat is representation mismatch: WeatherBench pressure-level inputs
may behave more like point samples than layer means, so the remap could smooth
useful wind shear or thermal inversions. That risk is acceptable for a single
ready slot because the change is initialization-only, side-by-side, low cost,
and scientifically supported by standard finite-volume remapping literature.
If implemented, tests should prove column-constant preservation, bounded edge
behavior, and unchanged incumbent flags. Watch short-lead `2m_temperature` and
`10m_u_component_of_wind`, the channels that prior initialization candidates
most often moved.
