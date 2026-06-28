---
schema_version: 1
slug: decaying-planetary-wave-initial-anchor
title: Decaying Low-Mode Initial-State Anchor
status: scrap
created_at: 2026-06-19T06:42:00Z
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

# Decaying Low-Mode Initial-State Anchor

## Hypothesis

The current incumbent has accumulated several successful balance and diagnostic
fixes, but it is still a dry, zero-orography, weakly forced sigma-coordinate
model. Its large-scale mass and height fields can drift away from the analyzed
planetary-wave phase over days 3 to 15, especially in `mean_sea_level_pressure`
and `geopotential_500`. A weak, decaying spectral anchor to the initialized
large-scale state should preserve the slow Rossby-wave envelope long enough to
reduce medium-range mass-field error while still allowing synoptic and
mesoscale evolution in unanchored modes.

The mechanism is inspired by spectral nudging, but it is deliberately narrower
than full analysis nudging: it uses only the same-time initialized state,
anchors only the lowest nonzero total wavenumbers, decays with forecast time,
and is disabled during the time-reversed DFI initializer.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_low_mode_anchor`.
Preserve the incumbent initialization, DFI span, weak-HS forcing, log-pressure
and hydrostatic layer initialization, symmetric exact-Coriolis split,
stability-aware residual correction, Richardson 10 m wind diagnostic, theta
tendency, theta layer-mean recentering, horizontal diffusion, output variables,
lead schedule, metrics, and deterministic evaluation gates.

For the candidate only:

- after DFI has produced the positive-time starting state, store that filtered
  starting state as the anchor, not the raw pressure-level analysis;
- build a smooth modal mask from `coords.horizontal.modal_axes` that is one for
  low nonzero total wavenumbers, for example total wavenumber `1 <= n <= 6`,
  tapers to zero over `6 < n <= 10`, and is exactly zero for the global
  wavenumber-zero mode and for all higher modes;
- after each positive-time inner step and existing filters, replace only the
  masked part of `vorticity`, `divergence`, `temperature_variation`, and
  `log_surface_pressure` with a convex blend toward the matching masked anchor
  coefficients;
- use one fixed weak relaxation, for example an e-folding time of 8 forecast
  days with an additional forecast-time envelope that halves the relaxation by
  day 5, so the anchor is active during spinup and medium-range phase drift but
  cannot lock the day-15 state to persistence;
- leave tracers, `sim_time`, near-surface output residuals, pressure-level
  interpolation, and all requested output variables unchanged;
- fall back to the incumbent next state whenever the masked blend would produce
  nonfinite values or shape mismatches.

This is not a new diffusion, viscosity, semi-implicit weighting, smoother, or
theta recentering rule. It does not damp high wavenumbers and does not preserve
zonal means exactly; it adds a weak memory of the initialized nonzero planetary
wave state.

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
  - None. `DycoreModel.forecast`, input variables, emitted variables, lead
    steps, target variables, protocols, and metric definitions remain
    unchanged.
- Tests to update:
  - Unit-test the modal anchor mask: zero at total wavenumber zero, one across
    the protected nonzero low modes, smooth finite taper, and zero above the
    taper.
  - Unit-test the step filter on synthetic modal states: masked coefficients
    move monotonically toward the anchor, unmasked coefficients and tracers are
    unchanged, and finite fallback returns the incumbent next state.
  - Verify the anchor state is taken after DFI initialization and that the new
    filter is applied only during positive-time rollout.
  - Verify the candidate factory preserves every incumbent option except the
    low-mode anchor selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 3 to 10 if
    low-wavenumber phase and amplitude drift is a remaining error source.
  - Late `10m_u_component_of_wind` may improve slightly if large-scale wind
    phase is better constrained without changing the surface-layer diagnostic.
- Expected neutral metrics:
  - Lead-zero and day-1 fields should remain close to the incumbent because the
    anchor uses the DFI-filtered starting state and the blend is weak.
  - `2m_temperature` should be mostly neutral because the accepted residual
    correction and theta mean recentering are unchanged.
- Possible regressions:
  - Anchoring planetary modes can delay real synoptic evolution and worsen
    phase RMSE even if the large-scale amplitude looks more realistic.
  - Blending low-mode temperature and pressure can perturb geostrophic balance,
    causing Z500, MSLP, or wind guardrail regressions.
  - If the current incumbent's remaining error is dominated by local physics or
    surface diagnostics, the iteration delta may be clean but near zero.

## Risks

- Numerical stability:
  - Moderate. The blend is bounded and excludes the global zero mode, but it
    modifies prognostic modal coefficients every positive-time inner step.
- Compute cost:
  - Low. The mask is precomputed from modal axes and the filter is elementwise;
    it adds no transforms, forecast steps, output volume, or worker changes.
- Data leakage:
  - Low. It uses only the same forecast's initialized state and fixed spectral
    geometry. It must not use later verification fields, validation scores,
    learned climatology, or golden data.
- Physical plausibility:
  - Moderate. Spectral nudging is an established way to retain large-scale flow
    constraints, but using only the initial state is a medium-range memory
    hypothesis rather than a full data-assimilation method.
- Rollback complexity:
  - Low. Remove one adapter option, one step-filter helper, one factory/export,
    one registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_low_mode_anchor`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_low_mode_anchor --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` with
    clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_low_mode_anchor --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that low-mode
    initial-state memory is not a material remaining error source. Any early
    Z500, MSLP, or 10 m wind guardrail failure would show that planetary-mode
    anchoring disrupts balanced forecast evolution more than it helps.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds
    the current incumbent from side-by-side flags and applies positive-time
    step filters through `time_integration.step_with_filters`.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py`
    exposes `modal_axes`, modal masks, and total-wavenumber indexing needed for
    a low-mode filter.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_00-02-28_theta-zero-mode-thermal-recentering/decision.md`
    accepted the current incumbent and notes the remaining tradeoff is late
    `10m_u_component_of_wind`, not early diagnostic instability.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_03-32-34_mass-conserving-logp-spectral-smoother/decision.md`
    rejected a high-mode log-pressure smoother as effectively neutral, so this
    proposal targets nonzero low-mode phase memory instead of pressure-noise
    smoothing.
  - von Storch, H., Langenberg, H., and Feser, F. 2000. A Spectral Nudging
    Technique for Dynamical Downscaling Purposes. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(2000)128%3C3664:ASNTFD%3E2.0.CO;2
  - Waldron, K. M., Paegle, J., and Horel, J. D. 1996. Sensitivity of a
    Spectrally Filtered and Nudged Limited-Area Model to Outer Model Options.
    Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1996)124%3C0529:SOASFA%3E2.0.CO;2
  - Miguez-Macho, G., Stenchikov, G. L., and Robock, A. 2004. Spectral nudging
    to eliminate the effects of domain position and geometry in regional climate
    model simulations. Journal of Geophysical Research: Atmospheres.
    https://doi.org/10.1029/2003JD004495

## Researcher Notes

This is decorrelated from the two untriaged proposal files. It is not
`leith-nonlinear-eddy-viscosity`, because it adds no state-dependent
dissipation and does not compute vorticity-gradient viscosity. It is not
`offcentered-semi-implicit-gravity-wave`, because it leaves the implicit
operator and Crank-Nicolson weighting unchanged.

It also avoids the recent rejected mechanisms. It is not
`mass-conserving-logp-spectral-smoother`, because it does not smooth high-mode
surface pressure; it anchors nonzero low-mode balanced state coefficients. It
is not `zonal-mean-theta-recentering`, because it excludes the total-wavenumber
zero mode and applies only a weak decaying blend rather than exact
latitude-by-latitude theta preservation. It is not the rejected 10 m wind
diagnostic, weak-HS forcing, or theta scalar-advection family, because it does
not alter output shear scaling, forcing algebra, or scalar transport form.

The closest staged idea is `planetary-wave-preserving-horizontal-diffusion`,
but that only removes low-mode numerical damping from the diffusion filter. The
present proposal adds initialized low-mode memory after the accepted filters,
so it tests whether planetary-wave phase drift, not cumulative diffusion alone,
is a remaining forecast error source.

## Evaluator Notes

### 2026-06-19T06:48:12Z

Decision: move to `scrap`.

The proposal is implementable, but the scientific and scoring risk is too high
for the current incumbent. A decaying blend back toward the initialized
low-mode state is effectively a persistence anchor on prognostic vorticity,
divergence, temperature, and log pressure. It uses no future truth fields, but
any gain would be hard to separate from suppressing real Rossby-wave phase
evolution rather than improving the dycore.

Recent evidence argues against stronger anchoring/recentering ideas. The
accepted theta zero-mode recentering already used a narrow global thermal
constraint and still left late 10 m wind as the limiting guardrail, while the
stronger zonal-mean theta recentering passed fast but became nonfinite from day
6 onward with early wind, Z500, and MSLP guardrail failures. The rejected
mass-conserving log-pressure smoother was stable but effectively neutral.
Compared with the already staged planetary-wave-preserving diffusion idea,
this anchor is more intrusive because it repeatedly edits balanced low modes
toward the initial state. Scrap it rather than spending a ready slot on a
memory mechanism with high balance and phase-error risk.
