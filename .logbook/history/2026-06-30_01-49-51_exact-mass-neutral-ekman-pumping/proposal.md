---
schema_version: 1
slug: exact-mass-neutral-ekman-pumping
title: Exact Surface-Mass-Neutral Ekman Pumping Increment
status: ready
created_at: 2026-06-30T01:45:03Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
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

# Exact Surface-Mass-Neutral Ekman Pumping Increment

## Hypothesis

The accepted `dino_ri2m_ekman_coupled` closure showed a large positive signal by
coupling bounded lower-layer stress to an area-neutral log-surface-pressure
pumping increment. That accepted projection is neutral in the area mean of
`delta log(ps)`, but global dry surface mass is proportional to the area mean of
`ps`, not to the area mean of `log(ps)`. For finite local increments, a
log-neutral pressure update can still introduce a small global surface-mass
change through the exponential map.

Replacing only the Ekman pumping projection with an exact surface-mass-neutral
log-pressure increment should preserve the accepted stress and pumping pattern
while removing a physically spurious pressure zero-mode. This targets
`mean_sea_level_pressure` and balanced thickness without repeating the recent
neutral roughness redistribution, subthreshold pressure-work heating, or staged
Coriolis-scaled Ekman-depth geometry change.

## Mechanism

Register one side-by-side candidate such as `dino_ri2m_ekman_massfix` derived
from `ekman_coupled_dinosaur_dycore_model()`.

Inside `_ekman_coupled_surface_step_filter`, keep the incumbent stress formula,
drag coefficient, fixed boundary-layer depth, vertical taper, equatorial
pumping taper, wind caps, pressure cap, finite fallback, and wind projection.
Change only the projection of `raw_log_pressure_increment`.

Add a helper such as `_bounded_surface_mass_neutral_logp_increment` that:

- takes `raw_log_pressure_increment`, current nodal `surface_pressure`, the
  existing coupled pressure cap, and quadrature weights;
- solves for one scalar offset by monotone bisection so
  `area_mean(surface_pressure * (exp(clipped(raw_delta - offset)) - 1)) == 0`
  within numerical tolerance;
- applies the same absolute cap used by the incumbent pressure increment, so
  every local `delta log(ps)` remains bounded even when the mass-neutral offset
  is active;
- falls back exactly to the incumbent `_bounded_area_neutral_field` projection
  if the surface-pressure field is nonpositive, the bisection bracket is invalid,
  or the candidate increment is nonfinite;
- keeps the existing modal/nodal projection-scale safety check after the helper.

The resulting pressure update is still a bounded log-pressure increment, but
its conserved scalar is the area-weighted surface pressure implied by the
forecast state. No forecast input, output variable, lead, metric, or evaluation
protocol changes.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one candidate key such as `dino_ri2m_ekman_massfix`.
- API changes:
  - None.
- Tests to update:
  - Verify the helper preserves `sum(weights * ps * exp(delta))` for finite
    synthetic pressure fields.
  - Verify every returned local increment is within the incumbent cap.
  - Verify zero raw increment returns zero and reproduces the incumbent no-op.
  - Verify nonpositive, nonfinite, or invalid-bracket inputs fall back to the
    incumbent log-area-neutral projection.
  - Verify the candidate factory preserves all `dino_ri2m_ekman_coupled` flags
    except the new mass-neutral pumping selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` if the accepted Ekman pumping is injecting a small
    dry-mass zero mode during long rollouts.
  - `geopotential_500` if better surface-mass consistency reduces balanced
    thickness drift.
  - `10m_u_component_of_wind` should retain most of the accepted Ekman gain
    because the wind stress increment is unchanged.
- Expected neutral metrics:
  - `2m_temperature`, because the RI2m diagnostic, low-mode T2m memory, and
    thermal tendencies are untouched.
- Possible regressions:
  - The incumbent log-area-neutral increment may be acting as an empirical MSLP
    compensator. Exact pressure-mass neutrality could give back a small part of
    the accepted surface-pressure skill.

## Risks

- Numerical stability:
  - Low to moderate. The pressure increment remains capped and finite-guarded,
    but it changes the mass scalar conserved by a high-signal accepted closure.
- Compute cost:
  - Low. It adds one scalar bisection over a surface field inside an existing
    filter and no new spectral transforms.
- Data leakage:
  - None. It uses only the current forecast surface pressure, the incumbent
    Ekman pumping increment, fixed caps, and grid quadrature weights.
- Physical plausibility:
  - High. A closed dry surface-pressure update should not create or remove
    global dry mass through a boundary-layer pumping proxy.
- Rollback complexity:
  - Low. Remove one helper/flag, one factory/export, one registry key, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_ekman_massfix`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_massfix --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    incumbent iteration primary `-0.16500618979404214`, clean diagnostics, and
    no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_ekman_massfix --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` against cached incumbent
    validation primary `-0.16591150807771451` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the incumbent
    log-area-neutral projection is already sufficient or empirically better.
    Any MSLP, Z500, or U10 guardrail failure would show the exact mass repair
    disrupts the accepted stress-pumping balance.

## Citations

- de Roode, S. R. and Siebesma, A. P. 2020. "A Bound on Ekman Pumping."
  Journal of Advances in Modeling Earth Systems.
  https://doi.org/10.1029/2019MS001976
- Tan, B. 2000. "Ekman Pumping for Stratified Planetary Boundary Layers Adjacent
  to a Free Surface or Topography." Journal of the Atmospheric Sciences.
  https://doi.org/10.1175/1520-0469(2000)057%3C3334:EPFSPB%3E2.0.CO;2
- Diamantakis, M. and Flemming, J. 2014. "Global mass fixer algorithms for
  conservative tracer transport in the ECMWF model." ECMWF Technical Memorandum
  734.
  https://www.ecmwf.int/sites/default/files/elibrary/2013/9055-global-mass-fixer-algorithms-conservative-tracer-transport-ecmwf-model.pdf
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to
  Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Local positive evidence:
  `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/decision.md`
  accepted the bounded coupled Ekman stress-pumping closure with iteration delta
  `+0.04799113626142959` and validation delta `+0.04683104652127085`.
- Local negative evidence:
  `.logbook/history/2026-06-29_21-03-42_static-roughness-weighted-ekman-coupling/decision.md`
  found static roughness redistribution effectively neutral, and
  `.logbook/history/2026-06-29_13-02-18_ekman-pressure-work-thermal-coupling/decision.md`
  found pressure-work heating stable but subthreshold.

## Researcher Notes

This is intentionally not a coefficient, roughness, pressure-work, or Ekman-depth
variant. It preserves the accepted stress amplitude and geometry and changes
only the mathematical invariant enforced by the log-pressure pumping increment.
It is also distinct from staged
`.logbook/research/staging/coriolis-scaled-ekman-depth-coupling.md`, which
changes the effective vertical mass receiving the stress impulse; this proposal
keeps that geometry fixed and repairs the surface-pressure mass projection.

## Evaluator Notes

### 2026-06-30T01:48:49Z

Decision: move to `ready`; ranked first for the next Orchestrator selection.

This is the strongest of the two fresh proposals because it makes a narrow,
mechanistic change inside the already accepted `dino_ri2m_ekman_coupled` filter:
only the log-surface-pressure pumping projection changes, while the accepted
stress formula, drag coefficient, vertical taper, equatorial taper, caps, finite
fallback, and modal projection safety checks remain intact. The existing code
already has a capped bisection helper for area-neutral increments, so the
surface-pressure-weighted bisection is implementable with a small helper and
focused tests.

The scientific claim is sound. Under hydrostatic balance, surface pressure is
proportional to the atmospheric mass above the surface, so conserving the
area-weighted mean of `ps` is the relevant dry-mass invariant, not the
area-weighted mean of `log(ps)`. A log-neutral finite increment can still change
mean `ps` through the exponential map. The proposal's scalar-offset solve is
also consistent with the broader numerical-modeling practice of applying global
mass fixers when a transport or projection step has the wrong integral
invariant.

This does not duplicate the staged Coriolis-scaled Ekman-depth proposal. The
depth proposal changes how the accepted stress impulse is vertically distributed
and is therefore another nearby Ekman geometry experiment. This proposal keeps
that geometry and tests a different invariant in the pressure increment. It also
avoids the recently weak Ekman-adjacent classes: it is not static roughness, not
pressure-work thermal coupling, and not output wind veering.

Main risk: the incumbent log-area-neutral projection may be an empirical
compensator, so exact surface-mass neutrality could be stable but subthreshold
or slightly negative. That risk is acceptable because the implementation surface
is small, rollback is clean, and even a negative result would clarify whether
the accepted Ekman gain depends on a pressure zero-mode artifact.

Implementation guardrails for the Orchestrator: use the cached incumbent scores
as authoritative; do not rerun the incumbent; keep the bisection bracket and
nonpositive/nonfinite pressure fallbacks exact; preserve the current pressure
cap before and after modal projection; and add direct synthetic tests that
`sum(weights * ps * exp(delta))` is preserved within tolerance for finite
positive `ps`.
