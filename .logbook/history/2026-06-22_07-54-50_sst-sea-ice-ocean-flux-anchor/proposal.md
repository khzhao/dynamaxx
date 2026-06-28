---
schema_version: 1
slug: sst-sea-ice-ocean-flux-anchor
title: SST and Sea-Ice Anchored Ocean Bulk Heat Flux
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

# SST and Sea-Ice Anchored Ocean Bulk Heat Flux

## Hypothesis

The accepted ocean bulk sensible heat flux produced a large iteration and
validation gain, but its lower-boundary temperature anchor is still a proxy:
lead-zero `2m_temperature` when available, otherwise the initialized lowest
model-layer air temperature. Over open ocean, the physical lower boundary for a
bulk sensible heat flux is sea-surface temperature, not screen-level air
temperature. Over sea ice, the same open-ocean heat exchange should be strongly
reduced or disabled because sea ice insulates the ocean from the atmosphere.

The WeatherBench2 initial state already includes dynamic `sea_surface_temperature`
and `sea_ice_cover` channels. Persisting those initial lower-boundary fields for
the fixed 1-15 day forecast window should make the accepted ocean heat-flux
mechanism more physical without changing the forecast contract, target
variables, lead times, metrics, or deterministic gates.

## Mechanism

Register a side-by-side candidate under a short alias, for example
`dino_obulk_sstice`, that reproduces the full incumbent behavior plus one new
selector. Do not append a suffix to the full incumbent name, because the accepted
run already demonstrated filename-component failures in `dynamaxx-eval`
artifact writes.

For the candidate only:

- keep the accepted land-sea `2m_temperature` residual and ocean bulk sensible
  heat-flux tendency unchanged except for the ocean anchor and effective ocean
  weight;
- when `sea_surface_temperature` is present, finite, positive, and grid-aligned,
  use its lead-zero value as the persisted ocean temperature anchor in Dinosaur
  latitude order;
- when `sea_ice_cover` is present and valid in `[0, 1]`, multiply the accepted
  ocean weight by `1 - sea_ice_cover`, so compact sea ice falls back toward the
  incumbent non-flux trajectory rather than applying an open-ocean exchange;
- when either field is absent, nonfinite, or shape-incompatible, fall back
  exactly to the accepted incumbent anchor and ocean weighting;
- retain the accepted transfer coefficient, wind-speed dependence, minimum
  e-folding time, single-step temperature-increment cap, land mask handling,
  DFI behavior, output variables, and residual corrections;
- bound the SST-air temperature difference used in the tendency before applying
  the existing step cap, so isolated bad SST values cannot dominate a forecast.

This is not a new bulk-flux coefficient sweep and not another residual-memory
variant. It keeps the accepted ocean heat-flux process but replaces the proxy
air-temperature boundary with the available analyzed lower-boundary fields.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for the SST and sea-ice
    anchor extraction, validation helpers, selector flag, and short-alias
    factory.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` for factory export.
  - `src/dynamaxx/dycore/registry.py` for a short candidate name such as
    `dino_obulk_sstice`.
  - `tests/dycore/models/dinosaur/` and `tests/dycore/test_registry.py` for
    focused helper, fallback, factory, and registry tests.
- Registry changes:
  - Add exactly one short side-by-side model alias. The alias should instantiate
    the full accepted incumbent and enable only the SST/sea-ice selector.
- API changes:
  - None. `DycoreModel.forecast`, forecast inputs, output variables, target
    variables, lead times, splits, and metric definitions remain unchanged.
- Tests to update:
  - SST anchor is used over open ocean when finite and aligned.
  - Sea-ice cover smoothly attenuates the ocean heat-flux weight.
  - Missing, nonfinite, or misaligned SST/sea-ice fields reproduce the accepted
    incumbent exactly.
  - Land points, residual corrections, and non-temperature state leaves are
    unchanged except through the accepted ocean flux path.
  - The short alias is registered and the full model name is not lengthened.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2-15 over open ocean and ice-edge regions, where
    the current air-temperature anchor can misrepresent the persisted ocean
    lower boundary.
  - Small secondary improvements in `mean_sea_level_pressure` or
    `geopotential_500` are possible if the lower-column thermal tendency becomes
    less biased without increasing mass noise.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because no
    momentum tendency or wind diagnostic is changed.
  - Land `2m_temperature` should remain governed by the accepted land-sea
    residual path.
- Possible regressions:
  - Persisted SST can be stale under strong ocean-front advection or rapidly
    evolving sea ice.
  - If the lead-zero screen-temperature anchor was empirically compensating for
    other missing surface physics, replacing it with SST could reduce the
    accepted gain.

## Risks

- Numerical stability:
  - Low to moderate. The forcing already exists and is capped, but a new anchor
    can sharpen local temperature gradients; finite checks and the accepted step
    cap must remain authoritative.
- Compute cost:
  - Low. The candidate adds two per-initial-condition fields and local array
    operations; no extra rollout steps, workers, or output volume.
- Data leakage:
  - Low. Uses only lead-zero initial-state SST and sea-ice cover, plus static
    land fraction. It must not read future target values.
- Physical plausibility:
  - High over open ocean and sea ice. Bulk air-sea flux formulas use SST or skin
    temperature and account for ice-covered surfaces differently from open
    water.
- Rollback complexity:
  - Low. Remove one selector, helper path, factory/export, registry alias, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_obulk_sstice`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_obulk_sstice --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    accepted incumbent, clean diagnostics, and no fixed early-lead or
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_obulk_sstice --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta, especially with neutral or
    worse `2m_temperature`, would show that the accepted air-temperature anchor
    is a better empirical lower-boundary proxy for this dry dycore than
    persisted SST and sea-ice cover.

## Citations

- Local history:
  `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/implementation.md`
  records that the accepted implementation uses initial `2m_temperature` as the
  ocean anchor when present, not true SST or a prognostic ocean skin
  temperature.
- Local source:
  `src/dynamaxx/dycore/models/dinosaur/xarray_utils.py` lists
  `sea_surface_temperature` and `sea_ice_cover` as dynamic single-level
  WeatherBench2 channels available to the initial state.
- Fairall, C. W., Bradley, E. F., Hare, J. E., Grachev, A. A., and Edson, J. B.
  2003. "Bulk Parameterization of Air-Sea Fluxes: Updates and Verification for
  the COARE Algorithm." Journal of Climate.
  https://doi.org/10.1175/1520-0442(2003)016%3C0571:BPOASF%3E2.0.CO;2
- NOAA PMEL Ocean Climate Stations flux documentation describes COARE bulk
  fluxes including sensible heat flux and identifies SST, air temperature, wind,
  and related near-surface variables as inputs.
  https://www.pmel.noaa.gov/ocs/flux-documentation
- ECMWF public research experiment documentation describes short-range
  uncoupled forecasts using persisted initial SST and sea-ice cover as a
  practical alternative to a fully coupled ocean.
  https://apps.ecmwf.int/ifs-experiments/
- ECMWF OpenIFS physical-process documentation lists surface exchange and
  turbulent mixing among the subgrid physical processes represented in IFS.
  https://confluence.ecmwf.int/display/OIFS/3.2%2BOpenIFS%3A%2BPhysical%2BProcesses

## Researcher Notes

This builds directly on the accepted ocean heat-flux incumbent but changes a
different mechanism from the staged generic bulk-surface flux notes. Those notes
asked whether adding a surface heat-flux process helps. The accepted run showed
yes. This proposal asks whether the lower-boundary state inside that accepted
process should be the analyzed ocean/ice surface rather than an air-temperature
proxy. It avoids the recent failed output-only wind memory path and avoids the
rejected weak-HS integration path.

## Evaluator Notes

### 2026-06-22T07:53:02Z

Decision: move to `ready`; ranked 1 of the two current proposals.

The mechanism is scientifically well supported and tightly scoped to a known
limitation of the accepted incumbent. Local implementation history records that
the accepted ocean-bulk sensible heat-flux path uses lead-zero `2m_temperature`
or the lowest model layer as the ocean thermal anchor, not SST. Repository source
inspection confirms `sea_surface_temperature` and `sea_ice_cover` are available
dynamic single-level channels, and the current adapter already has a contained
ocean-weight and thermal-anchor path where this selector can be added without
changing the forecast API or fixed protocols.

External checks support the key physical claims. NOAA PMEL documents COARE bulk
air-sea flux calculations, including sensible heat flux, and cites Fairall et
al. 2003 as the algorithm basis:
https://www.pmel.noaa.gov/ocs/flux-documentation. NOAA PMEL also describes
air-sea heat fluxes as a primary mechanism by which the ocean influences the
atmosphere: https://www.pmel.noaa.gov/ocs/air-sea-fluxes. NSIDC describes sea
ice as insulating the ocean from the atmosphere and inhibiting heat transfer:
https://nsidc.org/learn/parts-cryosphere/sea-ice/science-sea-ice. ECMWF public
experiment records include atmosphere-only forecasts forced by persisted sea-ice
concentration from operational analysis:
https://apps.ecmwf.int/ifs-experiments/. Recent arXiv work on ECMWF AIFS marine
fields further supports that sea ice strongly controls near-surface
thermodynamics and that explicit surface-ocean representation can improve
surface temperature skill: https://arxiv.org/html/2604.25559v1.

This is not a duplicate of staged `bulk-surface-sensible-heat-flux`: that older
proposal asked whether to add a generic bulk surface heat flux. The accepted
history already answered that positively with a large validation gain. This
proposal now tests a narrower, higher-quality lower-boundary selector inside
that accepted process, replacing an acknowledged air-temperature proxy with
analysis SST over open water and attenuating open-ocean exchange under sea ice.

Implementation concerns for the Orchestrator and Implementer: keep the candidate
on a short registry alias such as `dino_obulk_sstice`; preserve the cached
incumbent as the comparison baseline; use only lead-zero fields; require exact
grid alignment and finite checks; and retain incumbent fallback for missing,
nonfinite, or shape-incompatible SST or sea-ice inputs. Persisted SST and sea ice
can be stale near fronts and rapidly moving ice edges, so the SST-air departure
bound and existing step cap should remain authoritative.
