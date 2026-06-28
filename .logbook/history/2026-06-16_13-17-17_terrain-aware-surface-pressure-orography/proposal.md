---
schema_version: 1
slug: terrain-aware-surface-pressure-orography
title: Add Terrain-Aware Surface Pressure and Orography
status: ready
created_at: 2026-06-16T10:52:48Z
author_role: Researcher
target_model: dinosaur_dfi
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add Terrain-Aware Surface Pressure and Orography

## Hypothesis

The current `dinosaur_dfi` incumbent still runs on a flat planet: the adapter
passes zero modal orography into the primitive equations, computes output
geopotential with zero surface height, and falls back to
`mean_sea_level_pressure` as the sigma-coordinate surface pressure when
`surface_pressure` is absent. ERA5 and WeatherBench-style inputs distinguish
surface pressure from mean sea-level pressure, especially over terrain. Treating
sea-level pressure as surface pressure makes high-terrain columns too deep,
misplaces sigma layers, and weakens the hydrostatic link between pressure,
geopotential, and mass fields.

A terrain-aware candidate should improve `mean_sea_level_pressure` and
`geopotential_500` by using forecast-time static orography and a physically
consistent surface pressure estimate instead of the flat-planet fallback. This is
not another pressure-level extrapolation repair: it changes the mass coordinate
and orographic geopotential used by the dycore and diagnostics, while preserving
the finite output contract established by the accepted baseline.

## Mechanism

Add an optional adapter path that supplies grid-aligned static surface height to
the Dinosaur equation and output diagnostics. The side-by-side candidate should
keep DFI enabled and use a new registered model name such as
`dinosaur_dfi_terrain`.

The candidate mechanism should:

- Load or accept static `orography` for the WeatherBench2 grid. If the stored
  constant is surface geopotential, convert it to meters by dividing by gravity;
  if it is already height, keep it in meters after a unit check.
- Convert the gridpoint terrain to filtered modal orography with the existing
  Dinosaur spectral helpers before constructing the primitive-equation object.
- Replace the zero-orography argument in `_trajectory_function` with the filtered
  modal terrain, and pass the same terrain into
  `primitive_equations.get_geopotential_on_sigma` during output packing.
- Replace the current MSLP-as-surface-pressure fallback with a terrain-aware
  surface pressure estimate when `surface_pressure` is absent. A specific
  implementable path is to use pressure-level geopotential, the static terrain,
  and `vertical_interpolation.get_surface_pressure` to infer surface pressure
  from the lead-zero column. If neither surface pressure nor enough geopotential
  information is present, keep the current fallback.
- Emit `mean_sea_level_pressure` from model surface pressure using a simple
  bounded hydrostatic reduction based on lowest-model-layer temperature and
  terrain height, instead of returning raw surface pressure under the MSLP name.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add a side-by-side factory for `dinosaur_dfi_terrain` so the incumbent
    `dinosaur_dfi` remains comparable.
- API changes:
  - No public `DycoreModel.forecast(ForecastInput) -> WeatherState` change is
    required. The model can lazily cache grid-aligned constants internally or
    accept an optional private terrain provider at construction time.
- Tests to update:
  - Add a deterministic no-JIT forecast test showing nonzero terrain preserves
    output shape, requested variables, and finite values.
  - Add a helper test that MSLP fallback is not used as surface pressure when
    terrain and pressure-level geopotential are available.
  - Add a diagnostic test that output geopotential includes surface geopotential
    from terrain and that the zero-terrain default reproduces current behavior.
  - Add registry tests confirming `dinosaur_dfi_terrain` is available and still
    has `apply_digital_filter_initialization=True`.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at most leads, especially over major terrain where
    the current raw-surface-pressure-as-MSLP diagnostic is physically wrong.
  - `geopotential_500` at days 1-7 if terrain-aware hydrostatic columns and
    orographic pressure-gradient tendencies reduce mass-field imbalance.
  - Primary score could improve without relying on a near-surface residual,
    because two mass-field targets are directly affected.
- Expected neutral metrics:
  - `2m_temperature` may be mostly neutral because this proposal does not add a
    land surface, radiation, or boundary-layer temperature diagnostic.
- Possible regressions:
  - `10m_u_component_of_wind` can regress if orographic pressure gradients excite
    low-level wind errors. The rejected hyperdiffusion history shows the early
    10 m wind gate is sensitive.
  - MSLP may worsen near steep terrain if the sea-level reduction is too simple
    or if the stored orography units are mishandled.

## Risks

- Numerical stability:
  - Moderate. Nonzero orography introduces stationary pressure-gradient forcing
    that the flat incumbent avoided. Spectral filtering of terrain is required to
    reduce Gibbs ringing and fast-wave noise.
- Compute cost:
  - Low. Static terrain preparation is one grid-sized field per process, and the
    forecast step cost is unchanged apart from existing orography terms.
- Data leakage:
  - Low. Static orography is a forecast-time constant and does not use future
    verification fields, validation scores, or fitted parameters.
- Physical plausibility:
  - Good. Surface pressure, terrain-following coordinates, orographic
    geopotential, and MSLP reduction are standard components of primitive-equation
    NWP models.
- Rollback complexity:
  - Low to moderate. The side-by-side registry candidate can be removed cleanly,
    but tests must protect the default zero-terrain behavior.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_terrain`.
  - Require finite forecasts, zero diagnostic issues, and no obvious MSLP
    outliers over high terrain.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_terrain --workers 4`.
  - Support for the hypothesis is a primary-score improvement over
    `dinosaur_dfi`, preferably led by `mean_sea_level_pressure` or
    `geopotential_500` without an early-lead `10m_u_component_of_wind` guardrail
    failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_terrain --workers 4`
    only after iteration promotion.
  - Validation should show the same mass-field direction, not a gain isolated to
    one split or one lead.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with worse primary score, broad Z500/MSLP
    regressions, or an early 10 m wind gate failure would show that terrain
    forcing and MSLP reduction are not beneficial under this fixed protocol.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  builds zero modal orography, falls back from missing `surface_pressure` to
  `mean_sea_level_pressure`, and returns surface pressure for both
  `surface_pressure` and `mean_sea_level_pressure`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  already includes `orography_tendency`, `filtered_modal_orography`, and
  geopotential diagnostics that accept nonzero nodal orography.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  implements `get_surface_pressure` from pressure-level geopotential and
  orography.
- ECMWF open data parameter documentation lists surface pressure (`sp`) and mean
  sea-level pressure (`msl`) as distinct surface fields.
  https://www.ecmwf.int/en/forecasts/datasets/open-data
- ECMWF IFS Documentation, CY48R1 Part III, describes the hybrid vertical
  coordinate using fixed A/B coefficients and the surface pressure field.
  https://www.ecmwf.int/sites/default/files/elibrary/2023/81369-ifs-documentation-cy48r1-part-iii-dynamics-and-numerical-procedures.pdf
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review. https://journals.ametsoc.org/view/journals/mwre/109/4/1520-0493_1981_109_0758_aeaamc_2_0_co_2.xml
- Rasp, S. et al. 2023. WeatherBench 2: A benchmark for the next generation of
  data-driven global weather models. https://arxiv.org/abs/2308.15560

## Researcher Notes

This proposal is distinct from accepted `finite-pressure-level-extrapolation`,
which only made pressure-level output finite below the diagnosed model column.
Here the state coordinate, orographic geopotential, and MSLP diagnostic are made
terrain-aware before scoring.

It is also distinct from staged `near-surface-anomaly-diagnostics`: it does not
persist initial 2 m temperature or 10 m wind residuals and is aimed primarily at
mass-field consistency. It is distinct from staged
`held-suarez-relaxation-forcing` because it adds static lower-boundary geometry
rather than thermal relaxation or Rayleigh drag. The current incumbent
`dinosaur_dfi` has validation mean skill still negative for MSLP and Z500, with
day-15 MSLP bias about +45 Pa, so a mass-coordinate proposal remains
scientifically motivated.

## Evaluator Notes

2026-06-16T10:58:43Z - Move to `staging`.

This is scientifically credible but not the best next implementation target.
Source inspection confirms the incumbent still passes zero modal orography into
the primitive equations, passes zero nodal orography to sigma-level geopotential
diagnostics, falls back from missing `surface_pressure` to
`mean_sea_level_pressure`, and emits model surface pressure for both
`surface_pressure` and `mean_sea_level_pressure`. ECMWF parameter documentation
supports treating `sp` and `msl` as distinct surface fields, and IFS dynamics
documentation supports the importance of surface pressure and orography in
vertical-coordinate dynamics.

The implementation risk is higher than the proposal text implies. The local
processed constants store exposes `geopotential_at_surface`, `land_sea_mask`,
and `soil_type`, not an `orography` constant channel, so the implementation must
convert surface geopotential to height with an explicit unit check. The fixed
evaluation `ForecastInput` currently contains time-varying state channels only;
year-2020 state metadata includes `mean_sea_level_pressure` but no
`surface_pressure`. A terrain-aware candidate therefore needs private static
constant loading or an injected terrain provider without changing the public
forecast API, plus a robust pressure-level geopotential fallback for diagnosed
surface pressure.

Keep staged behind `standard-atmosphere-reference-profile`. Terrain has a
stronger direct mass-field mechanism than the older staged output diagnostic,
but nonzero orography can excite pressure-gradient and low-level wind errors,
and the simple MSLP reduction could become a target-specific diagnostic repair
if implemented too narrowly. Reconsider for ready after the lower-surface-area
reference-profile experiment, or if a Researcher narrows the data-loading and
MSLP-reduction plan with tests that preserve the zero-terrain incumbent path.

2026-06-16T12:04:45Z - Keep in `staging` after re-triage against
`dinosaur_dfi`.

This rises in relevance now that `standard-atmosphere-reference-profile` was
rejected with only a sub-threshold `+0.00023612927630622949` iteration delta.
The history explicitly points future work toward mass-coordinate/orography
handling, and source inspection still confirms the incumbent uses zero modal
orography, zero nodal orography for sigma geopotential diagnostics, and
`mean_sea_level_pressure` as the surface-pressure fallback when no
`surface_pressure` channel is present.

Keep it behind `pressure-aware-sigma-layer-grid`, not in ready. Terrain remains
more invasive: it needs private or injected static constant access, conversion
from `geopotential_at_surface` to height, filtered modal orography, diagnosed
surface pressure from pressure-level geopotential when possible, and an MSLP
reduction that must not become a narrow scoring patch. Nonzero orography can
also excite pressure-gradient noise and low-level wind errors, which is a known
guardrail risk from the rejected hyperdiffusion experiment. This is the best
staged follow-up if the pressure-aware grid is diagnostic-clean but
insufficient, especially if a Researcher narrows the surface-pressure and MSLP
diagnostic plan with tests that preserve the incumbent flat path.

2026-06-16T13:02:50Z - Move to `ready` after Iteration 7 re-triage
against `dinosaur_dfi`.

The ready directory is empty, there are no new proposal files, and the two
recently scored follow-ups changed the ranking. The standard-atmosphere
reference profile was diagnostic-clean but produced only a sub-threshold
`+0.00023612927630622949` iteration delta, so another small reference-split
experiment is not the right next step. The pressure-aware sigma grid was also
diagnostic-clean but regressed the iteration primary score by
`-0.10322710509965427`, so a new candidate should avoid changing the accepted
equidistant sigma layer placement.

This terrain proposal is the strongest remaining implementable idea because it
keeps the incumbent DFI path and vertical grid while attacking a larger physical
inconsistency: the adapter still initializes with zero modal orography, computes
sigma-level geopotential with zero nodal orography, uses
`mean_sea_level_pressure` as the fallback surface pressure, and emits model
surface pressure for both `surface_pressure` and `mean_sea_level_pressure`.
The scientific distinction between surface pressure and MSLP is supported by
ECMWF parameter documentation, and the implementation has local hooks:
`WeatherBench2Source.read_constants`, `primitive_equations.filtered_modal_orography`,
`primitive_equations.get_geopotential_on_sigma`, and
`vertical_interpolation.get_surface_pressure`.

Promote exactly one ready idea with constraints. The implementation should be a
side-by-side `dinosaur_dfi_terrain` candidate that preserves DFI, preserves the
fixed forecast/evaluation protocol, reads or injects static
`geopotential_at_surface` as terrain, keeps the accepted sigma grid, and uses no
validation-tuned constants. The main risks remain nonzero-orography
pressure-gradient noise and a too-simple MSLP reduction, but this has the best
current benefit-to-risk ratio because it can affect both `mean_sea_level_pressure`
and `geopotential_500` while producing useful evidence even if the candidate
fails.
