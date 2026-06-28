---
schema_version: 1
slug: geopotential-intercept-surface-pressure-init
title: Initialize Surface Pressure From Geopotential Intercepts
status: scrap
created_at: 2026-06-18T15:50:23Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Initialize Surface Pressure From Geopotential Intercepts

## Hypothesis

When `surface_pressure` is absent, the incumbent initializes
`log_surface_pressure` directly from `mean_sea_level_pressure`. That collapses
two distinct pressure concepts and can overstate column mass over elevated
terrain even though the accepted rollout remains flat with zero prognostic
orography. The older terrain/orography candidate showed that mass-coordinate
handling has large score leverage but failed guardrails because it changed too
many prognostic and diagnostic paths at once. A narrower same-time
geopotential-intercept surface-pressure fallback may improve mass initialization
without adding terrain forcing or changing output diagnostics.

## Mechanism

Register a side-by-side model named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_geopotential_sp_init`.
Preserve the incumbent dynamics, zero modal orography, weak-HS forcing, DFI,
near-surface residuals, symmetric Coriolis split, pressure-level output
interpolation, and fixed protocols.

Change only `_surface_pressure_values` for candidates where
`surface_pressure` is unavailable but `mean_sea_level_pressure` and a complete
pressure-level `geopotential` stack are present:

- use the existing pressure-level geopotential profile to estimate the pressure
  where relative height crosses the surface datum, following the local
  `vertical_interpolation.get_surface_pressure` helper or an equivalent
  bounded intercept calculation;
- bound the derived surface pressure to a physically broad range and fall back
  to the incumbent MSLP value wherever the intercept is nonfinite or outside
  bounds;
- use the derived surface pressure only for the initial `log_surface_pressure`
  modal state and pressure-to-sigma remap;
- keep prognostic orography zero and keep `mean_sea_level_pressure` output on
  the incumbent surface-pressure-as-MSLP path for this first test.

This isolates initial column-mass estimation from the previously rejected
terrain/orography, terrain pressure-cycle, and flux-form pressure-continuity
families.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. The candidate uses only existing initial-state channels and local
    helper functions.
- Tests to update:
  - Unit-test that explicit `surface_pressure` still takes precedence.
  - Unit-test a synthetic geopotential profile with a known pressure intercept.
  - Verify nonfinite or out-of-bound intercepts fall back to MSLP.
  - Verify candidate factory preserves all incumbent flags except the new
    surface-pressure initialization fallback.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at early to medium leads if
    MSLP-as-surface-pressure currently initializes too much mass in elevated
    columns.
  - `2m_temperature` may improve indirectly if lower-column pressure placement
    improves log-pressure remapping.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be less exposed than in wind-control
    proposals because vector winds are not directly modified.
- Possible regressions:
  - Changing initial `log_surface_pressure` can disturb geostrophic and
    hydrostatic balance, especially over terrain-correlated regions.
  - Keeping output MSLP on the incumbent path while changing initialized surface
    pressure may improve dynamics but worsen the scored MSLP diagnostic.

## Risks

- Numerical stability:
  - Moderate. The rollout is unchanged, but initial column mass changes
    spatially.
- Compute cost:
  - Low. It adds one pressure-level intercept calculation per initial state.
- Data leakage:
  - Low. It uses only same-time initial `geopotential` and pressure channels
    already present in `ForecastInput.initial_state`.
- Physical plausibility:
  - Moderate. Hydrostatic pressure-height relationships are standard, but
    pressure reduction and terrain-related pressure diagnostics are known to be
    uncertain, especially over high terrain.
- Rollback complexity:
  - Low. Remove one adapter option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_geopotential_sp_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_geopotential_sp_init --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no early MSLP/Z500 or wind guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_geopotential_sp_init --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A terrain-like early MSLP/Z500 guardrail failure would show that changing
    initial surface pressure without prognostic orography disrupts balance. A
    clean near-zero delta would show the MSLP fallback is not a material
    remaining error source.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
    falls back from `surface_pressure` to `mean_sea_level_pressure` in
    `_surface_pressure_values`.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
    includes `get_surface_pressure`, a pressure-level geopotential intercept
    helper.
  - History: `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography/decision.md`
    rejected full terrain/orography after severe early Z500 and MSLP guardrail
    failures; this proposal does not add prognostic orography.
  - History: `.logbook/history/2026-06-18_11-53-08_flux-form-surface-pressure-continuity/decision.md`
    rejected changing surface-pressure continuity during rollout; this proposal
    changes only initialization fallback.
  - ECMWF ERA5 model-level documentation describes surface pressure, surface
    geopotential, and hydrostatic geopotential reconstruction from pressure,
    temperature, and humidity. https://confluence.ecmwf.int/plugins/viewsource/viewpagesrc.action?pageId=158636068
  - MITgcm documentation summarizes the hydrostatic primitive-equation relation
    between pressure, geopotential, density, and temperature.
    https://mitgcm.readthedocs.io/en/latest/overview/hydro_prim_eqn.html
  - Pauley, P. M. 1998. An Example of Uncertainty in Sea Level Pressure
    Reduction. Weather and Forecasting.
    https://doi.org/10.1175/1520-0434(1998)013%3C0833:AEOUIS%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of `terrain-aware-surface-pressure-orography`: it keeps
modal orography at zero, does not change pressure-gradient terms, does not
alter geopotential output datum, and does not perform a surface-to-sea-level
pressure output cycle. It is also distinct from scrapped `terrain-reduced-pressure-cycle`,
which required static surface geopotential outside the forecast API; this
proposal uses only the already available pressure-level geopotential stack.

It is not a duplicate of `flux-form-surface-pressure-continuity`, pressure
anchoring, variable-selective pressure remapping, or quasi-monotone output
interpolation. Those changed rollout pressure tendency, global pressure modes,
vertical remapping choices, or scored output interpolation. This proposal
tests a single initialization fallback for column mass and explicitly treats
the full terrain/orography history as negative guardrail evidence.

## Evaluator Notes

### 2026-06-18T15:55:59Z

Decision: move to `scrap`.

The proposal is narrow in code surface, but it is poorly ranked under the
current evidence. The last several pressure, terrain, sigma, and geopotential
experiments have all supplied negative signal for this family: full
terrain-aware surface pressure/orography failed severe early Z500 and MSLP
guardrails, variable-selective pressure initialization regressed by
`-0.005133070800804607`, flux-form surface-pressure continuity regressed by
`-0.015126833559440334`, sigma-native hydrostatic initialization regressed by
`-0.008345744027537627`, and output-only hypsometric Z was neutral-negative
with a `+7.385768302790055%` 24 h Z500 regression.

The mechanism also has an internal consistency problem for this incumbent. It
would infer a different initial `log_surface_pressure` from pressure-level
geopotential while deliberately keeping zero prognostic orography and the
incumbent MSLP output path. That can create an unbalanced initial column-mass
change without the terrain pressure-gradient and output-diagnostic treatment
needed to make the interpretation physically coherent. In practice, this is
likely to repeat the recent pressure-initialization and terrain-adjacent
failure mode rather than isolate a safe mass-initialization improvement.

Scrapping this does not reject all future terrain or pressure work, but a
future proposal would need stronger balance treatment and clear evidence that
it avoids the current flat-orography/MSLP-as-output mismatch. It is weaker than
the ready stability-aware residual proposal and weaker than staged fallbacks
that avoid directly changing initial column mass.
