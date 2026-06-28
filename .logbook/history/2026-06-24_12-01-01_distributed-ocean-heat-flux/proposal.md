---
schema_version: 1
slug: distributed-ocean-heat-flux
title: Distribute Ocean Bulk Heat Flux Through Lower Sigma Layers
status: ready
created_at: 2026-06-24T11:52:46Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Distribute Ocean Bulk Heat Flux Through Lower Sigma Layers

## Hypothesis

The accepted ocean bulk sensible heat flux improved the Dinosaur chain, but the
current implementation applies the whole bounded thermal tendency to only the
lowest sigma layer. In real marine boundary layers, turbulent sensible heat
exchange is vertically mixed through a finite depth rather than deposited into
one model layer. Concentrating the heat in the lowest layer can over-sharpen
near-surface static stability and couple too strongly to screen-temperature and
MSLP diagnostics.

Keeping the accepted column-integrated ocean heat flux but distributing it
through a fixed lower-sigma mixed-layer taper should preserve the useful ocean
thermal anchor while reducing lowest-layer shocks. This is a vertical
distribution change, not a flux-amplitude retune.

## Mechanism

Register a side-by-side candidate such as `dino_hsl2_mass_dse_ocean_flux_taper`
derived from `dino_hsl2_mass_dse`.

For the candidate only:

- preserve the accepted ocean-weight mask, temperature anchor, transfer
  coefficient, exchange depth, land-sea handling, maximum per-step column heat
  cap, DFI, weak-HS forcing, HSL, DSE transport, residuals, and output contract;
- replace the current lowest-layer-only ocean temperature tendency with a fixed
  lower-column sigma taper, for example nonzero for `sigma >= 0.75` and largest
  near the surface;
- normalize the taper by local sigma-layer pressure thickness so the
  column-integrated dry static energy tendency equals the accepted ocean heat
  flux before clipping;
- apply the same sign and same total heat increment as the incumbent accepted
  ocean forcing, only redistributed vertically;
- keep the tendency zero over land and for invalid land-sea masks exactly as in
  the incumbent;
- fall back to the incumbent lowest-layer-only forcing if taper weights,
  pressure thickness, or distributed tendency diagnostics are nonfinite.

The proposal does not add latent heat, momentum drag, SST/sea-ice inputs, static
stability gates, or a new surface residual.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry key for
    `dino_hsl2_mass_dse_ocean_flux_taper`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead schedule, metrics,
    and protocols stay fixed.
- Tests to update:
  - Verify the taper is finite, nonnegative, lower-column confined, and
    normalized by layer pressure thickness.
  - Verify the distributed tendency preserves the incumbent column-integrated
    heat increment on a synthetic ocean column.
  - Verify land columns and invalid masks remain no-op.
  - Verify fallback reproduces the incumbent lowest-layer tendency for nonfinite
    diagnostics.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` over ocean and coastal grid cells at days 2 to 15 if the
    accepted heat flux is useful but too shallowly deposited.
  - `mean_sea_level_pressure` and `geopotential_500` may improve if smoother
    lower-column heating reduces hydrostatic shocks from the accepted
    lowest-layer source.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because no momentum
    tendency or wind diagnostic changes.
- Possible regressions:
  - If the accepted score gain relies specifically on warming or cooling the
    lowest layer, distributing the same heat over multiple layers can dilute the
    `2m_temperature` benefit.
  - Heating a deeper lower column can affect thickness more strongly and spend
    MSLP/Z500 guardrail margin.

## Risks

- Numerical stability:
  - Low to moderate. The total heat increment remains capped, but more layers
    receive direct temperature tendency.
- Compute cost:
  - Low. It adds a fixed vertical taper and local normalization.
- Data leakage:
  - None. It uses the incumbent ocean mask, initial temperature anchor, and
    fixed sigma-coordinate weights only.
- Physical plausibility:
  - High for direction of change: turbulent ocean-atmosphere sensible heat flux
    is a boundary-layer process. The exact fixed taper is a reduced
    parameterization rather than a full PBL scheme.
- Rollback complexity:
  - Low. Remove one forcing option, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_ocean_flux_taper`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_ocean_flux_taper --workers 4`
  - Support requires primary delta at least `+0.002` against cached
    `dino_hsl2_mass_dse`, clean diagnostics, and no fixed RMSE guardrail
    failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_ocean_flux_taper --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the accepted
    lowest-layer ocean heat-flux placement is already the better empirical
    compromise. Any early MSLP, Z500, or 10 m wind guardrail failure would show
    that deeper thermal forcing is too invasive.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
    `_OceanBulkSensibleHeatFluxForcingSigma` and currently inserts the accepted
    ocean heat tendency into the lowest sigma layer.
  - Dynamaxx history:
    `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/decision.md`
    accepted the ocean bulk sensible heat-flux mechanism that this proposal
    preserves.
  - Dynamaxx research:
    `.logbook/research/staging/exact-ocean-bulk-heat-flux-split.md` changes
    time integration of the same flux, while this proposal changes only vertical
    distribution at fixed total heat input.
  - Fairall, C. W., Bradley, E. F., Rogers, D. P., Edson, J. B., and Young,
    G. S. 1996. Bulk parameterization of air-sea fluxes for Tropical
    Ocean-Global Atmosphere Coupled-Ocean Atmosphere Response Experiment.
    Journal of Geophysical Research. https://doi.org/10.1029/95JC03205
  - Large, W. G., McWilliams, J. C., and Doney, S. C. 1994. Oceanic vertical
    mixing: A review and a model with a nonlocal boundary layer
    parameterization. Reviews of Geophysics.
    https://doi.org/10.1029/94RG01872
  - Holtslag, A. A. M. and Boville, B. A. 1993. Local versus nonlocal
    boundary-layer diffusion in a global climate model. Journal of Climate.
    https://doi.org/10.1175/1520-0442(1993)006%3C1825:LVNBLD%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of generic bulk surface heat-flux staging because it
does not change the accepted flux law, exchange coefficient, ocean mask, or
temperature anchor. It is also distinct from static-stability-gated ocean heat
flux and exact ocean-flux splitting: no stability-dependent amplitude gate and
no new split integrator are introduced.

The proposal is decorrelated from the latest DSE-HSL failures. It leaves
mass-DSE transport, pressure-thickness handling, hydrostatic inversion, vertical
DSE transport, and initialization unchanged. The only tested question is whether
the already accepted ocean heat source should enter a finite lower-column mixed
layer rather than a single sigma layer.

## Evaluator Notes

### 2026-06-24T11:59:50Z

Decision: move to `ready`; ranked 1 of 3 new proposals. Ready now: yes.

This is the strongest next experiment because it preserves the accepted
ocean-bulk sensible heat-flux law, mask, anchor, sign, cap, and fixed
evaluation contract while changing only where the already accepted heat
increment enters the lower column. The accepted ocean-bulk experiment remains
the clearest nearby positive evidence, with iteration delta
`+0.0714278996861683` and validation delta `+0.07032535118514627`; local source
inspection confirms `_OceanBulkSensibleHeatFluxForcingSigma` currently applies
the entire tendency to the lowest sigma layer.

The scientific direction is also defensible. Boundary-layer literature supports
surface exchange being mixed through a finite atmospheric boundary layer rather
than treated as a single-level thermal deposit, while this proposal avoids a
new amplitude, SST/sea-ice anchor, stability gate, latent heat term, or momentum
drag. It is distinct from staged `exact-ocean-bulk-heat-flux-split`, which only
changes source integration and was previously staged because the accepted
timescale and cap make exactness likely low leverage. It is also distinct from
`static-stability-gated-ocean-heat-flux`, which changes coupling strength.

The main risk is dilution of the accepted `2m_temperature` benefit or stronger
lower-column thickness/pressure coupling if too much heat reaches aloft. The
implementation should therefore keep the column-integrated heat increment and
existing step cap exactly comparable to the incumbent, use a fixed conservative
lower-sigma taper, and include tests proving land/no-mask fallback and
column-integrated dry static energy preservation.
