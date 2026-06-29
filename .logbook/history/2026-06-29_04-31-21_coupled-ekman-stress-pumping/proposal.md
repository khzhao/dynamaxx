---
schema_version: 1
slug: coupled-ekman-stress-pumping
title: Coupled Ekman Stress and Pumping Boundary-Layer Closure
status: ready
created_at: 2026-06-29T04:25:11Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Coupled Ekman Stress and Pumping Boundary-Layer Closure

## Hypothesis

The current incumbent has a successful diagnostic 10 m wind treatment and a
successful 2 m temperature diagnostic, but it still lacks a coupled
boundary-layer dynamical closure. Staged ideas already isolate either a surface
stress tendency or an Ekman-pumping log-pressure tendency. In the real boundary
layer, those are linked: surface stress slows and turns low-level flow, creating
ageostrophic convergence or divergence that feeds cyclone pressure tendencies.

A weak paired stress-plus-pumping tendency should be more physically balanced
than a mass-only pressure forcing and less likely than drag-only momentum
damping to shift MSLP in the wrong phase. It targets `mean_sea_level_pressure`
and `10m_u_component_of_wind` through the rollout state, not through another
output diagnostic or residual-memory tweak.

## Mechanism

Register one side-by-side candidate such as `dino_ri2m_ekman_coupled` derived
from `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`. Preserve the incumbent
initialization, mass-DSE HSL, tropical WTG, vertical-DSE ramp, low-mode T2m
memory, RI2m temperature diagnostic, output variables, target variables, lead
schedule, and fixed evaluation protocols.

For this candidate only, compose a positive-time boundary-layer forcing or step
filter with two linked parts:

- diagnose lowest-layer wind, lower-layer pressure, and latitude from the
  candidate forecast state;
- compute a bounded bulk surface stress `tau = rho * C_d * |V| * V`, optionally
  using the existing land-sea fraction path only as a static roughness weight;
- apply a capped momentum tendency over the lowest one or two sigma layers,
  with a vertical taper that conserves global axial angular momentum by
  subtracting the area-weighted zonal acceleration mean;
- derive a matching Ekman-pumping or boundary-layer mass-convergence proxy from
  the same stress field, suppressing it smoothly where `|f|` is small;
- add only a globally mass-neutral `log_surface_pressure` tendency from that
  pumping proxy, after removing the area-weighted mean tendency;
- enforce a fixed ratio cap between the pressure tendency and the applied stress
  so the pressure effect cannot be tuned independently of momentum drag;
- leave temperature, humidity tracers, WTG heating, vertical-DSE increment,
  residual-memory corrections, final wind diagnostics, and MSLP output
  conversion unchanged;
- finite-fallback to the incumbent zero added tendency if any stress, pumping,
  transform, pressure, or mass-neutrality diagnostic is invalid.

The first implementation should use one fixed weak drag coefficient and one
fixed pressure-tendency cap. It should not run coefficient sweeps, change the
incumbent comparison cache, or add any new evaluation diagnostics.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` if placing the
    forcing inside the primitive-equation class is cleaner than an adapter
    step filter
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one candidate factory and registry key for `dino_ri2m_ekman_coupled` or
    the final short alias.
- API changes:
  - None. Forecast inputs, outputs, target variables, metrics, lead days, and
    fixed protocols remain unchanged.
- Tests to update:
  - Verify zero wind, invalid mask, and equatorial taper cases reduce to the
    incumbent added tendency.
  - Verify momentum tendency is capped, lower-layer-confined, and globally
    axial-angular-momentum neutral after mean removal.
  - Verify log-pressure tendency is globally mass-neutral and is tied to the
    same stress field as the momentum tendency.
  - Verify temperature, tracers, WTG selectors, residual-memory selectors, and
    output diagnostics are unchanged directly.
  - Verify finite fallback and registry availability.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 2-15 if missing boundary-layer
    stress-convergence coupling contributes to cyclone amplitude or phase error.
  - `10m_u_component_of_wind` if lower-layer free-slip momentum is still too
    energetic after the accepted diagnostic wind correction.
  - `geopotential_500` may improve indirectly through better pressure and storm
    track evolution.
- Expected neutral metrics:
  - `2m_temperature` should remain near incumbent because no direct thermal
    source or output residual is changed.
- Possible regressions:
  - Drag can weaken real low-level jets or cyclones, while a crude pumping proxy
    can put the pressure tendency in the wrong phase.
  - Coupling two tendencies increases implementation risk relative to a
    single-channel diagnostic proposal.

## Risks

- Numerical stability:
  - Moderate. The proposal touches prognostic momentum and mass every inner
    step. Strict caps, global mean removal, equatorial tapering, and finite
    fallback are mandatory.
- Compute cost:
  - Low to moderate. It adds wind transforms, local stress algebra, and area
    reductions per step, which is realistic for the reported resource envelope.
- Data leakage:
  - None. The closure uses only current forecast state, static geometry or
    land-sea mask, and fixed constants. It must not use future truth,
    validation statistics, new splits, or golden data.
- Physical plausibility:
  - Moderate to high. Surface stress and Ekman pumping are standard
    boundary-layer dynamics, but this is a reduced dry spectral-model closure.
- Rollback complexity:
  - Low to moderate. Remove one forcing/filter path, one factory/export, one
    registry key, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_ekman_coupled`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_coupled --workers 4`.
  - Compare against the cached incumbent artifacts in `.logbook/leaderboard.json`;
    candidate comparisons should not rerun the incumbent unless the cache is
    concretely invalid under `roles/PROTOCOL.md`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no early day-1-through-day-5 or variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_ekman_coupled --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show coupled
    boundary-layer momentum and mass closure is not a material remaining error
    source. Any early MSLP or U10 guardrail failure would show the closure
    perturbs accepted balance too strongly.

## Citations

- Ekman, V. W. 1905. "On the Influence of the Earth's Rotation on
  Ocean-Currents." https://empslocal.ex.ac.uk/people/staff/gv219/classics.d/Ekman05.pdf
- Beljaars, A. C. M. 1995. "The parametrization of surface fluxes in large-scale
  models under free convection." Quarterly Journal of the Royal Meteorological
  Society and ECMWF Technical Memorandum 215. https://doi.org/10.21957/j0j3qfke
- ECMWF OpenIFS physical-process documentation describes surface-layer
  Monin-Obukhov exchange and turbulent vertical transport.
  https://confluence.ecmwf.int/display/OIFS/3.2%2BOpenIFS%3A%2BPhysical%2BProcesses
- Garratt, J. R. 1992. The Atmospheric Boundary Layer. Cambridge University
  Press. https://books.google.com/books/about/The_Atmospheric_Boundary_Layer.html?id=xeEVtBRApAkC
- Dynamaxx research:
  `.logbook/research/staging/ekman-pumping-logp-tendency.md` tests a mass-only
  Ekman-pumping pressure tendency, while
  `.logbook/research/staging/bulk-aerodynamic-surface-stress.md` tests a
  stress-only momentum tendency. This proposal tests the coupled, same-stress
  momentum-plus-mass mechanism.
- Dynamaxx history:
  `.logbook/history/2026-06-28_06-42-52_momentum-only-sl-vertical-advection/decision.md`
  rejected an unstable momentum-only vertical-transport change, motivating a
  capped boundary-layer stress closure rather than another transport rewrite.

## Researcher Notes

This is deliberately not another final wind diagnostic, not a roughness-only
10 m output correction, and not an MSLP output-reduction formula. It is also
not a duplicate of existing Ekman or surface-stress staging because those files
isolate only one side of the boundary-layer coupling. The new mechanism is the
paired stress and pumping constraint: the mass tendency is derived from, capped
by, and finite-fallback tied to the same stress tendency that changes low-level
momentum.

## Evaluator Notes

### 2026-06-29T04:29:49Z

Decision: move to `ready`; ready ranking `1 of 1`.

This is the strongest current next candidate because it turns two staged
single-channel boundary-layer ideas into one constrained physical test. The
staged `ekman-pumping-logp-tendency` was kept out of ready partly because a
mass-only pumping proxy can have the wrong phase, and the staged
`bulk-aerodynamic-surface-stress` was kept out of ready partly because
stress-only drag can spend MSLP/Z500 guardrail margin without a matched mass
response. This proposal directly addresses both evaluator concerns by deriving
the pressure tendency from the same stress field, enforcing global mass and
axial-angular-momentum neutrality, and capping the pressure response relative
to the applied stress.

The literature basis is adequate for a bounded dycore experiment. Ekman-layer
stress, surface turbulent momentum exchange, Monin-Obukhov-style surface-layer
transfer, and boundary-layer vertical transport are standard physical-process
families. The proposal stays within the fixed search contract: side-by-side
candidate, no new outputs, no target-variable or lead changes, no golden run,
no coefficient sweep, and reuse of the cached incumbent metrics unless the
protocol cache rules find a concrete invalidation.

Implementation should be conservative so the Orchestrator can select exactly
one candidate: register one candidate such as `dino_ri2m_ekman_coupled`, use
one predeclared weak drag coefficient and one pressure-tendency cap, apply only
lowest-layer or lowest-two-layer momentum forcing, remove the global zonal
acceleration and global log-pressure tendency means, taper smoothly near the
equator, leave T2m memory/RI2m diagnostics/WTG/vertical-DSE paths unchanged,
and require finite fallback to the incumbent added tendency. Score with the
fixed `pytest`, `fast`, `iteration`, and conditional `validation` gates only.

This should be preferred over promoting either staged single-channel Ekman or
bulk-stress file. Expected upside is primarily MSLP and U10, with possible Z500
secondary benefit and near-neutral T2m. Reject without revision if the
iteration delta is near zero or if early MSLP/U10 guardrails show that the
coupled closure is still out of phase.
