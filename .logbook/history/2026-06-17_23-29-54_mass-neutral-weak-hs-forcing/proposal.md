---
schema_version: 1
slug: mass-neutral-weak-hs-forcing
title: Make Weak Held-Suarez Heating Globally Mass-Neutral
status: ready
created_at: 2026-06-17T23:24:07Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Make Weak Held-Suarez Heating Globally Mass-Neutral

## Hypothesis

The accepted weak Held-Suarez forcing was a large gain, but later forcing
variants that changed equilibrium geometry or DFI coupling were either harmful
or too small. The remaining risk in the accepted thermal-only forcing is that
its Newtonian heating can change the global layer-mean thermal mass/thickness
budget, shifting MSLP and geopotential even when the useful signal is primarily
relaxation of regional thermal anomalies.

Subtracting the area-weighted global mean of the weak-HS temperature tendency
in each sigma layer should preserve the anomaly-relaxation benefit while
removing a globally uniform heating/cooling component that a dry dycore without
full physics may not balance correctly. This is a bounded source-formulation
change, not a damping sweep, saturation adjustment, state-level dealiasing, or
output correction.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs`.
Preserve incumbent DFI, log-pressure initialization, hydrostatic layer-mean
temperature initialization, near-surface residuals, no-drag weak-HS settings,
vertical advection, diffusion, timestep, spectral resolution, output variables,
and protocols.

Add a new tracer-safe Held-Suarez forcing class or option. It computes the
current weak-HS nodal temperature tendency, then subtracts the horizontal
area-weighted mean tendency independently for each sigma layer before converting
the result to modal `temperature_variation`. Vorticity, divergence,
`log_surface_pressure`, tracers, equilibrium-temperature geometry, and
relaxation rates remain unchanged. The subtraction should use fixed quadrature
weights from the spherical grid and no target-variable or validation feedback.

The candidate should be single-strength and deterministic. It should not alter
the accepted weak-HS coefficients, add Rayleigh drag, add seasonal displacement,
or change DFI behavior.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs`.
- API changes:
  - None. Forecast shape, variables, lead times, deterministic API, and fixed
    WeatherBench2 protocols are unchanged.
- Tests to update:
  - Unit-test the forcing on synthetic thermal fields and verify the
    area-weighted layer-mean temperature tendency is zero.
  - Verify nonzero anomaly tendencies are preserved after removing the mean.
  - Verify vorticity, divergence, `log_surface_pressure`, tracers, and
    `sim_time` tendency leaves match the incumbent tracer-safe forcing.
  - Verify the candidate factory preserves all incumbent flags except the
    mass-neutral weak-HS option.
  - Add registry coverage and a non-JIT finite smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium and long leads if
    globally uniform weak-HS heating/cooling is contributing to mass/thickness
    drift.
  - `2m_temperature` may remain improved if the accepted weak-HS benefit comes
    from anomaly relaxation rather than changing the global mean thermal budget.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to neutral because the candidate
    remains wind-sparing and adds no drag or wind projection.
- Possible regressions:
  - If the accepted weak-HS gain depends on correcting a real global-mean
    thermal bias, subtracting the mean tendency will remove useful signal.
  - Layerwise mean removal could slightly change vertical static stability and
    mass-field phase.

## Risks

- Numerical stability:
  - Low to moderate. The forcing remains bounded and thermal-only, but it
    changes an accepted source term throughout the forecast.
- Compute cost:
  - Low. It adds one weighted horizontal mean per sigma layer per forcing call.
- Data leakage:
  - Low. The correction uses only forecast state and fixed grid weights.
- Physical plausibility:
  - Moderate. Conserving global layer-mean thermal tendency is a simplified
    energy/thickness constraint, but dry Held-Suarez forcing is itself idealized.
- Rollback complexity:
  - Low. The change is one forcing option plus one side-by-side factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no fixed RMSE guardrail failure, and no early `2m_temperature`
    or `10m_u_component_of_wind` guardrail regression.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative iteration delta would show that the accepted weak-HS global
    mean heating component is useful or harmless. Any early 2 m temperature,
    MSLP, Z500, or 10 m wind guardrail failure would show the mean-neutral
    forcing disrupts the accepted thermal balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` defines
  `_TracerSafeHeldSuarezForcingSigma`, which currently applies thermal-only
  weak-HS tendencies and zero tendencies for wind, pressure, and tracers.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
  implements the standard Held-Suarez relaxation profile used by the adapter.
- History: `.logbook/history/2026-06-16_16-27-03_wind-sparing-held-suarez-relaxation/decision.md`
  accepted weak wind-sparing Held-Suarez relaxation with iteration delta
  `+0.06357275459004397` and validation delta `+0.062227260743318746`.
- History: `.logbook/history/2026-06-16_23-51-06_calendar-aware-solar-relaxation/decision.md`
  rejected changing equilibrium geometry with iteration delta
  `-0.040271379533892704`, so this proposal preserves geometry and rates.
- History: `.logbook/history/2026-06-16_22-41-21_dry-dfi-weak-hs-split/decision.md`
  found splitting weak-HS out of DFI was clean but neutral, so this proposal
  changes the forecast source formulation instead of the DFI branch.
- Held, I. M. and Suarez, M. J. 1994. A Proposal for the Intercomparison of the
  Dynamical Cores of Atmospheric General Circulation Models. Bulletin of the
  American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Skamarock, W. C. and Klemp, J. B. 2008. A time-split nonhydrostatic
  atmospheric model for weather research and forecasting applications. Journal
  of Computational Physics. https://doi.org/10.1016/j.jcp.2007.01.037

## Researcher Notes

This is not a Held-Suarez coefficient variant, not seasonal forcing, not dry
DFI splitting, and not Rayleigh drag. It leaves the accepted weak-HS rates and
equilibrium profile fixed while removing only the layerwise global-mean thermal
tendency from the forecast source.

It is also distinct from broad damping, top sponge, saturation adjustment,
moist virtual-temperature dynamics, and nonlinear tendency dealiasing. The
confidence is low to moderate because the accepted global-mean weak-HS heating
may be part of the benefit, but the proposal is a concrete bounded forcing
formulation change from an underexplored family and is easy to revert.

## Evaluator Notes

### 2026-06-17T23:27:52Z

Decision: move to `ready`.

This is the strongest current proposal because it is a bounded
source-formulation change that preserves the accepted weak Held-Suarez rates,
equilibrium geometry, DFI behavior, forecast API, and output path. Source
inspection shows the accepted weak-HS path is already isolated in
`_TracerSafeHeldSuarezForcingSigma.explicit_terms`: it computes a nodal
thermal tendency, converts only that tendency to modal
`temperature_variation`, and returns zero tendencies for vorticity,
divergence, log surface pressure, and tracers. Subtracting a layerwise
area-weighted global mean at that point is therefore feasible with a small code
surface and no direct metric-facing correction.

The risk is real: the large accepted weak-HS gain may depend partly on a useful
global-mean thermal tendency, and recent source/physics changes have produced
large negative deltas when they disturbed balanced mass, height, or wind
evolution. However, this proposal avoids the failed families that changed
equilibrium geometry (`-0.040271379533892704`), split weak-HS out of DFI with
near-zero effect (`+0.0000017470501787464343`), added moist feedback
(`-0.055193744700895`), or added saturation adjustment
(`-0.026391567842939834`). It is ready as the sole ready item, with the fixed
fast, iteration, and validation gates unchanged.
