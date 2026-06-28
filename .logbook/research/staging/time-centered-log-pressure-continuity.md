---
schema_version: 1
slug: time-centered-log-pressure-continuity
title: Time-Center Log-Surface-Pressure Continuity Across Each Inner Step
status: staging
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

# Time-Center Log-Surface-Pressure Continuity Across Each Inner Step

## Hypothesis

The incumbent's `log_surface_pressure` tendency is computed explicitly from the current-step diagnostic `u_dot_grad_log_sp`, while divergence, temperature, and pressure-gradient adjustment are advanced through the accepted off-centered semi-implicit SIL3 step. This can leave the continuity update slightly less time-centered than the coupled mass and thermal adjustment, producing slow MSLP and thickness drift without any obvious nonfinite instability.

A guarded trapezoidal continuity correction for `log_surface_pressure` across each accepted inner step should better align the prognostic mass update with the time-centered divergence and pressure-gradient evolution, improving `mean_sea_level_pressure` and `geopotential_500` without anchoring the pressure field, changing DFI, or adding damping.

## Mechanism

Register a side-by-side candidate extending the incumbent name with `_tc_logp_continuity`. Preserve the incumbent equation, solver, DFI, weak-HS analysis equilibrium, exact Coriolis Strang split, theta tendency, theta recentering, semi-implicit off-centering strength, residual correction, output variables, and fixed protocols.

For this candidate only, wrap the positive-time inner-step function:

- evaluate the incumbent step from `prev_state` to `raw_next_state`;
- recompute `nodal_log_pressure_tendency` from both `prev_state` and `raw_next_state` using the existing `PrimitiveEquationsSigma` diagnostic path;
- replace only `raw_next_state.log_surface_pressure` with `prev_state.log_surface_pressure + 0.5 * dt * (logp_dot_prev + logp_dot_next)` in modal space;
- preserve vorticity, divergence, temperature variation, tracers, and `sim_time` from the raw next state;
- apply the same post-step filters already used by the incumbent after the corrected state, without adding a projection or zero-mode anchor;
- do not apply this wrapper inside DFI for the first candidate, so the test isolates positive-time mass continuity rather than DFI routing;
- fall back to `raw_next_state.log_surface_pressure` if either tendency, the corrected field, or the surface pressure implied by it is nonfinite or nonpositive.

This is a time-centering change to the continuity discretization, not a pressure limiter, mass restore, global pressure anchor, or divergence cleanup.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate with a `_tc_logp_continuity` suffix.
- API changes:
  - None. Forecast inputs, emitted variables, lead steps, metrics, and splits stay fixed.
- Tests to update:
  - Unit-test that a zero continuity tendency leaves `log_surface_pressure` unchanged.
  - Verify the trapezoidal update changes only `log_surface_pressure` and preserves all other state leaves.
  - Verify nonfinite or nonpositive corrected pressure falls back to the incumbent raw next state.
  - Verify DFI still uses the incumbent step path.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 2 to 15 if explicit continuity timing contributes to mass drift.
  - `geopotential_500` through better coupled pressure-thickness evolution.
- Expected neutral metrics:
  - `2m_temperature` should stay near incumbent because thermal tendencies and residual correction are unchanged.
  - `10m_u_component_of_wind` should stay near incumbent because momentum and surface wind diagnostics are unchanged.
- Possible regressions:
  - The raw SIL3 state may already be tuned around explicit continuity, so a cleaner time-centering can perturb accepted phase relationships.
  - Applying the correction only in positive-time rollout may introduce a small DFI/rollout mismatch.

## Risks

- Numerical stability:
  - Moderate. It touches a prognostic mass variable every inner step, so finite and positive-pressure guards are required.
- Compute cost:
  - Low to moderate. It adds one extra continuity diagnostic evaluation per inner step, but no extra lead times or resolution.
- Data leakage:
  - None. It uses only previous and candidate next forecast states.
- Physical plausibility:
  - High. Time-centered continuity is consistent with the semi-implicit treatment of fast mass and gravity-wave adjustment.
- Rollback complexity:
  - Low to moderate. Remove one step wrapper, one option, one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_tc_logp_continuity`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_tc_logp_continuity --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_tc_logp_continuity --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show continuity time-centering is not a material remaining mass-error source. Any early MSLP guardrail failure would show the incumbent explicit continuity timing is safer.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` computes `nodal_log_pressure_tendency` explicitly from `u_dot_grad_log_sp` and advances coupled divergence, temperature, and log pressure through the semi-implicit operator.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds the positive-time step function and post-step filters, giving a localized implementation hook without changing the public API.
- Dynamaxx history: `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md` accepted off-centered SIL3, so this proposal preserves the accepted fast-mode damping strength and only revisits continuity timing.
- Dynamaxx history: `.logbook/history/2026-06-21_08-11-13_startup-subcycled-first-day-rollout/decision.md` rejected startup-only subcycling with early MSLP degradation, so this proposal applies a fixed all-lead continuity discretization rather than a first-day time-step change.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for atmospheric models: a review. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to Geophysics. Springer.

## Researcher Notes

This avoids the rejected pressure-anchor and divergence-filter families: it does not set a zero mode, project divergence, limit increments, or restore DFI mass. It is also not an off-centering weakening proposal; the SIL3 off-centering remains exactly the incumbent value.

## Evaluator Notes

### 2026-06-21T18:04:23Z

Decision: move to `staging`; ranked 2 of 3 in this triage pass.

The mechanism is physically plausible and technically feasible, but it should
not be the next ready experiment. Source inspection confirms
`nodal_log_pressure_tendency` is available on `PrimitiveEquationsSigma`, and a
guarded wrapper around the positive-time inner step could recompute the
continuity tendency before and after the raw step while preserving all non-mass
state leaves. That makes the proposal implementable without source-code
contract or fixed-protocol changes.

Keep staged because recent pressure and time-discretization evidence is
unfavorable for another prognostic mass-equation change. The rejected
flux-form surface-pressure continuity rewrite was clean but strongly negative
with iteration delta `-0.015126833559440334`. The startup subcycled first-day
rollout regressed by `-0.012135241988475931` and failed the early MSLP guard.
The first-step divergence balance filter and Helmholtz momentum projection were
essentially neutral-negative, and the mass-conserving log-pressure smoother
was clean but only `+0.0000014025155478103457`, far below promotion.

This proposal is narrower than those failures because it preserves the
off-centered SIL3 strength and only time-centers the log-surface-pressure
update, but it still touches the prognostic mass field every inner step. The
incumbent's accepted semi-implicit/off-centered balance may already rely on the
current explicit continuity timing. Reconsider this idea only after lower-risk
diagnostic candidates are exhausted or a read-only diagnostic shows a concrete
continuity time-centering residual in the incumbent.
