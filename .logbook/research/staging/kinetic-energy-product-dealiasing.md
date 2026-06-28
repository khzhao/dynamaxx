---
schema_version: 1
slug: kinetic-energy-product-dealiasing
title: Dealias Only the Kinetic-Energy Product in the Divergence Tendency
status: staging
created_at: 2026-06-21T12:19:53Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Dealias Only the Kinetic-Energy Product in the Divergence Tendency

## Hypothesis

The incumbent computes the nonlinear Bernoulli term in
`kinetic_energy_tendency` from nodal products of the resolved horizontal wind,
then transforms kinetic energy back to modal space before applying the
Laplacian. Pseudo-spectral quadratic products can alias unresolved variance
back into retained modes. Prior broad tendency dealiasing was stable but too
weak, and pressure-gradient product dealiasing is already staged; the kinetic
energy product is a narrower remaining quadratic source that directly enters
only the divergence tendency.

Filtering the modal kinetic-energy product before the Laplacian should reduce
aliased divergent acceleration without applying a post-step divergence cleanup,
without changing pressure-gradient products, and without changing the accepted
off-centered semi-implicit gravity-wave treatment.

## Mechanism

Register one side-by-side candidate with a suffix such as `_ke_product_dealias`.
Preserve the incumbent DFI, weak-HS forcing, analysis-HS equilibrium, theta
tendency, theta recentering, off-centering, residual memory, and output
diagnostics.

For this candidate only:

- add an opt-in selector to `PrimitiveEquationsBase` or
  `PrimitiveEquationsSigma` that affects only `kinetic_energy_tendency`;
- compute nodal kinetic energy exactly as the incumbent does from
  `aux_state.cos_lat_u`;
- transform kinetic energy to modal space and apply a fixed two-thirds or
  smooth cosine mask to the kinetic-energy scalar product before the Laplacian;
- keep the modal Laplacian, vorticity flux, pressure-gradient product,
  horizontal scalar advection, vertical advection, implicit terms, DFI filters,
  and horizontal diffusion unchanged;
- clip the final explicit tendency through the existing coordinate-system clip
  path as today;
- fall back to the incumbent unmasked product if the masked kinetic energy is
  nonfinite.

This is not a one-time divergence filter and not high-wavenumber divergence
cleanup. It changes a specific quadratic product before it creates a divergence
tendency.

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
  - Add one side-by-side candidate model ending in `_ke_product_dealias`.
- API changes:
  - None. Forecast inputs, outputs, lead times, and fixed scoring protocols are
    unchanged.
- Tests to update:
  - Unit-test the kinetic-energy mask shape on the Dinosaur modal grid.
  - Verify low modes pass unchanged and masked high modes are attenuated.
  - Verify only `divergence` tendency changes for a synthetic state; vorticity,
    temperature, log pressure, and tracers keep incumbent tendencies.
  - Verify nonfinite masked diagnostics fall back to incumbent behavior.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if aliased
    Bernoulli forcing is feeding divergent mass/thickness noise.
  - `10m_u_component_of_wind` may improve modestly if lower-level wind products
    currently alias into divergent adjustment.
- Expected neutral metrics:
  - `2m_temperature` should remain near incumbent because thermal tendency,
    residual correction, and weak-HS forcing are unchanged.
- Possible regressions:
  - The kinetic-energy product may already be sufficiently controlled by the
    accepted off-centering and horizontal diffusion. Removing product variance
    can also weaken physically meaningful nonlinear energy transfer.

## Risks

- Numerical stability:
  - Low to moderate. The filter is stabilizing, but it modifies a core
    nonlinear momentum term each step.
- Compute cost:
  - Low. It adds one modal mask application to an existing transform path.
- Data leakage:
  - None. It uses only the current forecast state.
- Physical plausibility:
  - Good. Dealiasing quadratic products is standard in pseudo-spectral fluid
    solvers; the narrow product scope keeps the mechanism interpretable.
- Rollback complexity:
  - Low. Remove one selector, one helper/mask, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run fixed `iteration` against the cached incumbent using the Orchestrator's
    worker policy.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failure.
- Validation gate:
  - Run fixed `validation` only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with clean
    diagnostics and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that kinetic-energy
    product aliasing is not a material remaining error. Any early wind, MSLP, or
    Z500 guardrail failure would show the mask removes useful nonlinear
    dynamics.

## Citations

- Orszag, S. A. 1971. Numerical simulation of incompressible flows within simple
  boundaries: accuracy. Journal of Fluid Mechanics, 49, 75-112. Discusses
  pseudo-spectral accuracy and aliasing control.
- Canuto, C., Hussaini, M. Y., Quarteroni, A., and Zang, T. A. 2007. Spectral
  Methods: Evolution to Complex Geometries and Applications to Fluid Dynamics.
  Springer. Covers spectral product aliasing and filtering.
- Code reference: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements `kinetic_energy_tendency` as a nodal quadratic product feeding the
  modal divergence tendency.

## Researcher Notes

This differs from rejected `nonlinear-tendency-exponential-dealiasing`, which
attenuated a broader set of explicit tendencies, and from staged
`pressure-gradient-product-dealiasing`, which targets `RT' grad(log ps)`.
It also avoids the latest rejected `first-step-divergence-balance-filter`
family: no state divergence is filtered after initialization or after a step.

## Evaluator Notes

### 2026-06-21T12:28:02Z

Decision: move to `staging`; plausible but not the next experiment.

The proposal is scientifically defensible: kinetic energy is a quadratic
pseudo-spectral product feeding the divergence tendency, and product dealiasing
is a standard numerical-control mechanism. It is also narrower than broad
tendency filtering and avoids the latest rejected first-step divergence cleanup
because it acts at a source product rather than filtering state divergence.

Do not promote it now. The anti-aliasing family has produced clean but
subthreshold evidence: smooth nonlinear tendency dealiasing was only
`+0.0007881219001772966`, absolute-vorticity flux dealiasing was only
`+0.00017069712459116815`, and the first-step divergence balance filter was
slightly negative at `-0.000013124438319467302` with clean guardrails. This
proposal also overlaps active staged ideas, especially
`pressure-gradient-product-dealiasing`, `two-thirds-explicit-tendency-dealiasing`,
and `kinetic-energy-skew-momentum-advection`. Preserve it as a narrower
Bernoulli-term backup, but choose only one product-dealiasing candidate at a
time and keep the mask fixed before any score run.
