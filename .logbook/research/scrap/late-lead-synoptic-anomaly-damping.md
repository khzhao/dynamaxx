---
schema_version: 1
slug: late-lead-synoptic-anomaly-damping
title: Dampen Late-Lead Synoptic Output Anomalies Toward the Initial State
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

# Dampen Late-Lead Synoptic Output Anomalies Toward the Initial State

## Hypothesis

The current incumbent has useful short-lead mass and wind skill, but the
iteration CSV shows `mean_sea_level_pressure`, `geopotential_500`, and
`10m_u_component_of_wind` become worse than persistence at later daily leads.
For example, MSLP skill is positive at 24-48 h but negative by 72 h, Z500 turns
negative after about 144 h, and 10 m zonal wind turns negative after about
96 h. This is consistent with predictable synoptic anomalies losing phase
coherence faster than the coarse dry dycore can maintain. A lead-ramped,
output-only damping of late-lead synoptic anomalies toward the analyzed initial
state should retain the incumbent's early skill while preventing long-lead
mass and wind outputs from underperforming a persistence baseline.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_synoptic_anomaly_damp`.
Preserve the incumbent forecast trajectory, initialization, DFI, weak-HS
forcing, Coriolis split, theta formulation, off-centering, near-surface
residuals, land-sea T2m residual memory, output variables, lead schedule, and
fixed protocols.

For the candidate only, apply a final diagnostic transform to selected
synoptic outputs after the incumbent WeatherState is packed:

- apply only to `mean_sea_level_pressure`, `geopotential_500`, and
  `10m_u_component_of_wind` when each channel is present in both initial and
  forecast output states;
- leave `2m_temperature` unchanged so this experiment is decorrelated from
  recent surface-temperature residual work;
- compute the forecast anomaly relative to the corresponding analyzed initial
  channel and multiply that anomaly by a fixed lead-dependent damping factor;
- keep the factor exactly `1.0` through short leads where the incumbent beats
  persistence, then ramp smoothly toward a conservative late-lead floor such as
  `0.65`;
- optionally apply the damping only to broad synoptic scales by reusing the
  existing spherical-harmonic split helper; if that adds implementation risk,
  use a full-field damping with stricter channel-invariance tests;
- fall back exactly to the incumbent channel if initial data are absent,
  nonfinite, or shape-incompatible.

This is not a mass-diagnostic residual-memory proposal: it does not add the
lead-zero forecast residual back to mass channels. It directly shrinks late-lead
forecast anomalies around the analyzed initial state, and it excludes
`2m_temperature`.

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
  - None. The forecast contract, requested variables, target variables, leads,
    metrics, and evaluation protocols remain unchanged.
- Tests to update:
  - Unit-test lead-ramp values, absent-channel fallback, finite fallback, and
    exact no-op behavior before the ramp starts.
  - Verify `2m_temperature` remains unchanged relative to the incumbent.
  - Verify only the three selected synoptic channels can differ and that lead
    zero remains the analyzed initial state when requested.
  - Verify the candidate factory preserves every incumbent option except the
    final synoptic anomaly damping selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` after day 3, `10m_u_component_of_wind` after day
    4, and `geopotential_500` after day 6, where current skill is below
    persistence in the incumbent iteration CSV.
  - Aggregate primary score if late-lead gains exceed any reduced dynamical
    anomaly amplitude.
- Expected neutral metrics:
  - `2m_temperature`, because this candidate does not touch it.
  - Early-lead mass and wind metrics, because the ramp is exactly no-op at
    short leads.
- Possible regressions:
  - Real large-amplitude synoptic development at late leads may be damped too
    strongly, increasing RMSE against verifying analyses.
  - Full-field damping can reduce useful small-scale wind signals; a low-mode
    implementation lowers that risk but is slightly more complex.

## Risks

- Numerical stability:
  - Low. The forecast trajectory is unchanged and the transform is bounded.
- Compute cost:
  - Negligible for full-field damping; low if a spectral low-mode split is used.
- Data leakage:
  - None. It uses only forecast initial conditions, forecast lead, and constants
    fixed before scoring.
- Physical plausibility:
  - Moderate. Weather predictability decays with lead time, and persistence is
    an accepted baseline, but output anomaly damping is a simplified closure
    rather than a prognostic physics improvement.
- Rollback complexity:
  - Low. Remove one helper/flag, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_synoptic_anomaly_damp`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_synoptic_anomaly_damp --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_synoptic_anomaly_damp --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that late-lead
    anomaly damping removes useful signal faster than it prevents drift below
    persistence. Any early mass or wind guardrail failure would show the ramp
    is not conservative enough.

## Citations

- Citation or source:
  - Local evidence: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.csv` shows current-incumbent MSLP, Z500, and 10 m zonal-wind skill crossing below persistence at late leads.
  - Local history: `.logbook/history/2026-06-16_15-28-07_mass-diagnostic-analysis-residuals/decision.md` found mass diagnostic residuals safe but too weak, with iteration delta `+0.00042505322207886387`; this proposal uses anomaly damping instead of residual addition.
  - Local history: `.logbook/history/2026-06-22_01-43-33_land-sea-wind-residual-memory/decision.md` rejected a near-surface wind residual-memory extension, so this proposal does not modify residual memory or land-sea wind coefficients.
  - Lorenz, E. N. 1969. The predictability of a flow which possesses many scales of motion. Tellus. https://doi.org/10.3402/tellusa.v21i3.10086
  - Rasp, S., Dueben, P. D., Scher, S., Weyn, J. A., Mouatadid, S., and Thuerey, N. 2020. WeatherBench: A benchmark dataset for data-driven weather forecasting. Journal of Advances in Modeling Earth Systems. https://doi.org/10.1029/2020MS002203

## Researcher Notes

The staged queue already contains pressure-continuity, mass-filter, diffusion,
and saved-time-filter ideas. This proposal is deliberately different: it does
not alter surface-pressure tendency, the time integrator, horizontal diffusion,
or saved-state temporal filtering. It is an output-only test of whether the
current dry dycore's late-lead synoptic anomalies are less useful than a
conservative persistence-weighted anomaly, while leaving the recently accepted
`2m_temperature` land-sea mechanism untouched.

## Evaluator Notes

### 2026-06-22T05:19:01Z

Decision: move to `scrap`.

Reject this as too close to persistence blending and metric post-processing for
a model-selection experiment under the fixed protocol. It damps three scored
output channels toward their analyzed initial values without changing the
forecast trajectory, mass continuity, pressure-gradient balance, surface
diagnostics, or a physically identifiable missing process. The proposal is
explicitly motivated by channels crossing below the persistence baseline, so
the transform would mostly make the metrics easier by shrinking late-lead
anomalies rather than improving the dycore state.

The negative prior evidence is strong enough to avoid spending an iteration:
`mass-diagnostic-analysis-residuals` was safe but subthreshold at
`+0.00042505322207886387`, `land-sea-wind-residual-memory` regressed the
current incumbent by `-0.0005121116477311283`, and broad damping-style changes
have repeatedly been neutral or negative unless tied to a specific numerical
imbalance. The staged queue already contains more defensible mass/wind ideas
such as causal saved-time filtering, pressure-continuity fixes, and
state-dependent momentum or diffusion mechanisms. If late synoptic error is a
real remaining bottleneck, it should be pursued through one of those physical
or numerical mechanisms, not by output anomaly shrinkage toward persistence.
