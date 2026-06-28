---
schema_version: 1
slug: sigma-native-hydrostatic-initialization
title: Initialize Sigma Temperatures From Sigma-Native Hypsometric Thickness
status: ready
created_at: 2026-06-18T07:23:54Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
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

# Initialize Sigma Temperatures From Sigma-Native Hypsometric Thickness

## Hypothesis

The accepted layer-mean hydrostatic initialization improved both iteration and
validation by replacing raw pressure-level temperatures with hypsometric
temperature estimates before the log-pressure pressure-to-sigma remap. That
still estimates temperature on the input pressure-level stack first, then
interpolates the corrected temperature to the model's sigma levels.

A sigma-native variant should reduce a remaining mismatch between analyzed
geopotential thickness and the actual sigma layers consumed by the primitive
equation. Computing hydrostatic layer temperatures after mapping analyzed
geopotential to the target sigma pressures may better initialize column
thickness without changing the accepted Strang Coriolis rollout, DFI window,
weak Held-Suarez forcing, residual outputs, sigma grid, or evaluation protocol.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init`.
Preserve every incumbent option except the temperature initialization estimator.

When pressure-level geopotential is available:

- convert temperature, geopotential, winds, and optional humidity to Dinosaur
  latitude order and units as the incumbent already does;
- interpolate analyzed geopotential, analyzed temperature fallback, winds, and
  optional humidity to sigma centers using the incumbent log-pressure
  pressure-to-sigma path;
- compute each column's sigma-center pressure from
  `sigma_center * surface_pressure`;
- estimate sigma-layer virtual temperatures from adjacent sigma-center
  geopotential differences and adjacent `log(pressure)` differences;
- convert virtual temperature to dry temperature with bounded same-time
  humidity when humidity exists;
- reconstruct sigma-center dry temperature from adjacent layer estimates, with
  one-sided top and bottom values, broad physical bounds such as 150 K to 350 K,
  and fallback to the incumbent sigma-interpolated analyzed temperature for
  nonfinite or invalid estimates;
- proceed with the incumbent vorticity, divergence, tracer, and
  `log_surface_pressure` construction.

This changes only the same-time initialization estimate for
`temperature_variation`; it does not change pressure-level output diagnostics,
rollout dynamics, DFI coefficients, or forecast API.

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
  - None. `DycoreModel.forecast`, output variables, lead times, target
    variables, and fixed protocols remain unchanged.
- Tests to update:
  - Unit-test the sigma-native helper on an analytic hydrostatic column.
  - Verify the helper falls back to incumbent sigma-interpolated temperature for
    missing geopotential, nonfinite estimates, or invalid pressure spacing.
  - Verify vorticity, divergence, `log_surface_pressure`, tracers, and output
    variables are unchanged by the option at initialization.
  - Verify the candidate factory preserves all Strang incumbent flags except
    the new sigma-native hydrostatic initialization flag.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at early to medium leads if
    a residual sigma-layer thickness mismatch remains after the accepted
    pressure-level layer-mean hydrostatic initialization.
  - `2m_temperature` after the near-surface residual decays if lower-column
    thermal structure is initialized with less vertical remap error.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be near neutral because wind
    interpolation, Coriolis Strang splitting, diffusion, and residual output
    correction are unchanged.
- Possible regressions:
  - Local sigma-native thermal changes may perturb balanced pressure gradients
    more than the pressure-level layer-mean estimator.
  - If the accepted pressure-level estimator already gives the best compromise
    for this coarse vertical stack, the primary movement may be clean but
    sub-threshold or negative.

## Risks

- Numerical stability:
  - Low to moderate. The change is initialization-only and bounded, but it feeds
    DFI and can shift fast-wave balance.
- Compute cost:
  - Low. It adds one same-time geopotential remap and local vertical arithmetic
    per initial state, within the reported `--workers 4` resource envelope.
- Data leakage:
  - Low. It uses only same-time analysis fields already available to the
    incumbent initialization and no future targets, validation feedback, or
    golden artifacts.
- Physical plausibility:
  - High. The hypsometric relation directly links layer virtual temperature to
    geopotential thickness, and the proposal applies it on the model layers that
    the rollout actually uses.
- Rollback complexity:
  - Low. Remove one adapter flag, one helper path, one factory/export, one
    registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`
    against the Strang incumbent, clean diagnostics, and no fixed RMSE guardrail
    failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the remaining
    error is not controlled by sigma-native hydrostatic initialization. Any
    early `geopotential_500`, `mean_sea_level_pressure`, or
    `10m_u_component_of_wind` guardrail failure would show that the local
    thermal remap disrupts balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  computes pressure-level hydrostatic layer-mean temperatures before
  log-pressure pressure-to-sigma interpolation.
- History: `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted pressure-level layer-mean hydrostatic initialization with iteration
  delta `+0.004688970185515728` and validation delta `+0.005305927605172567`.
- History: `.logbook/history/2026-06-17_08-03-52_conservative-pressure-thickness-init-remap/decision.md`
  rejected broad conservative all-field remapping, so this proposal changes
  only the thermal estimate consumed by the incumbent sigma state.
- Arakawa, A. and Suarez, M. J. 1983. Vertical Differencing of the Primitive
  Equations in Sigma Coordinates. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1983)111%3C0034:VDOTPE%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of the active staged
`hypsometric-target-geopotential-diagnostic`: that idea is output-only and
changes pressure-level geopotential diagnosis, while this proposal changes only
the same-time initialized sigma temperature. It also differs from scrapped
`sigma-thickness-global-closure-init`: this is a local sigma-layer
hypsometric estimate, not a bounded global zero-mode correction after the state
is built.

The proposal uses the accepted hydrostatic initialization as positive evidence
and the rejected remap/edge experiments as negative evidence against changing
all fields or interpolation contracts.

## Evaluator Notes

### 2026-06-18T07:28:25Z

Decision: move to `ready`; rank 1 current recommendation.

This is the strongest current next experiment. It is not a duplicate of the
accepted pressure-level layer-mean hydrostatic initialization because it moves
the same hypsometric constraint onto the actual sigma layers consumed by the
rollout, after the incumbent log-pressure remap. It is also narrower than the
rejected conservative pressure-thickness remap because it changes only the
initialized thermal estimate, not winds, humidity, surface pressure,
diagnostics, the Coriolis Strang split, DFI window, weak-HS forcing, or the
forecast API.

Prior history supports trying one more carefully scoped hydrostatic
initialization refinement: hydrostatic-thickness initialization and
layer-mean hydrostatic initialization both accepted with material iteration and
validation gains, while broader column remaps and small thermal zero-mode
repairs were negative or too weak. Source inspection confirms the incumbent
computes hydrostatic layer-mean temperatures before pressure-to-sigma
interpolation, and the adapter already has the local pressure-to-sigma and
state-construction hooks needed for a side-by-side sigma-native helper.

Important risks remain. The latest DFI-Coriolis consistency experiment was
clean but sub-threshold, so balance-consistency refinements should not be
assumed to promote automatically. This proposal can perturb DFI balance and
short-lead mass fields, so the implementation should use bounded finite
fallbacks to the incumbent sigma-interpolated temperature and explicitly guard
day-1 through day-5 `geopotential_500`, `mean_sea_level_pressure`, and
`10m_u_component_of_wind`.
