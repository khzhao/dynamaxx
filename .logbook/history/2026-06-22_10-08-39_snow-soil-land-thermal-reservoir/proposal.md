---
schema_version: 1
slug: snow-soil-land-thermal-reservoir
title: Snow-Insulated Land Soil Thermal Reservoir Forcing
status: ready
created_at: 2026-06-22T07:48:53Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf
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

# Snow-Insulated Land Soil Thermal Reservoir Forcing

## Hypothesis

The accepted incumbent now has land-sea-aware `2m_temperature` residual memory
and an ocean-only bulk sensible heat flux, but land points still lack a
prognostic lower-boundary heat reservoir. Over land, medium-range screen
temperature is strongly affected by soil heat storage, snow insulation, and
surface type. The WeatherBench2 initial state includes dynamic land-surface
fields such as `soil_temperature_level_4` and `snow_depth`. A very weak
land-only thermal reservoir forcing, attenuated by snow depth, may reduce
land-side `2m_temperature` drift after the accepted residual begins to decay
without perturbing the ocean flux or changing output variables.

This is not an output-only residual-memory variant. The candidate would add a
bounded prognostic temperature tendency in the lowest sigma layer over land,
using persisted lead-zero land-surface reservoir information.

## Mechanism

Register a side-by-side candidate under a short alias, for example
`dino_land_soilflux`, that reproduces the accepted ocean-bulk incumbent and
enables one land-reservoir selector. Do not append to the full incumbent model
name, because the accepted run already exceeded filesystem filename-component
limits for long `dynamaxx-eval` artifacts.

For the candidate only:

- reuse the accepted land-sea fraction loader and keep the accepted ocean bulk
  sensible heat flux unchanged over ocean;
- for each initial condition, read `soil_temperature_level_4` when present,
  finite, positive, and grid-aligned; blend it conservatively with the lead-zero
  `2m_temperature` or lowest-layer air temperature to form a persisted land
  reservoir anchor;
- cap the reservoir-air temperature departure, for example by allowing the deep
  soil term to shift the land anchor only a few kelvin from lead-zero screen
  temperature;
- compute a land-only lowest-layer thermal tendency toward that anchor with a
  slow fixed e-folding floor, for example no faster than 10-14 days, and a small
  single-step temperature-increment cap;
- attenuate the coupling by a bounded snow-insulation factor derived from
  `snow_depth` when available, with snow-covered points approaching zero land
  reservoir exchange rather than forcing air rapidly toward deep soil;
- leave vorticity, divergence, log-surface pressure, tracers, pressure-level
  interpolation, output residual corrections, and target variables unchanged
  except through the resulting lowest-layer thermal trajectory;
- fall back exactly to the accepted incumbent if land fraction, soil
  temperature, snow depth, or the tendency diagnostics are unavailable,
  nonfinite, or shape-incompatible.

The mechanism is a land substrate heat-storage tendency, not a generic turbulent
bulk flux coefficient change. It tests the complementary land-side boundary
condition after the accepted ocean-only flux demonstrated strong leverage.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for selector flags,
    initial-state land reservoir extraction, finite validation helpers, forcing
    composition, and the short-alias factory.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` for factory export.
  - `src/dynamaxx/dycore/registry.py` for a short candidate name such as
    `dino_land_soilflux`.
  - `tests/dycore/models/dinosaur/` and `tests/dycore/test_registry.py` for
    focused forcing, fallback, factory, and registry tests.
- Registry changes:
  - Add exactly one short side-by-side alias. The alias should instantiate the
    full accepted incumbent behavior plus the land-reservoir selector.
- API changes:
  - None. `DycoreModel.forecast`, initial-state format, output variables, target
    variables, lead times, splits, and metrics remain unchanged.
- Tests to update:
  - Pure-ocean points reproduce the accepted incumbent exactly.
  - Pure-land snow-free points receive a bounded tendency toward the land
    reservoir anchor.
  - Increasing snow depth monotonically weakens the land-reservoir coupling.
  - Missing or invalid soil/snow channels reproduce the accepted incumbent.
  - Only lowest-layer temperature tendency changes directly; wind, pressure,
    tracer, and output variable lists are unchanged.
  - The short alias is registered and does not extend the full incumbent name.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3-15 over land, especially where the current dry
    dycore drifts away from the initialized land thermal state after residual
    memory decays.
  - Small secondary improvements in `mean_sea_level_pressure` or
    `geopotential_500` are possible if lower-column thermal drift is reduced
    without creating strong column expansion.
- Expected neutral metrics:
  - Ocean `2m_temperature` should remain governed by the accepted ocean bulk
    sensible heat flux.
  - `10m_u_component_of_wind` should be nearly neutral because no momentum
    tendency or wind diagnostic is changed.
- Possible regressions:
  - Deep soil temperature can be out of phase with screen temperature during
    strong diurnal or synoptic transitions, so the anchor blend and caps must be
    conservative.
  - Even weak land heating or cooling can alter MSLP through hydrostatic
    thickness if applied too strongly.

## Risks

- Numerical stability:
  - Low to moderate. The tendency is local and capped, but it changes the
    prognostic thermal state over land every positive-time step.
- Compute cost:
  - Low. Adds one or two initial fields and local arithmetic; no new transforms,
    workers, lead times, or output channels.
- Data leakage:
  - Low. Uses only lead-zero land-surface fields and static land fraction, never
    future verification data.
- Physical plausibility:
  - Moderate to high. Soil heat storage and snow insulation are first-order land
    surface controls on screen temperature, but this is deliberately a stripped
    reservoir surrogate rather than a full land-surface model.
- Rollback complexity:
  - Low. Remove one selector, one forcing/helper path, one factory/export, one
    registry alias, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_land_soilflux`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_land_soilflux --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    accepted incumbent, clean diagnostics, and no fixed early-lead or
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_land_soilflux --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta, especially one dominated
    by land `2m_temperature` or MSLP/Z500 regressions, would show that the
    accepted land residual and weak-HS equilibrium already capture the useful
    land thermal signal or that this simple soil reservoir is too crude.

## Citations

- Local history:
  `.logbook/history/2026-06-21_23-32-41_land-sea-contrast-surface-temperature/decision.md`
  accepted a large gain from separating land and ocean `2m_temperature`
  behavior.
- Local history:
  `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/decision.md`
  accepted an ocean-only prognostic heat-exchange process, motivating a
  complementary land-side lower-boundary test.
- Local source:
  `src/dynamaxx/dycore/models/dinosaur/xarray_utils.py` lists
  `soil_temperature_level_4` and `snow_depth` as dynamic single-level
  WeatherBench2 channels available in the initial state.
- Noilhan, J. and Planton, S. 1989. "A Simple Parameterization of Land Surface
  Processes for Meteorological Models." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1989)117%3C0536:ASPOLS%3E2.0.CO;2
- Viterbo, P. and Beljaars, A. C. M. 1995. "An Improved Land Surface
  Parameterization Scheme in the ECMWF Model and Its Validation." Journal of
  Climate.
  https://doi.org/10.1175/1520-0442(1995)008%3C2716:AILSPS%3E2.0.CO;2
- Dutra, E., Balsamo, G., Viterbo, P., Miranda, P. M. A., Beljaars, A.,
  Schar, C., and Elder, K. 2010. "An Improved Snow Scheme for the ECMWF Land
  Surface Model: Description and Offline Validation." Journal of
  Hydrometeorology.
  https://doi.org/10.1175/2010JHM1249.1
- ECMWF OpenIFS physical-process documentation lists surface exchange and
  turbulent mixing as represented subgrid processes in the IFS.
  https://confluence.ecmwf.int/display/OIFS/3.2%2BOpenIFS%3A%2BPhysical%2BProcesses

## Researcher Notes

This is deliberately separate from the accepted ocean bulk heat-flux mechanism.
It leaves ocean points on the accepted incumbent path and tests whether land
surface thermal storage supplies additional recoverable `2m_temperature` skill.
It is also distinct from staged generic bulk-surface heat-flux proposals because
the forcing is wind-independent, land-only, tied to soil heat storage, and
attenuated by snow insulation. It avoids recent failed residual-memory variants
by changing the prognostic lower-layer temperature tendency rather than only
blending forecast outputs.

## Evaluator Notes

### 2026-06-22T07:53:02Z

Decision: move to `staging`, not `ready`.

The scientific premise is plausible but the proposal is a weaker next experiment
than `sst-sea-ice-ocean-flux-anchor`. External checks support the broad land
surface claims: ECMWF training material describes land-surface modeling with
soil, snow, vegetation, lakes, coastal water, and a 4-layer soil heat and water
budget, with each surface tile coupled to the lowest atmospheric model level:
https://events.ecmwf.int/event/435/contributions/4690/attachments/2631/4840/1_Boussetta_surface_intro.pdf.
ECMWF soil-temperature verification highlights land-atmosphere processes such
as snowpack melting and heat diffusion in soil as relevant to near-surface
forecast performance:
https://www.ecmwf.int/en/elibrary/73888-soil-temperature-ecmwf-assessment-using-ground-based-observations.
Dutra et al. 2010 support the snow-insulation claim for ECMWF land-surface
modeling, including reduced soil freezing and changed basal heat flux under the
improved snow scheme:
https://research.fs.usda.gov/download/treesearch/36970.pdf.

Keep staged because this is a broader prognostic land thermal forcing, not just
a better selector inside an already accepted ocean process. The deep
`soil_temperature_level_4` anchor can be phase-lagged relative to screen
temperature during synoptic transitions, and even a weak land-only lowest-layer
thermal tendency can perturb hydrostatic thickness, MSLP, and Z500. The active
staging queue already contains several lower-column or screen-temperature
thermal ideas, including `lower-column-thermal-iau-spinup`,
`solar-weighted-thermal-tendency`, `lead-bounded-screen-temperature-anomaly`,
and the older generic `bulk-surface-sensible-heat-flux`; this proposal is not an
exact duplicate, but it belongs behind the narrower SST/sea-ice refinement.

If promoted later, require a short alias such as `dino_land_soilflux`, exact
incumbent fallback for missing or invalid land, soil, and snow inputs, very
conservative coupling and step caps, and explicit tests that ocean points remain
bitwise on the accepted ocean-bulk incumbent path.

### 2026-06-22T10:07:23Z

Decision: re-triage from `staging` to `ready`; rank 1 current implementation
recommendation.

What changed: the previously preferred SST/sea-ice ocean-anchor refinement was
implemented and rejected with only `+0.0000030296370109317294` iteration
primary-score delta against the cached ocean-bulk incumbent. That result makes
further boundary-anchor refinements less attractive for the next iteration. The
two new proposals are plausible but weaker as immediate evaluation targets:
`exact-ocean-bulk-heat-flux-split` is likely to be near numerical noise under
the accepted 900 second inner step and 6 day minimum e-folding cap, and
`lake-ice-thermal-reservoir` is geographically narrow for a global primary
metric.

This land-soil reservoir remains implementable and now has the best cost-risk
tradeoff among inspected ideas. It targets a broader land area than the lake
proposal, is complementary to the accepted ocean-bulk flux, and follows the
same bounded lower-layer thermal-tendency pattern that already produced a large
accepted ocean-side gain. The main risk remains phase error from deep soil
temperature and hydrostatic pressure coupling, so the Implementer should keep
the coupling slow, cap the anchor departure and per-step temperature increment,
preserve exact ocean incumbent behavior, and use a short alias such as
`dino_land_soilflux`.
