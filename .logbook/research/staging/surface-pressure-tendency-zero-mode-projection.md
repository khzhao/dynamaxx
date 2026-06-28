---
schema_version: 1
slug: surface-pressure-tendency-zero-mode-projection
title: Project Surface-Pressure Tendency Onto a Conservative Zero Mode
status: staging
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

# Project Surface-Pressure Tendency Onto a Conservative Zero Mode

## Hypothesis

The earlier global pressure anchor was a state correction and was too blunt.
The remaining mass-field error may instead come from small inconsistencies in
the divergence-driven `log_surface_pressure` tendency that accumulate before
diagnostic output. A tendency-level zero-mode projection can preserve the
resolved pressure anomaly pattern while preventing global dry-mass drift, which
is more consistent with continuity than post-step pressure anchoring.

## Mechanism

Add an opt-in candidate that wraps the primitive-equation tendency used by the
incumbent. For the candidate only, compute the incumbent tendency exactly, then
remove the quadrature-weighted zero mode from the `log_surface_pressure`
tendency after converting the tendency to an approximate surface-pressure
increment. The projection leaves nonzero mass modes, vorticity, divergence,
temperature, tracers, weak-HS forcing, offcentered SIL3, Coriolis splitting,
theta recentering, residual correction, and output diagnostics unchanged. It
uses the incumbent tendency if pressure or projection diagnostics are nonfinite.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model suffix such as `_ps_tendency_zero_mode`.
- API changes:
  - None.
- Tests to update:
  - Verify finite projection removes the weighted global pressure increment.
  - Verify nonzero spatial pressure-tendency anomalies are preserved.
  - Verify fallback behavior on nonfinite diagnostics.
  - Verify the candidate factory preserves all incumbent settings except the
    new pressure-tendency projection.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` if residual global mass drift remains after the
    accepted analysis-HS equilibrium and offcentered rollout.
  - `geopotential_500` if pressure drift feeds hydrostatic interpolation.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should be close to
    incumbent because no residual-memory or surface diagnostic path changes.
- Possible regressions:
  - The global pressure tendency may already contain physically meaningful
    adjustment from the sigma-coordinate solver; removing it can harm MSLP.

## Risks

- Numerical stability:
  - Moderate. A continuity-tendency projection is safer than state anchoring,
    but it touches the prognostic mass equation.
- Compute cost:
  - Low. It adds one weighted reduction per step.
- Data leakage:
  - None. It uses only the current model state and tendency.
- Physical plausibility:
  - Moderate. Dry-mass conservation is physically motivated, but projecting
    `log_surface_pressure` tendency is an approximation to pressure tendency.
- Rollback complexity:
  - Low to moderate because it may require a selector in the primitive-equation
    tendency path.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Compare to cached incumbent metrics; require delta at least `+0.002`, clean
    diagnostics, and fixed guardrails.
- Validation gate:
  - Run validation only after iteration promotion and require delta at least
    `+0.001`.
- Outcome that would falsify the hypothesis:
  - Negative iteration movement or an MSLP guardrail failure would show that the
    global pressure tendency is needed or that state-level mass drift is not a
    limiting error.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-16_17-43-05_global-mean-pressure-anchor/decision.md`
  rejected a post-step global pressure anchor as too weak.
- Laprise, R. 1992. The Euler equations of motion with hydrostatic pressure as
  an independent variable. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C0197:TEEOMW%3E2.0.CO;2
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP
  and climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is intentionally not another global pressure anchor. The proposed change
acts before state update at the tendency level and removes only the global
pressure increment, preserving resolved pressure anomalies. It should still be
penalized if the Evaluator prefers not to touch the prognostic mass equation
after several pressure-family failures.

## Evaluator Notes

### 2026-06-21T06:22:22Z

Decision: move to `staging`; ranked 3 of the currently reviewed ideas.

The mechanism is more defensible than a post-step pressure anchor because it
acts at the continuity-tendency level and preserves nonzero pressure modes.
Mass conservation is a legitimate dycore concern, and the proposal is cheap,
deterministic, and not output-only.

Keep it staged rather than ready. The current incumbent benefited from local
surface-pressure dependence in the accepted analysis-HS equilibrium, while a
recent fixed-pressure follow-up regressed primary score. Earlier pressure-family
ideas have also tended to be weak or risky under the fixed gates. This proposal
touches the prognostic mass equation directly, so it should wait behind the
narrower mass-weighted theta recentering candidate unless diagnostics later
show a specific global dry-mass drift that the incumbent still fails to control.
