---
schema_version: 1
slug: layer-interface-flux-form-vertical-advection
title: Layer Interface Flux Form Vertical Advection
status: scrap
created_at: 2026-06-21T04:30:49Z
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

# Layer Interface Flux Form Vertical Advection

## Hypothesis

The incumbent keeps the Dinosaur centered vertical-advection treatment. Centered
advective-form vertical transport can be accurate for smooth flow, but over
15-day forecasts it can introduce layer-integral drift and phase error in
baroclinic structures. A conservative layer-interface flux-form vertical
advection option should better preserve column structure for theta and momentum
proxies while avoiding the larger behavior change of a full semi-Lagrangian or
upwind rollout.

## Mechanism

Add a candidate vertical-advection formulation that uses the existing sigma-dot
diagnostic and layer geometry, but computes vertical transport as the
difference of interface fluxes. For each advected prognostic field in the
current vertical-advection path, reconstruct centered interface values from
neighboring sigma levels, multiply by the interface sigma-dot flux, impose zero
normal flux at the top and bottom boundaries, and divide the resulting flux
difference by layer thickness.

The experiment should keep the incumbent horizontal advection, DFI,
semi-implicit offcentering, weak Held-Suarez forcing, residual corrections, and
evaluation output unchanged. It should not add an upwind limiter, a vertical
Courant limiter, or a semi-Lagrangian departure solve; the point is to isolate
conservative flux form from previously considered vertical-advection stabilizers.

## Implementation Scope

- Expected files: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  and any local vertical-advection helper already used by the Dinosaur model.
- Registry changes: add one incumbent-derived model with a suffix such as
  `_flux_form_vertical_adv`.
- API changes: no public API changes; one internal vertical-advection
  formulation option is enough.
- Tests to update: add a shape and finite-value test for the flux-form vertical
  tendency, including the top and bottom boundary flux convention.

## Expected Metric Movement

- Expected improvements: `geopotential_500` and `2m_temperature` at medium and
  longer leads through better vertical phase and column thermal-structure
  retention.
- Expected neutral metrics: `mean_sea_level_pressure`, because log-surface
  pressure tendency and output reduction are not directly changed.
- Possible regressions: `10m_u_component_of_wind` if centered interface fluxes
  alter near-surface shear without enough damping.

## Risks

- Numerical stability: moderate; centered flux-form transport can still ring
  near sharp vertical gradients, so the fast gate must catch nonfinite or noisy
  trajectories.
- Compute cost: low; the method adds local vertical interface arithmetic only.
- Data leakage: none; the formulation uses only current forecast state.
- Physical plausibility: high; flux-form transport is a standard way to improve
  conservation in atmospheric dynamical cores.
- Rollback complexity: low; the candidate is isolated behind a formulation
  option and does not change incumbent factories.

## Evaluation Plan

- Fast gate: run the fixed `fast` protocol and inspect for finite outputs and
  obvious vertical-advection instability.
- Iteration gate: run the fixed `iteration` protocol with the standard worker
  policy; require either aggregate improvement or a Z500/T2m gain without
  material wind and MSLP guardrail failures.
- Validation gate: run fixed `validation` only after the iteration result
  supports the conservative-transport hypothesis.
- Outcome that would falsify the hypothesis: fast instability, broad degradation
  in Z500, or lower-tropospheric temperature regressions that indicate centered
  interface fluxes are increasing vertical noise.

## Citations

- Lin, S.-J., and R. B. Rood, 1996: Multidimensional flux-form
  semi-Lagrangian transport schemes. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Lin, S.-J., 2004: A vertically Lagrangian finite-volume dynamical core for
  global models. Monthly Weather Review. https://doi.org/10.1175/1520-0493(2004)132%3C2293:AVLFDC%3E2.0.CO;2

## Researcher Notes

This is distinct from the staged smoothed-sigma-dot, theta-upwind, upwind
rollout, and vertical-Courant-limited ideas, and from the rejected
semi-Lagrangian vertical-transport proposal. It is not an initialization-only
variant. The proposed experiment isolates conservative layer-interface flux form
while deliberately leaving smoothing, upwinding, departure-point transport, and
evaluation protocols unchanged.

## Evaluator Notes

### 2026-06-21T04:35:33Z

Decision: move to `scrap`; ranked third of the three new proposals.

The proposal is physically respectable, but it is not the right use of the
current search budget. It would replace the centered vertical-advection form
for multiple prognostic and tracer tendencies, making it another broad
vertical-transport discretization test. The active staging queue already
contains better-bounded vertical-advection follow-ups: smoothed sigma-dot,
theta-upwind/upwind, and a local vertical-Courant limiter. The Courant limiter
is especially preferable if diagnostics later implicate vertical transport
because ordinary flow remains on the incumbent centered operator.

Prior evidence also lowers priority. Removing vertical advection failed the
fast gate with nonfinite forecasts, while the theta skew-symmetric scalar
advection change was clean but slightly negative, showing that formal
conservative/split-form transport arguments alone have not translated into
fixed-metric gains. A centered layer-interface flux form may improve column
conservation, but it still risks changing all vertically advected fields and
breaking the empirically matched sigma-coordinate balance. Scrap this duplicate
vertical-transport-family variant and retain the existing staged vertical
experiments as the canonical paths if the Orchestrator revisits that axis.
