---
schema_version: 1
slug: bulk-aerodynamic-surface-stress
title: Bulk Aerodynamic Surface Stress For Lower-Level Momentum
status: staging
created_at: 2026-06-23T14:35:50Z
author_role: Researcher
target_model: dino_hsl2_theta_dse_hsl
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Bulk Aerodynamic Surface Stress For Lower-Level Momentum

## Hypothesis

The incumbent already uses an ocean-weighted bulk sensible heat flux, but
low-level momentum has no comparable surface stress tendency. A weak,
finite-capped bulk aerodynamic stress in the lowest sigma layer should reduce
near-surface wind overpersistence and improve the `10m_u_component_of_wind`
target without changing output diagnostics or evaluation contracts.

## Mechanism

Compose a new explicit forcing with the incumbent equation. Diagnose lowest
layer wind speed from modal vorticity/divergence, compute
`C_D |V| V / h_bl`, weight it by the existing land-sea/ocean mask when
available, cap the per-step wind decrement, and transform the resulting vector
momentum tendency back to modal vorticity and divergence. Keep the forcing
zero-mean in the global angular-momentum sense by subtracting the area-weighted
lowest-layer zonal acceleration before the curl/divergence transform. If any
diagnostic is nonfinite, return a zero tendency and exactly recover the
incumbent path.

## Implementation Scope

- Expected files: `adapter.py` for a `_BulkSurfaceStressForcingSigma` class and
  `_compose_bulk_surface_stress_equation`; `__init__.py` and `registry.py` for
  a short side-by-side model alias such as `dino_hsl2_sfcstress`.
- Registry changes: add one factory derived from
  `dry_static_energy_hsl_transport_dinosaur_dycore_model()` with an
  `apply_bulk_surface_stress` boolean.
- API changes: none; no new inputs or outputs are required. Reuse the existing
  land-sea fraction loader when available, and fall back to an all-surface
  bounded stress if the mask is unavailable.
- Tests to update: add unit tests for finite stress tendencies, cap behavior,
  zero-tendency fallback on nonfinite inputs, and unchanged factory settings for
  the incumbent.

## Expected Metric Movement

- Expected improvements: `10m_u_component_of_wind` at days 1-7, with possible
  secondary `mean_sea_level_pressure` improvement from less noisy low-level
  convergence.
- Expected neutral metrics: `geopotential_500` should be mostly neutral because
  the forcing is confined to the lowest sigma layer and capped.
- Possible regressions: excessive drag could weaken synoptic lows and degrade
  MSLP or low-level temperature advection.

## Risks

- Numerical stability: vector drag can overdamp weak or stagnant winds if the
  speed floor is mishandled; use a smooth speed floor and per-step cap.
- Compute cost: one additional lowest-layer wind diagnostic per inner step;
  practical under the reported CPU/GPU envelope.
- Data leakage: no future data; optional land-sea mask is static lower-boundary
  information already used by accepted incumbent ancestry.
- Physical plausibility: a single-layer stress is crude and lacks full boundary
  layer mixing; keep coefficients weak and cite it as a stress closure, not a
  complete PBL scheme.
- Rollback complexity: low, because the forcing is composed side-by-side and
  can return exactly zero.

## Evaluation Plan

- Fast gate: run `uv run pytest` and
  `uv run dynamaxx-eval fast --model dino_hsl2_sfcstress`.
- Iteration gate: run
  `uv run dynamaxx-eval iteration --model dino_hsl2_sfcstress --workers 4`,
  requiring primary-score promotion and no early MSLP/wind guardrail failure.
- Validation gate: run
  `uv run dynamaxx-eval validation --model dino_hsl2_sfcstress --workers 4`
  only after iteration promotion.
- Outcome that would falsify the hypothesis: `10m_u_component_of_wind` does not
  improve enough to offset neutral thermal fields, or capped drag creates
  measurable MSLP/Z500 guardrail regressions.

## Citations

- Garratt, J. R. (1992), The Atmospheric Boundary Layer, Cambridge University
  Press, https://doi.org/10.1017/CBO9780511622635.
- Fairall, C. W., Bradley, E. F., Rogers, D. P., Edson, J. B., and Young,
  G. S. (1996), "Bulk Parameterization of Air-Sea Fluxes for Tropical
  Ocean-Global Atmosphere Coupled-Ocean Atmosphere Response Experiment,"
  Journal of Geophysical Research, 101(C2), 3747-3764,
  https://doi.org/10.1029/95JC03205.
- Local code reference:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py`, accepted
  `_OceanBulkSensibleHeatFluxForcingSigma` composition and finite fallback
  pattern.

## Researcher Notes

This is distinct from the rejected land-sea wind residual memory candidate,
which was an output residual correction and scored near neutral. This proposal
changes a prognostic lower-boundary momentum tendency, keeps the forecast
contract unchanged, and does not touch HSL trajectory geometry or pressure-work
terms. It also differs from broad boundary-layer-drag staging ideas by tying
the closure to the accepted bulk-flux infrastructure and by enforcing a
zero-net zonal acceleration guard.

## Evaluator Notes

### 2026-06-23T14:38:43Z

Decision: move to `staging`.

The mechanism is physically plausible and forecast-contract compatible. Bulk
aerodynamic stress is a real lower-boundary momentum closure, the accepted
ocean bulk sensible heat flux shows the codebase can benefit from carefully
bounded lower-boundary physics, and this proposal is more mechanistic than the
rejected land-sea wind residual-memory diagnostic.

Do not put it in `ready` for the next run. The active staging queue already
contains several lower-boundary momentum ideas, including weak Rayleigh drag,
geostrophic-sparing drag, Richardson momentum mixing, and surface-drag thermal
dissipation. This proposal also requires wind transform, vector stress,
curl/divergence reconstruction, masking, caps, and angular-momentum guard logic
inside the rollout path. That is a larger implementation and balance surface
than the moist-static-energy HSL follow-up.

Keep it staged because it is a useful differentiated fallback if the next
thermodynamic-transport experiment fails. Promotion should require either
diagnostics showing a material remaining `10m_u_component_of_wind` low-level
momentum sink error or exhaustion of the narrower accepted-HSL transport
follow-ups. If later promoted, it should use a single predeclared weak
coefficient and strict per-step caps to avoid spending MSLP/Z500 guardrail
margin.
