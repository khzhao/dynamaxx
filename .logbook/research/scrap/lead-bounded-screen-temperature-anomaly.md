---
schema_version: 1
slug: lead-bounded-screen-temperature-anomaly
title: Limit Late-Lead 2 m Temperature Departure from the Analysis
status: scrap
created_at: 2026-06-22T05:16:38Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
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

# Limit Late-Lead 2 m Temperature Departure from the Analysis

## Hypothesis

The current incumbent's `2m_temperature` remains worse than persistence at every
iteration lead even after the accepted land-sea residual memory. The iteration
CSV for the current incumbent reports `skill_vs_persistence` from `-0.482` at
24 h to about `-1.56` after 240 h for `2m_temperature`, while the accepted
land-sea change left other scored variables nearly unchanged. A dry primitive
equation rollout without a land-surface energy balance can grow unrealistic
screen-temperature departures from the analyzed surface state; bounding only
the excessive late-lead screen-temperature anomaly should preserve useful
synoptic evolution while preventing the diagnostic from drifting far beyond a
persistence-quality envelope.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_t2m_anomaly_bound`.
Preserve the incumbent rollout, DFI, weak-HS equilibrium, theta tendency and
recentering, semi-implicit off-centering, scale-separated residuals, land-sea
T2m residual memory, Richardson 10 m wind diagnostic, output variables, lead
schedule, and fixed protocols.

For the candidate only, apply a final diagnostic guard to `2m_temperature`
after the incumbent residual correction:

- compute the local anomaly from the analyzed initial screen temperature,
  `forecast_t2m(lead) - initial_t2m`;
- keep lead zero exact and keep early leads close to incumbent by using a lead
  ramp that is zero at 0 h and weak through day 2;
- define a fixed growing magnitude envelope, for example a few kelvin plus a
  small square-root-in-lead term, so ordinary weather evolution is retained but
  large dry-dycore screen-temperature drift is clipped;
- replace only values whose absolute anomaly exceeds the envelope with the
  signed envelope value around the initial `2m_temperature`;
- leave `mean_sea_level_pressure`, `geopotential_500`, `10m_u_component_of_wind`,
  pressure-level fields, trajectory states, and residual-decay coefficients
  unchanged;
- fall back exactly to the incumbent output if `2m_temperature` is absent,
  nonfinite, or shape-incompatible.

This is not another land-sea residual-memory proposal: it does not change the
accepted residual split or decay. It is also not the staged bulk-Richardson or
orographic-lapse diagnostic because it does not create a new raw screen
temperature; it only bounds excessive late-lead departure after the accepted
diagnostic path.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry entry for the candidate name above.
- API changes:
  - None. Forecast inputs, outputs, leads, metrics, and evaluation commands stay
    unchanged.
- Tests to update:
  - Unit-test lead-zero exactness, no-op behavior inside the anomaly envelope,
    clipping outside the envelope, and finite fallback.
  - Verify non-`2m_temperature` channels are unchanged relative to the incumbent.
  - Verify the candidate factory preserves every incumbent flag except the new
    final T2m anomaly-bound selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3-15, where the current incumbent remains strongly
    below persistence.
  - Aggregate primary score if the reduction in excessive screen-temperature
    drift outweighs small losses in fast local T2m evolution.
- Expected neutral metrics:
  - `mean_sea_level_pressure`, `geopotential_500`, and
    `10m_u_component_of_wind`, because neither the trajectory nor their output
    diagnostics change.
- Possible regressions:
  - If real near-surface air-mass changes require large local T2m departures
    from the initial state, the envelope can make the diagnostic too persistent.
  - Guardrails could fail if the envelope is too tight at early leads.

## Risks

- Numerical stability:
  - Low. This is a bounded output-only operation after the forecast trajectory.
- Compute cost:
  - Negligible. It adds local elementwise arithmetic for one channel.
- Data leakage:
  - None. It uses only the forecast initial state, forecast lead, and fixed
    constants chosen before scoring.
- Physical plausibility:
  - Moderate. Persistence is a strong baseline for screen temperature when a
    model lacks explicit land-surface thermal inertia, but a hard anomaly
    envelope is a simplified diagnostic closure.
- Rollback complexity:
  - Low. Remove one helper/flag, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_t2m_anomaly_bound`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_t2m_anomaly_bound --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_t2m_anomaly_bound --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that late-lead T2m
    anomaly growth is not the recoverable error source. Any early T2m guardrail
    failure would show the envelope is too intrusive.

## Citations

- Citation or source:
  - Local evidence: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.csv` reports current-incumbent `2m_temperature` skill below persistence at every daily lead.
  - Local history: `.logbook/history/2026-06-21_23-32-41_land-sea-contrast-surface-temperature/decision.md` accepted an output-only land-sea T2m residual-memory change with iteration delta `+0.01662292654392855` and validation delta `+0.01672614488585067`.
  - Local history: `.logbook/history/2026-06-22_01-43-33_land-sea-wind-residual-memory/decision.md` rejected the analogous wind residual memory, so this proposal does not extend the mechanism to wind.
  - Rasp, S., Dueben, P. D., Scher, S., Weyn, J. A., Mouatadid, S., and Thuerey, N. 2020. WeatherBench: A benchmark dataset for data-driven weather forecasting. Journal of Advances in Modeling Earth Systems. https://doi.org/10.1029/2020MS002203
  - ECMWF Newsletter 178, "Improved two-metre temperature forecasts in the 2024 upgrade", describes 2 m temperature as a diagnostic surface-layer variable rather than a prognostic dycore state. https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade

## Researcher Notes

The staged queue already contains raw T2m diagnostic ideas
`bulk-richardson-2m-temperature-diagnostic`, `orographic-lapse-screen-temperature`,
and `diurnal-surface-residual-memory`. This proposal avoids those mechanisms:
it does not change lower-column surface-layer physics, terrain reduction, solar
phase, or residual-memory coefficients. It is a narrower test of whether the
remaining T2m failure is dominated by excessive departure from a strong
persistence baseline after the accepted land-sea correction.

## Evaluator Notes

### 2026-06-22T05:19:01Z

Decision: move to `staging`; no ready promotion.

The proposal is implementable and narrowly scoped: it changes only the final
`2m_temperature` diagnostic, preserves the incumbent trajectory and recently
accepted land-sea residual path, and has negligible compute and rollback cost.
The cached incumbent iteration CSV supports the stated bottleneck: current
`2m_temperature` skill versus persistence is negative at every daily lead,
from `-0.482133367693959` at 24 h to about `-1.54` to `-1.58` across the
late leads. Recent history also supports keeping some surface-temperature
diagnostic ideas alive because `land-sea-contrast-surface-temperature` was
accepted with iteration delta `+0.01662292654392855` and validation delta
`+0.01672614488585067`.

Keep this staged rather than ready because the mechanism is a hard
initial-state anomaly envelope. That is closer to persistence-bounded metric
post-processing than the accepted land-sea surface-type mechanism, and it is
less physically grounded than already staged alternatives such as
`bulk-richardson-2m-temperature-diagnostic`, `orographic-lapse-screen-temperature`,
or `diurnal-surface-residual-memory`. The prior `bounded-screen-temperature-layer-init`
run also warns that same-time screen-temperature anchoring can be numerically
clean while reducing aggregate skill. This proposal can be reconsidered only
after stronger surface-temperature diagnostics are exhausted or after a
Researcher adds evidence that the remaining error is dominated by unphysical
late-lead amplitude excursions rather than real air-mass evolution.

### 2026-06-27T19:07:18Z

Decision: demote to `scrap`.

The just-accepted land/ocean low-mode T2m memory already adds a physically
bounded late-lead residual component and improved both iteration and
validation. This proposal is now too close to persistence-bounded
post-processing: it clips final T2m departures around the initial analysis
without adding a distinct surface-layer, land-cover, or lower-column mechanism.

Given the current ready queue contains a more physical bounded Richardson T2m
diagnostic, this anomaly envelope would be a lower-quality use of an iteration
slot and has higher evaluation-overfit risk. Preserve the history as negative
guidance against hard T2m persistence envelopes unless future diagnostics show
large, localized, non-meteorological amplitude outliers.
