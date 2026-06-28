---
schema_version: 1
slug: skew-symmetric-horizontal-scalar-advection
title: Use Skew-Symmetric Horizontal Scalar Advection
status: staging
created_at: 2026-06-18T08:47:58Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
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

# Use Skew-Symmetric Horizontal Scalar Advection

## Hypothesis

The Strang incumbent still advects temperature variation and passive tracers
with one algebraic form of horizontal scalar advection:
`scalar * divergence - div(u * scalar)`. In the continuous equations this is
equivalent to `-u . grad(scalar)`, but the two forms are not exactly equivalent
after spherical harmonic truncation, nodal products, and modal clipping.

A skew-symmetric average of the conservative-product identity and the direct
advective-gradient identity should reduce nonlinear scalar variance drift and
aliasing-like truncation error without changing the accepted Strang Coriolis
split, DFI, weak Held-Suarez forcing, hydrostatic layer initialization,
near-surface residual correction, vertical advection, diffusion strength, time
step, or forecast contract.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_skew_scalar_adv`.
Preserve every incumbent option except an opt-in horizontal scalar-advection
form inside the primitive-equation object.

Add a small equation option that changes only `horizontal_scalar_advection` for
temperature variation and passive tracers:

- compute the incumbent product-rule tendency exactly as today;
- compute a direct-gradient tendency by transforming the scalar to modal space,
  taking the spherical horizontal gradient with the existing grid operators,
  multiplying by the already diagnosed `cos_lat_u` wind components in nodal
  space, and transforming the resulting nodal tendency back to modal space;
- return the arithmetic mean of the incumbent product-rule form and the direct
  advective-gradient form;
- leave vorticity, divergence, kinetic-energy, Coriolis, pressure-gradient,
  vertical-advection, implicit, and weak-HS tendencies unchanged;
- use the same scalar-advection form in DFI and positive-time rollout because
  this is a model-equation change, not a DFI-only consistency experiment.

This is not a new damping curve. It changes the discrete product identity used
for resolved scalar advection and does not add a modal filter after the step.

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
  - None. `DycoreModel.forecast`, emitted variables, lead times, and fixed
    protocols remain unchanged.
- Tests to update:
  - Unit-test that the skew option reduces to the incumbent tendency for a
    spatially constant scalar field.
  - Unit-test that the direct-gradient branch has the same shape, tree
    structure, and finite values as the incumbent branch for synthetic modal
    states.
  - Verify vorticity, divergence, implicit terms, weak-HS forcing, filters, DFI
    span, and Strang Coriolis flags are unchanged by the candidate factory.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if scalar
    truncation error in temperature transport is feeding hydrostatic thickness
    and mass-field drift.
  - `10m_u_component_of_wind` may improve indirectly if smoother thermal
    advection reduces balanced pressure-gradient phase error.
- Expected neutral metrics:
  - Early `2m_temperature` should remain close to incumbent because the
    accepted near-surface residual correction and weak-HS rates are unchanged.
- Possible regressions:
  - The incumbent product-rule form may already be empirically compensating
    other truncation errors.
  - Averaging the two discrete forms can weaken sharp scalar gradients and
    behave like mild implicit smoothing even without an explicit filter.

## Risks

- Numerical stability:
  - Low to moderate. Skew-symmetric forms are commonly used for nonlinear
    stability, but this changes every scalar tendency during DFI and rollout.
- Compute cost:
  - Moderate. The direct-gradient branch adds transforms and products for
    temperature and tracers, but the reported 48 CPU, 174 GiB RAM, and
    `--workers 4` evaluation budget should be adequate for one side-by-side
    candidate.
- Data leakage:
  - None. The change uses only forecast state, fixed grid operators, and
    physical constants.
- Physical plausibility:
  - High as a structure-preserving discretization test. It is not a learned
    correction and not a tuned dissipation coefficient.
- Rollback complexity:
  - Low. Remove one primitive-equation option, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_skew_scalar_adv`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_skew_scalar_adv --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the Strang incumbent, clean diagnostics, no early day 1-5 RMSE guardrail
    failure, and no variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_skew_scalar_adv --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that scalar
    product-form error is not a material remaining source of skill loss. Any
    early Z500, MSLP, or 10 m wind guardrail failure would show that the skew
    form disrupts the accepted balance more than it helps.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  currently implements `horizontal_scalar_advection` as
  `scalar * divergence - div_sec_lat(u * scalar, v * scalar, grid)`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds the
  accepted Strang incumbent and composes DFI, weak-HS forcing, filters, and
  exact Coriolis splitting around the primitive equation.
- History: `.logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing/decision.md`
  rejected smooth tendency filtering as clean but sub-threshold with iteration
  delta `+0.0007881219001772966`, so this proposal tests a structural product
  form rather than another filter.
- Active staging: `.logbook/research/staging/two-thirds-explicit-tendency-dealiasing.md`
  proposes a sharp modal cutoff. This proposal does not zero high modes and is
  therefore a different anti-aliasing mechanism.
- Arakawa, A. 1966. Computational Design for Long-Term Numerical Integration of
  the Equations of Fluid Motion: Two-Dimensional Incompressible Flow. Part I.
  Journal of Computational Physics. https://doi.org/10.1016/0021-9991(66)90015-5
- Morinishi, Y., Lund, T. S., Vasilyev, O. V., and Moin, P. 1998. Fully
  Conservative Higher Order Finite Difference Schemes for Incompressible Flow.
  Journal of Computational Physics. https://doi.org/10.1006/jcph.1998.5962
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of staged two-thirds tendency dealiasing, symmetric
diffusion placement, RK4, or upwind vertical advection. It keeps the same
time-stepper, diffusion, vertical advection, and modal support, and changes only
the discrete horizontal scalar product identity.

The recent DFI-Coriolis and sigma-native hydrostatic rejections are used as
negative evidence: this proposal avoids DFI-only operator consistency and does
not alter hydrostatic initialization. The closest negative evidence is the
sub-threshold smooth tendency filter, which suggests this family may be stable
but small; the skew form is proposed because it is a different, conservation-
motivated mechanism rather than a stronger damping parameter.

## Evaluator Notes

### 2026-06-18T08:53:53Z

Decision: move to `staging`; rank as the strongest anti-aliasing fallback, not
as ready.

The proposal is distinct from the staged two-thirds cutoff and from the rejected
smooth exponential tendency filter. Source inspection confirms
`horizontal_scalar_advection` is a localized primitive-equation hook for
temperature variation and tracers, so a side-by-side scalar-advection form is
implementable without changing vorticity, divergence, Coriolis, DFI, forcing,
or output packing. The Arakawa and skew-symmetric discretization literature
supports the broad conservation/stability motivation.

The limiting evidence is effect size and implementation subtlety. The closest
scored anti-aliasing experiment was clean and slightly positive, but only
`+0.0007881219001772966`, below promotion. A skew form is a more structural
test than another filter, but correctly forming the direct-gradient branch on
the spherical grid with the existing `cos_lat_u` and metric factors is more
error-prone than the proposal wording suggests. Keep it staged ahead of the
sharp two-thirds cutoff only if a later anti-aliasing experiment is desired;
do not spend the next iteration here while a lower-surface wind-residual
candidate is available.

### 2026-06-18T10:25:42Z

Decision: keep in `staging`; current staged rank 4.

The rejection of the surface-wind residual removes the old reason to rank this
below that ready candidate, but it remains a later fallback. The mechanism is
stronger than another explicit modal filter because it tests a discrete
product-form identity for scalar advection, and it could teach something useful
about scalar transport even if the score is small.

Do not promote it now. The closest scored anti-aliasing experiment was clean
but only `+0.0007881219001772966`, and implementing the direct-gradient branch
with the existing spherical metric factors is subtler than a simple adapter
flag. Keep it ahead of the sharp two-thirds cutoff because it is less likely to
act as extra diffusion, but behind the lower-surface initialization,
geopotential diagnostic, diffusion-ordering, and omega-spinup ideas.

### 2026-06-18T11:49:28Z

Decision: keep in `staging`, staged fallback rank 4.

The new momentum-skew proposal is broader and riskier than this scalar-only
product-form test, so this remains the highest-ranked anti-aliasing family
candidate. It stays behind the hypsometric, omega-spinup, and diffusion-heating
fallbacks because the only direct scored anti-aliasing evidence is still a
clean but subthreshold `+0.0007881219001772966` iteration delta.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 4.

No new evidence makes anti-aliasing the top mechanism. Keep this as the best
anti-aliasing candidate because it changes a scalar product form rather than
adding a sharp modal cutoff or broad momentum rewrite. It remains behind the
hypsometric, omega, and diffusion-heating fallbacks because the closest scored
anti-aliasing experiment was clean but subthreshold.

### 2026-06-18T17:21:29Z

Decision: keep in `staging`, still the best anti-aliasing fallback but below
the ready near-surface diagnostic and the leading transient/energy-budget
staged ideas.

The prior smooth tendency-filter experiment was clean and slightly positive but
only `+0.0007881219001772966`, so this family remains plausible but low
expected effect size. This proposal is preferable to a sharp two-thirds cutoff
because it tests a conservation-motivated product form rather than removing
near-truncation tendencies, but it is not as compelling as the bounded
output-only Richardson wind diagnostic for the next implementation.
