---
schema_version: 1
slug: shape-preserving-logp-sigma-initialization
title: Use Shape-Preserving Log-Pressure Interpolation for Sigma Initialization
status: staging
created_at: 2026-06-20T14:53:43Z
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

# Use Shape-Preserving Log-Pressure Interpolation for Sigma Initialization

## Hypothesis

The accepted log-pressure initialization and hydrostatic layer-mean temperature
initialization show that pressure-to-sigma initialization remains high leverage.
However, broad remaps that changed the interpretation of pressure-level inputs
were rejected: conservative pressure-thickness remapping and variable-selective
pressure-linear scalar initialization both degraded primary score. The useful
part of the incumbent is therefore likely the all-field log-pressure coordinate,
not pointwise linear interpolation itself.

A shape-preserving monotone cubic interpolation in log pressure can preserve the
accepted vertical coordinate while reducing slope discontinuities and local
overshoot in temperature, wind, and passive humidity profiles. This may improve
early balance and lower-column shear without reverting scalars to
pressure-linear interpolation or treating pressure-level inputs as layer means.

## Mechanism

Register a side-by-side candidate that keeps all incumbent physics and changes
only pressure-to-sigma initialization of three-dimensional pressure-level
fields.

The candidate should:

- keep the accepted hydrostatic layer-mean temperature construction before
  interpolation;
- keep log pressure as the vertical interpolation coordinate for temperature,
  horizontal winds, and humidity;
- replace the current piecewise linear log-pressure interpolation with a
  Fritsch-Carlson or Hyman-style shape-preserving cubic Hermite interpolation
  wherever a column has enough finite source levels;
- constrain each interpolated value to the local source-level envelope for its
  bracketing interval, so wind, temperature, and humidity do not overshoot;
- retain the incumbent nearest finite extrapolation outside the analyzed
  pressure range;
- fall back to incumbent linear log-pressure interpolation for columns with too
  few finite levels, nonmonotone pressure coordinates, or nonfinite cubic
  diagnostics;
- leave sigma grid placement, DFI, weak-HS forcing, analysis-offset HS
  equilibrium, theta tendency, off-centering, Coriolis split, residual
  corrections, and output interpolation unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_vertical_interpolation.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory with a suffix such as `_pchip_logp_init`.
- API changes:
  - None. Forecast inputs, outputs, metrics, splits, and lead times stay fixed.
- Tests to update:
  - Unit-test shape preservation on monotone and nonmonotone synthetic columns.
  - Verify constant and linear-in-log-pressure profiles are reproduced.
  - Verify local envelope bounds and finite fallback behavior.
  - Verify the candidate factory preserves all incumbent settings except the
    initialization interpolation selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at early-to-medium leads
    if smoother initialized vertical thermal structure reduces adjustment.
  - `10m_u_component_of_wind` if vertical wind shear near the lowest sigma
    layers is initialized with fewer interpolation kinks or overshoots.
  - `2m_temperature` if lower-layer temperature profiles retain sharper but
    bounded inversions.
- Expected neutral metrics:
  - Lead-zero fields should remain close to the incumbent because the same
    log-pressure coordinate and same source fields are used.
- Possible regressions:
  - The current linear log-pressure interpolation may already be best matched
    to the coarse pressure-level input semantics.
  - Cubic slopes can introduce subtle phase or shear changes even with envelope
    limits.

## Risks

- Numerical stability:
  - Low to moderate. This is initialization-only and finite-guarded, but it
    changes all initialized three-dimensional fields.
- Compute cost:
  - Low. The extra column interpolation work occurs once per initial state.
- Data leakage:
  - None. The method uses only same-time input pressure-level analyses and fixed
    interpolation rules.
- Physical plausibility:
  - Moderate to high. Shape-preserving cubic interpolation is a standard
    numerical method for monotonicity and overshoot control. The physical
    assumption is that log pressure remains the right vertical coordinate for
    this sigma adapter.
- Rollback complexity:
  - Low. Remove one interpolation helper/selector, one factory/export, one
    registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_name> --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show linear all-log-p
    initialization remains preferable. Any early Z500, MSLP, or 10 m wind
    guardrail failure would show shape-preserving cubic slopes disrupt the
    accepted initialized balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` selects
  log-pressure pressure-to-sigma interpolation when
  `use_log_pressure_initialization=True`.
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py` implements
  the incumbent pressure-linear and log-pressure interpolation helpers.
- Dynamaxx history:
  `.logbook/history/2026-06-17_00-55-17_log-pressure-sigma-initialization/decision.md`
  accepted all-field log-pressure initialization.
- Dynamaxx history:
  `.logbook/history/2026-06-18_10-29-23_variable-selective-pressure-initialization/decision.md`
  rejected reverting scalars to pressure-linear interpolation, so this proposal
  keeps all fields in log pressure.
- Dynamaxx history:
  `.logbook/history/2026-06-17_08-03-52_conservative-pressure-thickness-init-remap/decision.md`
  rejected finite-layer conservative remapping, so this proposal keeps
  pressure-level values as point samples.
- Fritsch, F. N. and Carlson, R. E. 1980. Monotone piecewise cubic
  interpolation. SIAM Journal on Numerical Analysis.
  https://doi.org/10.1137/0717021
- Hyman, J. M. 1983. Accurate monotonicity preserving cubic interpolation. SIAM
  Journal on Scientific and Statistical Computing. https://doi.org/10.1137/0904045
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: A review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of rejected `variable-selective-pressure-initialization`
because it does not change any variable family back to pressure-linear
interpolation. It is not rejected `conservative-pressure-thickness-init-remap`
because it does not reinterpret pressure-level inputs as layer means. It is not
scrapped quasi-monotone pressure output interpolation because it changes only
the initial pressure-to-sigma remap and leaves scored pressure-level output
interpolation unchanged.

The proposal deliberately preserves the accepted all-log-pressure coordinate and
tests a different numerical property: shape preservation and smooth local
slopes during initialization.

## Evaluator Notes

### 2026-06-20T14:57:48Z

Decision: move to `staging`.

This is scientifically plausible and implementable, but it should not be the
next ready experiment. The accepted log-pressure initialization and accepted
hydrostatic layer-mean temperature initialization show that initialization is
high leverage, and source inspection confirms the current log-pressure
pressure-to-sigma path is a compact linear interpolation helper that could
accept a guarded shape-preserving interpolant. The proposal also avoids the
main failure modes of prior pressure remaps by keeping all fields in log
pressure and preserving pressure-level values as point samples.

Keep staged because the intervention still touches all initialized 3D
temperature, wind, and humidity fields, and recent pressure/init history is
mixed: conservative pressure-thickness remapping regressed iteration by
`-0.006775878375613553`, variable-selective pressure initialization regressed
by `-0.005133070800804607`, and related generic pressure-output interpolation
ideas have already been scrapped. A bounded PCHIP-style initializer is
narrower than those failures, so it is not a duplicate and not scrap, but its
expected score signal is less direct than the ready DFI-balanced HS-equilibrium
ordering test.

### 2026-06-21T02:45:40Z

Decision: keep in `staging`; superseded for the next run by
`vector-wind-pchip-sigma-init`.

The new wind-only PCHIP proposal is a cleaner model-selection candidate because
it isolates the low-level wind interpolation hypothesis while leaving scalar
temperature and humidity initialization untouched. That reduces exposure to the
mixed pressure-remap history and avoids coupling a wind-shear test to early
T2m, MSLP, or Z500 initialization changes. Keep this all-field version staged
as a broader fallback if the wind-only candidate is clean but subthreshold or
if diagnostics later indicate scalar log-pressure interpolation overshoot.
