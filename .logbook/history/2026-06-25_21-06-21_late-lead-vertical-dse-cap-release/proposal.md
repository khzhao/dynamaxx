---
schema_version: 1
slug: late-lead-vertical-dse-cap-release
title: Late-Lead Vertical DSE Cap Release
status: ready
created_at: 2026-06-25T20:26:17Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Late-Lead Vertical DSE Cap Release

## Hypothesis

The unrestricted `vertical-dse-transport-mass-hsl` candidate produced a large
iteration primary-score gain of `+0.0550844901388417` but failed the 24 h MSLP
single-lead guardrail. The accepted current incumbent recovered most of that
signal with a zero-through-24 h, full-by-72 h ramp, broad low-mode pressure
guard, and fixed `0.05 K` per-step cap. The latest baroclinic-mode follow-up
then showed that exposing more vertical-DSE structure early can damage
`2m_temperature`.

The remaining path with the best risk profile is therefore not earlier spinup.
It is to leave the first five forecast days exactly incumbent and test whether
the accepted per-step cap is too conservative only after the fixed early
guardrail window. A late-lead cap release may recover part of the unrestricted
vertical-DSE signal at days 6 to 15 while preserving the accepted early
temperature and pressure behavior.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_latecap`, derived from
`dino_hsl2_mass_dse_wtg_vdse_ramp`.

Inside `pressure_ramped_vertical_dse_increment_temperature_tendency`:

- compute the incumbent pressure-ramped, low-mode-pressure-guarded
  vertical-DSE increment exactly as today;
- keep the current maximum per-step temperature increment exactly
  `0.05 K` through 120 forecast hours, so saved leads through day 5 are
  bitwise or tolerance-identical to the incumbent;
- after 120 h, increase only the cap by a fixed smooth forecast-time schedule,
  for example from `0.05 K` at 120 h to `0.08 K` by 192 h, with no further
  growth afterward;
- apply the wider cap only to the already pressure-guarded vertical-DSE
  increment, leaving ramp weights, low-mode guard, WTG relaxation, mass-DSE HSL
  transport, weak-HS forcing, surface residuals, and output packing unchanged;
- retain the incumbent cap when `sim_time`, step size, pressure thickness,
  vertical-DSE diagnostics, or capped modal tendency is nonfinite;
- keep all constants fixed before any scoring and do not tune the cap from
  iteration or validation metrics.

This is not lead-dependent output smoothing and not a WTG-only microvariant.
It changes one safety limiter on the already accepted vertical-DSE increment,
and only after the first five days.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key such as
    `dino_hsl2_mass_dse_wtg_vdse_latecap`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead schedule, metrics,
    and fixed evaluation protocols remain unchanged.
- Tests to update:
  - Verify the late cap schedule is exactly `0.05 K` through 120 h, smoothly
    reaches the fixed late cap by 192 h, and remains bounded afterward.
  - Verify synthetic increments smaller than the incumbent cap are unchanged.
  - Verify synthetic increments larger than the incumbent cap but smaller than
    the late cap differ only after the late-release time.
  - Verify disabled selector and nonfinite diagnostics fall back to exact
    incumbent behavior.
  - Verify the candidate factory preserves every incumbent flag except the new
    late cap selector and model name.
  - Add registry and finite smoke-forecast coverage.

## Expected Metric Movement

- Expected improvements:
  - Iteration primary score should improve by roughly `+0.002` to `+0.008` if
    the accepted `0.05 K` cap suppresses useful late vertical-DSE adjustment.
  - `geopotential_500` and `mean_sea_level_pressure` at days 6 to 15 should
    improve most directly if late hydrostatic thickness and pressure phase are
    under-adjusted by the incumbent cap.
  - Validation primary score should improve by roughly `+0.001` to `+0.005` if
    the late-lead signal is not split-specific.
- Expected neutral metrics:
  - Saved leads through day 5 should remain exactly or nearly exactly
    incumbent by construction, including early `2m_temperature`, MSLP, Z500,
    and 10 m wind guardrail summaries.
  - `10m_u_component_of_wind` should move mainly through downstream mass-field
    feedback, not through any direct wind or surface diagnostic change.
- Possible regressions:
  - The accepted cap may be essential for suppressing late noisy thermal
    impulses, so relaxing it can worsen late MSLP, Z500, or `2m_temperature`.
  - Larger late thermal increments can feed pressure-gradient and wind errors
    after day 6 even if the first five days are protected.

## Risks

- Numerical stability:
  - Moderate. The change relaxes a safety limiter on a high-signal tendency, but
    only after the early guardrail window and with the incumbent finite
    fallback.
- Compute cost:
  - Negligible. It adds one forecast-time scalar schedule and uses the same
    tendency computation.
- Data leakage:
  - None. The schedule is a fixed function of forecast model time and constants
    chosen before scoring.
- Physical plausibility:
  - Moderate. Limiters are numerical safeguards, and allowing more vertical-DSE
    adjustment after spinup is plausible if early imbalance was the primary
    failure mode. The cap schedule remains empirical and must not become a
    validation-tuned coefficient.
- Rollback complexity:
  - Low. Remove one cap-schedule selector, one factory/export, one registry key,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_latecap`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_latecap --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    `dino_hsl2_mass_dse_wtg_vdse_ramp`, clean diagnostics, no early day-1-to-5
    mean RMSE guardrail failure, and no variable-by-lead RMSE guardrail failure.
  - The Scorer should explicitly confirm that leads through 120 h are
    incumbent-equivalent before interpreting any late-lead gains.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_latecap --workers 4`
    only after iteration promotion.
  - Support requires validation primary-score delta at least `+0.001` with
    clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the incumbent cap
    is not suppressing useful late vertical-DSE signal. Any day-1-to-day-5
    guardrail movement above numerical noise would show the implementation is
    not actually preserving the early incumbent trajectory.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-24_05-18-28_vertical-dse-transport-mass-hsl`
  measured a large vertical-DSE iteration gain of `+0.0550844901388417` but
  rejected the candidate after a 24 h MSLP guardrail failure.
- Dynamaxx history:
  `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg`
  accepted the current pressure-ramped and capped vertical-DSE incumbent with
  clean iteration and validation guardrails.
- Dynamaxx history:
  `.logbook/history/2026-06-25_17-17-23_baroclinic-mode-vertical-dse-spinup`
  rejected earlier internal vertical-DSE spinup after early `2m_temperature`
  mean RMSE regressed by `+2.6769825875213316%`.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: a review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lorenz, E. N. 1969. The predictability of a flow which possesses many scales
  of motion. Tellus. https://doi.org/10.1111/j.2153-3490.1969.tb00444.x

## Researcher Notes

This is distinct from the scrapped `late-lead-synoptic-anomaly-damping` and
staged `lead-dependent-spectral-smoothing` because it does not shrink output
anomalies or smooth fields toward persistence. The forecast trajectory changes
only through the already accepted vertical-DSE tendency, and only after day 5.

It is also distinct from `tropopause-capped-vertical-dse-increment`: that staged
idea reduces part of the accepted vertical-DSE increment near the upper
stability transition, while this proposal keeps the accepted increment intact
through day 5 and then tests whether the safety cap is too tight at late leads.
The recent baroclinic-mode rejection is treated as negative evidence against
earlier thermal spinup, which is why this proposal is an exact early no-op.

## Evaluator Notes

### 2026-06-25T20:33:00Z

Decision: move to `ready`; ranked 1 of 4 current proposals.

This is the best next candidate. It is implementable as a small side-by-side
selector on the accepted vertical-DSE path, keeps the forecast contract and
fixed evaluation protocols unchanged, and is an exact no-op through the
day-1-to-day-5 guardrail window by construction. That directly avoids repeating
the rejected early internal-mode spinup failure while still testing remaining
headroom from the high-signal vertical-DSE mechanism.

The change has low blast radius: one fixed forecast-time cap schedule, incumbent
finite fallback behavior, unchanged WTG/mass-DSE/output paths, and focused
factory/registry/unit tests. The main risk is that the accepted `0.05 K` cap is
already optimal, but the expected upside is cleanly tied to late-lead MSLP/Z500
and should be reversible if iteration is subthreshold.
