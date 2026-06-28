---
schema_version: 1
slug: theta-hydrostatic-pressure-output-reconstruction
title: Reconstruct Pressure-Level Temperature and Geopotential from Theta Hydrostatics
status: ready
created_at: 2026-06-21T18:00:06Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Reconstruct Pressure-Level Temperature and Geopotential from Theta Hydrostatics

## Hypothesis

The incumbent now advances thermodynamics through an accepted dry potential-temperature tendency, but `dinosaur_state_to_weather_state` still reconstructs pressure-level temperature, wind, and geopotential by independently interpolating sigma-level fields to pressure levels. Independent pressure-level interpolation can leave `temperature_*` and `geopotential_*` slightly inconsistent with the same hydrostatic column, especially near the surface where finite nearest extrapolation is active.

A coupled pressure-level diagnostic that interpolates dry potential temperature, converts back to temperature at the requested pressure, and recomputes geopotential from the same virtual-temperature column may reduce `geopotential_500` and pressure-level thermal errors without changing the prognostic trajectory, target variables, lead times, or fixed evaluation protocols.

## Mechanism

Register a side-by-side candidate extending the incumbent name with `_theta_hydrostatic_output`. Preserve the incumbent initialization, DFI, weak Held-Suarez analysis equilibrium, Coriolis Strang split, theta tendency, theta recentering, semi-implicit off-centering, scale-separated residuals, and Richardson 10 m wind diagnostic.

For this candidate only:

- in `dinosaur_state_to_weather_state`, diagnose sigma-level pressure and dry potential temperature from the forecast temperature and surface pressure;
- interpolate sigma-level dry potential temperature to requested pressure levels in the existing finite pressure-coordinate path;
- convert interpolated potential temperature back to pressure-level temperature using the exact requested pressure level;
- recompute pressure-level geopotential by vertically integrating the same sigma virtual-temperature column and sampling that hydrostatic profile at pressure levels;
- keep wind, humidity, surface pressure, mean sea-level pressure, 2 m temperature, and 10 m wind output paths unchanged;
- use the incumbent independent interpolation for any column with nonfinite pressure, temperature, humidity, or hydrostatic reconstruction diagnostics;
- do not alter the prognostic Dinosaur state, DFI state, evaluation target variables, splits, metrics, or lead schedule.

This is a coupled thermodynamic output reconstruction, not a standalone Z500 correction or a change to pressure interpolation coordinates.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate with an `_theta_hydrostatic_output` suffix.
- API changes:
  - None. The model still implements `DycoreModel.forecast` and emits only requested WeatherState variables.
- Tests to update:
  - Verify pressure-level temperature reconstructed through theta matches direct temperature for an isothermal hydrostatic column.
  - Verify geopotential and temperature are reconstructed from the same finite sigma virtual-temperature column.
  - Verify nonfinite or nonpositive pressure diagnostics fall back to the incumbent output path.
  - Verify the candidate factory preserves every incumbent behavior except the output reconstruction selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at days 1 to 10 if inconsistent pressure-level thermal and height diagnostics remain after the accepted theta tendency.
  - `2m_temperature` should be indirectly neutral to slightly positive only through better lower-column thermal consistency when pressure-level temperature channels are requested.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because wind dynamics and the Richardson 10 m diagnostic are unchanged.
  - `mean_sea_level_pressure` should remain close to incumbent because surface pressure and MSLP reduction are not changed.
- Possible regressions:
  - Output-only changes have been fragile in history; even a physically consistent reconstruction can degrade the fixed primary score if the incumbent interpolation compensates other errors.
  - Hydrostatic resampling near below-ground pressure levels may affect early Z500 guardrails if fallback coverage is incomplete.

## Risks

- Numerical stability:
  - Low. The forecast state is unchanged, but output finiteness must be guarded.
- Compute cost:
  - Low. The candidate adds pressure-level thermodynamic algebra during output packing only.
- Data leakage:
  - None. It uses only the forecast state and fixed pressure-level metadata.
- Physical plausibility:
  - Moderate to high. Pressure-level temperature and geopotential should be mutually consistent under the hydrostatic primitive-equation approximation.
- Rollback complexity:
  - Low. Remove one output selector, one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_hydrostatic_output`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_hydrostatic_output --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_theta_hydrostatic_output --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that coupled theta-hydrostatic output consistency is not a material remaining fixed-score source. Any early Z500 guardrail failure would show the incumbent interpolation is safer.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently interpolates sigma fields to pressure levels in `dinosaur_state_to_weather_state` and separately computes sigma geopotential with `primitive_equations.get_geopotential_on_sigma`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` exposes dry potential-temperature conversion helpers used by the accepted theta tendency.
- Dynamaxx history: `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md` accepted theta-form thermodynamics, motivating pressure-level diagnostics that respect the same variable.
- Dynamaxx history: `.logbook/history/2026-06-18_14-39-05_hypsometric-target-geopotential-diagnostic/decision.md` rejected a standalone geopotential output diagnostic, so this proposal couples temperature and geopotential rather than adjusting Z500 alone.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum conserving vertical finite-difference scheme and hybrid vertical coordinates. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AECAAM%3E2.0.CO;2
- Rasp, S. et al. 2024. WeatherBench 2: A Benchmark for the Next Generation of Data-Driven Global Weather Models. Journal of Advances in Modeling Earth Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This avoids another surface diagnostic, screen-temperature nudge, startup-only correction, off-centering change, or diffusion/projection variant. It is not a duplicate of scrapped pressure-output remaps because it does not change the vertical interpolation coordinate alone; it makes pressure-level `temperature` and `geopotential` thermodynamically consistent and leaves the prognostic dycore untouched.

## Evaluator Notes

### 2026-06-21T18:04:23Z

Decision: move to `ready`; ranked 1 of 3 in this triage pass.

This is the only current proposal I would keep implementable now. Source
inspection confirms the output path is localized: `dinosaur_state_to_weather_state`
currently builds sigma-level temperature, winds, humidity, and moist
geopotential, then sends all pressure-level fields through the same independent
sigma-to-pressure interpolation. The accepted theta tendency helpers also
already exist in `primitive_equations.py`, so a side-by-side theta-based
temperature/geopotential output selector can be implemented without changing
the forecast contract, fixed protocols, target variables, DFI, or positive-time
trajectory.

The readiness is low-confidence, not a broad endorsement of pressure-output
post-processing. Prior output history is negative to mixed: log-pressure output
interpolation missed promotion and failed many variable-lead guardrails, and
the hypsometric target-level geopotential diagnostic was slightly negative with
a `7.385768302790055%` 24 h `geopotential_500` RMSE regression. The dry
geopotential diagnostic also showed that removing the incumbent virtual
temperature humidity correction causes a large first-day Z500 failure, so this
candidate must preserve the current moist sigma geopotential inputs and use
strict finite fallback.

Keep it in `ready` because it is small, reversible, output-only, and tests a
specific consistency gap introduced by the accepted theta thermodynamic
tendency: pressure-level temperature and geopotential are currently emitted as
separate interpolated diagnostics rather than as one theta-hydrostatic column.
If this cleanly produces a near-zero or negative iteration delta, future
pressure-level output reconstruction ideas should be treated as exhausted or
held to much stronger read-only evidence.
