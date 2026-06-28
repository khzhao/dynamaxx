---
schema_version: 1
slug: absolute-vorticity-flux-dealiasing
title: Dealias the Absolute-Vorticity Momentum Flux Product
status: ready
created_at: 2026-06-20T04:46:29Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
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

# Dealias the Absolute-Vorticity Momentum Flux Product

## Hypothesis

The incumbent forms the vector-invariant absolute-vorticity flux
`(zeta + f) k x v` in nodal space, then transforms the combined vector back to
modal curl/divergence tendencies. Broad nonlinear tendency dealiasing was too
weak, and pressure-gradient product dealiasing is already staged, but the
absolute-vorticity flux is a different nonlinear source: it directly controls
rotational wind phase and can alias enstrophy into divergent modes. Filtering
only this product near truncation may reduce wind and mass-field noise without
weakening the accepted pressure-gradient or thermodynamic paths.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_av_flux_dealias`.
Preserve the incumbent trajectory options, DFI, weak-HS forcing, Coriolis
Strang split, theta tendency, theta recentering, off-centering, residual
memory, output diagnostics, and fixed protocols.

For this candidate only:

- add an opt-in product filter inside `PrimitiveEquationsSigma.curl_and_div_tendencies`;
- compute the incumbent nodal absolute-vorticity flux components
  `-v * (zeta + f) * sec2_lat` and `u * (zeta + f) * sec2_lat`;
- transform only those two product fields to modal space, apply a fixed smooth
  attenuation active only near the total-wavenumber truncation, then transform
  them back to nodal space;
- leave pressure-gradient products, vertical-advection momentum terms,
  kinetic-energy tendency, scalar advection, humidity terms, diffusion, and
  output packing unchanged;
- use the same selector in DFI and positive-time rollout for equation
  consistency;
- fall back to the incumbent unfiltered flux when filtered fields are nonfinite
  or shape-incompatible.

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
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. Forecast contract, target variables, lead schedule, metrics, and
    protocols remain fixed.
- Tests to update:
  - Unit-test that low total-wavenumber coefficients are unchanged while
    near-truncation coefficients are attenuated.
  - Verify pressure-gradient, scalar-advection, kinetic-energy, and output paths
    are unchanged by the selector.
  - Verify finite fallback returns the incumbent flux.
  - Verify the candidate factory preserves every incumbent option except the
    absolute-vorticity flux dealias selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium leads if aliased vorticity flux is
    contributing to wind phase drift.
  - `geopotential_500` and MSLP if less aliased momentum forcing reduces
    spurious divergent adjustment.
- Expected neutral metrics:
  - `2m_temperature` should remain close to incumbent because thermodynamic
    tendency, weak-HS forcing, and near-surface residuals are unchanged.
- Possible regressions:
  - The vorticity flux carries real synoptic eddy momentum transfer; excessive
    attenuation can under-develop waves and degrade Z500 or wind skill.
  - If broad nonlinear dealiasing was weak because aliasing is not a material
    error source, this narrower version may still be subthreshold.

## Risks

- Numerical stability:
  - Low to moderate. The change damps a nonlinear source term but touches
    vorticity and divergence tendencies every step.
- Compute cost:
  - Low to moderate. It adds two modal/nodal product-filter transforms per
    explicit tendency evaluation.
- Data leakage:
  - None. It uses only current forecast state and fixed spectral geometry.
- Physical plausibility:
  - Moderate to high. Dealiasing nonlinear products is standard in spectral
    fluid solvers, and this proposal confines it to the vector-invariant
    momentum flux.
- Rollback complexity:
  - Low. Remove one equation selector/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_av_flux_dealias`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_av_flux_dealias --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_av_flux_dealias --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show absolute-
    vorticity flux aliasing is not a material remaining error source. Wind or
    Z500 guardrail failures would show the filter removes useful eddy momentum
    structure.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  forms the absolute-vorticity flux product in
  `PrimitiveEquationsSigma.curl_and_div_tendencies`.
- Dynamaxx history:
  `.logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing/decision.md`
  found broad nonlinear tendency dealiasing clean but subthreshold, motivating a
  more product-specific test.
- Dynamaxx research:
  `.logbook/research/staging/pressure-gradient-product-dealiasing.md` targets a
  pressure-gradient product; this proposal targets the separate
  absolute-vorticity momentum flux product.
- Canuto, C., Hussaini, M. Y., Quarteroni, A., and Zang, T. A. 2007. Spectral
  Methods: Evolution to Complex Geometries and Applications to Fluid Dynamics.
  Springer. https://doi.org/10.1007/978-3-540-30728-0
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
  Atmospheric Models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241

## Researcher Notes

This is not a divergence-zero-mode projection and does not remove any modal
state component. It is not passive humidity routing and does not change
residual memory. It is also distinct from staged `pressure-gradient-product-
dealiasing`: the filtered product here is the absolute-vorticity momentum flux,
while pressure-gradient products and scalar thermodynamics remain on the
incumbent path. The proposal should be considered lower priority if the
Evaluator treats prior broad dealiasing evidence as decisive, but it is
mechanically separate from the recent rejected residual and humidity ideas.

## Evaluator Notes

### 2026-06-20T04:52:50Z

Decision: move to `ready`; ranked 1 of 1 ready proposals.

This is the strongest current proposal because it is a narrow, testable
nonlinear-product experiment with a precise source hook. Source inspection
confirms `PrimitiveEquationsSigma.curl_and_div_tendencies` forms the
absolute-vorticity flux in nodal space immediately before the modal curl and
divergence operators. Filtering only that product is distinct from staged
`pressure-gradient-product-dealiasing`, staged two-thirds full-tendency
dealiasing, and the rejected broad smooth tendency filter.

The scientific basis is sound enough for a ready experiment. Spectral-method
literature supports dealiasing nonlinear products, and spectral dynamical-core
notes formulate the vorticity/divergence tendencies from absolute-vorticity,
vertical-advection, and pressure-gradient vector terms. The closest local
history is not decisive against this narrower test: broad nonlinear tendency
dealiasing was stable and slightly positive at `+0.0007881219001772966` but
subthreshold, so a product-specific vorticity-flux test can still teach whether
wind and mass-field errors are coming from a more specific aliased source.

Implementation constraints for the Orchestrator to pass on: keep the filter
smooth and active only near truncation; leave pressure-gradient, scalar
advection, kinetic-energy, diffusion, thermodynamic, residual-memory, and
output paths unchanged; use the same selector in DFI and positive-time rollout;
unit-test that low total wavenumbers are unchanged; and account for the two
extra product transforms per explicit tendency call.
