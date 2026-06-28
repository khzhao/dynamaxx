---
schema_version: 1
slug: pressure-gradient-product-dealiasing
title: Dealias the Explicit Pressure-Gradient Product Only
status: staging
created_at: 2026-06-19T11:47:54Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/filtering.py
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

# Dealias the Explicit Pressure-Gradient Product Only

## Hypothesis

The accepted off-centered semi-implicit solver strongly improved the fast
gravity-wave and mass-field part of the forecast, but the nonlinear explicit
pressure-gradient product `R T' grad(log ps)` is still formed in nodal space and
then transformed back to spectral space. Aliasing in this product can inject
spurious divergent tendencies that the implicit gravity-wave solve must then
damp after the fact. A narrow dealiasing pass on this pressure-gradient product
should reduce mass-field noise while avoiding the broad skill loss and weak
effect size seen in previous full-tendency or full-state diffusion changes.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_pg_dealias`.
Preserve incumbent initialization, DFI, weak Held-Suarez forcing, exact symmetric
Coriolis split, theta tendency, theta mean recentering, fixed SIL3
off-centering, horizontal diffusion floor, near-surface diagnostics, output
variables, and lead schedule.

Add an opt-in pressure-gradient product filter inside
`PrimitiveEquationsSigma.curl_and_div_tendencies`:

- compute the incumbent nodal pressure-gradient product terms
  `rt * grad_log_ps_u` and `rt * grad_log_ps_v`;
- transform only those two product fields to modal space, apply a fixed smooth
  high-wavenumber attenuation that is zero or near-zero on planetary and
  synoptic modes and active only close to truncation, then transform back to
  nodal space;
- combine the filtered pressure-gradient product with the unchanged vertical
  advection and absolute-vorticity flux terms before computing curl and
  divergence tendencies;
- leave scalar advection, kinetic-energy tendency, log-pressure tendency,
  humidity correction terms, tracers, horizontal diffusion, and output
  interpolation unchanged;
- use the same candidate path in DFI and positive-time rollout for operator
  consistency;
- fall back to the incumbent unfiltered product if the filtered product is
  nonfinite or shape-incompatible.

This is a targeted product-space dealiasing candidate, not another broad
hyperdiffusion-strength change, two-thirds full-tendency filter, Leith viscosity,
or output residual.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py` if a reusable modal
    attenuation helper is cleaner than an equation-local helper
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. The forecast input/output contract and fixed evaluation protocols stay
    unchanged.
- Tests to update:
  - Unit-test that low total-wavenumber coefficients of a synthetic product are
    preserved while near-truncation coefficients are attenuated.
  - Verify only the pressure-gradient product path changes when the option is
    enabled; scalar advection and kinetic-energy tendencies remain bitwise or
    tolerance-equivalent to incumbent helpers.
  - Verify finite fallback returns the incumbent product when the candidate
    helper receives nonfinite inputs.
  - Verify the candidate factory preserves every incumbent flag except the new
    pressure-gradient product dealiasing selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` from days 3 to 15 if
    pressure-gradient product aliasing is a remaining source of divergent
    mass-field noise after off-centering.
  - Primary score may improve with less near-surface exposure than broad
    diffusion because 2 m and 10 m diagnostics are not directly altered.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should remain close to the
    incumbent because the accepted surface residual and Richardson diagnostic
    paths are unchanged.
- Possible regressions:
  - The explicit pressure-gradient product also carries real balanced
    baroclinic structure; filtering it too strongly could under-drive synoptic
    development and worsen Z500 phase.
  - If prior broad tendency dealiasing was weak because aliasing is not a
    material error source, this targeted variant may also be clean but neutral.

## Risks

- Numerical stability:
  - Low to moderate. The change damps only a selected explicit product, but it
    changes the vorticity/divergence tendencies that feed the semi-implicit
    solve.
- Compute cost:
  - Low to moderate. It adds two modal/nodal transforms per explicit tendency
    evaluation unless implemented by reusing existing transformed fields.
- Data leakage:
  - None. The filter uses only fixed spectral geometry and the current forecast
    state.
- Physical plausibility:
  - Moderate to high. Dealiasing nonlinear products is standard in spectral
    fluid solvers, and this proposal applies it to the product most directly
    tied to gravity-wave and mass-field errors.
- Rollback complexity:
  - Medium. The equation-class option must be isolated so the incumbent and
    staged diffusion proposals remain untouched.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failures, and
    at least `+0.002` primary-score improvement.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4` only
    after iteration promotion.
  - Support requires clean diagnostics, no guardrail failures, and at least
    `+0.001` validation primary-score improvement.
- Outcome that would falsify the hypothesis:
  - A negative or sub-threshold clean iteration delta would indicate this
    pressure-gradient aliasing path is not a material remaining error source.
  - Early Z500 or MSLP guardrail deterioration would indicate the filter removed
    useful balanced pressure-gradient structure.

## Citations

- Canuto, C., Hussaini, M. Y., Quarteroni, A., and Zang, T. A. 2007. Spectral
  Methods: Evolution to Complex Geometries and Applications to Fluid Dynamics,
  sections on aliasing and spectral filtering.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics, second edition,
  sections on sigma-coordinate primitive-equation pressure-gradient terms.
- Source reference:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`, where
  `curl_and_div_tendencies` forms `rt * grad(log ps)` before modal curl and
  divergence operators.
- Source history: `.logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing/decision.md`
  found broad explicit-tendency dealiasing clean but below threshold, motivating
  a narrower product-specific test.

## Researcher Notes

This is not a duplicate of the active `two-thirds-explicit-tendency-dealiasing`
or `leith-nonlinear-eddy-viscosity` proposals. Those change broad tendency or
state-dependent dissipation behavior. This proposal touches only the explicit
pressure-gradient product inside the vorticity/divergence tendency, leaving
scalar transport, existing horizontal diffusion, and all output diagnostics on
the incumbent path. It also differs from the rejected divergence-selective
gravity-wave damping because it does not damp the divergence state after a step;
it suppresses an aliased source term before it enters the semi-implicit update.

## Evaluator Notes

### 2026-06-19T11:53:51Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

The mechanism is plausible and source inspection confirms a precise hook:
`curl_and_div_tendencies` forms the nodal `rt * grad_log_ps` pressure-gradient
product before transforming the combined vector terms back to modal space. A
product-specific modal attenuation is more targeted than broad tendency
filtering and could test whether remaining mass-field noise comes from this
particular nonlinear source term.

Do not promote it ahead of the DFI theta-recenter candidate. Recent local
evidence is weak for this family: smooth nonlinear tendency dealiasing was clean
but sub-threshold at `+0.0007881219001772966`, the mass-conserving log-pressure
smoother was effectively neutral at `+0.0000014025155478103457`, diffusion
ordering was slightly negative, and the accepted off-centered SIL3 incumbent
already delivered large mass-field gains. This proposal is distinct enough to
keep staged as a later, isolated pressure-gradient experiment, but prior
dealiasing and diffusion history makes it a lower-probability next target.
