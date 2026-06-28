---
schema_version: 1
slug: mass-neutral-clipped-wtg-dse
title: Mass-neutral clipped WTG DSE closure
status: ready
rank: 1
priority: high
created_at: 2026-06-25T08:59:45Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg
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

# Mass-neutral clipped WTG DSE closure

## Hypothesis

The accepted WTG filter forms a mass-DSE anomaly, clips the resulting
temperature increment, and then removes a layerwise area-mean temperature
offset. That is stable, but after clipping and over horizontally varying
surface pressure, area-neutral temperature is not exactly the same as
mass-neutral dry-static-energy forcing. A pressure-thickness-weighted neutral
closure should preserve the accepted WTG anomaly damping while reducing small
hydrostatic thickness and surface-pressure side effects.

## Mechanism

Add a side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_mneutral`, derived from
`dino_hsl2_mass_dse_wtg`. Keep the accepted WTG latitude envelope, sigma
envelope, low-mode mask, relaxation timescale, and raw increment cap. Replace
only the post-clipping offset with a mass-weighted DSE neutralizer:

- compute the clipped WTG temperature increment exactly as the incumbent does;
- convert it to a layer mass-DSE increment with
  `layer_pressure_thickness * Cp * clipped_temperature_increment`;
- subtract the WTG-mask-weighted, quadrature-weighted layer mean of that mass
  increment, divided back by guarded `layer_pressure_thickness * Cp`;
- retain the existing finite-diagnostic fallback to the incumbent state.

This changes the conservation closure of the accepted WTG increment, not its
geographic support. The candidate should remain a purely positive-time rollout
operator.

## Implementation Scope

- Expected files: add one opt-in WTG neutralization selector in `adapter.py`;
  expose one factory through `__init__.py`; add one registry key in
  `registry.py`; add focused WTG closure and registry tests.
- Registry changes: add `dino_hsl2_mass_dse_wtg_mneutral`; keep
  `dino_hsl2_mass_dse_wtg` unchanged when the selector is disabled.
- API changes: none. No target variables, lead times, outputs, or evaluation
  protocols change.
- Tests to update: verify exact zero mass-DSE integral of the accepted mask for
  synthetic finite states, fallback on nonpositive pressure thickness, unchanged
  no-op for zero anomaly, and model/registry construction.

## Expected Metric Movement

- Expected improvements: small gains in `geopotential_500` and
  `mean_sea_level_pressure`, especially early leads, if the accepted WTG filter
  leaves a residual layer mass-DSE increment after clipping.
- Expected neutral metrics: `10m_u_component_of_wind` should stay close to the
  accepted WTG incumbent because the same broad tropical thermal anomaly is
  still damped.
- Possible regressions: if the accepted area-neutral closure is empirically
  beneficial, mass-neutral closure may weaken the WTG gain and return a
  slightly negative iteration delta.

## Risks

- Numerical stability: low. The proposal adds a weighted mean subtraction and
  keeps the incumbent caps and finite fallback.
- Compute cost: low. The extra reductions are small relative to the existing
  WTG DSE diagnostics.
- Data leakage: none. The closure uses only forecast state, pressure thickness,
  constants, and fixed quadrature weights.
- Physical plausibility: moderate to high. Dry static energy and hydrostatic
  thickness are mass-weighted column quantities, so the compensating correction
  is closer to the target invariant than an area-mean temperature offset.
- Rollback complexity: low. The change is a side-by-side selector.

## Evaluation Plan

- Fast gate: run `uv run pytest` plus `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_mneutral`.
- Iteration gate: run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_mneutral --workers <worker_count>` and compare against compatible cached incumbent metrics for `dino_hsl2_mass_dse_wtg`.
- Validation gate: run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_mneutral --workers <worker_count>` only after iteration promotion.
- Outcome that would falsify the hypothesis: a subthreshold iteration delta
  with clean guardrails would show that the accepted WTG skill does not depend
  on this residual mass-DSE closure; an MSLP or Z500 guardrail failure would
  show that the weighted neutralizer perturbs balanced thickness too much.

## Citations

- Chavas, D. R. and A. Peters, 2023: Static Energy Deserves Greater Emphasis
  in the Meteorology Community. Bulletin of the American Meteorological
  Society. https://doi.org/10.1175/BAMS-D-22-0013.1
- Sobel, A. H., J. Nilsson, and L. M. Polvani, 2001: The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences. https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Local code reference:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` defines
  `nodal_sigma_layer_pressure_thickness` and mass-weighted DSE transport;
  `adapter.py` applies the accepted WTG filter.
- Local history reference:
  `.logbook/history/2026-06-25_06-00-55_ocean-weighted-tropical-wtg-mass-dse/decision.md`.

## Researcher Notes

This is not a repeat of staged `area-neutral-mass-dse-hsl` or
`column-neutral-mass-dse-increment`, which act on the HSL thermal transport
tendency. This proposal touches only the accepted WTG relaxation closure after
temperature clipping. It directly incorporates the recent lesson by preserving
the accepted WTG support and adding a compensating mass-DSE mechanism instead
of narrowing tropical columns.

## Evaluator Notes

### 2026-06-25T09:05:19Z

Decision: move to `ready`; ranked 1 of 3 new WTG follow-up proposals.

This is the strongest next model-selection idea. It is exactly one bounded
side-by-side candidate, preserves the fixed forecast contract and evaluation
protocols, and derives directly from the current `dino_hsl2_mass_dse_wtg`
incumbent. The recent ocean-weighted WTG rejection argues against simply
narrowing accepted support; this proposal keeps the accepted tropical and
vertical mask intact and instead tests whether the post-clipping compensation
should conserve the same layer mass-DSE quantity the filter damps.

The implementation surface is small: one neutralization selector, one registry
entry, factory/export wiring, and focused closure/fallback tests. Compute cost
should be close to the incumbent because it adds reductions inside the existing
WTG diagnostic path rather than another rollout pass or another hydrostatic
diagnostic. The scientific basis is adequate for a low-cost probe: WTG sources
support weak tropical free-tropospheric temperature gradients, and the static
energy literature supports treating dry static energy as the relevant
thermodynamic invariant.

Main risk is signal size. Prior conservation projections in the mass-DSE/HSL
neighborhood have often been safe but subthreshold, and the accepted
area-neutral WTG closure may already be empirically balanced. Still, among the
three new proposals, this has the best cost-risk profile and the cleanest path
to a rollbackable side-by-side model.
