---
schema_version: 1
slug: lake-ice-thermal-reservoir
title: Lake and Lake-Ice Thermal Reservoir Forcing
status: staging
created_at: 2026-06-22T10:02:44Z
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

# Lake and Lake-Ice Thermal Reservoir Forcing

## Hypothesis

The accepted incumbent now includes land-sea-aware near-surface residual memory
and an ocean-only bulk sensible heat flux, but inland lakes remain on the land
or ocean fallback path depending only on coarse land-sea fraction. Lakes have
large thermal inertia, seasonal phase lag, and ice insulation that can strongly
affect local near-surface temperature. WeatherBench2 exposes static
`lake_cover` and `lake_depth` plus dynamic `lake_ice_temperature` and
`lake_ice_depth`; a weak lake-only lowest-layer temperature tendency can test
whether this missing inland-water reservoir improves `2m_temperature` without
changing the accepted ocean flux or using the rejected SST/sea-ice ocean anchor.

This is not a nearby SST/sea-ice ocean-boundary variant. The failed anchor
changed the accepted open-ocean flux anchor and sea-ice attenuation globally.
This proposal leaves open ocean exactly on the accepted incumbent path and acts
only where static lake cover is present, with lake-depth and lake-ice fields
controlling a separate inland-water reservoir.

## Mechanism

Register a short side-by-side candidate such as `dino_lake_thermal`. The
candidate should instantiate the accepted ocean-bulk incumbent and enable one
additional lake-reservoir selector.

For the candidate only:

- load `lake_cover` and `lake_depth` from static WeatherBench2 constants using
  the same grid-alignment and finite-validation pattern as the land-sea mask;
- for each initial condition, read dynamic `lake_ice_temperature` and
  `lake_ice_depth` when present and valid;
- form a lake reservoir anchor from lead-zero `2m_temperature` or lowest-layer
  air temperature, adjusted only where lake cover is present by a bounded
  lake-depth thermal-inertia factor;
- where lake ice is present, move the anchor weakly toward the valid
  `lake_ice_temperature` and attenuate the exchange as lake ice depth grows,
  representing insulation rather than open-water exchange;
- apply a slow, capped, lake-only lowest-layer temperature relaxation after the
  accepted dynamics step, with no direct wind, pressure, or tracer tendency;
- blend by static lake cover so non-lake land and accepted ocean points are
  bitwise incumbent when the selector is active;
- fall back exactly to the accepted incumbent if any required lake fields are
  missing, nonfinite, out of range, or grid-incompatible.

The first implementation should not add a full FLake model, lake prognostic
state, lake moisture flux, lake-effect precipitation, SST changes, or land soil
reservoir forcing.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for lake static-field
    loading, dynamic lake-field extraction, selector flag, split tendency, and
    short-alias factory.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` for factory export.
  - `src/dynamaxx/dycore/registry.py` for a short model alias.
  - Focused tests under `tests/dycore/models/dinosaur/` plus
    `tests/dycore/test_registry.py`.
- Registry changes:
  - Add exactly one short side-by-side alias, for example `dino_lake_thermal`.
- API changes:
  - None. Forecast input format, returned variables, lead selection, metrics,
    and fixed protocols remain unchanged.
- Tests to update:
  - Verify zero lake cover reproduces the accepted incumbent exactly.
  - Verify lake-covered, ice-free points relax slowly toward the bounded lake
    reservoir anchor.
  - Verify increasing lake ice depth monotonically attenuates exchange and valid
    lake ice temperature influences only lake-covered points.
  - Verify missing or invalid lake fields trigger exact incumbent fallback.
  - Verify only lowest-layer temperature changes directly and the candidate uses
    a short registry alias.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2-15 over lake-rich regions and downwind coastal
    lake grid cells if the current land/ocean fallback misses lake thermal lag.
  - Small aggregate primary-score gain if the lake signal is coherent enough in
    the fixed global evaluation.
- Expected neutral metrics:
  - Open-ocean `2m_temperature` should remain on the accepted ocean-bulk path.
  - `10m_u_component_of_wind`, `mean_sea_level_pressure`, and `geopotential_500`
    should move little because the forcing is weak, local, and thermal-only.
- Possible regressions:
  - Lake area is limited globally, so the aggregate score effect may be too
    small to clear the iteration threshold.
  - A static lake-cover blend can misrepresent small lakes at 1.5 degree
    resolution or situations where lake thermal influence is advected downwind.

## Risks

- Numerical stability:
  - Low to moderate. The tendency is local and capped, but it changes
    prognostic lower-layer temperature on lake grid cells.
- Compute cost:
  - Low. It loads a small number of static/dynamic single-level fields and adds
    local arithmetic only.
- Data leakage:
  - Low. It uses lead-zero lake fields and static constants, never future target
    values or validation statistics.
- Physical plausibility:
  - Moderate. Lake thermal inertia and lake ice insulation are well established
    in NWP, but this is a deliberately reduced one-layer atmospheric coupling,
    not a prognostic lake model.
- Rollback complexity:
  - Low. Remove one selector, helper functions, one factory/export, one
    registry alias, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_lake_thermal`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_lake_thermal --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    accepted incumbent, clean diagnostics, and no fixed early-lead or
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_lake_thermal --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta would show that lake thermal inertia is
    too geographically limited or already absorbed by the accepted residual and
    weak-HS paths. Any early MSLP or Z500 guardrail failure would show the
    lake-only thermal tendency is too intrusive.

## Citations

- Local source:
  `src/dynamaxx/dycore/models/dinosaur/xarray_utils.py` lists `lake_cover`,
  `lake_depth`, `lake_ice_temperature`, and `lake_ice_depth` as WeatherBench2
  static or dynamic single-level variables available to the adapter layer.
- Dynamaxx history:
  `.logbook/history/2026-06-22_07-54-50_sst-sea-ice-ocean-flux-anchor/decision.md`
  rejected changing the accepted open-ocean SST/sea-ice anchor; this proposal
  therefore leaves open ocean untouched and isolates inland lake cover.
- Dutra, E., Stepanenko, V. M., Balsamo, G., Viterbo, P., Miranda, P. M. A.,
  Mironov, D., and Schar, C. 2010. "An offline study of the impact of lakes on
  the performance of the ECMWF surface scheme." Boreal Environment Research,
  15, 100-112.
  https://www.borenv.net/BER/archive/pdfs/ber15/ber15-097.pdf
- Balsamo, G. et al. 2012. "On the contribution of lakes in predicting
  near-surface temperature in a global weather forecasting model." Tellus A,
  64, 15829. https://doi.org/10.3402/tellusa.v64i0.15829
- ECMWF. "Interactive lakes in the Integrated Forecasting System." ECMWF
  Newsletter No. 141, 2014.
  https://www.ecmwf.int/sites/default/files/elibrary/2013/17360-interactive-lakes-integrated-forecasting-system.pdf
- Mironov, D. V. 2008. "Parameterization of lakes in numerical weather
  prediction. Description of a lake model." COSMO Technical Report No. 11.
  https://www.cosmo-model.org/content/model/cosmo/misc/flake/docs/ParLak_Part1_a.pdf

## Researcher Notes

This is not a duplicate of `snow-soil-land-thermal-reservoir` in staging: that
idea targets land soil heat storage and snow insulation, while this proposal
targets static lake fraction, lake depth, and lake ice fields. It is also not a
duplicate of the failed SST/sea-ice ocean anchor because it does not replace the
accepted ocean anchor or alter sea-ice attenuation over open ocean. The expected
effect is geographically narrower but mechanistically decorrelated from the
exact ocean-flux integration proposal.

## Evaluator Notes

### 2026-06-22T10:07:23Z

Decision: move to `staging`, ranked second among the two new proposals.

The scientific premise is valid. Repository source inspection confirms
`lake_cover`, `lake_depth`, `lake_ice_temperature`, and `lake_ice_depth` are
listed as available single-level fields in
`src/dynamaxx/dycore/models/dinosaur/xarray_utils.py`. External literature also
supports the broad claim that lake heat storage and lake ice can affect
near-surface forecasts: Balsamo et al. 2012 report beneficial lake impacts in
global ECMWF IFS simulations, especially over lake-rich regions, and ECMWF
newsletter material describes non-negligible near-surface temperature impact
from FLake lake-atmosphere interaction:
https://www.tandfonline.com/doi/full/10.3402/tellusa.v64i0.15829 and
https://www.ecmwf.int/sites/default/files/elibrary/2013/17360-interactive-lakes-integrated-forecasting-system.pdf.

The proposal is not ready because the fixed primary metric is global and the
lake signal is geographically narrow at the repository's 1.5 degree grid. The
recent SST/sea-ice ocean-anchor experiment is also negative context for
boundary-condition refinements that are physically cleaner but change only a
limited part of the accepted ocean-bulk path; it produced only
`+0.0000030296370109317294` iteration delta. This lake idea is more distinct
than that rejected anchor change, but it adds more implementation surface than
the exact-split proposal while probably affecting fewer globally weighted
verification points than land-wide reservoir ideas.

Keep staged as a plausible decorrelated surface-physics experiment. If promoted
later, require a short alias such as `dino_lake_thermal`, exact incumbent
fallback for missing or invalid lake fields, conservative lake-depth and
lake-ice attenuation, and tests proving non-lake land and accepted open-ocean
points remain on the incumbent path.
