---
schema_version: 1
slug: coherent-u-residual-gate
title: Gate 10 m Wind Residual Memory by Flow Coherence
status: ready
created_at: 2026-06-21T21:34:31Z
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

# Gate 10 m Wind Residual Memory by Flow Coherence

## Hypothesis

The accepted Richardson 10 m wind diagnostic and scale-separated residual memory
made near-surface wind a high-value output path, but recent broad wind
diagnostics regressed early `10m_u_component_of_wind`. That suggests the raw
diagnostic is useful, while carrying the full initial `10m_u_component_of_wind`
residual can be harmful in columns where the model's lower-layer flow is not
coherent with the analyzed surface wind.

A local coherence gate can preserve the accepted residual where the lower-column
flow supports it and damp only sign-inconsistent or weak-flow residual memory.
This targets the residual carry, not the raw 10 m wind diagnostic, so it avoids
another broad day-1 wind diagnostic replacement.

## Mechanism

Register a side-by-side candidate extending the incumbent name with
`_u_residual_coherence_gate`. Preserve the incumbent trajectory, DFI, weak-HS
analysis equilibrium, theta tendency, theta mean recentering, off-centered SIL3,
scale-separated residual split, pressure-level outputs, and Richardson 10 m
wind diagnostic.

For this candidate only:

- leave raw `10m_u_component_of_wind` diagnosis unchanged;
- compute the existing lead-zero residual as analyzed `10m_u_component_of_wind`
  minus raw model `10m_u_component_of_wind`;
- diagnose a coherence factor from same-time analyzed 10 m wind, raw diagnosed
  10 m wind, lowest sigma-layer `u`, and the next sigma-layer `u`;
- keep the factor near one when analyzed and model near-surface winds have the
  same sign and the lower-column shear does not imply a reversal;
- smoothly reduce the residual amplitude where the residual would reverse the
  raw wind sign, where the raw lower-column flow is weak, or where the lower two
  sigma layers disagree strongly;
- apply the factor only to the `10m_u_component_of_wind` residual before the
  accepted high/low spectral split and lead decay;
- preserve lead-zero exactness by continuing to overwrite requested lead zero
  with the analyzed field;
- leave `2m_temperature` residuals and all mass/geopotential fields on the
  incumbent path;
- fall back to the incumbent residual if any required wind field is absent,
  shape-incompatible, or nonfinite.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate with suffix `_u_residual_coherence_gate`.
- API changes:
  - None. Forecast inputs, outputs, lead schedule, metrics, and fixed protocols
    remain unchanged.
- Tests to update:
  - Unit-test same-sign, opposite-sign, weak-flow, and nonfinite fallback cases.
  - Verify lead-zero `10m_u_component_of_wind` still exactly matches analysis.
  - Verify only the `10m_u_component_of_wind` residual amplitude changes; raw
    wind diagnosis, `2m_temperature`, MSLP, Z500, pressure-level fields, and
    trajectory state stay on the incumbent path.
  - Verify candidate factory preserves incumbent flags except the new residual
    gate selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at early and medium leads if the accepted residual
    sometimes over-persists inconsistent surface wind increments.
  - Primary score can improve with minimal movement in non-wind targets because
    the change is output-side and one-channel.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, and `geopotential_500` should be
    effectively neutral.
- Possible regressions:
  - The accepted residual may already be empirically optimal; damping it can
    undercorrect real surface-wind representativeness errors.
  - A poor coherence proxy can reduce useful residuals during fronts or jets
    where vertical shear is physically real.

## Risks

- Numerical stability:
  - Low. The rollout state and raw diagnostics are unchanged.
- Compute cost:
  - Low. The gate adds local algebra to an existing output residual path.
- Data leakage:
  - Low. It uses only same-time initial analysis and forecast fields already
    used by the incumbent residual correction.
- Physical plausibility:
  - Moderate. Surface-layer coupling depends on flow direction, stability, and
    shear; the proposal uses only a bounded subset of that information.
- Rollback complexity:
  - Low. Remove one helper/flag, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    incumbent, clean diagnostics, and no fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show residual coherence
    is not a useful remaining wind-error source. Any early `10m_u_component_of_wind`
    guardrail failure would show the gate removes too much useful residual.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
    `_apply_scale_separated_near_surface_residual_correction` and the accepted
    Richardson 10 m wind diagnostic.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/decision.md`
    accepted the bounded Richardson 10 m wind diagnostic with large wind gains.
  - Dynamaxx history:
    `.logbook/history/2026-06-20_17-12-34_gradient-wind-surface-diagnostic/decision.md`
    rejected a broad curvature-aware wind diagnostic after early wind guardrail
    regression, motivating a narrower residual-only gate.
  - Beljaars, A. C. M. and Holtslag, A. A. M. 1991. Flux Parameterization over
    Land Surfaces for Atmospheric Models. Journal of Applied Meteorology.
    https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2
  - Stull, R. B. 1988. An Introduction to Boundary Layer Meteorology. Kluwer.
    https://doi.org/10.1007/978-94-009-3027-8

## Researcher Notes

This is not another raw 10 m wind diagnostic. The accepted Richardson diagnostic
is preserved exactly. It is also not the staged stability-bounded residual
amplitude proposal, which caps residuals by lower-column stability for both
surface targets. This proposal changes only the `10m_u_component_of_wind`
residual and only through directional/shear coherence, using the latest wind
diagnostic failures as negative evidence against broad replacement.

## Evaluator Notes

### 2026-06-21T21:38:13Z

Moved to `ready`. This is the strongest next candidate in the current batch
because it is output-side, one-channel, easy to roll back, and directly
incorporates the negative evidence from the rejected broad gradient-wind
diagnostic without changing the accepted Richardson raw wind path. The main
risk is undercorrecting useful wind residuals, but the proposed same-time
coherence gate is bounded, fallback guarded, and unlikely to perturb mass,
temperature, or geopotential guardrails. Rank 1 of 3 for the Orchestrator's
next selection consideration.
