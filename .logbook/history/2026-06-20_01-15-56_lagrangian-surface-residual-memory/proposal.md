---
schema_version: 1
slug: lagrangian-surface-residual-memory
title: Advect Scale-Separated Surface Residual Memory with the Forecast Flow
status: ready
created_at: 2026-06-20T00:57:57Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Advect Scale-Separated Surface Residual Memory with the Forecast Flow

## Hypothesis

The incumbent's accepted scale-separated residual correction leaves the broad
`2m_temperature` and `10m_u_component_of_wind` residual pattern fixed in
geographic coordinates while its amplitude decays. That is a large improvement,
but the remaining iteration metrics still show strongly negative mean
`2m_temperature` skill and negative mean 10 m zonal-wind skill. Part of the
remaining loss may be phase error: broad lower-boundary or air-mass residuals
should move with the low-level flow, while a stationary residual pattern becomes
misaligned after a few days.

A conservative flow-following residual correction should preserve the accepted
low/high scale split but advect only the low-mode residual component forward
with the model's own near-surface wind. This tests a different mechanism from
changing residual decay constants: it changes residual phase, not just residual
amplitude.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian`.
Preserve the incumbent rollout, DFI, weak Held-Suarez forcing, log-pressure and
hydrostatic layer initialization, Strang Coriolis split, theta tendency, theta
mean recentering, SIL3 off-centering, Richardson 10 m wind diagnostic, and the
accepted high-mode residual path.

For the candidate only:

- split initial `2m_temperature` and `10m_u_component_of_wind` residuals with
  the same low-mode mask and high-mode fallback as the incumbent;
- leave the high-mode residual correction exactly on the incumbent
  stability-aware local decay path;
- for each requested positive lead, diagnose a flow displacement from the
  model's saved low-level wind, using either the Richardson 10 m wind or the
  lowest sigma-layer wind converted to meters per second;
- advect the low-mode residual by a bounded backward semi-Lagrangian departure
  on the periodic longitude and bounded latitude grid, with displacement capped
  to a fixed practical value such as 15 degrees per 24 hours and no more than
  45 degrees total;
- use bilinear interpolation in grid space after converting to Dinosaur
  latitude order, with exact lead-zero preservation and finite fallback to the
  incumbent stationary low-mode residual;
- decay the advected low-mode residual with the incumbent low-mode decay
  envelope, so only phase changes relative to the accepted model;
- leave pressure-level fields, `mean_sea_level_pressure`, `geopotential_500`,
  prognostic state variables, and fixed evaluation protocols unchanged.

This is not another low-mode mass residual. It applies only to the two
near-surface channels already corrected by the accepted incumbent and uses the
forecast flow to move the residual pattern.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory with the `_lagrangian` suffix.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, and protocols
    remain fixed.
- Tests to update:
  - Unit-test periodic longitude interpolation, latitude clipping, displacement
    caps, finite fallback, and exact lead-zero output.
  - Verify zero wind exactly reproduces the incumbent scale-separated residual
    correction.
  - Verify high-mode residuals remain incumbent-equivalent and only the low-mode
    residual phase changes.
  - Verify non-near-surface channels are unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3 to 15 if the stationary low-mode residual becomes
    phase-wrong as synoptic air masses move.
  - `10m_u_component_of_wind` at medium and late leads if broad low-level wind
    residuals propagate with the low-level flow.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500`, because the change is
    output-only and limited to the accepted near-surface residual channels.
- Possible regressions:
  - The flow-following residual can advect a land/surface representativeness
    error that should have remained geographically fixed.
  - Interpolation can smear useful low-mode amplitude if the displacement cap is
    too large or the wind proxy is biased.

## Risks

- Numerical stability:
  - Very low. The dycore trajectory is unchanged.
- Compute cost:
  - Low. Adds per-lead grid interpolation for two 2D residual fields, not inner
    step work.
- Data leakage:
  - Low. Uses only the same initial analysis residual and forecast-time model
    winds. It must not use future truth or validation-derived displacement
    tuning.
- Physical plausibility:
  - Moderate. Semi-Lagrangian advection is standard for transported fields, but
    the residual may combine advected air-mass error and fixed surface error.
- Rollback complexity:
  - Low. Remove one helper/flag, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lagrangian --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean diagnostics
    and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show that the useful
    accepted residual is geographically fixed, not flow-following. Any early
    2 m temperature or 10 m wind guardrail failure would show the advection is
    too intrusive.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_apply_scale_separated_near_surface_residual_correction`, the accepted
  stationary low/high residual split.
- Dynamaxx history:
  `.logbook/history/2026-06-19_21-12-19_scale-separated-surface-residual-memory/decision.md`
  accepted scale-separated residual memory with iteration delta
  `+0.03993409285933447` and validation delta `+0.04067763036264238`.
- Staniforth, A. and Cote, J. 1991. "Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. "Atmospheric
  transport schemes: desirable properties and a semi-Lagrangian view on
  finite-volume discretizations." In Numerical Techniques for Global
  Atmospheric Models. https://doi.org/10.1007/978-3-642-11640-7_8
- Rasp, S. et al. 2024. "WeatherBench 2: A Benchmark for the Next Generation of
  Data-Driven Global Weather Models." Journal of Advances in Modeling Earth
  Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This is not a duplicate of staged `diurnal-surface-residual-memory`, which
changes temporal phase using solar/local-time structure for `2m_temperature`.
This proposal changes horizontal phase by advecting both accepted residual
channels with forecast flow. It is also not a duplicate of the rejected
`low-mode-mass-diagnostic-residual-memory`; no MSLP or Z500 residual is carried,
and the mechanism is flow-following near-surface residual phase rather than
stationary mass residual amplitude.

## Evaluator Notes

### 2026-06-20T01:00:53Z

Decision: move to `ready`; rank 1 of the fresh proposal set and recommended
next implementation.

This is the strongest candidate because it extends the one recent mechanism
with large validated signal: scale-separated near-surface residual memory
improved iteration by `+0.03993409285933447` and validation by
`+0.04067763036264238`. The fresh proposal keeps the dycore trajectory,
pressure diagnostics, Z500, MSLP, fixed protocols, target variables, and
high-mode residual path unchanged, so the implementation risk is lower than
the prognostic IAU and vertical-transport proposals. It tests a clear new axis:
horizontal phase of the already accepted low-mode residual, not amplitude
tuning.

The mechanism is scientifically plausible but bounded. Staniforth and Cote
1991 review semi-Lagrangian advection as a standard atmospheric-model transport
approach, supporting the use of backward departure/interpolation for transported
patterns: https://journals.ametsoc.org/view/journals/mwre/119/9/1520-0493_1991_119_2206_slisfa_2_0_co_2.xml.
The main risk is physical, not numerical: part of the near-surface residual may
be fixed surface or representativeness error and should not move with air-mass
flow. That risk is acceptable for `ready` because the proposal is output-only,
finite fallback is explicit, zero-wind equivalence to the incumbent is
testable, and a negative result would cleanly tell the loop that the accepted
low-mode residual is geographically anchored.
