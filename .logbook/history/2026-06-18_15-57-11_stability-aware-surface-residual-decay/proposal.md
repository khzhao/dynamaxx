---
schema_version: 1
slug: stability-aware-surface-residual-decay
title: Make Near-Surface Diagnostic Residual Decay Stability-Aware
status: ready
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

# Make Near-Surface Diagnostic Residual Decay Stability-Aware

## Hypothesis

The accepted near-surface residual correction applies one fixed 48 hour decay to
both `2m_temperature` and `10m_u_component_of_wind`. That recovered a large
diagnostic gap, but real surface-layer memory is not spatially uniform: stable,
weakly mixed boundary layers preserve unresolved screen-level anomalies longer,
while convective or strongly sheared columns mix them away faster. A bounded
stability-aware decay should improve near-surface targets without perturbing
the prognostic dycore or mass-field diagnostics.

## Mechanism

Register a side-by-side model named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual`.
Preserve the incumbent forecast trajectory, DFI, weak-HS forcing, symmetric
Coriolis split, initialization, output variables, and fixed protocols.

Replace only the scalar decay inside `_apply_near_surface_residual_correction`:

- keep the accepted lead-zero model-minus-analysis residual definition for
  `2m_temperature` and `10m_u_component_of_wind`;
- diagnose a local lower-column stability proxy from the output trajectory, for
  example a lowest-two-sigma potential-temperature difference normalized by
  low-level wind shear or a bounded bulk-Richardson-like index;
- assign a deterministic local decay timescale bounded between fixed values,
  such as 18 and 72 hours, with longer memory in stable weakly mixed columns
  and shorter memory in mixed or unstable columns;
- apply the resulting decay field independently at each output lead and grid
  point;
- leave all pressure-level fields, `mean_sea_level_pressure`, geopotential,
  vorticity/divergence, temperature trajectory, humidity tracers, and evaluation
  protocols unchanged.

This remains an output diagnostic surrogate for missing surface-layer
post-processing, not a new thermal forcing, wind residual rotation, or
validation-tuned decay sweep.

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
  - None. The forecast contract and emitted channels remain unchanged.
- Tests to update:
  - Unit-test decay-timescale bounds for stable, neutral, and unstable synthetic
    lower-column states.
  - Verify zero residual reproduces the uncorrected trajectory.
  - Verify lead zero still exactly matches available analyzed near-surface
    channels.
  - Verify pressure-level variables, MSLP, geopotential, and uncorrected
    channels are unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` and `10m_u_component_of_wind` at days 2 to 7 if the fixed
    48 hour residual either decays too fast in stable columns or too slowly in
    mixed columns.
  - Primary score may improve with little mass-field movement because the
    change is output-only and limited to the two accepted residual channels.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500` should be identical to the
    incumbent apart from row-ordering roundoff because their output path is not
    modified.
- Possible regressions:
  - Local stability proxies derived from coarse sigma layers may misclassify
    surface-layer memory and retain stale residuals during frontal transitions.
  - The `10m_u_component_of_wind` day-1 guardrail is sensitive; any change to
    wind residual decay must be watched closely.

## Risks

- Numerical stability:
  - Low. The prognostic trajectory is unchanged.
- Compute cost:
  - Low. It adds a few local lower-column diagnostics during output correction.
- Data leakage:
  - Low if the decay uses only forecast trajectory fields and same-time initial
    residuals. It must not use future truth, validation statistics, or learned
    station corrections.
- Physical plausibility:
  - Moderate. Operational screen-level diagnostics use surface-layer similarity
    concepts; this is a coarse surrogate because the dycore lacks skin
    temperature, roughness, and turbulent fluxes.
- Rollback complexity:
  - Low. Remove one residual-decay option, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, improved or neutral near-surface RMSE, and no fixed guardrail
    failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show fixed 48 hour decay
    is already sufficient. Any early 10 m wind guardrail failure would show the
    stability proxy is harmful for the scored near-surface diagnostic.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` applies a
    fixed exponential near-surface residual decay in
    `_apply_near_surface_residual_correction`.
  - History: `.logbook/history/2026-06-16_14-27-30_near-surface-anomaly-diagnostics/decision.md`
    accepted fixed near-surface residuals with validation delta
    `+0.03575996912567381`.
  - History: `.logbook/history/2026-06-18_08-58-52_coriolis-rotated-surface-wind-residual/decision.md`
    rejected inertially rotating the wind residual; this proposal changes only
    local decay strength and does not rotate or phase-shift wind residuals.
  - ECMWF Newsletter 178 describes 2 m temperature as a diagnostic derived from
    surface and lowest-model-level information using Monin-Obukhov similarity
    theory. https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade
  - ECMWF OpenIFS physical-process documentation describes Monin-Obukhov surface
    layer treatment and boundary-layer turbulent diffusion.
    https://confluence.ecmwf.int/display/OIFS/3.2%2BOpenIFS%3A%2BPhysical%2BProcesses
  - WeatherBench 2 defines a medium-range benchmark with headline scores over
    surface and pressure-level variables. https://arxiv.org/abs/2308.15560

## Researcher Notes

This is not a duplicate of the accepted fixed near-surface residual correction:
it keeps the same residual channels and lead-zero matching but replaces one
global decay constant with a bounded physical stability proxy. It is not a
duplicate of rejected `coriolis-rotated-surface-wind-residual`, which changed
the vector phase of the wind correction and failed the day-1 wind guardrail.

It is also distinct from active staged physics and numerics ideas because it
does not change vertical advection, scalar advection, momentum advection,
diffusion, heating, IMEX order, dealiasing, hydrostatic initialization, or
geopotential operators. The expected effect is localized to already accepted
near-surface diagnostics, so the main risk is stale residual retention rather
than broad dycore instability.

## Evaluator Notes

### 2026-06-18T15:55:59Z

Decision: move to `ready`; ranked first as the recommended next implementation
target.

This is the strongest available next experiment because it is tightly scoped to
the same output-diagnostic family that produced the largest accepted gain in
the loop so far: fixed near-surface residual correction improved validation
primary score by `+0.03575996912567381` without moving mass-field diagnostics.
The current proposal keeps the incumbent forecast trajectory, pressure-level
fields, MSLP, Z500, initialization, DFI, weak-HS forcing, and symmetric
Coriolis split unchanged. That is a materially lower-risk surface area than
staged omega spinup, diffusion heating, scalar/momentum advection rewrites,
vertical-advection changes, RK4 rollout, or sigma/geopotential operator edits.

It is ranked above `exponential-boundary-layer-rayleigh-drag` because the drag
proposal spends scarce early and long-lead wind margin in a prognostic momentum
path. Weak-HS history explicitly noted long-lead `10m_u_component_of_wind` as
the largest accepted cost, and the recent wind-residual rotation failed the
day-1 wind guardrail. This residual-decay proposal can still affect the scored
10 m wind channel, but it does so only through the already accepted diagnostic
residual amplitude and can be bounded between fixed timescales.

It is ranked above `geopotential-intercept-surface-pressure-init` because
recent pressure, terrain, sigma, and geopotential refinements have repeatedly
regressed or failed to promote: variable-selective pressure initialization,
flux-form surface-pressure continuity, sigma-native hydrostatic
initialization, and output-only hypsometric Z all supplied negative evidence.
This ready item avoids that failure cluster completely.

This is not a duplicate of rejected wind-residual rotation because it does not
phase-rotate the wind residual or introduce inertial timing. It is also not a
duplicate of the accepted fixed residual correction because it tests whether a
single global 48 h decay is too blunt, using same-forecast lower-column
stability as the only added signal. It should remain a conservative candidate:
the Implementer should use fixed predeclared bounds, no validation-tuned
constants, no future truth, and tests proving pressure-level outputs are
unchanged.
