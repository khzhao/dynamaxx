---
schema_version: 1
slug: pressure-thickness-corrected-mass-dse-hsl
title: Subtract Pressure-Thickness Advection from Mass-DSE HSL
status: ready
created_at: 2026-06-23T21:55:20Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Subtract Pressure-Thickness Advection from Mass-DSE HSL

## Hypothesis

The incumbent `dino_hsl2_mass_dse` improved by transporting
`delta_p * s_prime`, where `delta_p` is sigma-layer pressure thickness and
`s_prime` is the dry-static-energy anomaly. That is a useful conservative
restaging, but dividing the transported mass-weighted tendency directly by the
local `delta_p` mixes two effects: advection of dry static energy and advection
of layer pressure thickness. For a layer-mass scalar, the scalar tendency is
more consistent with `(d(m s) / dt - s d(m) / dt) / m`.

The proposal tests whether subtracting the collocated HSL pressure-thickness
advection term preserves the accepted mass weighting while reducing residual
thermal/mass inconsistency in MSLP and Z500.

## Mechanism

Register a side-by-side model such as `dino_mass_dse_fluxcorr` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- preserve the accepted HSL2 departure, bilinear remap, finite fallback chain,
  unweighted DSE-HSL fallback, vertical theta tendency, adiabatic tendency,
  log-surface-pressure tendency, momentum tendencies, weak-HS forcing, surface
  residuals, ocean bulk flux, output variables, and fixed evaluation protocols;
- compute the incumbent layer pressure thickness `m = delta_p`;
- compute the accepted HSL horizontal tendency of `m * s_prime`;
- compute a matching HSL horizontal tendency of `m` using the same midpoint
  departure and finite diagnostics;
- form the corrected dry-static-energy horizontal tendency as
  `(d(m s_prime)/dt - s_prime * dm/dt) / safe_m`;
- convert only that corrected horizontal dry-static-energy tendency through
  `1 / c_p` before adding the incumbent vertical theta and adiabatic terms;
- fall back exactly to `dino_hsl2_mass_dse` if the pressure-thickness tendency,
  corrected scalar tendency, or converted temperature tendency is nonfinite or
  if any layer thickness is nonpositive.

This is not a flux-form surface-pressure continuity rewrite. The prognostic
mass equation and forecast contract remain unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add one short side-by-side factory and registry key for
    `dino_mass_dse_fluxcorr`.
- API changes:
  - None.
- Tests to update:
  - Verify the default and `dino_hsl2_mass_dse` tendencies are unchanged when
    the option is disabled.
  - Verify zero or constant pressure-thickness advection reduces to the
    accepted mass-DSE tendency.
  - Verify invalid pressure thickness or nonfinite corrected tendencies fall
    back to the incumbent mass-DSE path.
  - Verify model registration and unchanged forecast output variables.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 2-12 if the
    accepted mass-DSE branch is still carrying a pressure-thickness transport
    artifact into thermal thickness.
  - `2m_temperature` at medium leads if lower-column mass-weighted thermal
    advection becomes less biased in high- and low-pressure columns.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because momentum and the 10 m wind diagnostic
    remain on the incumbent path.
- Possible regressions:
  - The accepted uncorrected mass-DSE tendency may be empirically beneficial
    precisely because it couples thermal and pressure-thickness advection.
  - Short-lead MSLP could regress if subtracting `s_prime * dm/dt` weakens a
    useful mass-field compensation.

## Risks

- Numerical stability:
  - Moderate. The HSL trajectory is unchanged, but a new pressure-thickness HSL
    tendency enters every thermal horizontal tendency.
- Compute cost:
  - Low to moderate. One additional scalar HSL remap per layer and local algebra
    are added; grid size, lead count, and output volume are unchanged.
- Data leakage:
  - None. The candidate uses only the forecast state and fixed sigma geometry.
- Physical plausibility:
  - High as a finite-volume-style scalar transport consistency test, but
    incomplete because the actual log-pressure continuity equation is left
    unchanged by design.
- Rollback complexity:
  - Low. Remove one selector, one branch, one factory/export, one registry key,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_mass_dse_fluxcorr`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_mass_dse_fluxcorr --workers 4`
  - Support requires primary delta at least `+0.002` against cached
    `dino_hsl2_mass_dse`, clean diagnostics, and no fixed RMSE guardrail
    failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_mass_dse_fluxcorr --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean neutral or negative iteration delta would show that the accepted
    direct `d(m s_prime)/dt / m` form is the better empirical balance. Any
    early MSLP or Z500 guardrail failure would show the correction disrupts the
    accepted mass/thermal coupling.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  contains the accepted `use_layer_mass_weighted_dse_hsl_transport` branch and
  the shared bounded HSL scalar remap.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted `dino_hsl2_mass_dse` with iteration delta `+0.005725334705943053`
  and validation delta `+0.00546393735603079`.
- Dynamaxx history:
  `.logbook/history/2026-06-18_11-53-08_flux-form-surface-pressure-continuity/decision.md`
  rejected a broader prognostic pressure-continuity rewrite, so this proposal
  keeps log-pressure continuity unchanged.
- Lin, S.-J. and Rood, R. B. 1996. Multidimensional Flux-Form
  Semi-Lagrangian Transport Schemes. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric
  Transport Schemes: Desirable Properties and a Semi-Lagrangian View on
  Finite-Volume Discretizations. In Numerical Techniques for Global Atmospheric
  Models. https://doi.org/10.1007/978-3-642-11640-7_8
- Thuburn, J. 2008. Some Conservation Issues for the Dynamical Cores of NWP and
  Climate Models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is not a duplicate of the accepted layer-mass-weighted DSE-HSL proposal:
that candidate transported `delta_p * s_prime` and divided by `delta_p`
directly. This proposal tests the next conservative-form correction by removing
the pressure-thickness tendency part of that transported product.

It is distinct from staged `mass-flux-theta-transport`, which rewrites theta
transport with mass fluxes, and from rejected `flux-form-surface-pressure-
continuity`, which changed the prognostic mass equation. It also avoids the
recent rejected MSE-HSL path by adding no humidity or latent-energy term. The
main negative evidence is that broader pressure-continuity changes have been
fragile, so the implementation must keep exact incumbent fallback and watch
short-lead MSLP/Z500 guardrails closely.

## Evaluator Notes

### 2026-06-23T21:59:49Z

Decision: move to `ready`; rank 1 of 3 new proposals.

This is the strongest next model-selection candidate. It directly follows the
accepted `dino_hsl2_mass_dse` result by testing whether the incumbent
`d(delta_p * s_prime) / delta_p` thermal transport is carrying a
pressure-thickness advection artifact into hydrostatic thickness. The proposed
product-rule correction is mechanistic, local, and low-overfit: it adds a
matched pressure-thickness HSL tendency and keeps the prognostic log-pressure
equation, output contract, residuals, weak-HS forcing, momentum path, and fixed
evaluation protocols unchanged.

The cost-risk balance is better than the other two proposals. It has a larger
expected signal than a zero-mode-only projection, but avoids the new empirical
static-stability threshold and discontinuous selector in the gate proposal. The
main risk is real: the accepted direct mass-DSE tendency may be beneficial
because it couples thermal and pressure-thickness advection in a way the
current semi-implicit mass/pressure system already expects. That risk is
acceptable for one ready candidate because rollback is localized and the
proposal includes exact incumbent fallback on nonfinite or nonpositive layer
thickness diagnostics.

Recommendation: implement this first as the sole ready proposal, with no
validation or golden run unless the fixed iteration gate promotes it. Watch
short-lead `mean_sea_level_pressure` and `geopotential_500` closely; a clean
negative or subthreshold iteration delta should be treated as evidence that the
accepted direct mass-DSE coupling is the better empirical balance.
