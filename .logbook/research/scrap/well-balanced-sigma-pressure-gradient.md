---
schema_version: 1
slug: well-balanced-sigma-pressure-gradient
title: Add a Well-Balanced Sigma Pressure-Gradient Split
status: scrap
created_at: 2026-06-20T20:51:54Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a Well-Balanced Sigma Pressure-Gradient Split

## Hypothesis

The incumbent uses pure sigma coordinates with zero orography, but horizontal
surface-pressure gradients still enter the explicit pressure-gradient product
`R T' grad(log ps)`. In sigma coordinates, pressure-gradient force accuracy
depends on cancellation between reference-state and perturbation terms. Prior
history has already staged high-wavenumber pressure-product dealiasing and
Simmons-Burridge vertical weights; a different error source is low-order
imbalance in the split between the implicit reference-temperature pressure
gradient and the explicit perturbation product.

A well-balanced split that removes each layer's area-mean temperature anomaly
from the explicit `T' grad(log ps)` product and adds it to the linear reference
pressure-gradient coefficient for that step should reduce spurious divergent
mass tendencies without adding damping, changing vertical quadrature, or
altering output diagnostics.

## Mechanism

Register a side-by-side candidate with a suffix such as `_wb_pg_split`.
Preserve incumbent initialization, DFI, weak-HS analysis equilibrium, Coriolis
Strang split, theta tendency, theta recentering, off-centered SIL3, horizontal
diffusion, residual memory, output variables, and fixed protocols.

For this candidate only, inside the sigma primitive-equation pressure-gradient
calculation:

- compute the area-weighted layer mean of nodal `temperature_variation` using
  the existing horizontal quadrature weights;
- define `T'_eddy = T' - mean(T')` for the explicit nodal product with
  `grad(log ps)`;
- add the removed layer-mean anomaly to the reference-temperature coefficient
  used by the linear pressure-gradient and temperature-divergence coupling for
  the current tendency evaluation;
- keep the vertical operator and implicit inverse otherwise identical to the
  incumbent; this is not a Simmons-Burridge weight change;
- apply the same split in DFI and positive-time rollout for operator
  consistency;
- if the layer means or corrected product are nonfinite, fall back to the
  incumbent pressure-gradient product for that evaluation.

The implementation should be a fixed formulation, not a sweep over how much of
the layer mean to move. The full layer mean is moved because the objective is a
well-balanced decomposition, not empirical damping strength.

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
  - Add one side-by-side candidate factory and registry entry only.
- API changes:
  - None. Forecast input/output names, shapes, leads, target variables, and
    metrics remain unchanged.
- Tests to update:
  - Unit-test area-weighted layer-mean removal on synthetic nodal temperature
    fields.
  - Verify horizontally uniform temperature anomalies do not enter the explicit
    pressure-gradient product for the candidate.
  - Verify eddy temperature anomalies still produce explicit pressure-gradient
    tendencies.
  - Verify nonfinite layer means fall back to the incumbent product.
  - Add factory, registry, and finite non-JIT smoke forecast tests.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium leads if
    low-order pressure-gradient split imbalance is feeding divergent mass
    error.
  - `10m_u_component_of_wind` may improve indirectly if reduced mass noise
    improves balanced pressure-gradient wind evolution.
- Expected neutral metrics:
  - `2m_temperature` should remain close to incumbent because weak-HS forcing
    and surface residual correction are unchanged.
  - Lead-zero outputs should remain unchanged because initialization and output
    conversion are not modified.
- Possible regressions:
  - Moving layer-mean temperature anomaly into the linear split may alter the
    tuned semi-implicit balance and degrade phase propagation.
  - If the existing explicit product is already compensating other model
    errors, a formally cleaner split can still reduce WB2 score.

## Risks

- Numerical stability:
  - Moderate. The change touches core primitive-equation tendencies, although
    it does not add energy or remove damping.
- Compute cost:
  - Low. It adds one area-weighted mean per layer and tendency call.
- Data leakage:
  - None. The split uses only the forecast state and fixed quadrature weights.
- Physical plausibility:
  - Good. Well-balanced pressure-gradient formulations are standard for
    reducing spurious forcing when large hydrostatic or reference terms nearly
    cancel.
- Rollback complexity:
  - Moderate. Remove one primitive-equation option/path, one adapter flag, one
    factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_name> --workers 4`.
  - Support requires primary delta at least `+0.002`, clean diagnostics, no
    early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta, especially with MSLP/Z500
    regression, would show that this reference/eddy split is not a material
    remaining pressure-gradient error source.

## Citations

- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AECAAM%3E2.0.CO;2
- Arakawa, A. and Lamb, V. R. 1977. Computational design of the basic dynamical
  processes of the UCLA general circulation model. Methods in Computational
  Physics, volume 17.
- Lin, S.-J. 1997. A finite-volume integration method for computing
  pressure-gradient force in general vertical coordinates. Quarterly Journal of
  the Royal Meteorological Society.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: A review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is not the staged pressure-gradient product dealiasing proposal, which
targets high-wavenumber aliasing after forming the product. It is also not the
staged Simmons-Burridge operator proposal, which changes vertical hydrostatic
weights. This proposal changes the low-order reference/eddy split of the
pressure-gradient product while leaving damping, vertical weights, and outputs
unchanged.

## Evaluator Notes

### 2026-06-20T20:56:31Z

Decision: move to `scrap`; ranked third of the three new proposals.

The proposal is physically motivated but a poor fit for the next search budget.
It changes the core sigma pressure-gradient split and the effective
semi-implicit reference-temperature coupling during every tendency evaluation,
which is a broad primitive-equation operator change. Prior queue evidence
already contains safer pressure-gradient/operator variants in staging
(`pressure-gradient-product-dealiasing` and
`simmons-burridge-sigma-geopotential-operator`), and related history is weak:
broad nonlinear dealiasing was clean but subthreshold, mass-conserving
log-pressure smoothing was effectively neutral, absolute-vorticity flux
dealiasing was effectively neutral, and several fast-mode/damping/filter
families have failed to produce robust gains after the accepted off-centered
SIL3 improvement.

This also overlaps conceptually with the scrapped analysis-mean reference split:
both move thermal structure between explicit residual terms and the linear
reference operator to improve balance. The proposed per-step layer-mean split
is more intrusive than that scrapped idea because it modifies runtime pressure
gradient behavior rather than only the initialization/reference profile.
Scrapping it avoids spending implementation effort on another broad
pressure-gradient-family experiment unless future diagnostics identify this
specific layer-mean product as a measured error source.
