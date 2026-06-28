---
schema_version: 1
slug: simmons-burridge-sigma-geopotential-operator
title: Use Simmons-Burridge Sigma Geopotential Weights
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

# Use Simmons-Burridge Sigma Geopotential Weights

## Hypothesis

The incumbent uses pure sigma coordinates and the existing Durran-style
center-log-sigma weights for hydrostatic geopotential and the matched
semi-implicit temperature/divergence coupling. Accepted history shows that
hydrostatic consistency is high leverage, but the latest sigma-native
hydrostatic initialization was cleanly negative. That argues against another
initialization remap, not against the runtime vertical pressure-gradient
operator itself.

The vendored code already implements Simmons-Burridge style alpha and
interface-log-pressure coefficients for hybrid coordinates. A pure-sigma
specialization of that energy and angular-momentum conserving vertical
finite-difference form may reduce hydrostatic pressure-gradient and thickness
phase error during rollout while preserving the accepted Strang incumbent,
initialization, DFI, weak-HS forcing, near-surface residual correction,
horizontal diffusion, vertical advection, and output contract.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sb_sigma_geopotential`.
Preserve all incumbent behavior except the optional vertical hydrostatic
operator used by the pure-sigma primitive equation.

Implement a guarded pure-sigma Simmons-Burridge operator:

- add an adapter option such as `sigma_geopotential_operator="durran"` by
  default and `"simmons_burridge"` for the candidate;
- construct pure-sigma interface pressures from the existing sigma boundaries
  with an arbitrary positive reference surface pressure that cancels in the
  nondimensional pure-sigma ratios;
- compute layer alpha and interface log-pressure ratios with the same guarded
  formulas already used by the hybrid-coordinate helper;
- use the alternate weights consistently in sigma geopotential differences,
  the semi-implicit temperature/divergence coupling, and the implicit inverse
  matrix;
- use the same alternate `get_geopotential_on_sigma` path for pressure-level
  output reconstruction so the trajectory and diagnostic geopotential use one
  vertical operator;
- retain finite fallbacks or hard test failures for nonmonotone interfaces,
  nonfinite weights, or shape mismatches.

This is a runtime vertical-discretization proposal. It does not change
pressure-to-sigma initialization, does not repeat the sigma-native hydrostatic
temperature remap, and does not alter pressure-level output interpolation.

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
  - None. Forecast inputs, outputs, variable names, lead times, and fixed
    protocols remain unchanged.
- Tests to update:
  - Unit-test the pure-sigma Simmons-Burridge weights for finite values,
    monotone-interface assumptions, and expected matrix shapes.
  - Verify the candidate factory preserves all Strang incumbent flags except
    the sigma geopotential operator selector.
  - Verify the alternate operator is used consistently in `implicit_terms`,
    `implicit_inverse`, and `get_geopotential_on_sigma`.
  - Add an isothermal-column test comparing geopotential thickness against the
    analytic `R * T * log(p_bottom / p_top)` relation.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at early and medium leads
    if the remaining mass-field error is partly a vertical hydrostatic
    pressure-gradient quadrature error.
  - `2m_temperature` may improve indirectly if lower-column thickness evolution
    stays closer to the initialized hydrostatic structure after the accepted
    residual decays.
- Expected neutral metrics:
  - Lead-zero outputs should remain unchanged except for roundoff because
    initialization and output variables are preserved.
  - `10m_u_component_of_wind` should be close to neutral if the operator improves
    mass balance without upsetting the accepted Coriolis wind phase.
- Possible regressions:
  - The current Durran weights may already be the better discretization for this
    pure-sigma grid and scoring contract.
  - Changing the hydrostatic pressure-gradient operator can rapidly perturb
    balanced wind and mass fields, so early Z500/MSLP guardrails are the key
    risk.

## Risks

- Numerical stability:
  - Moderate. The change touches the semi-implicit operator and inverse matrix,
    so fast diagnostics must pass before any iteration run.
- Compute cost:
  - Low to moderate. The alternate weights are precomputed matrix operations and
    should not change grid size, lead count, or worker policy.
- Data leakage:
  - None. The operator uses only fixed sigma geometry and physical constants.
- Physical plausibility:
  - Moderate to high. Simmons-Burridge vertical differencing is a standard
    energy and angular-momentum conserving construction for terrain-following
    coordinates, but the candidate must prove that its pure-sigma specialization
    is not effectively a no-op or a worse quadrature for this model.
- Rollback complexity:
  - Low. Remove one operator selector, helper functions, one factory/export,
    one registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sb_sigma_geopotential`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sb_sigma_geopotential --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day 1-5 RMSE guardrail failure, and no variable+lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sb_sigma_geopotential --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A fast nonfinite result, ill-conditioned implicit inverse, early Z500/MSLP
    guardrail failure, or clean negative iteration delta would show that the
    incumbent vertical hydrostatic operator is preferable under the fixed
    protocol. A unit-test result showing the alternate weights are exactly
    identical to the incumbent should also stop implementation before scoring.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements pure-sigma `get_geopotential_weights_sigma`,
  `get_temperature_implicit_weights_sigma`, and the hybrid-coordinate
  Simmons-Burridge coefficient helpers.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  builds the accepted Strang incumbent with pure sigma coordinates and zero
  orography.
- History: `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted layer-mean hydrostatic initialization with validation delta
  `+0.005305927605172567`, showing hydrostatic consistency can matter.
- History: `.logbook/history/2026-06-18_07-30-18_sigma-native-hydrostatic-initialization/decision.md`
  rejected sigma-native hydrostatic initialization with iteration delta
  `-0.008345744027537627`; this proposal therefore avoids another
  initialization refinement.
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Laprise, R. 1992. The Euler Equations of Motion with Hydrostatic Pressure as
  an Independent Variable. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C0197:TEEOMW%3E2.0.CO;2

## Researcher Notes

This is explicitly retargeted to preserve the accepted Strang incumbent. It is
not a duplicate of the staged hypsometric target-geopotential diagnostic, which
changes only pressure-level geopotential output after the trajectory has been
computed. This proposal changes the runtime hydrostatic operator used by the
primitive equation and its matched implicit inverse.

It is also not another hydrostatic initialization refinement. The recent
sigma-native hydrostatic rejection is negative evidence against remapping
initial temperatures in sigma space, so this proposal keeps the accepted
pressure-level layer-mean initialization untouched. The risk is higher than an
output-only diagnostic because pressure-gradient changes can fail early
mass-field guardrails; that risk should be stated plainly if the Evaluator
triages this idea.

## Evaluator Notes

### 2026-06-18T08:53:53Z

Decision: move to `staging`; do not promote before lower-risk diagnostics.

The mechanism is scientifically legitimate but too broad for the next run.
Source inspection confirms the current pure-sigma path uses Durran-style sigma
weights in `get_geopotential_weights_sigma`,
`get_temperature_implicit_weights_sigma`, and the matched implicit matrix, while
the vendored hybrid-coordinate path contains Simmons-Burridge alpha and
interface log-pressure coefficients. A pure-sigma specialization is therefore
feasible, and the Simmons-Burridge citation supports the general conservative
vertical finite-difference motivation.

The recent evidence lowers priority. Hydrostatic consistency has produced large
accepted gains, but the latest sigma-native hydrostatic initialization was
cleanly negative (`-0.008345744027537627`) and previous pressure/output
geopotential experiments were fragile. This proposal touches the runtime
pressure-gradient/geopotential operator, semi-implicit temperature/divergence
coupling, implicit inverse, and geopotential output consistency. That is much
larger blast radius than the ready residual-rotation test.

Keep staged because it is not a duplicate of sigma-native initialization or the
hypsometric output diagnostic. Before any future promotion, the Orchestrator
should require a focused pre-implementation check that the proposed pure-sigma
weights are materially different from the incumbent and that the implicit
matrix remains finite and well conditioned.

### 2026-06-18T10:25:42Z

Decision: keep in `staging`; current staged rank 6.

The proposal is scientifically legitimate and not a duplicate of the failed
sigma-native hydrostatic initialization, but the latest evidence argues for
more caution. Hydrostatic layer consistency has accepted-history support, yet
the latest sigma-native hydrostatic initialization was a clean negative
`-0.008345744027537627`. This candidate touches the runtime hydrostatic
pressure-gradient/geopotential operator, semi-implicit temperature/divergence
coupling, implicit inverse, and geopotential diagnostic consistency, so the
blast radius is larger than the higher-ranked fallbacks.

Keep it as a later operator experiment only after a pre-implementation check
shows the pure-sigma Simmons-Burridge weights are materially different from the
incumbent and the implicit inverse remains finite and well conditioned.

### 2026-06-18T11:49:28Z

Decision: keep in `staging`, staged fallback rank 7.

The flux-form continuity proposal is a better first mass-field dynamics test
because it changes a single continuity tendency correction instead of the
runtime hydrostatic operator, semi-implicit coupling, implicit inverse, and
geopotential diagnostic consistency together. Keep this Simmons-Burridge idea
as a later vertical-operator experiment only after a pre-implementation check
confirms the pure-sigma weights differ materially from the incumbent and remain
well conditioned.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 8.

The flux-form continuity rejection lowers appetite for mass-field dynamics
changes but does not directly test this hydrostatic operator. Keep it staged
because the literature basis is legitimate and the idea is distinct from
initialization remaps. Rank it low because it touches pressure-gradient
geopotential weights, semi-implicit coupling, implicit inverse behavior, and
diagnostic consistency together, while recent sigma-native and pressure
initialization variants were clean negatives.
