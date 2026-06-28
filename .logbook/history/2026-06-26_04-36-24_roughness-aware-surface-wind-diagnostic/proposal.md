---
schema_version: 1
slug: roughness-aware-surface-wind-diagnostic
title: Roughness-Aware Surface Wind Diagnostic
status: ready
created_at: 2026-06-26T03:50:40Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_adapter.py
expected_eval_protocols:
  - leaderboard standard iteration evaluation with 4 workers against the valid incumbent cache
  - standard validation rerun only if the iteration score improves and guardrails pass
---

## Hypothesis

The current incumbent's biggest remaining score weakness is `2m_temperature`, but the local iteration and validation artifacts also show `10m_u_component_of_wind` loses skill at later leads and develops a negative bias. A roughness-aware output diagnostic for 10 m wind can address that channel without changing the forecast contract, dynamics, vertical-DSE path, or surface heat budget.

This is a deliberately low-coupling proposal: it only changes the diagnostic reduction from the model's lowest resolved wind to 10 m wind, using static surface information that is already part of the forecast context when available.

## Mechanism

Add an opt-in diagnostic variant such as `dino_hsl2_mass_dse_wtg_vdse_ramp_z0_10m`. Instead of using a single globally fixed near-surface wind reduction, blend a bounded roughness-length proxy from static fields such as land-sea mask, lake cover, sea-ice or ocean masks when available, and high/low vegetation cover when present. Convert that roughness proxy into a neutral log-law transfer factor and apply the existing stability correction or a bounded bulk-Richardson modifier already used by the surface diagnostics.

The result should reduce 10 m winds more strongly over rough vegetated land, less over ocean and lakes, and smoothly over coastlines. The diagnostic should fall back exactly to the incumbent path if static roughness inputs are unavailable, non-finite, or outside expected bounds.

## Implementation Scope

- Add a disabled-by-default adapter flag for roughness-aware 10 m wind diagnostics.
- Build a small helper that derives a smooth effective roughness length from existing static surface fields, with physically bounded values and no trainable state.
- Apply the transfer factor only to 10 m wind diagnostic outputs, including `10m_u_component_of_wind` and the matching v-component if the model emits it in a given protocol.
- Preserve all prognostic fields, pressure diagnostics, temperature diagnostics, and residual correction paths.
- Register a single new model factory and add tests for ocean/land/vegetation ordering, finite clipping, exact disabled behavior, and exact fallback when surface constants are missing.

## Expected Metric Movement

Expected movement is mainly positive for `10m_u_component_of_wind`, especially at land-dominated and later leads where the incumbent artifacts show late degradation. Other leaderboard channels should be neutral because the trajectory and non-wind diagnostics are unchanged. A realistic iteration-score gain is +0.001 to +0.006, with downside bounded by the diagnostic-only implementation.

## Risks

- If the current fixed reduction already implicitly matches the benchmark's average roughness, category-specific roughness could over-damp land winds.
- Static fields may not be present in every evaluation path, so fallback behavior must be exact and tested.
- A discontinuous land-ocean roughness transition could introduce coastal artifacts unless the mask is smoothed or blended.
- This may improve the u-component while leaving other dominant errors unchanged, so the aggregate score gain could be small.

## Evaluation Plan

Run the standard iteration evaluation with 4 workers against the valid incumbent cache. Inspect `10m_u_component_of_wind` by lead, and compare aggregate score movement to ensure any wind gain is not offset by accidental changes in `2m_temperature`, `geopotential_500`, or `mean_sea_level_pressure`. If iteration improves and guardrails are clean, run the standard validation comparison. Because this is output-side only, any non-wind metric movement should be treated as an implementation bug unless caused by shared residual output code.

## Citations

- Local current-incumbent artifacts: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv` and `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`, which show `10m_u_component_of_wind` skill weakening into later leads while `2m_temperature` remains the larger but riskier target.
- Local accepted baseline: `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg`, which establishes the current model and argues for preserving the accepted vertical-DSE and WTG trajectory.
- Monin, A. S. and Obukhov, A. M. (1954). "Basic laws of turbulent mixing in the surface layer of the atmosphere." Trudy Geofizicheskogo Instituta.
- Beljaars, A. C. M. and Holtslag, A. A. M. (1991). "Flux parameterization over land surfaces for atmospheric models." Journal of Applied Meteorology. https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLS%3E2.0.CO;2
- ECMWF. "IFS Documentation, Part IV: Physical Processes," surface layer and turbulent diffusion parameterization sections. https://www.ecmwf.int/en/elibrary/81147-ifs-documentation-cy48r1-part-iv-physical-processes

This is not a duplicate of the staged `bulk-aerodynamic-surface-stress` idea because it adds no prognostic drag or momentum tendency. It is not a duplicate of geostrophic or land-sea wind residual-memory proposals because it has no residual state, no learned bias memory, and no lead-dependent correction. It is also distinct from pressure-level log-law wind ideas because it uses the incumbent lowest-level diagnostic path plus static roughness blending rather than replacing the vertical interpolation scheme.

## Evaluator Notes

### 2026-06-26T03:55:51Z

Decision: move to `ready`; ranked 1 of 2 reviewed proposals. This is the only
proposal left in `ready` from this triage pass.

This is implementable now without changing the forecast contract or fixed
evaluation protocols. It is output-side only, leaves the accepted trajectory,
WTG, vertical-DSE, mass fields, T2m path, and residual corrections unchanged,
and can reuse the existing Richardson 10 m wind diagnostic plus the adapter's
static-surface loading and exact-fallback patterns. The current cached
incumbent has late `10m_u_component_of_wind` skill near or below zero with a
negative mean bias, so a fixed roughness-aware transfer factor has a plausible
path to a small aggregate gain while keeping blast radius low.

The main weakness is that this targets only one scored channel. The expected
aggregate gain is therefore narrow and should be treated as a threshold test,
not a high-ceiling mechanism. To keep the experiment fair, the Implementer
should use a single predeclared bounded roughness mapping, preserve exact
incumbent behavior when static constants are missing or invalid, include the
fixed `fast` gate even though the proposal front matter names only the
leaderboard iteration/validation flow, and avoid any coefficient tuning against
iteration or validation artifacts.
