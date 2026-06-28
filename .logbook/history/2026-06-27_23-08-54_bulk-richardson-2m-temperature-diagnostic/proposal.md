---
schema_version: 1
slug: bulk-richardson-2m-temperature-diagnostic
title: Diagnose 2 m Temperature with a Bounded Bulk-Richardson Surface Layer
status: ready
created_at: 2026-06-18T22:22:10Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
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

# Diagnose 2 m Temperature with a Bounded Bulk-Richardson Surface Layer

## Hypothesis

The incumbent still emits raw `2m_temperature` from the lowest sigma-layer
temperature before applying the accepted stability-aware residual correction.
The accepted Richardson 10 m wind diagnostic showed that replacing a lowest-layer
near-surface proxy with a bounded surface-layer diagnostic can produce large
score gains while leaving mass fields effectively unchanged. A temperature-only
surface-layer diagnostic based on lower-column potential-temperature stability
may improve `2m_temperature` after the residual decays while preserving the
accepted 10 m wind diagnostic and all pressure/geopotential paths.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_ri_2m_temp`.
Preserve the incumbent trajectory, DFI, weak Held-Suarez forcing,
log-pressure and hydrostatic initialization, symmetric exact-Coriolis split,
stability-aware near-surface residual correction, Richardson 10 m wind
diagnostic, horizontal diffusion, pressure-level interpolation, output
variables, and fixed evaluation protocols.

Add an opt-in raw `2m_temperature` diagnostic in `dinosaur_state_to_weather_state`:

- compute lower- and upper-layer potential temperature from the lowest two sigma
  layers using local sigma pressure, matching the accepted Richardson 10 m wind
  diagnostic's pressure/stability inputs;
- estimate nominal layer heights from the dry hypsometric relation and local
  surface pressure;
- form a bounded bulk-Richardson stability proxy from lower-layer static
  stability and wind shear, but use it only to limit the temperature diagnostic;
- diagnose a 2 m potential temperature by moving only a capped fraction of the
  lowest-layer potential-temperature difference toward the surface, with a
  tighter cap than the rejected two-layer extrapolation, for example no more
  than `1.5 K` equivalent departure from the lowest-layer temperature;
- convert the bounded 2 m theta diagnostic back to temperature with the 2 m
  pressure approximated by local surface pressure;
- leave `10m_u_component_of_wind` and `10m_v_component_of_wind` on the accepted
  Richardson path and leave pressure-level fields, surface pressure, MSLP,
  Z500, humidity, and the forecast trajectory unchanged;
- apply the existing stability-aware residual correction after packing, so lead
  zero still exactly matches the analyzed `2m_temperature`.

This proposal is not a linear two-layer shear extrapolation and does not change
10 m wind. It is a one-channel bounded surface-layer temperature diagnostic.

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
  - None. `DycoreModel.forecast`, input variables, output variables, lead times,
    target variables, splits, and metrics remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent flag except the new
    2 m temperature diagnostic selector.
  - Unit-test stable, neutral, and unstable synthetic lower columns, including
    finite fallback behavior and the fixed temperature-departure cap.
  - Verify only raw `2m_temperature` changes before residual correction; 10 m
    winds, pressure-level fields, surface pressure, MSLP, and Z500 should be
    bitwise or near-bitwise identical to the incumbent.
  - Verify lead-zero residual correction still exactly matches the analyzed
    `2m_temperature`.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2 to 15 if the lowest sigma-layer temperature is
    still a biased screen-level proxy after the accepted residual decays.
  - Primary score may improve without pressure/geopotential side effects because
    the change is output-only and confined to one near-surface thermal channel.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain governed by the accepted Richardson
    diagnostic and residual correction.
  - `mean_sea_level_pressure` and `geopotential_500` should be unchanged except
    for metric bookkeeping noise because the trajectory and pressure-level
    output path are unchanged.
- Possible regressions:
  - If the lowest sigma-layer temperature is already the best empirical proxy,
    the bounded surface-layer adjustment can still degrade `2m_temperature`.
  - Surface temperature without skin temperature, land cover, roughness, or
    fluxes is underdetermined, so the cap must be conservative.

## Risks

- Numerical stability:
  - Low. This is output-only and cannot feed back into rollout.
- Compute cost:
  - Low. It reuses local lower-column algebra already similar to the accepted
    Richardson wind diagnostic.
- Data leakage:
  - Low. It uses only forecast state and same-time initial residual correction
    already accepted in history; it must not inspect future truth or validation
    artifacts.
- Physical plausibility:
  - Moderate. Surface-layer theory supports diagnosing screen-level variables
    from lowest-model-level and surface information, but this adapter lacks the
    full surface energy balance used operationally.
- Rollback complexity:
  - Low. Remove one diagnostic option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_ri_2m_temp`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_ri_2m_temp --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_ri_2m_temp --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the accepted
    residual plus lowest-layer temperature is already the stronger 2 m
    diagnostic. Any early `2m_temperature` guardrail failure would show this
    bounded stability diagnostic remains too intrusive.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
    emits `2m_temperature` from the lowest sigma-layer temperature and then
    applies the accepted near-surface residual correction.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/decision.md`
    accepted a bounded Richardson 10 m wind diagnostic with large wind gains and
    effectively unchanged non-wind metrics.
  - Dynamaxx history:
    `.logbook/history/2026-06-17_13-35-18_surface-layer-diagnostic-extrapolation/decision.md`
    rejected a simple two-layer linear extrapolation after large 2 m temperature
    and 10 m wind guardrail failures; this proposal is temperature-only,
    potential-temperature based, and tightly capped.
  - ECMWF IFS Documentation Part IV: Physical Processes describes surface 2 m
    temperature and 10 m wind as surface-layer diagnostic products.
    https://www.ecmwf.int/sites/default/files/elibrary/2016/17117-part-iv-physical-processes.pdf
  - ECMWF Newsletter 178 describes 2 m temperature as a diagnostic variable
    derived with Monin-Obukhov similarity theory and stability safeguards.
    https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade
  - Beljaars, A. C. M. and Holtslag, A. A. M. 1991. Flux Parameterization over
    Land Surfaces for Atmospheric Models. Journal of Applied Meteorology.
    https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is not a duplicate of accepted `stability-aware-surface-residual-decay`
because it does not change residual amplitudes or decay timescales. It changes
the raw packed `2m_temperature` diagnostic before the accepted residual path is
applied. It is not a duplicate of accepted
`surface-layer-richardson-wind-diagnostic` because it leaves both 10 m wind
channels on that accepted path and targets only screen-level temperature.

This proposal also explicitly avoids the rejected
`surface-layer-diagnostic-extrapolation` mechanism. That candidate used a
linear two-layer extrapolation for both 2 m temperature and 10 m wind and failed
near-surface guardrails. The new mechanism uses potential temperature, a
bulk-Richardson stability proxy, a one-channel scope, and a fixed small cap.
The fresh scalar split-form rejection is unrelated: no prognostic scalar
transport operator changes here.

## Evaluator Notes

### 2026-06-18T22:26:00Z

Decision: move to `staging`; ranked 3 of 3 new proposals.

This remains implementable and materially different from the rejected
`surface-layer-diagnostic-extrapolation` candidate because it is temperature
only, capped, potential-temperature based, and preserves the accepted
Richardson 10 m wind diagnostic. The source path also supports feasibility:
raw `2m_temperature` is currently packed from the lowest sigma layer before the
accepted near-surface residual correction, so a side-by-side diagnostic can be
introduced without changing the rollout trajectory or forecast contract.

Keep it staged rather than ready because it is explicitly output-only and
targets one scored channel. That can be useful, as the accepted 10 m wind
diagnostic showed, but it also increases metric-targeting risk and does not
improve the physical trajectory. The closest scored surface diagnostic history
is strongly negative: the two-layer extrapolation candidate regressed primary
score by `-0.10115079559414197` and failed both near-surface RMSE guardrails.
This proposal reduces that risk with a cap and narrower scope, but screen-level
temperature is underdetermined without full surface energy balance, roughness,
land, and flux information.

If promoted later, implementation must keep lead-zero residual correction exact
and demonstrate that only raw `2m_temperature` changes before residual
application. It should not alter 10 m wind, pressure-level output, MSLP, Z500,
surface pressure, or the accepted trajectory.

### 2026-06-27T19:07:18Z

Decision: promote to `ready`; ready rank 1.

The new incumbent leaves `2m_temperature` as the clear limiting channel
(`validation` mean skill about `-0.9706`), while MSLP is only moderately
negative and Z500/U10 are positive. This proposal targets that dominant
weakness with the smallest blast radius: it changes only the raw T2m output
diagnostic before the accepted residual and current land/ocean low-mode memory
paths, and it cannot feed back into the rollout.

The prior two-layer surface extrapolation failure is still the main risk, but
this candidate is narrower, potential-temperature based, bounded, and benefits
from the positive precedent that the Richardson 10 m wind diagnostic produced a
large accepted gain without mass-field side effects. If selected, retarget the
candidate factory to derive from `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`
rather than the stale long model name in the older proposal body, preserve the
accepted land/ocean T2m memory exactly, and prove non-T2m channels are
unchanged before scoring.
