---
schema_version: 1
slug: first-step-divergence-balance-filter
title: Filter Only the First-Step High-Wavenumber Divergence Increment
status: ready
created_at: 2026-06-21T08:05:17Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/filtering.py
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Filter Only the First-Step High-Wavenumber Divergence Increment

## Hypothesis

The incumbent already uses DFI and semi-implicit off-centering to control
gravity-wave noise, so continuous divergence damping is likely too blunt.
However, pressure-level to sigma-coordinate initialization can still inject a
small high-wavenumber divergent adjustment in the first positive-time step. A
one-time filter of only the first-step divergence increment may reduce that
adjustment without damping balanced vorticity, temperature, or pressure
evolution during the rest of the forecast.

## Mechanism

Register a side-by-side candidate that preserves the incumbent equation,
DFI, weak-HS forcing, exact Coriolis split, theta tendency, theta recentering,
surface residuals, off-centering, and output packing. After the first
positive-time inner step only, compute the modal divergence increment relative
to the post-DFI initial state, attenuate only the high-total-wavenumber tail of
that increment with a fixed smooth taper, and add the filtered increment back to
the original divergence field. Leave vorticity, temperature variation,
log-surface pressure, tracers, and all later steps unchanged.

The filter must be deterministic, candidate-only, and fixed before scoring. It
must not use truth data, validation statistics, future forecast states, or
golden results. If the filtered first-step state is nonfinite, return the raw
incumbent first-step state.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py` if a reusable smooth
    high-wavenumber taper is needed
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` if a first-step
    hook is cleaner than wrapping the step function in the adapter
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model with a `_first_step_div_filter` suffix.
- API changes:
  - None. Forecast inputs, outputs, leads, and metrics stay unchanged.
- Tests to update:
  - Verify the filter is applied exactly once after DFI and before the second
    positive-time inner step.
  - Verify low wavenumbers of the divergence increment are preserved and the
    high-wavenumber tail is attenuated.
  - Verify no fields except divergence change in the first-step filter helper.
  - Verify finite fallback, registry construction, and a non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - Early `mean_sea_level_pressure` and `geopotential_500` if first-step
    divergent adjustment contaminates mass-field verification.
  - `10m_u_component_of_wind` could improve slightly if noisy divergent wind is
    reduced without altering vorticity.
- Expected neutral metrics:
  - Long leads should remain close to incumbent because no later-step damping is
    applied.
  - `2m_temperature` should be mostly neutral because temperature and residual
    diagnostics are untouched.
- Possible regressions:
  - Filtering divergence alone can disturb a physically meaningful first-step
    mass-wind adjustment, especially near steep pressure gradients.

## Risks

- Numerical stability:
  - Low if the taper is gentle and one-time; moderate if it breaks balance with
    the pressure and temperature fields.
- Compute cost:
  - Negligible to low. One modal taper at startup.
- Data leakage:
  - None. The operation uses only the current forecast state and a fixed mask.
- Physical plausibility:
  - Moderate. It is a bounded initialization-noise filter rather than a
    prognostic physical parameterization.
- Rollback complexity:
  - Low. Remove the wrapper, factory/export, registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Reuse valid cached incumbent metrics from `.logbook/leaderboard.json`.
  - Require primary-score delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4` only
    after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with the same
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the one-time
    divergent adjustment is not a material remaining error source. Any early
    wind or MSLP guardrail failure would show the first-step balance correction
    is too selective.

## Citations

- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a
  Digital Filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Temperton, C. 1988. Implicit Normal Mode Initialization. Monthly Weather
  Review. https://doi.org/10.1175/1520-0493(1988)116%3C1013:INMI%3E2.0.CO;2
- Dynamaxx history:
  `.logbook/history/2026-06-16_19-57-46_divergence-selective-gravity-wave-damping`
  tested continuous explicit divergence damping; this proposal is a one-time
  first-step increment filter instead.
- Dynamaxx history:
  `.logbook/history/2026-06-19_10-17-34_centered-dfi-offcenter-rollout/decision.md`
  found a DFI routing change neutral, so this proposal keeps DFI unchanged.

## Researcher Notes

This is not a forecast-contract change and not an ensemble, adapter, or metric
proposal. It is deliberately narrower than active staged divergence/offcentering
ideas: only one first-step increment is filtered, and only divergence is
changed.

## Evaluator Notes

### 2026-06-21T08:09:05Z

Decision: move to `staging`; keep as a staged backup behind the startup
subcycle.

The proposal is plausible and narrower than the active staged divergence
family because it changes only the first positive-time divergence increment
after DFI, not the full rollout, not vorticity, and not the mass or thermal
state directly. Digital-filter initialization literature supports the general
claim that initialized primitive-equation forecasts can contain spurious
high-frequency gravity-inertia noise, so the scientific direction is credible.

Do not put it in `ready` now. The nearest local evidence remains weak:
`.logbook/history/2026-06-16_19-57-46_divergence-selective-gravity-wave-damping/decision.md`
was clean but negative, and
`.logbook/history/2026-06-19_10-17-34_centered-dfi-offcenter-rollout/decision.md`
was essentially neutral. Active staging already contains
`dfi-divergence-gravity-mode-cleanup`, `divergence-selective-offcentering`, and
`equatorial-gravity-wave-divergence-sponge`; this file is distinct enough to
preserve, but the loop lacks read-only evidence that harmful high-wavenumber
divergent imbalance remains after the accepted DFI and off-centered rollout.
Implementation also risks breaking a physically meaningful first-step
mass-wind adjustment by filtering divergence alone.

### 2026-06-21T10:25:51Z

Decision: move from `staging` to `ready`; ranked as the single ready
model-selection candidate.

The reason to promote this now is comparative, not because the evidence became
strong. The previous note held it behind the startup-subcycle experiment; that
experiment has now been rejected with iteration delta `-0.012135241988475931`
and an early MSLP mean RMSE regression of `+2.3077781360493983%`. That result
argues against spending another run on smaller positive-time steps, but it does
not eliminate the possibility that a one-time initialized divergent increment
is still polluting early mass fields.

Among active staged model-selection ideas, this is one of the lowest-cost and
most reversible tests: it changes only the first positive-time high-wavenumber
divergence increment, leaves vorticity, temperature, log-surface pressure,
tracers, DFI, weak-HS forcing, residuals, off-centering, and later steps on the
incumbent path, and uses no truth data or protocol changes. It is narrower than
`dfi-divergence-gravity-mode-cleanup` because it targets the first positive-time
increment rather than editing the initialized DFI state, and it is much less
broad than grid-remapping, weak-HS rate-placement, or pressure-gradient
dealiasing experiments.

Negative evidence remains important for the Implementer and Scorer handoff:
continuous divergence-selective damping was clean but negative, centered DFI
off-centering was neutral, and filtering divergence alone can remove physically
balanced ageostrophic adjustment. The candidate should therefore use a fixed,
weak, high-wavenumber-only taper, include finite fallback, and be rejected
without validation unless it clears the cached-incumbent iteration gate. This
is a model-selection proposal, not infrastructure; the separate read-only
diagnostic sidecar remains infrastructure-only in staging.
