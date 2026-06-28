---
schema_version: 1
slug: pressure-ramped-vertical-dse-wtg
title: Pressure-Shock-Guarded Vertical DSE Transport on WTG Incumbent
status: ready
rank: 1
priority: high
created_at: 2026-06-25T12:21:45Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg
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

# Pressure-Shock-Guarded Vertical DSE Transport on WTG Incumbent

## Hypothesis

The rejected `vertical-dse-transport-mass-hsl` experiment was not a weak idea:
it improved the iteration primary score by `+0.0550844901388417` but failed the
fixed day-1 MSLP guardrail. That result says DSE-consistent vertical thermal
transport is a high-signal mechanism, but its immediate pressure adjustment is
too abrupt. The current WTG incumbent already improves downstream mass and wind
evolution, so a short-lead-shock-guarded vertical-DSE branch may preserve the
large medium-lead benefit while protecting the early pressure guardrail.

## Mechanism

Add one side-by-side model, for example `dino_hsl2_mass_dse_wtg_vdse_ramp`,
derived from `dino_hsl2_mass_dse_wtg`. Preserve the accepted mass-DSE HSL
horizontal transport and accepted WTG filter.

For this candidate only:

- compute both the incumbent theta-derived vertical thermal transport and the
  rejected DSE-derived vertical thermal transport;
- form only the incremental vertical-DSE tendency relative to the incumbent
  theta vertical tendency;
- multiply that increment by a fixed smooth forecast-time ramp, for example
  zero through the first 24 forecast hours, increasing to full strength by 72
  hours;
- cap the incremental temperature tendency per inner step and remove a
  layerwise low-mode area mean from the early ramp window so the increment does
  not apply a sudden broad pressure-thickness shock;
- add the guarded increment back to the accepted WTG incumbent tendency;
- fall back exactly to `dino_hsl2_mass_dse_wtg` if model time is unavailable,
  pressure thickness, DSE, sigma-dot, ramp weights, or selected tendencies are
  nonfinite.

This proposal is not an incumbent rerun of `vertical-dse-transport-mass-hsl`.
It changes the failure mode identified by the decision record: the short-lead
pressure shock.

## Implementation Scope

- Expected files: add one optional vertical-DSE increment selector in
  `primitive_equations.py`, initialize and propagate `sim_time` for this
  candidate in `adapter.py` if needed, expose a factory through `__init__.py`,
  register one model key, and add focused tests.
- Registry changes: add `dino_hsl2_mass_dse_wtg_vdse_ramp`; preserve
  `dino_hsl2_mass_dse_wtg` exactly when the selector is disabled.
- API changes: none. Forecast inputs, outputs, lead steps, target variables,
  metrics, and fixed protocols remain unchanged.
- Tests to update: ramp weights at 0, 24, and 72 hours; exact no-op before the
  ramp starts; finite capped vertical-DSE increment after ramp activation;
  early low-mode mean removal on synthetic fields; fallback when `sim_time` or
  pressure/DSE diagnostics are invalid; registry and smoke forecast coverage.

## Expected Metric Movement

- Expected improvements: `geopotential_500`, `mean_sea_level_pressure`, and
  `2m_temperature` after day 3 if DSE-consistent vertical transport was the
  source of the prior large primary-score gain.
- Expected neutral metrics: day-1 MSLP should be protected by the zero initial
  ramp; `10m_u_component_of_wind` should change mainly through balanced mass
  feedback rather than a direct momentum edit.
- Possible regressions: delaying the vertical-DSE increment can remove much of
  the prior aggregate gain, and any remaining broad thermal increment can still
  damage MSLP or Z500 once the ramp activates.

## Risks

- Numerical stability: moderate; the vertical transport scalar changes every
  step after the ramp, but the candidate is capped and finite-guarded.
- Compute cost: low to moderate; DSE is already diagnosed for the accepted
  horizontal path, but the candidate adds one vertical tendency and ramp/gating
  algebra.
- Data leakage: none; the ramp uses forecast model time and fixed constants,
  not validation outcomes or future truth.
- Physical plausibility: moderate to high; dry static energy is the same
  thermodynamic invariant that helped horizontal transport, and the ramp is a
  pragmatic guard against spinup shock.
- Rollback complexity: moderate; remove one selector, model-time plumbing if
  added, one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate: run `uv run pytest` and `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp`; require clean diagnostics.
- Iteration gate: compare fixed iteration against the cached
  `dino_hsl2_mass_dse_wtg` incumbent metrics. Review day-1 MSLP explicitly
  before any validation run because this proposal targets that guardrail.
- Validation gate: run fixed validation only after iteration promotion and
  clean guardrails.
- Outcome that would falsify the hypothesis: a clean subthreshold iteration
  delta would show that delaying the vertical-DSE increment removes the useful
  signal; any day-1 to day-5 MSLP guardrail failure would show the shock guard
  is insufficient.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-24_05-18-28_vertical-dse-transport-mass-hsl/decision.md`
  records the large positive iteration delta and day-1 MSLP guardrail failure
  that motivate this bounded restatement.
- Dynamaxx history:
  `.logbook/history/2026-06-25_01-45-51_tropical-wtg-mass-dse-relaxation/decision.md`
  accepted the current WTG incumbent and noted downstream mass and wind
  improvement.
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
  Assimilation Using Incremental Analysis Updates. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2

## Researcher Notes

This is materially different from the rejected unrestricted vertical-DSE
candidate because it is derived from the accepted WTG incumbent, applies only a
ramped incremental vertical-DSE tendency, and explicitly guards the known
short-lead MSLP failure mode. It is also distinct from active staged vertical
advection ideas, which change sigma-dot smoothing, Courant limiting, upwinding,
or vertical stencils. This proposal keeps the vertical operator and changes only
the thermodynamic scalar increment after an initial pressure-protection window.

## Evaluator Notes

### 2026-06-25T12:26:00Z

Decision: move to `ready`; ranked 1 of 3 new proposals.

This is the only candidate in the set that targets a previously score-scale
mechanism instead of making another small WTG refinement. The rejected
`vertical-dse-transport-mass-hsl` run improved iteration primary score by
`+0.0550844901388417` with clean diagnostics, and its terminal failure was
specific: `mean_sea_level_pressure` at 24 h regressed by `+12.24782391640764%`
against the single-lead guardrail. This proposal is a bounded restatement of
that mechanism on top of the current WTG incumbent, with a fixed zero-through-
24 h ramp, full strength only after 72 h, capped increments, early low-mode
mean removal, and finite fallback.

The proposal satisfies the loop constraints: it is one side-by-side model,
keeps forecast outputs and fixed evaluation protocols unchanged, does not use
future truth or validation tuning, and has focused tests for the known
guardrail-protection mechanism. The source scope is moderate because it touches
the primitive-equation tendency path and may require model-time plumbing, but it
is still narrower and more empirically justified than broad vertical-advection
rewrites. Its compute cost is also preferable to WTG-in-every-IMEX-stage
diagnostics.

Treat this as high risk but worth the next rollout slot. The Implementer should
keep the ramp constants fixed from the documented day-1 pressure-shock failure,
preserve exact incumbent behavior before ramp activation, and avoid any
validation/golden tuning. The Scorer should review day-1 through day-5 MSLP
guardrails explicitly before validation.
