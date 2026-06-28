---
schema_version: 1
slug: incumbent-richardson-10m-wind-diagnostic
title: Add Richardson 10 m Wind Diagnostic to the Current Incumbent
status: scrap
created_at: 2026-06-28T06:55:05Z
author_role: Researcher
target_model: dinosaur
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

# Add Richardson 10 m Wind Diagnostic to the Current Incumbent

## Hypothesis

The current incumbent `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m` includes the accepted bulk-Richardson 2 m temperature diagnostic but does not enable the existing surface-layer Richardson 10 m wind diagnostic. The raw 10 m wind output currently uses the lowest model-layer wind directly, which can overstate near-surface momentum in stable boundary layers and underrepresent wind reduction from lower-column stratification.

Enabling the already implemented bounded Richardson 10 m wind output on top of the current incumbent should improve the scored `10m_u_component_of_wind` channel without changing the prognostic trajectory, MSLP, Z500, T2m state evolution, fixed target variables, or forecast contract.

## Mechanism

Register one side-by-side candidate derived from `bulk_richardson_2m_temperature_diagnostic_dinosaur_dycore_model`, for example `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_ri10m`.

For the candidate only:

- preserve the incumbent rollout, HSL/DSE/WTG/vertical-DSE/T2m-memory/Richardson-T2m settings exactly;
- set `use_surface_layer_richardson_10m_wind_diagnostic=True`;
- leave `use_bulk_richardson_2m_temperature_diagnostic=True`;
- use the existing `_surface_layer_richardson_10m_wind` helper in `dinosaur_state_to_weather_state`;
- change only emitted `10m_u_component_of_wind` and `10m_v_component_of_wind` channels when those channels are requested;
- keep every pressure-level, MSLP, geopotential, surface-pressure, and 2 m temperature path incumbent-equivalent.

This is not another vertical-advection experiment. It is an output diagnostic using the current forecast column and the already available stability-aware helper.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one candidate factory and one registry key for `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_ri10m`.
- API changes:
  - None. Input state, output variable names, lead times, metrics, and fixed protocols remain unchanged.
- Tests to update:
  - Verify the candidate preserves every incumbent setting except model name and the 10 m Richardson selector.
  - Verify default incumbent behavior remains unchanged.
  - Verify the candidate changes 10 m wind output but leaves T2m, MSLP, and pressure-level fields unchanged for a controlled synthetic trajectory.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` across stable or weakly mixed boundary-layer cases.
  - Primary score if U10 remains a residual negative channel after the T2m improvements.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, and `geopotential_500`, because the change is output-only and does not feed back into rollout.
- Possible regressions:
  - U10 may worsen in convective or high-wind regimes if the Richardson reduction is too strong or if the lowest model-layer wind was already calibrated for 10 m.
  - If previous scoring showed the Richardson 10 m diagnostic helped only older incumbents, the current T2m/WTG/vertical-DSE stack may have a different U10 error structure.

## Risks

- Numerical stability:
  - Very low. The helper is output-only and bounded.
- Compute cost:
  - Negligible.
- Data leakage:
  - None. It uses only forecast lower-column wind, temperature, surface pressure, and fixed sigma geometry at each lead.
- Physical plausibility:
  - Moderate to high. Monin-Obukhov and bulk-Richardson ideas are standard boundary-layer diagnostics, and this code path already exists in the repository.
- Rollback complexity:
  - Low. Remove one factory/export/registry entry and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_ri10m`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_ri10m --workers 4`.
  - Promote only if the candidate beats the cached incumbent iteration score by the protocol threshold with clean diagnostics and no fixed guardrail failure.
- Validation gate:
  - Run fixed validation only after iteration promotion and require the protocol validation improvement threshold against cached incumbent validation.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, especially with U10 degradation, would show that the existing Richardson wind diagnostic does not match the current incumbent error structure.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` already implements `_surface_layer_richardson_10m_wind` and wires it through `use_surface_layer_richardson_10m_wind_diagnostic`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` defines `bulk_richardson_2m_temperature_diagnostic_dinosaur_dycore_model`, the current incumbent factory that enables RI2m but not RI10m.
- Dynamaxx history: `.logbook/history/2026-06-28_06-42-52_momentum-only-sl-vertical-advection/decision.md` rejected a prognostic vertical momentum transport after nonfinite forecasts, motivating output-only U10 work before more momentum-tendency changes.
- Garratt, J. R. 1992. The Atmospheric Boundary Layer. Cambridge University Press.
- Stull, R. B. 1988. An Introduction to Boundary Layer Meteorology. Kluwer Academic Publishers.
- ECMWF IFS Documentation, Part IV: Physical Processes, describes surface-layer stability and turbulent transfer parameterizations in operational weather models.

## Researcher Notes

This is not a duplicate of older `ri_10m_wind` registry entries because it specifically composes the existing Richardson 10 m diagnostic with the latest accepted HSL/DSE/WTG/vertical-DSE/T2m-memory/RI2m incumbent. It is also distinct from staged or scrapped momentum-mixing ideas because it does not alter the prognostic wind tendency.

## Evaluator Notes

### 2026-06-28T06:58:29Z

Decision: move to `scrap`.

The proposal rests on a false incumbent-state premise. Direct inspection of
`src/dynamaxx/dycore/models/dinosaur/adapter.py` and the registry factory for
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m` shows that the current incumbent
already inherits `use_surface_layer_richardson_10m_wind_diagnostic=True` while
also enabling `use_bulk_richardson_2m_temperature_diagnostic=True`. A direct
factory check confirmed both flags are true for the incumbent model instance.

The scientific boundary-layer rationale is not the issue: the earlier
surface-layer Richardson wind diagnostic was already accepted with large U10
gains, and surface-layer stability diagnostics are standard. The issue is that
this proposal would add no new behavior on top of the current incumbent. It is
therefore not a ready low-surface experiment; it is a duplicate/no-op against
the actual registered model chain.

Recommendation: do not implement. Future U10 work should target a genuinely
new signal beyond the existing Richardson diagnostic, such as a clearly bounded
geostrophic or roughness-related diagnostic, and should first verify the active
incumbent flags.
