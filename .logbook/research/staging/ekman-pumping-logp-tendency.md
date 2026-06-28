---
schema_version: 1
slug: ekman-pumping-logp-tendency
title: Add a Weak Ekman-Pumping Surface-Pressure Tendency
status: staging
created_at: 2026-06-21T19:46:17Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a Weak Ekman-Pumping Surface-Pressure Tendency

## Hypothesis

The incumbent has no explicit boundary-layer mass convergence mechanism. It
does have near-surface diagnostic residuals and a Richardson 10 m wind output,
but those do not feed back into the dry mass field. A weak, bounded Ekman
pumping tendency can represent the surface-stress-driven convergence/divergence
that modulates synoptic pressure without changing the forecast contract or
adding generic Rayleigh drag.

This targets `mean_sea_level_pressure` and downstream `geopotential_500` through
a trajectory-level mass tendency, not by output reconstruction.

## Mechanism

Add an opt-in primitive-equation forcing term or adapter-composed explicit ODE
that emits only a `log_surface_pressure` tendency. Preserve all incumbent
momentum, thermal, DFI, Coriolis, diffusion, residual, and output paths.

For each explicit tendency call:

- diagnose lowest-layer wind and low-level relative vorticity from the current
  state;
- form a small Ekman-pumping proxy proportional to the curl/divergence of a
  linear surface stress, smoothly suppressed near the equator where `f` is
  small;
- remove the area-weighted global mean of the proxy so total dry mass is not
  created or destroyed;
- cap the equivalent surface-pressure tendency to a fixed small Pa-per-day
  scale;
- add the finite, capped tendency to `log_surface_pressure`;
- use the incumbent zero tendency if wind, vorticity, or pressure diagnostics
  are nonfinite.

The proposed candidate should not apply direct momentum drag in the first test.
That makes it distinct from existing boundary-layer drag proposals and isolates
whether a missing Ekman mass-flux signal matters.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` if the forcing
    is cleaner inside the primitive-equation class
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate suffix such as `_ekman_logp`.
- API changes:
  - None.
- Tests to update:
  - Verify the tendency integrates to zero global surface-mass tendency.
  - Verify equatorial suppression and finite fallback.
  - Verify momentum, temperature, tracers, and output-variable lists are
    unchanged by the forcing object.
  - Add registry and finite non-JIT smoke coverage.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 2-15 if missing boundary-layer pumping
    contributes to pressure amplitude or phase errors.
  - `geopotential_500` if improved pressure evolution reduces thickness/height
    drift.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should be near neutral because
    direct thermal forcing, wind diagnostics, and residual memory are unchanged.
- Possible regressions:
  - A crude pumping proxy can introduce pressure tendencies with the wrong phase.
  - Suppressing or capping too strongly may make the candidate effectively
    neutral.

## Risks

- Numerical stability:
  - Moderate. The forcing touches the prognostic mass equation, but the global
    mean removal and local cap limit runaway pressure changes.
- Compute cost:
  - Low. It adds wind/vorticity diagnostics and reductions inside the existing
    tendency path.
- Data leakage:
  - None. It uses only forecast state, latitude, and fixed constants.
- Physical plausibility:
  - Moderate. Ekman pumping is physically real, but this is a minimal dry,
    coarse-grid parameterization rather than a full PBL scheme.
- Rollback complexity:
  - Low to moderate depending on whether the helper lands in `adapter.py` or
    `primitive_equations.py`.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002` with clean
    diagnostics and no fixed early RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion; require at least `+0.001` validation delta.
- Outcome that would falsify the hypothesis:
  - A negative MSLP contribution, an early MSLP guardrail failure, or a clean
    near-zero aggregate delta would show this mass-pumping closure is not useful
    for the current incumbent.

## Citations

- Repository code: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py:1284`
  computes the current explicit `log_surface_pressure` tendency only from
  sigma-coordinate continuity.
- Repository code: `src/dynamaxx/dycore/models/dinosaur/adapter.py:1893`
  already composes a thermal-only weak-HS forcing object, so a side-by-side
  explicit mass-only forcing can follow the same composition pattern.
- Repository history:
  `.logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium/decision.md:24`
  shows an analysis-conditioned physical forcing can materially improve both
  iteration and validation without changing fixed protocols.
- Repository history:
  `.logbook/history/2026-06-21_08-11-13_startup-subcycled-first-day-rollout/decision.md`
  warns that generic startup time-discretization changes worsened MSLP, so this
  proposal targets a missing physical mass tendency instead.
- Ekman, V. W. 1905. On the influence of the Earth's rotation on ocean-currents.
  Arkiv for Matematik, Astronomi och Fysik.
- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press.

## Researcher Notes

This is not a duplicate of staged `geostrophic-sparing-boundary-layer-drag`,
`exponential-boundary-layer-rayleigh-drag`, or `richardson-momentum-mixing`
because it does not damp or mix wind. It tests the mass-convergence side of
boundary-layer coupling only. It is also not another MSLP output-reduction or
pressure-level reconstruction idea: the correction enters the prognostic
`log_surface_pressure` tendency during rollout and is compared under the fixed
fast, iteration, and validation protocols.

## Evaluator Notes

### 2026-06-21T19:51:53Z

Decision: move to `staging`.

This is not an output-reconstruction, metric, split, or lead-time change. It
also differs from staged low-level drag proposals because it isolates the mass
convergence side of boundary-layer coupling instead of directly damping
momentum. The zero-global-mean cap and finite fallback make the idea cheap and
bounded enough to preserve as researchable.

Do not make it `ready` now. It touches the prognostic
`log_surface_pressure` tendency directly, and current history gives pressure
family ideas a high burden of proof: fixed-pressure analysis-HS regressed, the
surface-pressure tendency zero-mode projection is already staged, and generic
startup/time-discretization changes worsened MSLP. A pure Ekman-pumping proxy
without the corresponding surface-stress momentum tendency may also have the
wrong phase even if the mass integral is conserved. Keep staged behind more
local analysis-HS or diagnostic ideas, and only promote if later evidence shows
remaining MSLP error is specifically a missing boundary-layer mass-flux signal.
