---
schema_version: 1
slug: orographic-lapse-screen-temperature
title: Orographic Lapse-Rate Screen-Temperature Output Correction
status: staging
created_at: 2026-06-21T21:39:20Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
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

# Orographic Lapse-Rate Screen-Temperature Output Correction

## Hypothesis

A systematic, spatially structured part of the `2m_temperature` error
(area-weighted skill near `-1.47`) is elevation-driven. The spectral model
represents orography on a smooth, truncated grid, so its effective surface
height over mountains and plateaus differs from the true ERA5 grid-cell
elevation, and the screen temperature it diagnoses is therefore evaluated at the
wrong height. A near-surface temperature error of order the lapse rate times the
height discrepancy (roughly `6.5 K` per `1 km`) appears as a persistent
warm or cold bias over elevated and complex terrain. A bounded lapse-rate
correction that reduces the diagnosed screen temperature from the model surface
height to the reference grid elevation removes this systematic component, a
standard step in operational temperature post-processing.

## Mechanism

Register a side-by-side candidate named
`..._analysis_hs_eq_orog_lapse_t2m`. Preserve every incumbent setting.

For the candidate only:

- read the static surface geopotential / `orography` reference for the
  WeatherBench2 grid through `WeatherBench2Source.read_constants` (the field the
  accepted terrain-aware orography work already loads), and cache it grid-aligned;
- compute the height discrepancy between the model's effective (filtered, modal)
  surface geopotential height and the reference elevation;
- adjust the diagnosed `2m_temperature` by a fixed tropospheric lapse rate times
  that height discrepancy, with the lapse rate fixed (start near `6.5 K/km`) and
  the total correction clipped to a bounded magnitude so spurious large
  discrepancies cannot inject extreme values;
- apply only to `2m_temperature`; leave winds, pressure, geopotential,
  prognostic dynamics, and mass diagnostics unchanged;
- use the identical correction in DFI and positive-time rollout;
- fall back to the incumbent diagnostic if the reference orography is unavailable
  or nonfinite.

This is an **output diagnostic elevation correction**. It is distinct from
`lapse-rate-held-suarez-relaxation` (which sets the vertical lapse of the HS
equilibrium temperature -- a forcing property of the prognostic state) and from
`terrain-aware-surface-pressure-orography` (which feeds modal orography into the
dynamics and pressure diagnostics). It does not change the dynamics or the
pressure field; it only reduces the screen temperature to the correct height.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` (lapse correction in the
    `2m_temperature` diagnostic; reference-orography loading)
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes: add only the side-by-side candidate named above.
- API changes: none.
- Tests to update:
  - zero height discrepancy leaves `2m_temperature` unchanged;
  - a positive elevation discrepancy cools the screen temperature by the lapse
    rate times the discrepancy, and the clip bounds extreme cases;
  - non-`2m_temperature` outputs are byte-for-byte unchanged;
  - missing-orography fallback reproduces the incumbent;
  - registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements: `2m_temperature`, concentrated over elevated and complex
  terrain, at all leads (the bias is largely lead-independent).
- Expected neutral metrics: `mean_sea_level_pressure`, `geopotential_500`,
  `10m_u_component_of_wind`.
- Possible regressions: a fixed lapse rate is wrong in strongly stable or
  inverted boundary layers, so some cold-season high-terrain points could regress;
  the clip and the modest fixed lapse rate bound this.

## Risks

- Numerical stability: negligible; bounded diagnostic addition, no prognostic
  tendency.
- Compute cost: negligible; one cached static field and an elementwise term.
- Data leakage: none; uses static reference orography and model state only.
- Physical plausibility: high; height reduction by a standard lapse rate is
  routine temperature post-processing.
- Rollback complexity: low.

## Evaluation Plan

- Fast gate: `uv run pytest`; `uv run dynamaxx-eval fast --model ..._orog_lapse_t2m`;
  finite forecasts, zero diagnostic issues.
- Iteration gate: `uv run dynamaxx-eval iteration --model ..._orog_lapse_t2m --workers 4`;
  support is primary-score delta at least `+0.002`, clean diagnostics, no
  guardrail failure.
- Validation gate: `uv run dynamaxx-eval validation --model ..._orog_lapse_t2m --workers 4`
  only after iteration promotion; require validation delta at least `+0.001`.
- Falsification: a clean near-zero or negative iteration delta would show the
  smoothed-orography height error is not a material part of the `2m_temperature`
  deficit, or that a fixed lapse rate is too crude to help on net.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/data/weatherbench2.py` `read_constants`;
    `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography`
    loads static orography and feeds modal terrain to the dynamics.
  - Sheridan, P. et al. 2010. Influence of lapse-rate and elevation on near-surface
    temperature downscaling. International Journal of Climatology.
    https://doi.org/10.1002/joc.2095
  - WMO Guide to Meteorological Instruments and Methods of Observation
    (reduction of temperature to a reference level).
    https://library.wmo.int/idurl/4/68695

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-21 alongside
`land-sea-contrast-surface-temperature`. Both attack the dominant `2m_temperature`
error through spatial bias structure the spatially uniform accepted corrections
cannot represent -- one via surface type (land vs ocean), this one via elevation.
It is deliberately an output-only diagnostic and explicitly distinct from the
existing `lapse-rate-held-suarez-relaxation` (a forcing lapse, not an output
height reduction) and `terrain-aware-surface-pressure-orography` (a dynamics
input). Low implementation surface, so likelier to be picked than scrapped.

## Evaluator Notes

### 2026-06-21T23:30:36Z

Decision: move to `staging`; ranked 2 of 3 current proposals.

The idea is physically plausible and output-only, so it avoids the worst part
of the rejected terrain-aware dynamics candidate. A bounded lapse correction
could improve persistent elevated-terrain `2m_temperature` bias without
touching MSLP, Z500, winds, or the rollout trajectory.

Keep it staged rather than ready. It requires forecast-time static orography
loading and an unambiguous definition of the model's effective surface height;
both are more complex and easier to misalign than a land-sea mask. Repository
history is also strongly cautionary for terrain mechanisms:
`terrain-aware-surface-pressure-orography` improved primary score but failed
early MSLP/Z500 RMSE guardrails by large margins. This proposal is narrower,
but should wait behind the simpler land-sea diagnostic and must include exact
incumbent fallback for missing, nonfinite, or shape-incompatible constants if
promoted later.
