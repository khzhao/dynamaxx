---
schema_version: 1
slug: log-sigma-adiabatic-temperature-tendency
title: Use Log-Sigma Quadrature for the Adiabatic Temperature Term
status: staging
created_at: 2026-06-18T13:16:06Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
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

# Use Log-Sigma Quadrature for the Adiabatic Temperature Term

## Hypothesis

The incumbent's sigma-coordinate adiabatic temperature tendency uses
`PrimitiveEquationsSigma._t_omega_over_sigma_sp`, where the vertical integral
part of `omega / p` is built with `sigma_coordinates.cumulative_sigma_integral`.
The same source file already contains `cumulative_log_sigma_integral`, reflecting
that hydrostatic primitive-equation temperature and geopotential relations are
often better conditioned in log-pressure or log-sigma coordinates.

A candidate that changes only the quadrature used inside the adiabatic
temperature `omega / p` helper may reduce lower- and middle-tropospheric thermal
phase error without changing surface-pressure continuity, hydrostatic
initialization, pressure-level remapping, vertical-advection discretization, or
the accepted Strang Coriolis split.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_logsigma_adiabatic`.
Preserve the incumbent DFI, weak-HS forcing, near-surface residuals,
log-pressure initialization, hydrostatic layer initialization, horizontal
diffusion, centered vertical advection, 900 s inner step, and output contract.

Add an opt-in equation option for the sigma adiabatic temperature term:

- keep the incumbent `cumulative_sigma_integral` path as the default;
- for the candidate, compute only the `g_part` vertical integral in
  `_t_omega_over_sigma_sp` using a guarded log-sigma quadrature based on the
  existing `cumulative_log_sigma_integral` helper;
- leave `sigma_dot_full`, `sigma_dot_explicit`, vertical advection of state
  variables, `log_surface_pressure` tendency, pressure-gradient force, implicit
  gravity-wave terms, and all output interpolation unchanged;
- use the same option in DFI and positive-time rollout because this is a
  thermodynamic-equation discretization test, not a DFI-only merge variant;
- fall back to the incumbent path for nonfinite weights or incompatible vertical
  coordinates.

This is not another pressure-level-to-sigma initialization proposal and not a
direct rollout surface-pressure continuity correction. It targets the
temperature tendency's `omega / p` quadrature while keeping the accepted mass
and wind paths intact.

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
  - None. `DycoreModel.forecast`, input variables, output variables, lead times,
    metrics, and fixed protocols remain unchanged.
- Tests to update:
  - Unit-test that the default adiabatic helper reproduces the incumbent sigma
    integral path.
  - Unit-test the log-sigma option on a simple monotone sigma grid with finite
    tendencies and expected shape preservation.
  - Verify the option changes only temperature tendency outputs from
    `explicit_terms`; vorticity, divergence, log-surface-pressure, tracers, and
    implicit terms remain on the incumbent path.
  - Verify the candidate factory preserves all Strang incumbent flags except the
    new adiabatic-quadrature selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` after the accepted near-surface residual decays if
    adiabatic thermal drift is partly a vertical quadrature error.
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if cleaner
    temperature thickness evolution improves hydrostatic balance.
- Expected neutral metrics:
  - Early `10m_u_component_of_wind` should remain close to the incumbent because
    wind initialization, Coriolis splitting, pressure-gradient force, and
    near-surface residual correction are unchanged.
- Possible regressions:
  - The current Durran-style sigma quadrature may already be better matched to
    the rest of the sigma continuity discretization.
  - Thermal changes can still perturb balanced pressure gradients indirectly,
    so short-lead Z500/MSLP and 10 m wind guardrails remain important.

## Risks

- Numerical stability:
  - Low to moderate. The change is a bounded tendency-form switch but affects
    every DFI and rollout step.
- Compute cost:
  - Low. It reuses existing vertical integral helpers and does not change grid
    size, lead count, or worker count.
- Data leakage:
  - None. The mechanism uses only forecast state, fixed sigma geometry, and
    existing physical constants.
- Physical plausibility:
  - Moderate to high. Hydrostatic primitive-equation thermodynamics are closely
    tied to log-pressure structure, but this must remain consistent with sigma
    mass continuity.
- Rollback complexity:
  - Low. Remove one selector, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_logsigma_adiabatic`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_logsigma_adiabatic --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_logsigma_adiabatic --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the incumbent's
    adiabatic thermal error is not materially controlled by this quadrature.
    Any early Z500, MSLP, or 10 m wind guardrail failure would show the
    log-sigma tendency disrupts accepted balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements `PrimitiveEquationsSigma._t_omega_over_sigma_sp` and the incumbent
  adiabatic temperature tendency.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py`
  provides both `cumulative_sigma_integral` and `cumulative_log_sigma_integral`.
- History: `.logbook/history/2026-06-18_11-53-08_flux-form-surface-pressure-continuity/decision.md`
  rejected a direct surface-pressure continuity correction, so this proposal
  leaves `log_surface_pressure` tendency unchanged.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2

## Researcher Notes

This is distinct from active `upwind-vertical-advection-rollout`, which changes
the vertical transport operator for prognostic variables. It is also distinct
from active `analysis-omega-vertical-motion-spinup`, which injects same-time
analyzed vertical motion, and from `flux-form-surface-pressure-continuity`,
which changed the `log_surface_pressure` tendency directly.

The proposal deliberately avoids pressure-level-to-sigma initialization,
hydrostatic remaps, DFI-only Coriolis tweaks, near-surface wind residuals, and
direct continuity product-rule corrections called out in recent rejected
lessons.

## Evaluator Notes

### 2026-06-18T13:22:44Z

Decision: move to `staging`, not `ready`; current staged rank 6.

The proposal is distinct from the rejected direct surface-pressure continuity
correction and from the recent pressure-initialization/remap failures. Source
inspection confirms the named helper and target hook exist:
`sigma_coordinates.cumulative_log_sigma_integral` is available, and
`PrimitiveEquationsSigma._t_omega_over_sigma_sp` localizes the adiabatic
temperature `omega / p` quadrature while leaving `log_surface_pressure`
tendency and sigma-dot diagnostics elsewhere.

Keep it staged because the scientific case is weaker than the proposal implies.
The incumbent helper explicitly documents the Durran sigma-coordinate
`omega / p` approximation and currently combines a sigma integral of `G` with
log-sigma ratio weights. The existing log-sigma helper integrates with respect
to `d(log sigma)`, so substituting it only for the cumulative `G` integral risks
mixing quadrature measures without updating the matched continuity and
semi-implicit balance. Recent clean negative evidence from
`flux-form-surface-pressure-continuity` and
`sigma-native-hydrostatic-initialization` also argues against promoting another
sigma-balance change ahead of lower-risk diagnostics and split-order tests.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 6.

This remains worth keeping because literature uncertainty is not a blocker and
the implementation can be localized to one thermodynamic helper. It should sit
behind the staged output, transient spinup, diffusion-heating, and
anti-aliasing fallbacks because it changes a matched sigma-coordinate
adiabatic balance after several recent pressure, sigma, and continuity
experiments failed cleanly.
