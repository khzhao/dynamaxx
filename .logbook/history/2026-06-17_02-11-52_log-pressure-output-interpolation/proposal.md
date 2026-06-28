---
schema_version: 1
slug: log-pressure-output-interpolation
title: Use Log-Pressure Sigma-to-Pressure Output Interpolation
status: ready
created_at: 2026-06-17T02:00:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Log-Pressure Sigma-to-Pressure Output Interpolation

## Hypothesis

The accepted incumbent now initializes pressure-level temperature, wind, and
passive humidity on sigma layers with log-pressure interpolation, but still
diagnoses pressure-level outputs by interpolating sigma fields linearly in
sigma, which is equivalent to linear pressure in each column. Hydrostatic
thickness and many analyzed vertical profiles are closer to smooth functions of
log pressure than of pressure. Applying the same pressure-coordinate geometry on
the output remap may reduce diagnostic interpolation error for pressure-level
targets without perturbing the accepted forecast trajectory.

This explicitly builds on the accepted log-pressure initialization result rather
than changing the same mechanism again: input initialization remains unchanged,
and only the sigma-to-pressure diagnostic projection used for WeatherState
packing changes.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output`. It should preserve
all incumbent prognostic behavior: DFI, near-surface residuals, weak thermal-only
Held-Suarez relaxation, log-pressure pressure-to-sigma initialization, T80
truncation, 900 s inner step, finite nearest extrapolation, and the forecast API.

Add a sigma-to-pressure output option that interpolates each column in
`log(pressure)`:

- source coordinates are `log(sigma_center * surface_pressure_hpa)`, equivalently
  `log(sigma_center) + log(surface_pressure_hpa)` per column
- target coordinates are `log(pressure_level_hpa)`
- the same bounded nearest extrapolation policy is retained outside the column
  bounds to preserve the accepted finite-output repair
- near-surface diagnostic residual correction remains applied after output
  packing, as in the incumbent

The candidate should not alter `ForecastInput`, `WeatherState`, target
variables, lead times, metrics, DFI, forcing, or prognostic time stepping.

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
  - Add only `dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output`.
- API changes:
  - None. Preserve deterministic `forecast(ForecastInput) -> WeatherState`.
- Tests to update:
  - Add a focused interpolation helper test showing log-pressure sigma-to-pressure
    interpolation differs from linear-pressure interpolation on a profile that is
    linear in `log(p)` and exactly recovers the expected profile.
  - Verify the candidate factory preserves incumbent DFI, weak Held-Suarez,
    near-surface residuals, log-pressure initialization, default step size,
    default spectral wavenumbers, and finite extrapolation.
  - Add a non-JIT finite smoke forecast test for the candidate.
  - Verify canonical incumbent output interpolation remains unchanged.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` should be the most direct beneficiary because geopotential
    is hydrostatically reconstructed on sigma levels and then interpolated to
    pressure levels.
  - Pressure-level temperature and winds may improve in aggregate score
    components if diagnostic vertical remapping is a remaining source of
    pressure-level mismatch.
  - Primary score may improve without large RMSE guardrail movement, matching the
    accepted log-pressure initialization pattern.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and `mean_sea_level_pressure`
    should be nearly unchanged except for aggregate interactions, because they do
    not use pressure-level output interpolation.
- Possible regressions:
  - If the sigma-level trajectory has error structures that accidentally cancel
    under linear-pressure output interpolation, log-pressure output may worsen
    `geopotential_500` or pressure-level wind scores.
  - Higher-altitude extrapolation behavior could shift despite nearest-level
    bounding, so the fast diagnostic artifacts should be checked for the same
    finite guarantees as the accepted repair.

## Risks

- Numerical stability:
  - Low. This is output-only and should not affect time integration, DFI, or
    prognostic state evolution.
- Compute cost:
  - Low. It adds a logarithm to the existing vectorized vertical interpolation
    path and should fit comfortably within the reported `--workers 4` resources.
- Data leakage:
  - Low. The method uses only forecast-state pressure, fixed target pressure
    levels, and deterministic interpolation.
- Physical plausibility:
  - Moderate to high. Log-pressure vertical interpolation is standard for
    pressure-coordinate atmospheric profiles and is consistent with the
    incumbent's accepted log-pressure initialization.
- Rollback complexity:
  - Low. Remove one adapter option, one helper, one factory, and one registry
    entry if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output --workers 4`.
  - Compare against exact incumbent records for
    `dinosaur_dfi_surface_residual_weak_hs_logp_init`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean but negative iteration delta, any `geopotential_500` guardrail
    failure, or nonfinite pressure-level outputs would show that the current
    linear-pressure diagnostic remap is better for this fixed contract.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  calls `_interp_sigma_to_pressure_by_time` for output packing after the
  accepted log-pressure initialization trajectory.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  provides `interp_sigma_to_pressure`, `interp_pressure_to_sigma_log_pressure`,
  and the accepted finite nearest-extrapolation interpolation helper.
- JCSDA JEDI UFO documentation states that vertical interpolation using
  `air_pressure` or `air_pressure_levels` is performed in log air pressure.
  https://jcsda-jedi-docs.readthedocs-hosted.com/en/latest/inside/jedi-components/ufo/obsops.html
- MetPy's sigma-to-pressure interpolation example uses log interpolation from
  irregular sigma-level pressures to mandatory isobaric levels.
  https://unidata.github.io/MetPy/latest/examples/sigma_to_pressure_interpolation.html
- ECMWF IFS documentation expresses the discrete hydrostatic relation using
  logarithms of pressure ratios, supporting log-pressure geometry for vertical
  pressure-coordinate relationships.
  https://www.ecmwf.int/sites/default/files/elibrary/112024/81625-ifs-documentation-cy49r1-part-iii-dynamics-and-numerical-procedures.pdf

## Researcher Notes

This proposal accounts for prior negative evidence by keeping away from broad
forecast-dynamics changes: no time-step sweep, no hyperdiffusion, no divergence
damping, no T120 resolution change, no vertical-advection ablation, no pressure
grid change, and no Held-Suarez geometry change. It also avoids the terrain
candidate's failure mode by not changing orography, surface pressure, or early
mass-field prognostics.

It is related to, but not a duplicate of, the accepted log-pressure sigma
initialization. The accepted candidate changed pressure-level analysis input
projection before DFI and forecast rollout; this candidate changes only
post-rollout diagnostic output projection. It is also distinct from the rejected
mass-diagnostic residual candidate, which applied decaying output residuals to
mass channels and had too little effect. Here the mechanism is a deterministic
vertical coordinate correction for pressure-level diagnostics.

The proposal is intentionally low-risk and side-by-side. If it improves only
`geopotential_500` while leaving near-surface channels unchanged, it may still
be useful; if it is neutral, the result would indicate that the remaining
primary-score gain from log-pressure initialization came from trajectory
initialization rather than output remapping.

## Evaluator Notes

2026-06-17T02:02:53Z - Move to `ready`; rank 1 of 3 active ideas for iteration 20.

This is the strongest next implementation target. It has a narrow, physically
coherent mechanism: the incumbent now initializes pressure-level fields onto
sigma levels in log pressure, but source inspection confirms output packing
still calls `_interp_sigma_to_pressure_by_time`, which delegates to
`vertical_interpolation.interp_sigma_to_pressure` with target coordinates
`pressure / surface_pressure`. That is linear in sigma/pressure, not log
pressure. A side-by-side log-pressure output option is therefore distinct from,
and complementary to, the accepted `log-pressure-sigma-initialization` result.

The implementation surface is low relative to likely value. It should add a
single interpolation mode and registry factory while preserving DFI, near-
surface residual correction, weak Held-Suarez relaxation, log-pressure input
initialization, T80 truncation, the 900 s inner step, finite nearest
extrapolation, the forecast API, target variables, leads, and fixed protocols.
Because it is output-only, numerical-stability and rollback risk are much lower
than the staged semi-Lagrangian transport change and lower than hydrostatic
thermal-profile initialization.

The mechanism is also supported by both local and external evidence. The
accepted incumbent showed that log-pressure geometry can improve fixed primary
score without RMSE guardrail failures. Local source shows Dinosaur computes
pressure-level geopotential hydrostatically from sigma-level temperature,
humidity, and surface pressure before vertical remapping, so vertical remap
error can affect `geopotential_500` without changing the trajectory. External
checks support log-pressure vertical interpolation and hydrostatic
pressure-coordinate geometry: JCSDA UFO documents pressure-coordinate vertical
interpolation in log air pressure, and hypsometric/hydrostatic references relate
geopotential thickness to virtual temperature times a logarithmic pressure
ratio. These sources support the coordinate choice; they do not guarantee a
fixed WeatherBench2 improvement.

Relevant history favors this bounded diagnostic projection. Broad pressure and
vertical-coordinate changes were poor bets: pressure-aware sigma layers
regressed iteration primary by `-0.10322710509965427`, terrain/orography
improved primary but failed severe early Z500/MSLP RMSE guardrails, and
standard-atmosphere reference profile was nearly neutral. In contrast, accepted
near-surface residuals and log-pressure initialization were narrow adapter
changes with clean gates. This proposal follows the successful pattern without
reviving mass residual tuning or terrain coupling.

Risks to flag for the Implementer and Scorer: keep canonical incumbent output
interpolation unchanged; retain nearest-level finite extrapolation outside the
column bounds; apply near-surface residual correction after output packing as
before; compare against exact incumbent artifacts for
`dinosaur_dfi_surface_residual_weak_hs_logp_init`; and stop before validation if
iteration primary does not clear the fixed `+0.002` promotion gate or if
`geopotential_500` guardrails regress.
