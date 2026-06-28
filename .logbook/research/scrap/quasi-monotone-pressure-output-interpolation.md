---
schema_version: 1
slug: quasi-monotone-pressure-output-interpolation
title: Use Quasi-Monotone Vertical Interpolation for Pressure-Level Outputs
status: scrap
created_at: 2026-06-18T14:33:12Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Quasi-Monotone Vertical Interpolation for Pressure-Level Outputs

## Hypothesis

The incumbent outputs scored pressure-level temperature, winds, and geopotential
by linearly interpolating sigma-level fields to requested pressure levels with a
safe extrapolation rule. Linear interpolation is robust, but it is only
first-order accurate in vertical structure and can degrade smooth tropospheric
profiles after the accepted hydrostatic initialization has improved the
underlying sigma state. A shape-preserving quasi-monotone cubic interpolation
may improve pressure-level diagnostics, especially `geopotential_500`, without
changing the prognostic rollout, DFI, Coriolis split, surface residuals, or fixed
evaluation protocols.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_monotone_output`.
Preserve the complete incumbent forecast trajectory and only change sigma-to-
pressure output packing.

Add an opt-in interpolation path in `dinosaur_state_to_weather_state`:

- keep the incumbent pressure-level-to-sigma initialization unchanged;
- keep forecast state variables on the incumbent sigma grid for all inner steps;
- for pressure-level output variables, replace the default sigma-to-pressure
  linear interpolation with a one-dimensional monotone cubic Hermite/PCHIP-style
  interpolant along each column;
- compute slopes with a Fritsch-Carlson or Fritsch-Butland limiter so monotone
  source profiles stay monotone and local extrema do not overshoot;
- fall back to the incumbent nearest/safe extrapolation outside the sigma-level
  range instead of extrapolating cubic polynomials;
- apply the same interpolant to pressure-level temperature, u wind, v wind,
  geopotential, and optional humidity for consistency;
- leave `2m_temperature`, `10m_*_wind`, `surface_pressure`, and
  `mean_sea_level_pressure` on the incumbent output path.

This is not a log-pressure output interpolation experiment and not a
geopotential-only diagnostic replacement. It is a bounded vertical reconstruction
change for pressure-level fields emitted from the existing sigma trajectory.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast state, output variable names, shapes, target variables, lead
    times, and protocols remain unchanged.
- Tests to update:
  - Unit-test the monotone interpolant on increasing, decreasing, constant, and
    single-extremum columns.
  - Verify cubic interpolation does not overshoot the local source interval for
    monotone data.
  - Verify out-of-range targets use the incumbent safe extrapolation path.
  - Verify near-surface outputs and pressure outputs are routed through the
    intended separate paths.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and pressure-level temperature/wind components at early
    to medium leads if vertical reconstruction error remains after the accepted
    hydrostatic initialization.
  - Primary score may improve without disturbing `10m_u_component_of_wind`
    because low-level screen and wind diagnostics are unchanged.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and MSLP should be neutral
    except for aggregate interactions through unchanged shared output arrays.
- Possible regressions:
  - Cubic reconstruction may sharpen vertical gradients in a way that worsens
    pressure-level wind or Z500 even with monotone limiting.
  - If the prior rejected log-pressure output experiment failed because output
    interpolation changes are inherently misaligned with the metrics, this may
    also regress despite being less intrusive.

## Risks

- Numerical stability:
  - Low. The rollout trajectory is unchanged; risk is diagnostic RMSE movement,
    not forecast blow-up.
- Compute cost:
  - Low to moderate. It adds columnwise slope calculations at output conversion
    only, not per inner step.
- Data leakage:
  - None. The interpolant uses only forecast sigma fields and fixed pressure
    coordinates.
- Physical plausibility:
  - Moderate. Shape-preserving high-order vertical interpolation is a standard
    numerical reconstruction tool, but output diagnostics alone cannot correct
    true model-state errors.
- Rollback complexity:
  - Low. Remove one interpolation helper, one adapter option, one factory/export,
    one registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_monotone_output`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_monotone_output --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_monotone_output --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative iteration delta or any Z500/wind guardrail failure would
    show that higher-order shape-preserving output reconstruction is not aligned
    with the current fixed metrics.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  currently defines `interp_sigma_to_pressure` using linear interpolation with
  safe extrapolation for 3D output fields.
- History: `.logbook/history/2026-06-17_02-11-52_log-pressure-output-interpolation/decision.md`
  rejected a log-pressure output interpolation change with many guardrail
  failures; this proposal keeps the incumbent pressure coordinate choice and
  adds only monotone shape preservation.
- History: `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
  rejected a geopotential-only diagnostic change after short-lead Z500 guardrail
  failure; this proposal changes all pressure-level variables consistently and
  does not replace the geopotential formula.
- Fritsch, F. N. and Carlson, R. E. 1980. Monotone Piecewise Cubic
  Interpolation. SIAM Journal on Numerical Analysis.
  https://doi.org/10.1137/0717021
- ECMWF IFS Documentation CY48R1, Part III: Dynamics and Numerical Procedures,
  describes quasi-monotone cubic interpolation choices in operational vertical
  and semi-Lagrangian procedures. https://www.ecmwf.int/sites/default/files/elibrary/2023/81369-ifs-documentation-cy48r1-part-iii-dynamics-and-numerical-procedures.pdf
- Collins, W. G. 1983. Vertical interpolation of heights and temperatures for
  model input/output. NOAA/NMC technical report record.
  https://repository.library.noaa.gov/view/noaa/11524

## Researcher Notes

This is not a duplicate of active staged `hypsometric-target-geopotential-diagnostic`,
which targets geopotential reconstruction. It is also not a duplicate of the
rejected `log-pressure-output-interpolation`; the candidate keeps the incumbent
sigma-to-pressure target coordinate and only replaces the one-dimensional
reconstruction with a bounded monotone higher-order method.

The proposal uses the output-interpolation failures as negative evidence by
keeping the implementation diagnostic-only, reversible, and consistent across
pressure-level variables. If selected, it should be evaluated as a single
candidate, not as a sweep over interpolation families.

## Evaluator Notes

### 2026-06-18T14:37:31Z

Decision: move to `scrap`.

The monotone interpolation literature supports the numerical reconstruction
claim, and the proposal is lower stability risk because it is output-only.
Under current loop evidence it is still the wrong pressure-output follow-up.
The rejected log-pressure output interpolation produced only a subthreshold
aggregate gain with many variable+lead guardrail failures, and the rejected
dry-consistent geopotential diagnostic failed short-lead Z500. This candidate
would change all pressure-level temperature, wind, humidity, and geopotential
outputs, so its scored surface is broader than the staged hypsometric Z
diagnostic.

This is not the same algorithm as the rejected log-pressure remap, but it is in
the same broad output-interpolation family and has a weaker ranking than a
geopotential-only hypsometric diagnostic. Scrap it rather than stage another
generic pressure-output reconstruction while `hypsometric-target-geopotential-
diagnostic` remains available as the narrower, more physically targeted Z500
test.
