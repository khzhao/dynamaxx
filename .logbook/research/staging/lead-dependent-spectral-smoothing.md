---
schema_version: 1
slug: lead-dependent-spectral-smoothing
title: Lead-Dependent Predictability-Aware Spectral Smoothing
status: staging
created_at: 2026-06-22T15:04:10Z
author_role: Researcher
target_model: dino_hsl_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/filtering.py
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

# Lead-Dependent Predictability-Aware Spectral Smoothing

## Hypothesis

Predictability is scale dependent: small spatial scales lose deterministic skill
first, so by the medium range a single forecast's small-scale structure is
effectively uncorrelated with reality and contributes pure variance (error) to an
RMSE score. The model's existing dissipation (hyperdiffusion, exponential filter,
off-centered semi-implicit damping) is **constant in forecast time** -- it cannot
express the fact that the appropriate amount of small-scale detail to retain
*decreases as lead time grows*. Progressively damping the least-predictable high
wavenumbers as the forecast advances should reduce RMSE at long leads (where the
model currently degrades most: `mean_sea_level_pressure` and `2m_temperature`
fall well below persistence by day 10-15) by shedding small-scale variance that
is, on average, wrong. This is the deterministic analogue of why a smoothed or
ensemble-mean field scores better than a single rough field at long range.

## Mechanism

Register a side-by-side candidate named `dino_hsl_theta_leadsmooth`. Preserve
every incumbent setting; add a lead-dependent spectral low-pass applied to the
output (and optionally the prognostic spectral state) whose cutoff/attenuation
strengthens with forecast lead.

- Reuse the existing `exponential_filter` machinery in `filtering.py`, but make
  its attenuation a bounded, monotonically increasing function of forecast lead
  time (zero or minimal at lead 0, increasing toward a bounded maximum at day 15),
  with fixed coefficients.
- Apply it as a smoothing of the spectral fields with increasing strength at
  longer leads; keep the large scales (the predictable, balanced flow)
  essentially untouched at all leads and only progressively damp near-truncation
  scales.
- Keep all dynamics, forcing, transport, and the constant-in-time dissipation
  unchanged; this adds a separate lead-scheduled smoothing on top.
- Apply consistently and fall back to the incumbent (no extra smoothing) if the
  schedule produces nonfinite values.

## Implementation Scope

- Expected files: `filtering.py` (lead-scheduled attenuation), `adapter.py`
  (thread the lead/time into the filter), `__init__.py`, `registry.py`, tests.
- Registry changes: add only the side-by-side candidate.
- API changes: none.
- Tests to update: attenuation is monotone increasing in lead and bounded; large
  scales are preserved at all leads while near-truncation scales are increasingly
  damped; lead-0 reproduces the incumbent; nonfinite fallback holds; registry
  coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements: `mean_sea_level_pressure` and `2m_temperature` at days
  7-15, and any variable whose long-lead error is dominated by unpredictable
  small-scale variance.
- Expected neutral metrics: short-lead (day 1-3) skill, since smoothing is
  minimal there; `geopotential_500`, which is already large-scale dominated.
- Possible regressions: over-smoothing can remove real, still-skillful synoptic
  structure at medium leads and hurt `geopotential_500`; the bounded schedule and
  large-scale preservation limit this.

## Risks

- Numerical stability: improves or neutral; this only removes small-scale energy.
- Compute cost: negligible; reuses the existing spectral filter with a scalar
  schedule.
- Data leakage: none; the schedule is a fixed function of lead time, not of the
  verification.
- Physical plausibility: this is a **forecast-calibration / inductive-bias**
  change, not a new physical process -- it encodes scale-dependent predictability,
  a real and well-established property, rather than improving the dynamics.
- Rollback complexity: low.

## Evaluation Plan

- Fast gate: `uv run pytest`; `uv run dynamaxx-eval fast --model dino_hsl_theta_leadsmooth`;
  finite forecasts, zero diagnostic issues.
- Iteration gate: `uv run dynamaxx-eval iteration --model dino_hsl_theta_leadsmooth --workers 4`;
  support is primary-score delta at least `+0.002`, clean diagnostics, and -- importantly --
  no early day-1-to-5 RMSE guardrail regression (the smoothing must not buy long-lead
  gains by hurting short lead).
- Validation gate: `uv run dynamaxx-eval validation --model dino_hsl_theta_leadsmooth --workers 4`
  only after iteration promotion; require validation delta at least `+0.001`.
- Falsification: a clean near-zero or negative delta would show the model's
  long-lead small-scale structure is not net-harmful to RMSE, or that the constant
  dissipation already removes the unpredictable scales.

## Citations

- Citation or source:
  - Dynamaxx source: `filtering.py` `exponential_filter` damps high total
    wavenumbers with a fixed attenuation; the dycore applies it constant in time.
  - Lorenz, E. N. 1969. The predictability of a flow which possesses many scales
    of motion. Tellus (scale-dependent loss of predictability).
    https://doi.org/10.1111/j.2153-3490.1969.tb00444.x
  - Buizza, R., Miller, M., Palmer, T. N. 1999. Stochastic representation of model
    uncertainties in the ECMWF Ensemble Prediction System. QJRMS (smoothness and
    RMSE of best-estimate forecasts).
    https://doi.org/10.1002/qj.49712556006

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-22 as the second
orthogonal lever, decorrelated from the surface-flux and semi-Lagrangian veins and
from the constant-in-time diffusion family (`scale-selective-hyperdiffusion`,
`planetary-wave-preserving-horizontal-diffusion`), none of which schedule
dissipation by lead.

Honesty flag (the role values real improvement over metric-gaming, and this
conversation has tracked that distinction): this is explicitly a
**predictability-calibration** idea, not a physics improvement -- it reduces RMSE
by shedding small-scale variance that is statistically wrong at long range, which
is a legitimate and standard property of calibrated deterministic forecasts but is
not "better dynamics." It is included because it is genuinely orthogonal, untried,
and likely effective on this RMSE metric; the Evaluator/Orchestrator should weigh
it as a calibration lever rather than a dynamical advance. The iteration gate's
early-lead guardrail guards against buying long-lead RMSE by degrading short lead.

## Evaluator Notes

### 2026-06-22T17:26:11Z

Decision: move to `staging`; rank 1 of 2 current proposals; do not recommend
for the next implementation.

The scale-dependent predictability argument is coherent, and the current
`dino_hsl2_theta` incumbent still loses skill to persistence at late leads for
several scored variables. The mechanism is also cheap and mostly local if it is
implemented through the existing spectral filter machinery. Those points make
it worth preserving as a later calibration experiment.

It is not ready. The proposal's front matter targets the prior
`dino_hsl_theta`, and the current incumbent is `dino_hsl2_theta` at
`72efada4e0afbd8e34e3184dbcef90cb91cc051c`. More importantly, the idea is
explicitly a forecast-calibration/RMSE-smoothing lever rather than a dycore
physics improvement. Prior nearby evidence is weak: scale-selective
hyperdiffusion regressed, fixed spectral truncation failed the fast gate,
nonlinear tendency dealiasing and smooth analysis-HS spectral taper were clean
but subthreshold, and the scrapped late-lead synoptic anomaly damping proposal
was rejected for being metric-facing anomaly shrinkage. The active staged
`causal-saved-lead-time-filter` and
`planetary-wave-preserving-horizontal-diffusion` ideas already cover more
physically interpretable smoothing/filtering directions.

Keep this staged only as a bounded, explicitly labeled calibration fallback.
It should not be selected before a fresh Researcher pass produces a more
physical candidate for `dino_hsl2_theta`, and any future promotion would need a
fixed schedule, no validation tuning, no protocol change, and early-lead
guardrails that prevent buying long-lead RMSE with broad loss of structure.
