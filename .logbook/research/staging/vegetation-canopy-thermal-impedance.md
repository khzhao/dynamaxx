---
schema_version: 1
slug: vegetation-canopy-thermal-impedance
title: Vegetation-Canopy Thermal Impedance for Lower-Layer Temperature
status: staging
created_at: 2026-06-27T19:00:21Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem
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

# Vegetation-Canopy Thermal Impedance for Lower-Layer Temperature

## Hypothesis

The current incumbent has recovered a late-lead broad land/ocean `2m_temperature`
residual signal, but that accepted mechanism is output-side, low-mode, and
land/ocean aggregate. A remaining physically distinct error source may be the
absence of vegetated-canopy thermal impedance in the prognostic lower layer:
forested and dense-canopy grid cells exchange heat with the atmosphere through a
roughness sublayer and canopy air space, not as bare land with instantaneous
lowest-layer coupling. A weak, local, vegetation-weighted thermal impedance can
reduce lower-layer temperature drift over vegetated land while leaving the
accepted broad land/ocean residual memory untouched.

## Mechanism

Add one side-by-side candidate, for example `dino_vdse_t2m_canopy`, derived from
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`.

For this candidate only:

- load static `high_vegetation_cover`, `low_vegetation_cover`,
  `type_of_high_vegetation`, and `type_of_low_vegetation` with the same
  grid-validation and exact-fallback style used for land-sea fraction;
- construct a bounded canopy impedance weight over land from the maximum or
  weighted sum of high- and low-vegetation cover, with zero weight over open
  ocean and invalid static fields;
- persist a lead-zero canopy-air anchor from initial `2m_temperature` when
  present, otherwise from the initialized lowest sigma-layer temperature;
- after each positive-time dynamics step and existing incumbent filters, apply
  a weak, capped relaxation only to the lowest one or two sigma-layer
  temperatures over vegetated land:
  `dT = canopy_weight * alpha * (T_anchor - T_lowest)`;
- cap the per-step temperature increment well below the accepted ocean bulk
  heat-flux cap and keep the relaxation timescale multi-day so the mechanism is
  an impedance, not a hard analysis anchor;
- leave vorticity, divergence, log surface pressure, tracers, WTG, vertical-DSE,
  residual-memory decays, T2m broad land/ocean memory, and output variables
  unchanged;
- fall back exactly to the incumbent if the vegetation fields, anchor, or
  temperature increment diagnostics are missing, nonfinite, or shape-mismatched.

This is not a retry of the accepted land/ocean low-mode T2m memory: it does not
compute broad land/ocean residual means, does not alter output residual decay,
and does not add a late-lead residual correction. It is a local lower-boundary
thermal process keyed to vegetation structure.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one short side-by-side key such as `dino_vdse_t2m_canopy`.
- API changes:
  - None. Forecast inputs, returned variables, lead selection, metrics, and
    fixed protocols remain unchanged.
- Tests to update:
  - Verify zero vegetation cover is exactly incumbent-equivalent.
  - Verify dense vegetation relaxes the lowest-layer temperature toward the
    fixed lead-zero canopy-air anchor and respects the cap.
  - Verify ocean points, non-temperature state leaves, and output variable
    lists are unchanged directly.
  - Verify missing, nonfinite, or misaligned vegetation fields trigger exact
    incumbent fallback.
  - Verify the candidate factory preserves every incumbent selector except the
    canopy-thermal option and candidate name.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2-15 over vegetated land if part of the remaining
    cold drift is caused by treating canopy-covered land like an exposed lower
    boundary.
  - Small `geopotential_500` or `mean_sea_level_pressure` improvements are
    possible if lower-column thermal drift projects coherently onto thickness.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to neutral because no momentum
    tendency or wind diagnostic changes.
  - Ocean and sparsely vegetated regions should remain incumbent-like.
- Possible regressions:
  - The global score may be insensitive if vegetation-only lower-layer errors
    are too local or already absorbed by the accepted T2m residual memory.
  - A persistent lead-zero canopy anchor can hurt locations where the initial
    analysis-model mismatch is an interpolation artifact rather than real canopy
    heat storage.

## Risks

- Numerical stability:
  - Low to moderate. The tendency is local and capped, but it changes the
    prognostic lower-layer temperature every positive step.
- Compute cost:
  - Low. Static-field loading and local elementwise arithmetic are small
    compared with the existing spectral rollout.
- Data leakage:
  - Low. The mechanism uses only lead-zero state variables and static vegetation
    fields listed in the repository utilities; it must not inspect future
    target fields or validation statistics.
- Physical plausibility:
  - Moderate. Vegetation canopy air space and roughness-sublayer turbulence are
    real controls on surface energy exchange, but this is a reduced impedance
    surrogate rather than a full land model.
- Rollback complexity:
  - Low. Remove one selector/helper path, one factory/export, one registry key,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_vdse_t2m_canopy`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_vdse_t2m_canopy --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem` incumbent, clean diagnostics, and
    no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_vdse_t2m_canopy --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that vegetation
    canopy impedance is not a material remaining error source. Any early
    `2m_temperature` or MSLP guardrail failure would show the lower-layer
    thermal impedance is too strong or activates too broadly.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/xarray_utils.py` lists static
  `high_vegetation_cover`, `low_vegetation_cover`,
  `type_of_high_vegetation`, and `type_of_low_vegetation` fields that can be
  used without adding new dynamic targets.
- Dynamaxx history:
  `.logbook/history/2026-06-27_18-53-15_land-ocean-lowmode-t2m-memory/decision.md`
  accepted broad land/ocean low-mode T2m residual memory; this proposal keeps
  that path unchanged and tests a local prognostic vegetation process instead.
- Dynamaxx history:
  `.logbook/history/2026-06-22_10-08-39_snow-soil-land-thermal-reservoir/decision.md`
  rejected a broader land soil/snow reservoir as effectively neutral, arguing
  for a narrower vegetation-only impedance if land-surface work is revisited.
- Bonan, G. B. 2008. Forests and climate change: forcings, feedbacks, and the
  climate benefits of forests. *Science*. https://doi.org/10.1126/science.1155121
- Bonan, G. B. et al. 2018. Modeling canopy-induced turbulence in the Earth
  system. *Geoscientific Model Development*. https://doi.org/10.5194/gmd-11-1467-2018
- NCAR Community Land Model documentation describes vegetation-mediated surface
  energy and water fluxes in full land models:
  https://www.cesm.ucar.edu/models/clm

## Researcher Notes

This proposal is intentionally decorrelated from the recent failed
vertical-DSE sheltering, gating, and retiming experiments: it does not touch
the vertical-DSE increment, WTG support, mass-DSE HSL transport, or filter
ordering. It is also distinct from the just-accepted land/ocean low-mode T2m
memory because it changes a local lower-layer thermal process, not the
post-rollout residual-memory correction.

## Evaluator Notes

### 2026-06-27T19:07:18Z

Decision: move to `staging`.

The proposal is feasible and grounded in a real missing surface-exchange
process. Source inspection confirms that static vegetation constants exist in
`xarray_utils.py`, and the current adapter already has a grid-checked static
land-sea loading pattern that could be extended conservatively. Literature
checks support the broad canopy/roughness-sublayer premise: canopy turbulence
and roughness-layer parameterizations materially affect surface exchange and
near-surface thermal structure.

Keep staged rather than ready under the new
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem` incumbent. The mechanism changes
prognostic lower-layer temperature every positive step, so it carries more
MSLP/Z500 and early-T2m guardrail risk than an output-only diagnostic. The
recent accepted land/ocean low-mode T2m memory already captures a broad
late-lead T2m residual, while previous narrow land-surface thermal-reservoir
and redistributed heat-flux experiments were neutral or harmful. This is a
reasonable fallback if the lower-risk ready T2m diagnostic fails cleanly, but
it should not be the next implementation slot.
