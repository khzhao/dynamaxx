---
schema_version: 1
slug: vorticity-preserving-dfi-increment
title: Preserve Rotational Flow During Digital Filter Initialization
status: ready
created_at: 2026-06-18T00:39:09Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Preserve Rotational Flow During Digital Filter Initialization

## Hypothesis

The incumbent's accepted Lanczos digital filter initialization removes
high-frequency imbalance, but it applies the averaged DFI state to every
prognostic component. In normal-mode terms, most spurious gravity-wave spinup is
carried by divergent wind, temperature, and mass variables, while the rotational
vorticity component contains much of the balanced synoptic flow. The current
iteration artifact still has strongly negative mean skill for
`10m_u_component_of_wind`, so a DFI variant that keeps the analyzed rotational
component while accepting the filtered mass/divergence/thermal state may recover
some wind skill without discarding the accepted DFI benefit.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi`.
Preserve the incumbent pressure/log-pressure initialization, hydrostatic
layer-mean temperature initialization, weak Held-Suarez thermal forcing,
near-surface residual correction, T80 truncation, 900 s inner step, horizontal
diffusion filter, output variables, and public forecast API.

Add an optional DFI post-processing path:

- compute the raw initialized state with `weather_state_to_dinosaur_state`;
- run the existing `time_integration.digital_filter_initialization` exactly as
  the incumbent does;
- construct the rollout initial state from the DFI output, but replace only
  `vorticity` with the raw pre-DFI `vorticity`;
- leave DFI-filtered `divergence`, `temperature_variation`,
  `log_surface_pressure`, and tracers in place;
- apply no wind-space Helmholtz solve, no divergence correction, and no
  forecast-output residual beyond the accepted near-surface residual.

The proposal tests whether the accepted DFI gain comes primarily from filtering
fast mass/divergence/thermal modes, while DFI's rotational increment is neutral
or harmful for the current fixed score.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` only if a small
    reusable DFI merge helper is cleaner than adapter-local code
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi`.
- API changes:
  - None. Preserve `forecast(ForecastInput) -> WeatherState`, fixed target
    variables, lead times, metrics, and deterministic evaluation protocols.
- Tests to update:
  - Unit-test the merge helper on synthetic `primitive_equations.State` objects
    and verify only `vorticity` comes from the pre-DFI state.
  - Verify the candidate factory preserves every incumbent flag except the new
    vorticity-preserving DFI option.
  - Verify near-surface residual correction still applies after output packing.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at early to medium leads if DFI is overdamping or
    phase-shifting the balanced rotational wind component.
  - `geopotential_500` and `mean_sea_level_pressure` may stay positive if the
    DFI-filtered divergent, thermal, and mass fields still suppress gravity-wave
    spinup.
- Expected neutral metrics:
  - `2m_temperature` should retain the accepted weak-HS and near-surface
    residual behavior.
- Possible regressions:
  - If DFI's vorticity increment is needed for balance with the filtered
    divergence and mass fields, preserving raw vorticity may reintroduce spinup
    and hurt MSLP/Z500.
  - If the wind error is mostly bottom-layer diagnostic error rather than
    rotational initialization, the primary delta may be clean but sub-threshold.

## Risks

- Numerical stability:
  - Low to moderate. The proposal keeps the accepted DFI machinery, but combines
    raw and filtered components in a way that could slightly unbalance the state.
- Compute cost:
  - Low. It adds one tree merge after the existing DFI path and does not increase
    rollout length or resolution.
- Data leakage:
  - Low. It uses only same-time initial state components and the deterministic
    model DFI trajectory, not future targets or validation scores.
- Physical plausibility:
  - Moderate. Gravity-wave initialization theory supports preserving slow
    balanced modes, but this is an approximate modal split rather than a full
    normal-mode projection.
- Rollback complexity:
  - Low. The option is isolated behind one adapter flag and one registry entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the incumbent, clean diagnostics, no early day 1-5 RMSE guardrail failure,
    and no variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or sub-threshold iteration delta would show that the full
    accepted DFI state is better than preserving raw rotational flow. Any early
    MSLP/Z500 guardrail failure would show the merge disrupts mass balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` applies DFI
  inside `_trajectory_function` and initializes vorticity/divergence from
  pressure-level winds in `weather_state_to_dinosaur_state`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements `digital_filter_initialization` and the current SIL3 stepper used
  by the incumbent DFI path.
- History: `.logbook/history/2026-06-16_09-54-58_balanced-digital-filter-initialization/decision.md`
  accepted DFI with iteration delta `+0.004385840377088002`, so this proposal
  preserves the accepted mechanism rather than removing it.
- History: `.logbook/history/2026-06-17_22-19-32_continuity-balanced-divergence-init/decision.md`
  rejected a divergence-only continuity correction with iteration delta
  `-0.001312899911693144`, so this proposal does not introduce a new divergence
  solve.
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a
  Digital Filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Daley, R. 1981. Normal Mode Initialization. Reviews of Geophysics.
  https://doi.org/10.1029/RG019i003p00450
- Polavarapu, S., Ren, S., Clayton, A. M., Sankey, D., and Rochon, Y. 2004. On
  the Relationship between Incremental Analysis Updating and Incremental Digital
  Filtering. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2004)132%3C2495:OTRBIA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of accepted `balanced-digital-filter-initialization`;
it keeps the same DFI filter and asks whether only the vorticity increment
should be rejected. It is also distinct from rejected
`continuity-balanced-divergence-init`, which edited divergence directly, and
from rejected `helmholtz-wind-initialization`, which broadly reprojected winds.
The scrapped zero-mean vorticity projection targeted a likely no-op invariant
coefficient, while this proposal preserves the full analyzed rotational field.

The main negative evidence is that wind-control proposals have been risky, but
this one is initialization-only, component-local, and does not alter pressure,
temperature, divergence, or output diagnostics beyond the accepted incumbent
path.

## Evaluator Notes

### 2026-06-18T00:43:07Z

Decision: move to `ready`.

This is the strongest current candidate because it is narrow, reversible, and
directly probes the accepted DFI mechanism. Source inspection confirms the
adapter currently applies `digital_filter_initialization` inside
`_trajectory_function`, and `weather_state_to_dinosaur_state` constructs
separate modal `vorticity`, `divergence`, `temperature_variation`, and
`log_surface_pressure` fields, so a post-DFI state merge is implementable
without changing the public forecast API or fixed evaluation protocol.

The main risk is balance: previous wind-control work is negative evidence.
`helmholtz-wind-initialization` regressed by `-0.34423230670441374`, and
`continuity-balanced-divergence-init` was clean but still `-0.001312899911693144`.
This proposal is materially narrower because it does not recompute winds,
solve for divergence, change pressure, or alter thermal initialization. DFI
itself was accepted with iteration delta `+0.004385840377088002`, so preserving
the accepted filtered mass/divergence/thermal state while testing only the
rotational DFI increment is the best available next experiment. Guardrails
should focus on early MSLP/Z500 balance and 10 m wind movement.
