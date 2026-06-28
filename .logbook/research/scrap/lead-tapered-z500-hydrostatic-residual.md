---
schema_version: 1
slug: lead-tapered-z500-hydrostatic-residual
title: Apply a Lead-Tapered Hydrostatic Residual to Z500 Output
status: scrap
created_at: 2026-06-21T06:20:34Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Apply a Lead-Tapered Hydrostatic Residual to Z500 Output

## Hypothesis

The zero-orography sigma adapter reconstructs pressure-level geopotential
hydrostatically from the forecast column. Prior broad geopotential datum and
mass-residual ideas were either too static or too diffuse, but the target Z500
error may still contain a short-lived hydrostatic reconstruction residual at
lead zero. A low-mode residual that decays over the first few days can correct
initial hydrostatic mismatch without persisting a stale datum through the full
15-day window.

## Mechanism

Add an output-only candidate that changes only pressure-level geopotential
channels, with a fixed focus on `geopotential_500` when it is requested. After
raw trajectory conversion, compute the lead-zero residual between analyzed and
raw `geopotential_500`, retain only large horizontal scales with the existing
spherical-harmonic grid, and add it back to requested leads using a short
smooth taper that reaches zero by roughly day 5. Leave surface pressure, MSLP,
temperature, winds, humidity, prognostic state, DFI, residual correction, and
fixed evaluation protocols unchanged. Use the raw incumbent output if required
channels, shapes, transforms, or finite checks fail.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model suffix such as `_z500_hs_residual_taper`.
- API changes:
  - None.
- Tests to update:
  - Verify only `geopotential_500` changes when present.
  - Verify lead-zero matching, day-5 taper-to-zero behavior, low-mode split,
    and finite fallback.
  - Verify all non-geopotential target channels are unchanged.
  - Verify registry and non-JIT finite forecast coverage.

## Expected Metric Movement

- Expected improvements:
  - Early `geopotential_500` and aggregate primary score if lead-zero
    hydrostatic reconstruction mismatch is material.
- Expected neutral metrics:
  - MSLP, `2m_temperature`, and `10m_u_component_of_wind` should be unchanged
    except for metric aggregation noise.
- Possible regressions:
  - Output-only Z500 correction can fail variable+lead guardrails if the
    residual becomes stale or if it masks a dynamically meaningful height
    adjustment.

## Risks

- Numerical stability:
  - Very low because the change is output-only.
- Compute cost:
  - Low. It adds one low-mode transform per initial condition.
- Data leakage:
  - Low to moderate. It uses only same-time initial analysis fields, but it is a
    scored-channel diagnostic correction and should be held to strict
    guardrails.
- Physical plausibility:
  - Moderate. Hydrostatic reconstruction residuals are plausible, but the taper
    is an empirical approximation.
- Rollback complexity:
  - Low.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Require cached-incumbent delta at least `+0.002`, clean diagnostics, no
    early day-1-through-day-5 RMSE guardrail failure, and no variable-lead
    guardrail failure.
- Validation gate:
  - Run `validation` only after iteration promotion and require delta at least
    `+0.001`.
- Outcome that would falsify the hypothesis:
  - A subthreshold delta or any Z500 variable-lead guardrail failure would show
    that this residual is either too weak or too metric-facing to keep.

## Citations

- Dynamaxx source: `dinosaur_state_to_weather_state` in
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` reconstructs
  pressure-level geopotential from sigma-coordinate temperature, humidity, and
  zero orography.
- Dynamaxx history:
  `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
  rejected a geopotential output diagnostic after a day-1 Z500 guardrail
  failure, motivating a stricter low-mode and short-lead taper.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- ECMWF IFS Documentation Part III: Dynamics and Numerical Procedures,
  hydrostatic pressure and geopotential reconstruction in terrain-following
  coordinates.

## Researcher Notes

This is not the scrapped constant geopotential datum correction and not the
rejected dry-consistent geopotential diagnostic. It is narrower in lead time and
horizontal scale, and it never removes virtual-temperature effects from the
geopotential calculation. Because it is output-only on a scored channel, the
Evaluator should rank it behind trajectory-level proposals unless prior Z500
diagnostics strongly support it.

## Evaluator Notes

### 2026-06-21T06:22:22Z

Decision: move to `scrap`; ranked 4 of the currently reviewed ideas.

The hydrostatic-reconstruction concern is physically recognizable, but this is
an output-only correction to a single scored channel using an initial-analysis
residual and an empirical lead taper. Recent history is unfavorable for this
class: geopotential and mass diagnostic residuals have been weak or guardrail
risky, surface diagnostic variants have regressed the target they aimed to
help, and the accepted gains came from trajectory-level or physically
conditioned residual mechanisms rather than scored-channel patching.

The low-mode and short-lead restrictions reduce risk but do not change the core
problem: the candidate is likely to spend an iteration on a metric-facing
adapter with limited upside and possible Z500 guardrail exposure. The proposal
is distinct from earlier rejected geopotential diagnostics, but not strong
enough to keep in staging while cleaner thermodynamic and mass-balance ideas
remain available.
