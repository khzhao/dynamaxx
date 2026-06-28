---
schema_version: 1
slug: hybrid-sigma-pressure-rollout
title: Use the Vendored Hybrid Sigma-Pressure Rollout
status: scrap
created_at: 2026-06-18T00:39:09Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/coordinates.py
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

# Use the Vendored Hybrid Sigma-Pressure Rollout

## Hypothesis

The incumbent still runs a pure sigma-coordinate primitive-equation model. The
rejected pressure-aware sigma grid changed only pure-sigma layer placement and
regressed strongly, but it did not test the hybrid-coordinate equations already
vendored in Dinosaur. A hybrid sigma-pressure coordinate can make upper and
middle atmospheric layers less surface-pressure-following while keeping a
terrain-following lower boundary. Even with zero orography, this may reduce
spurious vertical coupling between surface-pressure errors and pressure-level
Z500/MSLP diagnostics while preserving the fixed forecast contract.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_hybrid`.
Preserve the incumbent output variables, lead times, DFI, weak Held-Suarez
thermal forcing, near-surface residual correction, T80 horizontal truncation,
900 s inner step, and WeatherBench2 evaluation protocols.

Add an adapter option that builds a `coordinate_systems.CoordinateSystem` with
`hybrid_coordinates.HybridCoordinates.ecmwf137_interpolated(layer_count)` or a
similarly fixed ECMWF-like `HybridCoordinates` with the same layer count as the
input pressure stack. Use the existing `primitive_equations.PrimitiveEquationsHybrid`
when the coordinate system is hybrid.

The initialization and output path should be deterministic and same-time only:

- use the incumbent `_surface_pressure_values` path for the required surface
  pressure field, retaining the current MSLP fallback if true surface pressure
  is absent;
- initialize pressure-level temperature, winds, and humidity to hybrid layer
  centers with log-pressure interpolation using
  `hybrid_coords.pressure_centers(surface_pressure_hpa)`;
- retain the accepted hydrostatic layer-mean temperature construction before
  pressure-to-hybrid remapping;
- reconstruct output geopotential with
  `primitive_equations.get_geopotential_on_hybrid`;
- add direct hybrid-to-pressure output interpolation in pressure or log-pressure
  coordinates with bounded nearest extrapolation, preserving finite-output
  behavior;
- keep the pure sigma incumbent path unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/coordinates.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_hybrid`.
- API changes:
  - None. The model still consumes `ForecastInput` and emits `WeatherState` with
    the same variable names and lead structure.
- Tests to update:
  - Verify hybrid grid construction is monotone and has the same layer count as
    inferred pressure levels.
  - Unit-test pressure-to-hybrid and hybrid-to-pressure interpolation on a
    profile linear in log pressure.
  - Verify `get_geopotential_on_hybrid` is used for hybrid output and sigma
    output remains unchanged for the incumbent.
  - Add registry coverage and a non-JIT finite smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium leads if hybrid layers reduce vertical
    coordinate error around the mid-troposphere.
  - `mean_sea_level_pressure` if upper-level pressure-gradient and mass
    tendencies become less coupled to lower-column surface-pressure error.
  - `2m_temperature` could improve modestly if the lower hybrid layer retains
    enough sigma behavior while reducing column drift aloft.
- Expected neutral metrics:
  - The accepted near-surface residual should keep early `2m_temperature` and
    `10m_u_component_of_wind` from changing abruptly at lead 0.
- Possible regressions:
  - Hybrid-coordinate wiring is broader than recent successful adapter changes
    and may fail fast if interpolation or units are mishandled.
  - The pressure-aware sigma-grid rejection is negative evidence that vertical
    coordinate changes can be clean but harmful.
  - If MSLP fallback surface pressure is the dominant problem, hybrid dynamics
    may not help and could move Z500/MSLP guardrails in the wrong direction.

## Risks

- Numerical stability:
  - Moderate to high. The codebase contains hybrid-coordinate operators, but the
    Dynamaxx adapter has not scored them in this WeatherBench2 contract.
- Compute cost:
  - Low to moderate. Layer count and horizontal resolution stay fixed, but
    hybrid geopotential and interpolation may add per-column work.
- Data leakage:
  - Low. Hybrid coefficients are fixed source constants and initialization uses
    only same-time analysis fields.
- Physical plausibility:
  - High as a dynamical-core formulation. Hybrid sigma-pressure coordinates are
    standard in operational atmospheric models.
- Rollback complexity:
  - Moderate. The change should be isolated behind one coordinate option, but it
    touches initialization, equation construction, geopotential diagnostics, and
    vertical output interpolation.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_hybrid`.
  - Require finite forecasts, zero diagnostic issues, and no shape or variable
    contract changes.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_hybrid --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day 1-5 RMSE guardrail failure, and no variable+lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_hybrid --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A fast nonfinite result, any fixed output-contract mismatch, or a clean
    negative iteration delta would show the hybrid coordinate is not suitable in
    this adapter. Early Z500/MSLP guardrail failure would argue against further
    vertical-coordinate source-form proposals without new diagnostics.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/hybrid_coordinates.py`
  defines `HybridCoordinates`, `ecmwf137_interpolated`, and fixed ECMWF/UFS
  hybrid-level resources.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements `PrimitiveEquationsHybrid`, `compute_diagnostic_state_hybrid`, and
  `get_geopotential_on_hybrid`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  already contains hybrid regridding helpers and pressure-coordinate
  interpolation primitives.
- History: `.logbook/history/2026-06-16_12-14-23_pressure-aware-sigma-layer-grid/decision.md`
  rejected a pure-sigma pressure-aware grid with iteration delta
  `-0.10322710509965427`; this proposal is broader and should be treated as
  higher risk, not as a small variant of that failed grid.
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- ECMWF IFS Documentation CY49R1, Part III, describes the hybrid vertical
  coordinate introduced by Simmons and Burridge and its role in the IFS
  dynamical equations.
  https://www.ecmwf.int/sites/default/files/elibrary/112024/81625-ifs-documentation-cy49r1-part-iii-dynamics-and-numerical-procedures.pdf
- Beck, J., Brown, J., Dudhia, J., Gill, D., Hertneky, T., Klemp, J.,
  Wang, W., Williams, C., Hu, M., James, E., Kenyon, J., Smirnova, T., and
  Kim, J.-H. 2020. An Evaluation of a Hybrid, Terrain-Following Vertical
  Coordinate in the WRF-Based RAP and HRRR Models. Monthly Weather Review.
  https://doi.org/10.1175/MWR-D-20-0106.1

## Researcher Notes

This is not a duplicate of rejected `pressure-aware-sigma-layer-grid`: that
candidate stayed in pure sigma coordinates and only changed deterministic layer
interfaces. This proposal uses the existing hybrid-coordinate primitive
equations and hybrid geopotential operators. It is also distinct from terrain
orography proposals because it keeps zero orography and does not add static
surface-height loading.

Confidence is lower than for narrow DFI or stepper proposals because the adapter
surface is larger. The reason to keep it in the proposal set is that it tests a
real dynamical-core formulation already present in source and supported by NWP
literature, while preserving the current forecast contract and fixed
evaluation protocols.

## Evaluator Notes

### 2026-06-18T00:43:07Z

Decision: move to `scrap`.

The scientific mechanism is real and source inspection confirms the vendored
code contains `HybridCoordinates`, `ecmwf137_interpolated`,
`PrimitiveEquationsHybrid`, and `get_geopotential_on_hybrid`. The problem is
adapter blast radius and prior evidence. `grid_metadata` currently constructs
only equidistant sigma coordinates, while `weather_state_to_dinosaur_state` and
`dinosaur_state_to_weather_state` both cast the vertical coordinate to
`SigmaCoordinates` and rely on sigma-specific pressure interpolation and
geopotential output. A correct hybrid candidate would therefore touch coordinate
construction, initialization, equation selection, geopotential diagnostics, and
pressure-level output interpolation in one experiment.

Recent vertical-coordinate and pressure-remap evidence is unfavorable:
`pressure-aware-sigma-layer-grid` regressed by `-0.10322710509965427`, and
`conservative-pressure-thickness-init-remap` later regressed by
`-0.006775878375613553`. The source also labels `PrimitiveEquationsHybrid` as
not thoroughly verified and intended for research use. This is too broad and
too risky for the current fixed model-selection loop; it should not occupy
staging while narrower, source-local ideas remain.
