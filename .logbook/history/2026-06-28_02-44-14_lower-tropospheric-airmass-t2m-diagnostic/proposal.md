---
schema_version: 1
slug: lower-tropospheric-airmass-t2m-diagnostic
title: Anchor 2 m Temperature Changes to Lower-Tropospheric Air-Mass Temperature
status: ready
created_at: 2026-06-27T23:17:41Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m
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

# Anchor 2 m Temperature Changes to Lower-Tropospheric Air-Mass Temperature

## Hypothesis

The current incumbent has accepted output-side land/ocean low-mode residual
memory and a bounded bulk-Richardson raw 2 m temperature diagnostic, yet
validation `2m_temperature` skill remains strongly negative at every lead. The
remaining failure is not just a small mean bias: the validation bias is only a
few tenths of a kelvin late in the forecast, while RMSE is far worse than
persistence. A plausible missing signal is the lower-tropospheric air-mass
temperature tendency. Real screen temperature changes over days are constrained
by both local surface coupling and advection of the lower-tropospheric air mass;
the incumbent's final T2m output is dominated by the surface-layer diagnostic
and same-time residual machinery.

A bounded final diagnostic that blends the incumbent corrected T2m toward
`initial_2m_temperature + beta * lower_tropospheric_temperature_anomaly` can
retain the accepted residual machinery while adding a forecast-state air-mass
change that is distinct from both residual persistence and another raw
bulk-Richardson formula.

## Mechanism

Register one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_airmass_t2m` or a shorter alias
such as `dino_ri2m_airmass_t2m` if artifact-name length is a concern.
Preserve the incumbent trajectory, DFI, weak-HS forcing, HSL/DSE transport, WTG,
vertical-DSE ramp, ocean heat flux, land/ocean low-mode T2m memory, bulk
Richardson raw T2m diagnostic, MSLP path, Z500 path, and 10 m wind path.

For this candidate only:

- compute the incumbent full corrected `WeatherState` exactly as today;
- from the same Dinosaur trajectory, compute a lower-tropospheric air-mass
  temperature at each saved lead using pressure-level temperature diagnostics
  already available inside `dinosaur_state_to_weather_state`, preferably a
  robust blend of 925 and 850 hPa temperatures where they are in-column, with
  exact fallback to the incumbent when the needed pressure levels are absent or
  nonfinite;
- compute the same air-mass temperature from the lead-zero initialized state;
- define an air-mass screen estimate
  `T2m_airmass = initial_T2m + beta * (T_airmass(lead) - T_airmass(0))`, with a
  fixed conservative `beta` in `[0, 1]` chosen before scoring and optionally a
  fixed land/ocean split that is no stronger than the accepted land-sea mask
  machinery;
- apply a smooth lead ramp that is zero at lead zero and weak through the first
  two days, so the accepted early residual and RI2m behavior are protected;
- update only the final emitted `2m_temperature` as a capped increment toward
  `T2m_airmass`, for example no more than `1.5 K` from the incumbent corrected
  value at any lead;
- leave all non-T2m channels bitwise or tolerance-equivalent to the incumbent;
- fall back exactly to the incumbent corrected T2m when pressure-level
  temperatures, initial T2m, land-sea masks, or ramp diagnostics are missing,
  nonfinite, or shape-incompatible.

This is not a new raw surface-layer diagnostic and not another residual-memory
proposal. It does not change the accepted lead-zero residual, low-mode
land/ocean memory, or bulk-Richardson raw T2m calculation; it adds a bounded
air-mass tendency signal after those accepted paths.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused adapter/output tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side candidate derived from
    `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`.
- API changes:
  - None. Forecast inputs, requested variables, output shapes, target
    variables, lead times, splits, and fixed protocols stay unchanged.
- Tests to update:
  - Verify lead zero remains the analyzed initial `2m_temperature`.
  - Verify non-T2m output channels are unchanged.
  - Verify zero lower-tropospheric temperature anomaly is a no-op.
  - Verify positive and negative air-mass anomalies move T2m by a bounded,
    ramped amount.
  - Verify missing 850/925 hPa temperature, absent initial T2m, nonfinite
    diagnostics, or invalid masks reproduce the incumbent exactly.
  - Verify the candidate factory preserves every incumbent selector except the
    new air-mass T2m output option and model name.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3-15 if the remaining error is partly failure to
    express lower-tropospheric air-mass temperature changes at screen level.
  - Primary score can improve without perturbing MSLP, Z500, or U10 because the
    change is final-output-only and T2m-only.
- Expected neutral metrics:
  - `mean_sea_level_pressure`, `geopotential_500`, and
    `10m_u_component_of_wind` should remain unchanged except for metric
    bookkeeping noise.
- Possible regressions:
  - In stable boundary layers, lower-tropospheric temperature anomalies can be
    decoupled from screen temperature, so the blend can overreact.
  - If the accepted residual memory already captures useful air-mass changes,
    this extra signal may be neutral or harmful.

## Risks

- Numerical stability:
  - Very low. The rollout state is unchanged.
- Compute cost:
  - Low. It reuses pressure-level temperature diagnostics and adds local
    elementwise algebra at saved output times.
- Data leakage:
  - Low. It uses only same-forecast initial fields, forecast-state pressure
    temperatures, static masks, and fixed constants. It must not inspect future
    truth or validation residuals.
- Physical plausibility:
  - Moderate. Lower-tropospheric temperature is a standard air-mass descriptor
    and is useful for near-surface temperature post-processing, but a fixed
    blend is still a reduced diagnostic rather than a full surface energy
    balance.
- Rollback complexity:
  - Low. Remove one output helper/selector, one factory/export, one registry
    key, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_airmass_t2m` using the
    final registered candidate name.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_airmass_t2m --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m` incumbent, clean diagnostics,
    and no fixed early or variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_airmass_t2m --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that
    lower-tropospheric air-mass temperature anomalies do not add useful screen
    temperature signal beyond the accepted residual and RI2m paths. Any early
    T2m guardrail failure would show the ramp or cap is too intrusive.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` already computes
  pressure-level temperature fields from the Dinosaur trajectory and packs
  `2m_temperature` through a raw diagnostic followed by accepted residual
  correction.
- Dynamaxx history:
  `.logbook/history/2026-06-27_18-53-15_land-ocean-lowmode-t2m-memory/decision.md`
  and
  `.logbook/history/2026-06-27_23-08-54_bulk-richardson-2m-temperature-diagnostic/decision.md`
  accepted the current T2m residual-memory and raw RI2m diagnostic paths, so
  this proposal preserves both.
- Dynamaxx history:
  `.logbook/history/2026-06-20_01-15-56_lagrangian-surface-residual-memory/decision.md`
  rejected advecting surface residuals and warns against moving accepted T2m
  residual memory spatially; this proposal uses forecast pressure-level
  temperature anomalies instead of advecting residual patterns.
- ECMWF Newsletter 178 describes 2 m temperature as a diagnostic variable
  derived from surface and lowest-model-level information using surface-layer
  theory:
  https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade
- Pichelli, E. et al. 2015. Spatial downscaling of 2-meter air temperature
  using operational forecast data. *Energies*. The paper uses operational model
  temperature information and local vertical gradients for T2m downscaling.
  https://doi.org/10.3390/en8042381
- Stull, R. B. 1988. *An Introduction to Boundary Layer Meteorology*. Springer.
  https://doi.org/10.1007/978-94-009-3027-8

## Researcher Notes

This is intentionally distinct from the just-accepted
`bulk-richardson-2m-temperature-diagnostic`: it does not change the raw
surface-layer formula and does not recompute 2 m potential temperature from the
lowest two sigma layers. It is also distinct from accepted
`land-ocean-lowmode-t2m-memory`: it does not alter residual splits, residual
decay, land/ocean broad residual means, or late residual memory.

It is not a hard persistence envelope like scrapped
`lead-bounded-screen-temperature-anomaly`; the only added signal is the model's
own lower-tropospheric temperature anomaly. If Evaluator considers it too
metric-facing, the clean rejection should be interpreted as evidence that
future T2m proposals need to change actual lower-boundary physics or bring
read-only diagnostics rather than another final-output operator.

## Evaluator Notes

### 2026-06-27T23:22:43Z

Decision: promote to `ready`; ready rank 1.

The current incumbent
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m` still has validation
`2m_temperature` mean skill around `-0.95734`, which dominates the primary
score drag. The proposed change is output-only, T2m-only, finite-guarded, and
derives its new signal from same-forecast lower-tropospheric temperature
anomalies rather than validation residuals or future truth. Source inspection
confirms the adapter already computes pressure-level temperature diagnostics
and has existing selector/factory patterns for side-by-side Dinosaur
candidates, so implementation surface and rollback cost are low.

This is close enough to prior T2m diagnostic work that it should be treated as
the last high-priority output-only T2m attempt unless it promotes cleanly. It is
not a duplicate of the accepted land/ocean low-mode residual memory or the
accepted bulk-Richardson raw screen diagnostic: it leaves both paths unchanged
and adds a bounded air-mass tendency after the incumbent correction. It is also
more physically grounded than the scrapped hard persistence envelope because
the adjustment follows forecast lower-tropospheric thermal evolution.

Literature checks support the general premise but not the exact fixed blend:
ECMWF describes 2 m temperature as a diagnostic derived from surface and
lowest-model-level information using surface-layer theory, while the proposal's
pressure-level anomaly blend is a reduced surrogate. Keep the cap, lead ramp,
and exact incumbent fallback strict. If selected, retarget the candidate from
the current incumbent and reject any implementation that perturbs MSLP, Z500,
U10, the forecast trajectory, fixed protocols, or accepted residual/RI2m paths.
