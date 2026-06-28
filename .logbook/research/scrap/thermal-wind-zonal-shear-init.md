---
schema_version: 1
slug: thermal-wind-zonal-shear-init
title: Initialize Zonal-Mean Wind Shear Toward Thermal-Wind Balance
status: scrap
created_at: 2026-06-19T05:06:32Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
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

# Initialize Zonal-Mean Wind Shear Toward Thermal-Wind Balance

## Hypothesis

The current incumbent initializes winds by pressure-to-sigma interpolation and
then applies DFI. Prior broad wind initialization changes were harmful, but the
incumbent still has negative long-lead `10m_u_component_of_wind` skill and
large thermodynamic errors. A narrow balance correction that adjusts only the
zonal-mean vertical shear of zonal wind toward the analyzed thermal-wind
relationship may improve large-scale wind and mass-field consistency without
editing eddy winds, divergence, surface pressure, output diagnostics, or the
forecast contract.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_thermal_wind_shear_init`.
Preserve the incumbent rollout, DFI, weak Held-Suarez forcing, log-pressure and
hydrostatic layer initialization, theta tendency, theta recentering, symmetric
exact Coriolis split, stability-aware residual correction, Richardson 10 m wind
diagnostic, pressure-level output interpolation, output variables, and fixed
protocols.

For the candidate only, add a guarded initialization option after pressure-level
fields have been interpolated to sigma but before modal vorticity/divergence
conversion:

- compute zonal means of sigma-level temperature, pressure, and zonal wind from
  the initialized nodal fields;
- estimate the thermal-wind shear implied by meridional gradients of
  hydrostatic thickness or layer-mean temperature, using a bounded Coriolis
  denominator that disables the correction in the deep tropics;
- vertically integrate the implied shear to form a balanced zonal-mean wind
  profile while preserving the incumbent column-mean or lowest-layer
  barotropic zonal wind;
- blend only a fixed conservative fraction of the difference between incumbent
  zonal-mean shear and thermal-wind shear, with a broad cap in meters per
  second so the correction cannot overwrite the analysis;
- add the resulting zonal-mean increment to `u_wind` only; leave `v_wind`,
  eddy components of `u_wind`, temperature, surface pressure, humidity, and all
  diagnostic residuals unchanged;
- continue with the incumbent modal `uv_nodal_to_vor_div_modal` conversion and
  DFI path;
- fall back to the incumbent initialization wherever pressure, temperature,
  latitude geometry, or corrected wind is nonfinite.

This is an initialization-balance proposal. It does not run model-selection
evaluations, change training, add new inputs, or alter the forecast contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, output variables, shapes, lead times, target
    variables, metrics, and splits are unchanged.
- Tests to update:
  - Unit-test thermal-wind shear calculation on a simple synthetic meridional
    temperature gradient with known shear sign.
  - Verify tropical masking, finite fallback, and fixed increment cap.
  - Verify eddy wind components, `v_wind`, temperature, pressure, humidity, and
    output variables remain unchanged by the initialization helper.
  - Verify the candidate factory preserves every incumbent option except the
    thermal-wind initialization selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and long leads if zonal-mean baroclinic
    wind shear is a remaining balance error after interpolation and DFI.
  - `geopotential_500` and `mean_sea_level_pressure` if better large-scale
    wind-temperature balance reduces geostrophic adjustment noise.
- Expected neutral metrics:
  - `2m_temperature` should be close to neutral early because thermal fields and
    near-surface residual correction are unchanged.
  - Lead-zero output channels should remain on the accepted residual and
    diagnostic path.
- Possible regressions:
  - ERA5 analyzed winds may already contain ageostrophic and boundary-layer
    shear that should not be projected toward thermal-wind balance.
  - Any wind initialization edit can perturb DFI balance and pressure-gradient
    adjustment, risking MSLP, Z500, or wind guardrail failures.

## Risks

- Numerical stability:
  - Moderate. The correction is bounded and zonal-mean only, but it changes the
    initialized wind state before DFI.
- Compute cost:
  - Low. It adds zonal means, latitude gradients, vertical integration, and one
    wind update per initial state.
- Data leakage:
  - None. It uses only same-time initial temperature, pressure, wind, latitude,
    and fixed physical constants.
- Physical plausibility:
  - Moderate. Thermal-wind balance is a large-scale extratropical constraint,
    but it is not valid in the deep tropics, boundary layer, or strongly
    ageostrophic flow.
- Rollback complexity:
  - Low to moderate. Remove one initialization helper/flag, one factory/export,
    one registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_thermal_wind_shear_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_thermal_wind_shear_init --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_thermal_wind_shear_init --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or sub-threshold iteration delta would show that the
    current interpolated wind shear is preferable. Any early MSLP/Z500 guardrail
    failure would show that the initialization correction disrupts rather than
    improves balance.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` interpolates pressure-level
  temperature and winds to sigma and then converts nodal winds to modal
  vorticity/divergence in `weather_state_to_dinosaur_state`.
- Dynamaxx history:
  `.logbook/history/2026-06-17_03-22-44_helmholtz-wind-initialization/decision.md`
  rejected a broad wind reinitialization with severe mass-field degradation,
  motivating a much narrower zonal-mean shear-only correction.
- Dynamaxx history:
  `.logbook/history/2026-06-18_00-44-09_vorticity-preserving-dfi-increment/decision.md`
  rejected a DFI wind-component merge, so this proposal edits only a physically
  diagnosed large-scale shear before DFI rather than preserving raw DFI
  increments.
- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press. The thermal-wind relation links vertical
  geostrophic wind shear to horizontal temperature gradients.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to
  Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Held, I. M. and Suarez, M. J. 1994. "A Proposal for the Intercomparison of the
  Dynamical Cores of Atmospheric General Circulation Models." Bulletin of the
  American Meteorological Society, 75, 1825-1830.
  https://www.gfdl.noaa.gov/bibliography/related_files/ih9401.pdf
- Stull, R. 2017. Practical Meteorology, section on thermal wind. University of
  British Columbia / LibreTexts.
  https://geo.libretexts.org/Bookshelves/Meteorology_and_Climate_Science/Practical_Meteorology_%28Stull%29/11%3A_General_Circulation/11.05%3A_Section_6-

## Researcher Notes

This is not a duplicate of rejected `helmholtz-wind-initialization`: that
candidate broadly reprojected winds and caused large MSLP/Z500 degradation. The
new proposal changes only the zonal-mean vertical shear of zonal wind, masks
the tropics, preserves the barotropic component, and leaves eddy winds and
divergence construction on the incumbent path.

It is also distinct from rejected `coriolis-rotated-surface-wind-residual` and
`monotone-shear-10m-wind-diagnostic`, which were output or near-surface wind
diagnostic ideas. This proposal targets the large-scale initialized wind
profile before DFI and should be rejected if the fixed gates show that even a
bounded thermal-wind correction spends too much mass-field or wind margin.

## Evaluator Notes

### 2026-06-19T05:10:10Z

Decision: move to `scrap`; ranked 3 of 3 new proposals.

The physical idea is recognizable, but it is a poor next experiment under the
current history. Broad wind initialization through Helmholtz diagnostics
regressed the iteration score by `-0.34423230670441374` with large MSLP and
Z500 guardrail failures, and the narrower vorticity-preserving DFI wind merge
also regressed (`-0.002335598569885189`). The incumbent already uses accepted
DFI, exact symmetric Coriolis splitting, stability-aware residual correction,
and a Richardson 10 m wind diagnostic; another pre-DFI wind edit has an
unfavorable cost-risk tradeoff.

This proposal is narrower than the failed Helmholtz initialization, but the
thermal-wind projection still changes analyzed zonal wind shear before modal
vorticity/divergence conversion. It depends on tunable choices for tropical
masking, vertical integration anchor, blend fraction, and caps, and thermal-wind
balance is not valid in the boundary layer, deep tropics, or strongly
ageostrophic flow. Those weak points directly overlap the fixed metrics'
sensitivity to early mass fields and late 10 m wind.

Do not spend a model-selection run on this family without new read-only
diagnostics showing a persistent, extratropical zonal-mean thermal-wind shear
imbalance after the incumbent initialization and DFI. If such diagnostics are
needed, stage them as an infrastructure/research analysis artifact separately
from model selection.
