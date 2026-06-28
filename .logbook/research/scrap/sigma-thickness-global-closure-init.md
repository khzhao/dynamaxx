---
schema_version: 1
slug: sigma-thickness-global-closure-init
title: Sigma Thickness Global Closure Initialization
status: scrap
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

# Sigma Thickness Global Closure Initialization

## Hypothesis

The incumbent already uses log-pressure initialization and layer-mean
hydrostatic temperature estimates, and broad pressure remaps have been
negative. A narrower remaining mismatch is that the final initialized sigma
state is never checked against the global-mean pressure-level geopotential
thickness implied by the same input analysis after all accepted remapping has
already happened.

A one-time, globally averaged sigma-thickness closure should reduce residual
column-thickness bias without changing the sigma grid, output interpolation,
or spatial pressure/geopotential fields. The expected effect is modest; the
idea is included because it targets a different mechanism from pressure-edge
clipping, pressure-aware layer placement, and hydrostatic layer-mean
temperature construction.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sigma_closure`.
Preserve the incumbent DFI, weak Held-Suarez forcing, near-surface residual
correction, log-pressure interpolation, hydrostatic layer-mean temperature
initialization, sigma grid, vertical advection, horizontal diffusion, output
variables, and fixed forecast API.

After `weather_state_to_dinosaur_state` builds the initial modal state, convert
only the initial temperature field back to nodal sigma levels, diagnose the
global-area-mean sigma geopotential thickness using
`primitive_equations.get_geopotential_on_sigma`, and compare a small set of
global-mean pressure-layer thicknesses against the same-time analyzed
geopotential. Apply a bounded layerwise correction only to the spectral
zero-wavenumber component of `temperature_variation` so the initialized sigma
column better matches the analyzed global-mean hypsometric thickness. Leave all
nonzero temperature modes, winds, divergence, vorticity, `log_surface_pressure`,
humidity tracers, and the output path unchanged.

The first implementation should use one fixed cap, for example no more than
1 K absolute correction per sigma layer, chosen before scoring. It should fall
back to the incumbent state when pressure-level geopotential is unavailable or
the diagnosed correction is nonfinite.

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
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sigma_closure`.
- API changes:
  - None. Preserve deterministic `forecast(ForecastInput) -> WeatherState`,
    emitted variables, lead times, fixed metrics, and WeatherBench2 protocols.
- Tests to update:
  - Unit-test the closure helper on an analytic hydrostatic column where the
    global-mean thickness residual is known.
  - Verify the cap bounds layerwise temperature-mean corrections and finite
    fallback returns the incumbent state.
  - Verify only selected zero-wavenumber `temperature_variation` coefficients
    change; winds, divergence, vorticity, `log_surface_pressure`, tracers, and
    nonzero temperature modes are unchanged.
  - Add registry coverage and a non-JIT finite smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at early to medium leads if
    residual global column-thickness mismatch remains after the accepted
    hydrostatic initialization.
  - `2m_temperature` may improve slightly after the near-surface residual
    decays if the lower-column mean is less biased.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to neutral because wind fields,
    divergence, vorticity, and surface residuals are not initialized
    differently.
- Possible regressions:
  - Even a global temperature-mean correction can alter pressure gradients
    through subsequent balanced adjustment.
  - If the accepted layer-mean hydrostatic initialization is already optimal,
    this may be clean but below the iteration promotion threshold.

## Risks

- Numerical stability:
  - Low to moderate. The correction is bounded and initialization-only, but it
    changes the thermal column consumed by DFI.
- Compute cost:
  - Low. It adds one initial diagnostic geopotential calculation and a few
    reductions per initial state.
- Data leakage:
  - Low. It uses only same-time analyzed pressure-level geopotential already
    present in the initialization input, not future targets, validation scores,
    golden data, or learned climatology.
- Physical plausibility:
  - Moderate. Global hypsometric closure is physically meaningful, but the
    spatially uniform correction is a simplified repair and may be too weak.
- Rollback complexity:
  - Low. The change is isolated behind one adapter flag and one factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sigma_closure`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sigma_closure --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the incumbent, clean diagnostics, no early day 1-5 RMSE guardrail failure,
    and no variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sigma_closure --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that residual
    global sigma-thickness closure is not a material remaining error source.
    Any early Z500, MSLP, or 10 m wind guardrail failure would show the thermal
    mean correction disrupts balance more than it helps.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` applies the
  incumbent log-pressure and layer-mean hydrostatic initialization before
  modal projection.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  provides `get_geopotential_on_sigma` and the sigma-coordinate hypsometric
  operators used to diagnose initialized column thickness.
- History: `.logbook/history/2026-06-17_08-03-52_conservative-pressure-thickness-init-remap/decision.md`
  rejected broad all-field conservative remapping with iteration delta
  `-0.006775878375613553`, motivating a global zero-mode correction rather than
  another full vertical remap.
- History: `.logbook/history/2026-06-17_15-45-30_bounded-log-pressure-init-extrapolation/decision.md`
  rejected pressure-edge clipping with iteration delta `-0.000955044360586`,
  so this proposal avoids changing edge extrapolation.
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

This is not a duplicate of accepted hydrostatic layer-mean initialization: that
changes the pressure-level temperature estimate before log-pressure remapping,
while this proposal checks and corrects only a bounded global zero-mode after
the full accepted initialization path has produced a sigma state.

It is also distinct from rejected pressure-aware sigma grids, conservative
pressure-thickness remapping, potential-temperature initialization, bounded
log-pressure edge extrapolation, output interpolation, and thermal rollout
recentring. Confidence is low to moderate because recent initialization
follow-ups have mostly been too small or negative, but the mechanism is
narrow, reversible, and not exhausted by the recorded failures.

## Evaluator Notes

### 2026-06-17T23:27:52Z

Decision: move to `staging`.

This is a coherent low-surface initialization idea, but not the strongest next
experiment. It is not an exact duplicate of conservative pressure-thickness
remapping or bounded log-pressure edge extrapolation because it only adjusts
the initialized thermal zero mode after the incumbent log-pressure and
layer-mean hydrostatic path. Source inspection confirms
`primitive_equations.get_geopotential_on_sigma` can diagnose the sigma-column
geopotential from nodal temperature, so the proposed mechanism is feasible.

The reason to hold it in staging is risk versus expected effect size. Recent
initialization and balance cleanups have been clean but negative or below the
primary gate: conservative pressure-thickness remap was `-0.006775878375613553`,
bounded log-pressure edge clipping was `-0.000955044360586`, and
continuity-balanced divergence initialization was `-0.001312899911693144`.
This proposal also changes the thermal mean consumed by DFI, so even a bounded
global correction can shift mass and height phase. Keep it as a plausible
fallback only after stronger source-formulation ideas are exhausted.

### 2026-06-18T00:43:07Z

Decision: keep in `staging`.

The new evidence lowers this idea's rank but does not make it an exact
duplicate. `mass-neutral-weak-hs-forcing` regressed by
`-0.05788584798245422` and failed `2m_temperature` guardrails, confirming that
global thermal-mean changes can be harmful for this incumbent. The clean
negative continuity-balanced divergence result and the sub-threshold nonlinear
tendency cleanup also argue against promoting another small balance repair
ahead of a more direct DFI component test.

Keep this as a fallback because source inspection still supports the proposed
sigma geopotential diagnostic path and the implementation would be bounded and
initialization-only. If revisited, the correction cap must be fixed before
scoring and the fast/iteration review should explicitly check early
`2m_temperature`, MSLP, and Z500 movement.

### 2026-06-18T01:56:57Z

Decision: move from `staging` to `scrap`.

New evidence makes this too weak for the active queue. The mass-neutral weak-HS
experiment showed a large `2m_temperature` failure when a global thermal-mean
source was removed, and continuity-balanced divergence plus
vorticity-preserving DFI increments were clean but negative. This proposal is
bounded and initialization-only, but it still changes the thermal zero mode
consumed by DFI, exactly the sort of small balance repair that recent history
has not rewarded.

The idea is not impossible, but its expected effect size is now lower than the
remaining staged numerical splits, and the adaptive reference-temperature
proposal is a better version of a thermal-split experiment if that family is
revisited. Scrapping this file does not imply the research loop is exhausted;
future Researcher passes should continue looking for genuinely new mechanisms.
