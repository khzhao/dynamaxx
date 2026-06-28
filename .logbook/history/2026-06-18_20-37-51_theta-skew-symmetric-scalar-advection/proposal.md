---
schema_version: 1
slug: theta-skew-symmetric-scalar-advection
title: Use Skew-Symmetric Horizontal Scalar Advection with Theta Transport
status: ready
created_at: 2026-06-18T20:33:04Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Use Skew-Symmetric Horizontal Scalar Advection with Theta Transport

## Hypothesis

The accepted theta incumbent transports a potential-temperature anomaly through
the existing horizontal scalar-advection identity,
`scalar * divergence - div(u * scalar)`. In the continuous equations this is
equivalent to direct advective-gradient transport, but the two forms are not
identical after spherical-harmonic truncation, nodal multiplication, and modal
clipping. A skew-symmetric average of the conservative-product and
advective-gradient forms may reduce nonlinear scalar variance drift in the
theta field, improving thermal thickness and mass-field evolution without
changing surface residuals, 10 m wind diagnostics, Coriolis splitting,
initialization, vertical advection, diffusion, or the fixed evaluation
contract.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_skew_scalar_adv`.
Preserve every incumbent option except an opt-in horizontal scalar-advection
form inside the sigma primitive equation.

Add a small equation selector:

- keep the incumbent product-rule scalar tendency as the default;
- compute the direct advective-gradient form by transforming the scalar to
  modal space, taking horizontal gradients with existing spherical-harmonic
  operators, multiplying by the already diagnosed horizontal wind, and
  transforming the nodal tendency back to modal space;
- return a fixed 0.5/0.5 skew-symmetric average of the product-rule and
  direct-gradient tendencies for temperature/theta and passive tracers;
- leave vorticity, divergence, kinetic energy, pressure-gradient force,
  log-surface-pressure tendency, vertical advection, implicit terms, weak-HS
  forcing, diffusion filters, Coriolis split, DFI span, output variables, and
  residual correction unchanged;
- use the same scalar-advection form in DFI and positive-time rollout.

This is a nonlinear scalar-transport discretization test. It is not a new modal
filter, not a pressure remap, not a wind residual, and not a change to the
accepted theta variable itself.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, and metrics
    remain fixed.
- Tests to update:
  - Unit-test that the incumbent default uses the existing product-rule scalar
    advection path.
  - Unit-test that the skew option returns the incumbent tendency for a
    spatially constant scalar field.
  - Unit-test that direct-gradient and averaged branches have finite values,
    matching shapes, and matching PyTree structure for synthetic modal states.
  - Verify vorticity, divergence, pressure, implicit, weak-HS, DFI, diffusion,
    Coriolis, residual, and Richardson diagnostic options are unchanged by the
    candidate factory.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium leads if theta transport aliasing contributes to
    thermal drift after the accepted residual decays.
  - `geopotential_500` and `mean_sea_level_pressure` if cleaner scalar
    transport improves hydrostatic thickness and balanced pressure evolution.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should stay close to the incumbent because
    prognostic momentum, Coriolis rotation, and the Richardson 10 m diagnostic
    are unchanged.
- Possible regressions:
  - The product-rule form may already compensate other truncation errors.
  - Averaging discrete forms may behave like mild smoothing and degrade sharp
    baroclinic gradients, indirectly moving Z500 or wind phase.

## Risks

- Numerical stability:
  - Low to moderate. Skew-symmetric forms are commonly used for nonlinear
    stability, but this changes scalar tendencies during both DFI and rollout.
- Compute cost:
  - Moderate. The direct-gradient branch adds transforms for temperature/theta
    and tracers, but the reported machine resources and `--workers 4` budget
    are adequate for one side-by-side candidate.
- Data leakage:
  - None. The mechanism uses only forecast state variables and fixed grid
    operators.
- Physical plausibility:
  - High as a structure-preserving scalar-transport discretization test; it is
    not learned and does not tune validation artifacts.
- Rollback complexity:
  - Low to moderate. Remove one equation selector, one factory/export, one
    registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_skew_scalar_adv`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_skew_scalar_adv --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_skew_scalar_adv --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show scalar-form
    aliasing is not a material remaining error source. Any early MSLP, Z500, or
    10 m wind guardrail failure would show the scalar-form change disrupts
    accepted balance.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
    implements `horizontal_scalar_advection` as the current product-rule path
    and routes the accepted theta tendency through it.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md`
    accepted theta-form thermal tendency and identified remaining pressure and
    geopotential side effects worth targeting.
  - Dynamaxx history:
    `.logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing/decision.md`
    found a clean but subthreshold positive signal from nonlinear tendency
    cleanup; this proposal changes the scalar form instead of adding a filter.
  - Kopriva, D. A. and Gassner, G. J. 2014. An energy stable discontinuous
    Galerkin spectral element discretization for variable coefficient advection
    problems. SIAM Journal on Scientific Computing.
    https://doi.org/10.1137/130928650
  - Morinishi, Y. 2010. Skew-symmetric form of convective terms and fully
    conservative finite difference schemes for variable density low-Mach number
    flows. Journal of Computational Physics.
    https://ui.adsabs.harvard.edu/abs/2010JCoPh.229..276M/abstract
  - Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP
    and climate models. Journal of Computational Physics.
    https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is not a near-duplicate of the accepted Richardson 10 m wind diagnostic:
it does not touch output wind packing, residual decay, or surface-layer
stability scaling. It is not a duplicate of the accepted theta tendency because
the transported thermodynamic variable remains potential temperature; only the
horizontal scalar-advection identity changes.

It is also distinct from active staged momentum-skew and two-thirds-dealiasing
ideas. Momentum-skew changes vorticity/divergence nonlinearities; this proposal
changes only scalar transport. Dealiasing proposals add modal masks or filters;
this proposal changes the resolved product identity and leaves modal support
unchanged. A related older-target staged scalar-skew note exists, but this file
is a fresh current-incumbent artifact with candidate naming and risk framing
updated for the accepted theta/Richardson/stability-aware model.

## Evaluator Notes

### 2026-06-18T20:36:37Z

Decision: move to `ready`; ranked 1 of 3 new proposals and recommended as the
next implementation target.

This is the clearest current-incumbent follow-up to the accepted
potential-temperature thermodynamic tendency. The accepted theta candidate
improved iteration by `+0.015447942083573918` and validation by
`+0.019234576988685914`, with the main remaining caveat being small day-1
`mean_sea_level_pressure` and geopotential sensitivity. A scalar-only
skew-symmetric horizontal advection option targets the transport form feeding
that thermal/thickness balance without changing wind diagnostics, residual
correction, Coriolis splitting, DFI span, diffusion coefficients, vertical
advection, output variables, metrics, or forecast contract.

The proposal is not a duplicate of the accepted theta tendency because the
thermodynamic variable remains unchanged and only the horizontal scalar
advection identity changes. It is also not a duplicate of the staged
momentum-skew or two-thirds-dealiasing ideas: this candidate leaves momentum
nonlinearities and modal support unchanged. A related older staged scalar-skew
proposal exists for the pre-Richardson/pre-theta incumbent; this current file
is the implementable artifact to use if selected, and the old staged file
should be treated as superseded context rather than a separate experiment.

Risks are moderate but bounded. Prior nonlinear tendency cleanup produced a
clean but subthreshold positive signal, so expected effect size may be small.
The implementation also must handle spherical metric factors carefully when
forming the direct-gradient branch. Even so, among this batch it has the best
mechanistic match to the current incumbent and avoids the stronger negative
history attached to permanent upwind vertical transport and the pressure-risk
profile of positive diffusion heating. Keep ready small by approving only this
proposal.
