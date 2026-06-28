---
schema_version: 1
slug: gradient-wind-surface-diagnostic
title: Curvature-Aware Gradient-Wind 10 m Diagnostic
status: ready
created_at: 2026-06-20T17:06:07Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
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

# Curvature-Aware Gradient-Wind 10 m Diagnostic

## Hypothesis

The current incumbent uses the accepted Richardson-number 10 m wind diagnostic,
but the iteration and validation breakdowns still show negative late-lead
`10m_u_component_of_wind` skill and a persistent low bias in zonal wind. The
rejected Coriolis-rotated surface wind residual showed that a broad vector
rotation can break day-1 surface wind guardrails, and the clean subthreshold
Ekman-inflow diagnostic suggests that a generic boundary-layer inflow correction
is too weak.

A narrower diagnostic should help if it only changes cases where the low-level
flow is visibly curved. In cyclonic and anticyclonic regions, geostrophic wind
can be systematically too strong or too weak because centrifugal acceleration is
missing from the balance. A bounded gradient-wind correction can adjust the 10 m
diagnostic speed without changing the prognostic trajectory, the residual memory
path, or the fixed evaluation contract.

## Mechanism

Register a side-by-side candidate with a suffix such as
`_gradient_10m_diag`. Preserve the entire incumbent rollout and only replace the
final `10m_u_component_of_wind` diagnostic.

After the Richardson diagnostic computes the near-surface vector wind:

- compute a smoothed low-level streamwise curvature proxy from the lowest-model
  wind and local relative vorticity;
- compute a same-grid pressure-gradient magnitude from surface pressure or
  lowest-layer geopotential, using the existing spherical spectral/nodal
  operators rather than finite-difference string logic;
- solve a bounded gradient-wind speed adjustment in the direction of the
  Richardson diagnostic wind, with latitude tapering near the equator and a
  finite fallback to the incumbent diagnostic;
- blend only when curvature and pressure-gradient signs are dynamically
  consistent, and cap the change to a small fractional range such as 15 percent;
- return the adjusted zonal component for the 10 m target while leaving all
  pressure-level and surface-temperature diagnostics unchanged.

The adjustment is diagnostic-only. It must not write back into the primitive
equation state, the DFI state, the weak-HS forcing, or the scale-separated
surface residual memory.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add a single opt-in model entry whose name appends
    `_gradient_10m_diag` to the current incumbent.
- API changes:
  - None. The model still returns one `WeatherState` with the same variables,
    lead times, and forecast contract.
- Tests to update:
  - Add a finite-output diagnostic test for zero curvature, cyclonic curvature,
    anticyclonic curvature, equatorial tapering, and cap enforcement.
  - Add a registry test for the side-by-side candidate.

## Expected Metric Movement

- Expected improvements:
  - Primary target is `10m_u_component_of_wind`, especially days 3-15 where the
    incumbent remains weakly or strongly negative.
  - A small aggregate primary-score gain is plausible even if only the 10 m wind
    component moves, because the proposal is isolated from the otherwise
    successful thermal and pressure changes.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, and `geopotential_500` should be
    bitwise or numerically unchanged except for any shared diagnostic helper
    refactoring.
- Possible regressions:
  - Day-1 10 m wind could regress if the curvature proxy activates in nearly
    straight flow. The cap, equatorial taper, and sign-consistency gate are
    required to avoid repeating the broad correction failure of the rejected
    Coriolis-rotated surface wind residual.

## Risks

- Numerical stability:
  - Low, because the trajectory is unchanged. The diagnostic must guard all
    divisions by Coriolis parameter, curvature radius, and pressure-gradient
    magnitude.
- Compute cost:
  - Low. One or two additional low-level derivative calculations per output time
    are compatible with the reported 4-worker evaluation setup.
- Data leakage:
  - None. The correction uses only the model forecast state at the valid lead.
- Physical plausibility:
  - Moderate. Gradient-wind balance is a large-scale curved-flow approximation,
    not a full turbulent surface-layer model. The proposal is intentionally
    bounded and should not claim to improve convective or terrain-driven winds.
- Rollback complexity:
  - Low. Removing the registry entry and diagnostic branch restores the
    incumbent behavior.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
  - Require finite outputs and no early 10 m wind guardrail failure.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Support the hypothesis if the primary score improves and the day-1/day-2
    10 m wind diagnostics are not degraded enough to offset late-lead gains.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4`.
  - Require validation movement to have the same sign as iteration movement, or
    at minimum no clear validation regression in the 10 m wind component.
- Outcome that would falsify the hypothesis:
  - Near-neutral aggregate movement plus any day-1 10 m wind degradation, or
    unchanged 10 m wind skill, would show that curvature balance is not the
    limiting diagnostic error.

## Citations

- Brill, K. F. (2014). "Revisiting an Old Concept: The Gradient Wind." Monthly
  Weather Review, 142, 1460-1471. https://doi.org/10.1175/MWR-D-13-00088.1
- Holton, J. R., and Hakim, G. J. (2013). "An Introduction to Dynamic
  Meteorology", 5th edition. Academic Press. https://doi.org/10.1016/C2009-0-63394-8
- Beljaars, A. C. M., and Holtslag, A. A. M. (1991). "Flux Parameterization
  over Land Surfaces for Atmospheric Models." Journal of Applied Meteorology,
  30, 327-341. https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2

## Researcher Notes

This is not a residual-memory proposal and does not change the accepted
scale-separated surface residual. It is also not the rejected Coriolis-rotated
surface wind residual: that idea applied a broad vector correction and failed
early 10 m wind guardrails, while this proposal is a same-direction,
curvature-gated speed diagnostic with a hard cap. It is distinct from staged
geostrophic surface wind ideas because it uses the curvature term as the
activation criterion and leaves straight-flow geostrophic cases close to the
incumbent Richardson diagnostic.

## Evaluator Notes

### 2026-06-20T17:10:51Z

Decision: move to `ready`; rank 1 of 1 ready proposal.

This is the strongest next experiment because it is output-diagnostic only,
keeps the accepted rollout, DFI, weak-HS equilibrium, scale-separated residual,
and fixed evaluation contract unchanged, and targets the current incumbent's
remaining late-lead `10m_u_component_of_wind` weakness. Source inspection shows
the accepted Richardson 10 m diagnostic is isolated in
`dinosaur_state_to_weather_state`, so a guarded opt-in diagnostic can be
implemented with low rollback cost.

It is close to staged `geostrophic-surface-wind-residual`, but the curvature
gate and same-direction speed cap make it a better immediate candidate after
the rejected Coriolis-rotated residual and subthreshold Ekman-inflow diagnostic.
The Implementer should keep all caps, latitude tapering, and sign-consistency
logic fixed before scoring and should require zero-curvature and nonfinite
fallback tests to reproduce the incumbent diagnostic exactly.
