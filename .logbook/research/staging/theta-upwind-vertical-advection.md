---
schema_version: 1
slug: theta-upwind-vertical-advection
title: Use Upwind Vertical Advection with the Theta Incumbent
status: staging
created_at: 2026-06-18T20:33:04Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
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

# Use Upwind Vertical Advection with the Theta Incumbent

## Hypothesis

The current incumbent improved thermodynamic evolution by transporting dry
potential temperature, but it still uses centered sigma-coordinate vertical
advection. Centered vertical transport can be dispersive when vertical motion
and static stability are noisy after pressure-to-sigma projection. Using the
existing sign-aware upwind vertical-advection operator may reduce vertical
ringing in potential-temperature, wind, and tracer transport, improving
`2m_temperature`, `geopotential_500`, and `mean_sea_level_pressure` without
changing the accepted surface residuals, Richardson 10 m wind diagnostic,
Coriolis split, initialization, diffusion strength, or forecast contract.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_upwind_vadv`.
Preserve every incumbent option except the vertical-advection callable passed
to the sigma primitive equation.

Add a small adapter selector for vertical advection:

- keep `sigma_coordinates.centered_vertical_advection` as the default incumbent
  path;
- pass `sigma_coordinates.upwind_vertical_advection` into
  `PrimitiveEquations` and `PrimitiveEquationsSigma` for the candidate;
- use the same upwind operator inside DFI and positive-time rollout, so this is
  a model-equation discretization test rather than a DFI-only merge variant;
- preserve the accepted potential-temperature tendency formulation, weak
  Held-Suarez forcing, exact symmetric Coriolis split, Richardson 10 m wind
  diagnostic, stability-aware near-surface residual correction, horizontal
  diffusion, output variables, lead selection, and deterministic gates;
- do not change the vertical coordinate, inner step, diffusion coefficient,
  pressure interpolation, output packing, or evaluation metrics.

This proposal tests vertical transport monotonicity on the already accepted
theta-form incumbent. It does not suppress vertical advection and does not
introduce semi-Lagrangian remapping or a new forecast contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, lead times,
    and fixed evaluation protocols remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent option except the
    vertical-advection scheme selector and model name.
  - Unit-test that `_primitive_equation` receives the requested vertical
    advection callable for both dry and humidity-carrying equation paths.
  - Verify the incumbent default remains centered vertical advection.
  - Verify a finite non-JIT smoke forecast with the candidate returns the same
    variables and shapes as the incumbent.
  - Add registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` from days 3 to 15 if lower-column theta ringing contributes
    to residual thermal drift after the accepted residual begins to decay.
  - `geopotential_500` and `mean_sea_level_pressure` if cleaner vertical thermal
    transport improves hydrostatic thickness and pressure-gradient balance.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain near the incumbent because wind
    initialization, Coriolis splitting, and the Richardson 10 m wind diagnostic
    are unchanged.
  - Lead-zero output should remain unchanged apart from existing residual
    correction behavior.
- Possible regressions:
  - First-order upwinding may be too diffusive, weakening baroclinic structure
    and degrading Z500 or wind phase.
  - The accepted centered scheme may already be empirically matched to the
    semi-implicit sigma-coordinate split, producing a clean but negative or
    subthreshold result.

## Risks

- Numerical stability:
  - Moderate. Upwinding is usually stabilizing for transport, but it changes all
    vertically advected state and tracer tendencies during DFI and rollout.
- Compute cost:
  - Low. The operator already exists, and the candidate does not change grid
    size, lead count, inner step count, output volume, or worker count.
- Data leakage:
  - None. The scheme uses only the forecast state and fixed grid geometry.
- Physical plausibility:
  - Moderate. Upwind transport is a standard monotone advection discretization,
    but its numerical diffusion can be excessive for a spectral primitive
    equation core.
- Rollback complexity:
  - Low. Remove one adapter option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_upwind_vadv`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_upwind_vadv --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_upwind_vadv --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that centered
    vertical advection is not a material remaining error source for the theta
    incumbent. Any early Z500, MSLP, or 10 m wind guardrail failure would show
    upwind diffusion disrupts accepted balance more than it helps.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py`
    already provides both centered and upwind vertical-advection operators.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
    builds the accepted theta incumbent through `_primitive_equation` without a
    vertical-advection selector.
  - History: `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md`
    accepted theta-form thermodynamic tendency, with small early MSLP
    sensitivity that motivates careful vertical-transport follow-up.
  - History: `.logbook/history/2026-06-16_20-56-11_vertical-advection-suppression/decision.md`
    rejected removing vertical advection; this proposal preserves vertical
    transport and changes only the discrete operator.
  - LeVeque, R. J. 2002. `Finite Volume Methods for Hyperbolic Problems`.
    Cambridge University Press. Cambridge Core notes first-order upwind methods
    for advection in its finite-volume introduction:
    https://www.cambridge.org/core/books/finite-volume-methods-for-hyperbolic-problems/finite-volume-methods/CB7B0A27A6D37AE3B906D4AE7C60A87E
  - ECMWF IFS Documentation CY48R1, Part III: Dynamics and Numerical
    Procedures, documents hydrostatic primitive-equation dynamics and numerical
    procedure context for vertical transport and semi-implicit schemes:
    https://www.ecmwf.int/sites/default/files/elibrary/2023/81369-ifs-documentation-cy48r1-part-iii-dynamics-and-numerical-procedures.pdf

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is not a near-duplicate of the accepted Richardson 10 m wind diagnostic:
that candidate changed an output-only surface wind diagnostic, while this
changes prognostic vertical transport for state variables and leaves 10 m wind
packing unchanged.

This is not a duplicate of the accepted potential-temperature thermodynamic
tendency: the incumbent theta-form tendency is preserved exactly, and this
proposal only changes the vertical advection operator used to transport that
state. It is also not a duplicate of the older staged
`upwind-vertical-advection-rollout` note because this file targets the current
theta/Richardson/stability-aware incumbent and explicitly incorporates the
accepted theta history and its MSLP side effect. The older staged file should
remain in place; this proposal is a fresh current-incumbent artifact.

## Evaluator Notes

### 2026-06-18T20:36:37Z

Decision: move to `staging`; ranked 3 of 3 new proposals.

This is implementable and not the same as the rejected vertical-advection
suppression experiment because it preserves explicit vertical transport and
uses an existing sign-aware operator. The current-incumbent rewrite is useful
because it carries forward the accepted Richardson 10 m wind diagnostic,
stability-aware residual correction, and theta thermodynamic tendency instead
of targeting the older Strang-only model.

Do not promote it now. The nearest direct history remains severe:
`.logbook/history/2026-06-16_20-56-11_vertical-advection-suppression` failed
the fast gate with nonfinite metrics once vertical advection was removed. This
proposal is safer than removal, but first-order upwinding would still alter all
vertically advected prognostic and tracer tendencies during both DFI and
rollout. The likely failure mode is excessive numerical diffusion in
baroclinic thermal and wind structure, which could erase the gains from the
accepted theta tendency.

A related older staged proposal,
`.logbook/research/staging/upwind-vertical-advection-rollout.md`, already
captures the same mechanism for an older incumbent and was repeatedly kept as
a low-priority fallback. Treat this current file as the up-to-date version if
the Orchestrator later wants to test upwind vertical advection, but do not run
both as separate ideas.
