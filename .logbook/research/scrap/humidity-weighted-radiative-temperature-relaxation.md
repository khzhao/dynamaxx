---
schema_version: 1
slug: humidity-weighted-radiative-temperature-relaxation
title: Add Humidity-Weighted Radiative Temperature Relaxation
status: scrap
created_at: 2026-06-18T18:48:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind
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

# Add Humidity-Weighted Radiative Temperature Relaxation

## Hypothesis

The incumbent is dynamically dry with a weak, zonally symmetric Held-Suarez
thermal relaxation. It carries passive humidity but does not use humidity to
represent radiative heating or cooling. Water vapor is a primary longwave
radiatively active gas, so a small, area-mean-neutral humidity-weighted thermal
relaxation may reduce lower- and middle-tropospheric temperature drift without
activating moist pressure-gradient dynamics or latent heating. The expected
benefit is mainly `2m_temperature` and possibly `geopotential_500` through
column thickness, while preserving the accepted near-surface residual and 10 m
wind diagnostic behavior.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_q_radiation`.
Preserve the incumbent DFI, weak Held-Suarez forcing, log-pressure and
hydrostatic initialization, symmetric exact-Coriolis split, stability-aware
near-surface residual correction, Richardson 10 m wind diagnostic, passive
humidity transport, and output contract.

Add an opt-in explicit thermal forcing composed after the incumbent weak
Held-Suarez forcing:

- require an existing passive `specific_humidity` tracer; if absent, the forcing
  is an exact no-op;
- compute finite bounded humidity in nodal sigma space, for example
  `clip(q, 0.0, 0.04)`;
- subtract an area-weighted layer mean humidity so the added heating has zero
  horizontal mean by layer at each step;
- apply a fixed, weak lower- and middle-tropospheric temperature tendency
  proportional to that humidity anomaly, with a smooth vertical taper that is
  negligible in the upper stratosphere and near the top sigma layer;
- cap the local tendency magnitude to a predetermined value such as
  `0.25 K day^-1` and use a fixed long timescale, avoiding parameter sweeps;
- leave humidity tracer tendencies, vorticity, divergence, `log_surface_pressure`,
  Coriolis splitting, DFI duration, and near-surface residual logic unchanged.

This is not moist virtual-temperature dynamics and not saturation adjustment.
Humidity acts only as a same-time radiative proxy in an extra thermal tendency.

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
  - None. The model consumes only the existing initial-state humidity channels
    that the incumbent already supports as passive tracers.
- Tests to update:
  - Unit-test no-op behavior when humidity is absent.
  - Unit-test finite clipping, area-mean removal, vertical taper shape, and
    tendency cap.
  - Verify the forcing changes only `temperature_variation` tendency and leaves
    humidity tracer tendency, winds, and `log_surface_pressure` unchanged.
  - Verify the candidate factory preserves all incumbent flags except the new
    humidity-radiative forcing option.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and long leads if the incumbent's thermal drift
    partly reflects missing humidity-correlated radiation.
  - `geopotential_500` if the temperature correction improves layer thickness
    without disturbing mass continuity.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because no
    momentum tendency, wind diagnostic, or surface residual timescale changes.
  - `mean_sea_level_pressure` should be less exposed than in pressure-continuity
    and terrain experiments because `log_surface_pressure` tendency is
    untouched.
- Possible regressions:
  - The sign and vertical structure of real radiative heating is more complex
    than this proxy; a crude humidity anomaly may warm or cool the wrong
    regions.
  - Passive humidity can drift in a dry model, so coupling temperature to it may
    amplify tracer transport errors.

## Risks

- Numerical stability:
  - Low to moderate. The tendency is bounded and weak, but it is applied every
    step.
- Compute cost:
  - Low. It adds one local forcing calculation and no new transforms beyond the
    existing nodal tracer conversion.
- Data leakage:
  - None. It uses only forecast-state humidity and fixed constants.
- Physical plausibility:
  - Moderate. Water vapor-radiation coupling is physical, but this is a highly
    reduced clear-sky proxy rather than a full radiation scheme.
- Rollback complexity:
  - Low. Remove one forcing option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_q_radiation`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_q_radiation --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_q_radiation --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show this reduced
    humidity-radiation proxy is not a useful remaining error source. Any early
    wind, MSLP, or Z500 guardrail failure would show the thermal forcing
    disrupts the accepted balanced rollout.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` composes
    the current weak Held-Suarez thermal forcing and carries humidity as a
    passive tracer when humidity channels are available.
  - Dynamaxx history:
    `.logbook/history/2026-06-17_18-02-45_bounded-moist-virtual-temperature-dynamics/decision.md`
    rejected active moist virtual-temperature dynamics with iteration delta
    `-0.055193744700895`; this proposal does not use humidity in pressure
    gradients or momentum tendencies.
  - Dynamaxx history:
    `.logbook/history/2026-06-17_19-31-12_bounded-saturation-adjustment/decision.md`
    rejected saturation adjustment and latent heating after early MSLP, Z500,
    and wind guardrail failures; this proposal does not modify humidity or add
    irreversible latent heating.
  - ECMWF Technical Memorandum 816, Hogan and Bozzo, "Radiation in numerical
    weather prediction", describes radiation as fundamental for atmospheric
    flow and near-surface temperature forecasts, with water-vapour continuum as
    a clear-sky absorption challenge.
    https://www.ecmwf.int/sites/default/files/elibrary/2017/17771-radiation-numerical-weather-prediction.pdf
  - ECMWF Newsletter 155, "A new radiation scheme for the IFS", notes that
    radiation drives atmospheric flows and that longwave radiative transfer
    improvements reduce temperature-profile biases.
    https://www.ecmwf.int/en/newsletter/155/meteorology/new-radiation-scheme-ifs
  - Mlawer, E. J. et al. 1997. Radiative transfer for inhomogeneous
    atmospheres: RRTM, a validated correlated-k model for the longwave.
    Journal of Geophysical Research.
    https://doi.org/10.1029/97JD00237

## Researcher Notes

This is distinct from rejected humidity mechanisms because humidity remains
passive dynamically. It does not activate moist virtual-temperature pressure
gradients, does not add saturation adjustment, does not alter geopotential
humidity diagnosis, and does not change humidity outputs.

It is also distinct from active staged `solar-weighted-thermal-tendency`, which
uses astronomical insolation geometry and is independent of humidity. This
proposal uses the forecast humidity field as a radiative proxy and removes the
horizontal layer mean to avoid duplicating the accepted global weak-HS thermal
source. It is not a near-surface residual variant; any surface-temperature
effect must arise through prognostic lower-column thermal evolution.

## Evaluator Notes

### 2026-06-18T18:47:01Z

Decision: move to `scrap`.

The physical motivation that water vapor is radiatively active is real, but the
proposed mechanism is too empirical for the next fixed-gate experiment. It
couples temperature to passive humidity anomalies with an arbitrary sign,
vertical taper, cap, and layer-mean removal while the current dry model does
not maintain a radiatively consistent humidity field. That creates a high risk
of amplifying tracer-transport errors or applying heating/cooling in the wrong
regions, especially after recent active-moist dynamics and saturation/latent
heating experiments failed badly.

The proposal is also weakened by nearby thermal-forcing history. Calendar-aware
solar relaxation and mass-neutral weak-Held-Suarez forcing both produced large
negative temperature-driven results, and the active staged
`solar-weighted-thermal-tendency` is already the cleaner radiation-related
fallback because it uses fixed orbital geometry rather than a drifting passive
tracer. This is not a duplicate of the rejected moist virtual-temperature or
saturation-adjustment candidates, but it remains a humidity-coupled positive
thermal forcing with too many predetermined constants and too little evidence
that it can beat the incumbent without perturbing Z500, MSLP, or wind balance.
