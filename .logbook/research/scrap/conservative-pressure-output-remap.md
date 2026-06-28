---
schema_version: 1
slug: conservative-pressure-output-remap
title: Use Conservative Pressure-Slab Output Remapping
status: scrap
created_at: 2026-06-18T17:18:05Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Conservative Pressure-Slab Output Remapping

## Hypothesis

The incumbent outputs pressure-level fields by interpolating sigma-layer fields
to requested pressure levels with finite nearest extrapolation. Recent
hypsometric-only Z500 diagnostics regressed, so changing just one target
diagnostic is not attractive. A conservative pressure-slab remap applied
consistently to pressure-level temperature, wind, humidity, and geopotential can
reduce vertical remapping noise without changing the prognostic trajectory,
surface residuals, pressure initialization, or fixed evaluation protocols.

The key distinction is to emit pressure-level values as averages over thin
pressure slabs centered on the WeatherBench pressure levels, using sigma-layer
pressure thickness overlaps, rather than as point samples from the sigma column.
This tests the output representation of a layer-mean sigma model against
pressure-level verification in a conservative way.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_conservative_pout`.
Preserve all incumbent forecast dynamics, initialization, DFI, forcing,
filters, Coriolis splitting, near-surface residual correction, and lead times.

Add an opt-in pressure-output remapper in `dinosaur_state_to_weather_state`:

- construct sigma-layer pressure boundaries from surface pressure and sigma
  interfaces for each forecast time and grid point;
- construct target pressure slabs around the configured WeatherBench pressure
  levels using midpoints in log-pressure space, clipped to finite pressure
  bounds;
- for temperature, horizontal wind components, humidity, and geopotential,
  compute pressure-thickness-weighted overlaps between source sigma layers and
  target slabs;
- divide overlap integrals by target slab thickness to emit finite layer-mean
  pressure-level values;
- use the incumbent finite interpolation fallback for slabs with no valid
  overlap, such as pressure levels above model top or below surface;
- keep surface variables (`2m_temperature`, `10m_u_component_of_wind`,
  `surface_pressure`, and `mean_sea_level_pressure`) on the incumbent path;
- do not alter the hydrostatic geopotential calculation on sigma layers before
  remapping.

This is an output conversion candidate only. It does not introduce
quasi-monotone limiting, new pressure initialization, terrain pressure
reduction, or a new vertical coordinate.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py` only if a
    reusable pressure-overlap helper is cleaner than an adapter-local helper
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, channel names, shapes, target variables,
    leads, and fixed protocols stay unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent flag except the
    conservative pressure-output option.
  - Unit-test overlap weights for monotone pressure columns, partial slabs,
    below-surface slabs, and above-top slabs.
  - Verify constant-with-height fields are preserved exactly by conservative
    remapping.
  - Verify surface diagnostics and near-surface residual correction are
    unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at early and medium leads if point interpolation from
    coarse sigma layers is a remaining vertical representation error.
  - Pressure-level temperature and wind diagnostics may become smoother and more
    layer-consistent, which can help aggregate primary score even though only
    Z500 is a fixed target pressure-level variable in the current summary.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should remain governed by
    the accepted stability-aware residual path.
  - `mean_sea_level_pressure` should remain unchanged because the candidate
    does not alter surface pressure or MSLP packing.
- Possible regressions:
  - WeatherBench pressure-level truth may be closer to point samples than to
    slab averages, especially at 500 hPa.
  - Conservative slab averaging may smooth sharp vertical gradients and degrade
    Z500 at short leads, similar in symptom to the rejected hypsometric target
    diagnostic.

## Risks

- Numerical stability:
  - Low. This is output-only and should not feed back into dynamics.
- Compute cost:
  - Low to moderate. Per-time, per-column overlap weights add vertical algebra
    over all output pressure levels but no extra rollout steps or resolution.
- Data leakage:
  - None. The remap uses only forecast sigma fields, surface pressure, fixed
    target pressure levels, and fixed constants.
- Physical plausibility:
  - Moderate to high for a layer-mean model. Conservative remapping is standard
    for transport and regridding, though the evaluation target semantics may be
    pressure-point rather than pressure-slab.
- Rollback complexity:
  - Low. Remove one output option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_conservative_pout`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_conservative_pout --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    diagnostics clean, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_conservative_pout --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that conservative
    pressure-slab output is not a material improvement over point interpolation.
    Any early Z500 guardrail regression would show slab averaging is the wrong
    representation for the fixed WeatherBench2 target.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  calls `_interp_sigma_to_pressure_by_time` for pressure-level output and keeps
  surface diagnostics on a separate path.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  already contains vertical regridding utilities, including conservative
  regridder classes that can guide an overlap-weight implementation.
- History: `.logbook/history/2026-06-18_14-39-05_hypsometric-target-geopotential-diagnostic/decision.md`
  rejected a geopotential-only output diagnostic after unfavorable 24 h Z500
  movement; this proposal remaps all pressure-level fields consistently instead
  of special-casing Z500.
- Research scrap: `.logbook/research/scrap/quasi-monotone-pressure-output-interpolation.md`
  is negative evidence against monotonicity-only pressure interpolation; this
  proposal uses pressure-thickness conservation rather than a monotone limiter.
- Lin, S.-J. and Rood, R. B. 1996. Multidimensional Flux-Form
  Semi-Lagrangian Transport Schemes. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Lauritzen, P. H., Nair, R. D., and Ullrich, P. A. 2010. A conservative
  semi-Lagrangian multi-tracer transport scheme on the cubed-sphere grid.
  Journal of Computational Physics. https://doi.org/10.1016/j.jcp.2009.10.036
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is not a duplicate of recent failed pressure-initialization candidates:
it does not change log-pressure initialization, sigma coordinates, hydrostatic
layer initialization, surface pressure continuity, or mass evolution. It is an
output remap only.

It is not a duplicate of accepted stability-aware residual decay because it
does not touch near-surface channels or residual timing. It is also distinct
from active staged Simmons-Burridge sigma geopotential and hydrostatic theta
initialization ideas, which modify equation operators or initialization rather
than pressure-level output remapping.

## Evaluator Notes

### 2026-06-18T17:21:29Z

Decision: move to `scrap`.

The idea is technically coherent and not an exact duplicate of the rejected
hypsometric-only Z500 diagnostic, but the current evidence makes it a poor
model-selection experiment. Recent output-remap history is consistently
unfavorable: log-pressure output interpolation was sub-threshold and failed
many variable-lead guardrails, conservative pressure-thickness initialization
remapping regressed primary score, and the latest hypsometric target
geopotential diagnostic was effectively neutral-negative with a `7.385768%`
24 h Z500 RMSE regression. The fixed WeatherBench pressure-level targets appear
closer to point samples than slab averages for this adapter.

Because the active target set primarily scores `geopotential_500` among
pressure-level fields, applying slab averaging to all pressure-level variables
adds implementation and smoothing risk without a clear path to beating the
iteration gate. The proposal is distinct from accepted near-surface residual
decay and from pressure-initialization failures, but it is too close to several
negative output/interpolation mechanisms to keep staged while stronger
near-surface and transient-spinup fallbacks remain available.
