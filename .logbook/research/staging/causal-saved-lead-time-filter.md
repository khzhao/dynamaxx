---
schema_version: 1
slug: causal-saved-lead-time-filter
title: Causally Time-Filter Saved Mass and Thermal Outputs
status: staging
created_at: 2026-06-19T21:03:11Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Causally Time-Filter Saved Mass and Thermal Outputs

## Hypothesis

The accepted off-centered SIL3 scheme strongly improved mass fields, but it
does not guarantee that the state saved exactly at a 24 hour multiple is free
of residual high-frequency gravity-wave phase. The fixed WeatherBench2 metrics
sample discrete valid times; if `log_surface_pressure` and hydrostatic
temperature still carry small sub-hour oscillations, the saved MSLP and Z500
fields can be noisier than the slowly balanced trajectory envelope.

A short causal time filter applied only to saved mass and thermal output states
can suppress residual fast oscillations at verification times without changing
the positive-time rollout, DFI state, forcing, off-centering, or wind control
variables. Because the filter is backward-looking, a lead's output never uses
states later than that lead.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_saved_time_filter`.
Preserve the incumbent forecast trajectory, DFI, weak-HS forcing, exact
symmetric Coriolis split, horizontal diffusion, theta tendency, theta mean
recentering, stability-aware residual decay, Richardson 10 m wind diagnostic,
output variables, lead schedule, and fixed evaluation protocols.

For this candidate only:

- during positive-time rollout, keep the actual carry state exactly incumbent;
- for each saved outer lead after lead zero, retain the current state plus the
  two preceding inner-step states when available;
- create a diagnostic saved state with a fixed causal low-pass stencil, for
  example `0.50 * x(t) + 0.30 * x(t - dt) + 0.20 * x(t - 2 dt)`;
- apply that diagnostic stencil only to `temperature_variation` and
  `log_surface_pressure`, because those directly affect `geopotential_500`,
  MSLP, and 2 m temperature diagnostics;
- leave `vorticity`, `divergence`, tracers, and the true carry state unfiltered
  so 10 m wind does not receive an artificial time lag;
- use the raw incumbent saved state for lead zero and for any output where the
  short inner-step history is unavailable;
- fall back to the raw saved state if the filtered diagnostic state is
  nonfinite or shape-incompatible.

This is an output-state time filter. It is not another DFI variant, not a
semi-implicit off-centering change, not a spatial log-pressure smoother, and
not a vertical normal-mode prognostic filter.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` if a reusable
    trajectory helper with inner-step output history is preferred.
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. The model still returns `WeatherState` at the requested lead steps
    with the same variables and shapes.
- Tests to update:
  - Unit-test the causal stencil on synthetic states and verify no future state
    contributes to an earlier saved lead.
  - Verify the carry state after the rollout is identical to the incumbent when
    the diagnostic filter is enabled.
  - Verify only `temperature_variation` and `log_surface_pressure` are filtered;
    vorticity, divergence, tracers, and `sim_time` are unchanged in saved
    diagnostic states.
  - Verify lead zero remains exact and finite fallback returns raw outputs.
  - Verify the candidate factory preserves every incumbent option except the
    saved-lead time-filter selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 1 to 7 if residual
    fast oscillations are contaminating discrete saved lead times.
  - `2m_temperature` may improve modestly because the lowest sigma-layer
    temperature diagnostic is filtered before the accepted residual correction.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because
    vorticity and divergence saved states are not filtered.
- Possible regressions:
  - A backward-looking time filter can introduce phase lag in evolving mass and
    temperature fields.
  - If the accepted off-centering has already removed the relevant fast modes,
    this diagnostic filter will be neutral or slightly worse.

## Risks

- Numerical stability:
  - Very low. The rollout carry state is unchanged; only saved diagnostic states
    are filtered.
- Compute cost:
  - Low to moderate. The implementation must retain a short inner-step history
    for saved outputs but does not change resolution, lead count, or model
    physics. Memory impact is bounded to two additional state snapshots during
    the inner scan.
- Data leakage:
  - Low. The filter is causal and uses no truth, validation statistics, fitted
    climatology, or future forecast states beyond the requested lead.
- Physical plausibility:
  - Moderate. Time filters and normal-mode initialization methods are standard
    approaches to suppressing high-frequency gravity oscillations, but the
    candidate applies the idea only to saved diagnostics rather than to the
    physical forecast state.
- Rollback complexity:
  - Low to moderate. Remove one trajectory-output helper, one adapter selector,
    one factory/export, one registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_saved_time_filter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_saved_time_filter --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure,
    and no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_saved_time_filter --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that saved-time
    high-frequency mass/thermal noise is not material. Any early MSLP, Z500,
    or T2m guardrail failure would show the causal lag costs more than the
    smoothing helps.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  already contains digital filter initialization and trajectory construction
  helpers; `adapter.py` converts saved Dinosaur states to WeatherState outputs.
- Dynamaxx history:
  `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md`
  accepted off-centered SIL3 but did not test saved-output time filtering.
- Dynamaxx history:
  `.logbook/history/2026-06-19_10-17-34_centered-dfi-offcenter-rollout/decision.md`
  rejected DFI solver routing as neutral, so this proposal avoids DFI routing
  and filters only saved positive-time diagnostics.
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a
  Digital Filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Peckham, S. E., Smirnova, T. G., Benjamin, S. G., Brown, J. M., and Kenyon,
  J. S. 2016. Implementation of a Digital Filter Initialization in the WRF
  Model and Its Application in the Rapid Refresh. Monthly Weather Review.
  https://doi.org/10.1175/MWR-D-15-0219.1
- Temperton, C. 1988. Implicit Normal Mode Initialization. Monthly Weather
  Review.
  https://doi.org/10.1175/1520-0493(1988)116%3C1013:INMI%3E2.0.CO;2

## Researcher Notes

This is decorrelated from the four recent rejected histories. It is not
`centered-dfi-offcenter-rollout` because DFI and rollout solvers remain
incumbent. It is not `dfi-theta-mean-recenter` because no DFI filters are
changed. It is not `theta-consistent-implicit-gravity-operator` because the
implicit pressure/gravity matrix is untouched. It is not
`ekman-inflow-10m-wind-diagnostic` because wind diagnostics are intentionally
left raw.

It is also not the scrapped `vertical-normal-mode-gravity-wave-filter`, which
would alter prognostic vertical modes. The actual forecast carry evolves as the
incumbent; only the saved diagnostic mass and thermal leaves are causally
time-filtered before WeatherState packing.

## Evaluator Notes

### 2026-06-19T21:10:25Z

Decision: move to `staging`; ranked 3 of 3 fresh proposals.

The mechanism is plausible enough to preserve but not strong enough for the
ready slot. Literature check: Lynch and Huang 1992 supports digital filtering
as a way to suppress spurious high-frequency oscillations in model variables,
but that is stronger evidence for initialization or full trajectory filtering
than for a one-sided diagnostic smoother applied only at saved verification
leads. Source inspection confirms the current forecast path returns saved
outer-step states from `trajectory_from_step` and converts them to
`WeatherState`; implementing this proposal would likely require a custom
saved-output history path or a trajectory helper change that touches shared
time-integration behavior.

The proposal is not a duplicate of the scrapped vertical normal-mode filter
because it leaves the carry state unchanged and avoids modal eigenbasis
selection, and it is not another DFI routing experiment. The risk is instead
metric-facing diagnostic smoothing: a backward-looking stencil can introduce a
real phase lag in evolving mass and thermal fields, and the accepted
off-centered SIL3 incumbent already delivered large MSLP/Z500 gains while the
recent centered-DFI routing change was essentially neutral.

Keep staged as a low-priority, bounded diagnostic experiment if future evidence
shows residual saved-time oscillations in mass or thermal outputs. If promoted,
the stencil weights must be fixed before scoring, no future state may enter any
lead, wind variables must remain raw, and tests must prove that the positive-time
carry state is exactly incumbent-equivalent.
