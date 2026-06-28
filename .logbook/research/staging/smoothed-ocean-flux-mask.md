---
schema_version: 1
slug: smoothed-ocean-flux-mask
title: Smooth the Ocean Bulk Heat-Flux Mask Near Coasts
status: staging
created_at: 2026-06-26T18:26:20Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
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

# Smooth the Ocean Bulk Heat-Flux Mask Near Coasts

## Hypothesis

The accepted ocean bulk sensible heat flux is high leverage, but its ocean
weight is derived directly from a gridded land-sea fraction. At 1.5 degree
resolution, coastal grid cells can mix land, ocean, sea ice, and complex
shoreline geometry. Applying the accepted flux with a sharp gridcell mask can
create lower-layer thermal discontinuities near coastlines that feed `2m_temperature`
and weakly affect height/pressure. A conservative low-mode smoothing of the
ocean weight should retain open-ocean flux strength while softening coastal
mask noise.

## Mechanism

Add one opt-in candidate, for example `dino_hsl2_mass_dse_wtg_vdse_smooth_obulk`.
Preserve the incumbent ocean heat-flux formula, temperature anchor, exchange
coefficient, per-step cap, land-sea T2m residual path, WTG, vertical-DSE, and
all output diagnostics.

When `apply_ocean_bulk_sensible_heat_flux` is active and a valid land-sea
fraction is available, create a diagnostic ocean-weight copy:

- transform the ocean weight to modal space on the existing horizontal grid;
- retain all modes through a conservative total wavenumber, for example 12,
  taper to zero by 20, and transform back to nodal space;
- clip the smoothed weight to `[0, 1]`;
- preserve exact incumbent weights over nearly pure land and nearly pure ocean,
  for example where the original weight is below `0.02` or above `0.98`;
- use the smoothed weight only for `_OceanBulkSensibleHeatFluxForcingSigma`;
- fall back exactly to the incumbent unsmoothed weight if any transform,
  clipping, shape, or finite diagnostic fails.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key, `dino_hsl2_mass_dse_wtg_vdse_smooth_obulk`.
- API changes:
  - None. Forecast inputs, output variables, lead times, protocols, and cached
    incumbent artifacts remain compatible.
- Tests to update:
  - Unit-test bounded smoothing, exact pure-land/pure-ocean preservation, and
    finite fallback.
  - Verify the smoothed mask is used only by ocean bulk heat flux, not by
    near-surface residual correction or emitted variables.
  - Verify the candidate factory preserves every incumbent selector except the
    new ocean-mask smoothing option.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at coastal and marginal ocean grid cells through smoother
    lower-layer thermal forcing.
  - Small `mean_sea_level_pressure` and `geopotential_500` improvements if
    coastal lower-column thermal noise projects onto large-scale mass fields.
- Expected neutral metrics:
  - Open-ocean and inland grid cells should remain effectively incumbent because
    pure weights are preserved.
  - `10m_u_component_of_wind` should be near neutral because momentum and wind
    diagnostics are unchanged.
- Possible regressions:
  - Coastal smoothing can leak ocean thermal memory onto land or weaken real
    coastal contrast.
  - The global aggregate may be too insensitive to coastal points to clear the
    `+0.002` iteration threshold.

## Risks

- Numerical stability:
  - Low. The candidate only changes a bounded multiplicative source weight for
    an already capped temperature tendency.
- Compute cost:
  - Low. One modal smoothing operation per grid setup, reused across initial
    conditions.
- Data leakage:
  - None. It uses only static land-sea fraction and fixed spectral cutoffs.
- Physical plausibility:
  - Moderate. Coarse-grid coastal exchange should be fractional rather than
    discontinuous, but spectral smoothing is a numerical approximation rather
    than a full subgrid coastline scheme.
- Rollback complexity:
  - Low. Remove one mask helper, selector, factory/export, registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_smooth_obulk`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_smooth_obulk --workers 4`.
  - Compare against the cached `dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent
    artifacts; the accepted incumbent cache is authoritative unless missing,
    unreadable, nonfinite, or fingerprint-incompatible under `roles/PROTOCOL.md`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-lead
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_smooth_obulk --workers 4` only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show coastal ocean
    mask sharpness is not a material remaining score source. Early T2m or MSLP
    guardrail failure would show the smoothing leaks too much forcing.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` derives
  `ocean_bulk_shf_ocean_weight` from the static land-sea fraction and passes it
  into `_OceanBulkSensibleHeatFluxForcingSigma`.
- Dynamaxx history:
  `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/decision.md`
  accepted the ocean bulk sensible heat-flux mechanism; this proposal preserves
  that formula and changes only the mask used by the accepted source.
- Monin-Obukhov similarity and bulk surface-layer fluxes are standard
  foundations for turbulent surface exchange; see the summary in Cambridge
  University Press, "Turbulent Fluxes and Scalar Profiles in the Surface Layer":
  https://www.cambridge.org/core/books/climate-change-and-terrestrial-ecosystem-modeling/turbulent-fluxes-and-scalar-profiles-in-the-surface-layer/4EF88A3F657FC918FAE62308A61B528D
- Hlywiak, J. and Nolan, D. S. 2023. Evaluating Atmospheric Surface Layer Flux
  Parameterization within the Coastal Regime. Monthly Weather Review.
  https://doi.org/10.1175/MWR-D-22-0303.1

## Researcher Notes

This is not a retry of `roughness-aware-surface-wind-diagnostic`: it does not
change 10 m wind output. It is also not `exact-ocean-bulk-heat-flux-split`,
`static-stability-gated-ocean-heat-flux`, or `lake-ice-thermal-reservoir`:
those alter source integration, stability dependence, or lake-specific physics.
This proposal changes only the static ocean mask feeding the already accepted
ocean heat-flux source, with exact incumbent fallback and pure-land/pure-ocean
guards.

## Evaluator Notes

### 2026-06-26T18:29:29Z

Decision: move to `staging`; ranked 2 of 2 evaluated proposals.

This is plausible and implementable, but not the best single ready candidate.
The accepted ocean bulk sensible heat flux was high leverage, and external
surface-layer literature supports the concern that coastal flux gradients can
be discontinuous or poorly represented. Smoothing a coarse 1.5 degree ocean
weight near mixed coastline grid cells is therefore physically reasonable if it
is bounded, preserves pure land and pure ocean weights, and falls back exactly
to the incumbent on any transform or finite-check failure.

The reason to stage rather than ready is expected score leverage. This proposal
acts only on coastal and marginal-ocean cells while the fixed primary metric is
global, and several lower-boundary or surface-residual refinements after the
accepted ocean flux have been clean but neutral or negative. It also introduces
a spectral transform into a static mask path, making it less minimal than the
WTG taper's scalar forecast-age multiplier. The expected aggregate gain may be
below the fixed `+0.002` iteration threshold even if coastal `2m_temperature`
improves locally.

Keep staged as a credible, decorrelated surface-physics fallback. If promoted
later, require one fixed smoothing schedule, no cutoff sweep, exact preservation
of nearly pure land/ocean weights, use only for
`_OceanBulkSensibleHeatFluxForcingSigma`, and tests proving that residual
correction masks, emitted variables, fixed protocols, and cached incumbent
comparisons remain unchanged.
