---
schema_version: 1
slug: zonal-anomaly-tropical-wtg-mass-dse
title: Zonal-anomaly tropical WTG mass-DSE relaxation
status: staging
rank: 2
priority: medium
created_at: 2026-06-25T05:42:00Z
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

# Zonal-anomaly tropical WTG mass-DSE relaxation

## Hypothesis

The accepted WTG filter damps low-mode tropical mass-DSE anomalies, including
zonal-mean meridional thermal structure. Some of that zonal-mean structure is
real seasonal Hadley-cell and monsoon signal, while excessive longitudinal
temperature gradients are closer to the WTG error targeted by the accepted
candidate. Applying the WTG relaxation only to zonal anomalies should preserve
useful meridional mean thermal gradients while retaining damping of Walker-scale
and convectively coupled longitudinal mass-DSE errors.

## Mechanism

Add a side-by-side model, for example `dino_hsl2_mass_dse_wtg_zonanom`, derived
from `dino_hsl2_mass_dse_wtg`. Keep the accepted WTG latitude/sigma envelopes,
low total-wavenumber projection, relaxation time, cap, layer-mean neutrality,
and finite fallback policy.

Inside `_tropical_wtg_mass_dse_relaxation_step_filter`, after the accepted
low-mode mass-DSE anomaly is reconstructed in nodal space, compute a longitude
mean at each latitude and sigma layer. Relax only the difference between the
low-mode mass-DSE anomaly and that zonal mean. The resulting increment should
still be mask supported, capped in Kelvin per inner step, and layer neutral as
in the incumbent.

This keeps the tropical WTG operator state based and causal. It does not change
HSL departure geometry, mass-DSE transport algebra, weak-HS forcing, surface
fluxes, vorticity, divergence, log-surface pressure, tracers, or output
diagnostics.

## Implementation Scope

- Expected files: add one optional zonal-anomaly WTG branch in `adapter.py`,
  expose a factory in `__init__.py`, register the model key in `registry.py`,
  and add focused tests under `tests/dycore/models/dinosaur/`.
- Registry changes: add `dino_hsl2_mass_dse_wtg_zonanom`; keep the incumbent
  `dino_hsl2_mass_dse_wtg` path exactly unchanged.
- API changes: none to the dycore API, fixed evaluation protocols, target
  variables, or lead schedules.
- Tests to update: registry construction; disabled-selector equivalence;
  zonal-mean-only synthetic mass-DSE anomalies produce zero extra WTG
  increment; non-zonal low-mode anomalies retain a bounded increment; layer
  neutrality and nonfinite fallback are preserved.

## Expected Metric Movement

- Expected improvements: `geopotential_500` and `mean_sea_level_pressure` at
  medium leads if preserving zonal-mean tropical thickness improves large-scale
  balance while longitudinal anomaly damping retains the accepted WTG gain.
- Expected neutral metrics: `10m_u_component_of_wind` should remain close if
  the accepted wind improvement mainly came from Walker-scale mass-field error.
- Possible regressions: the accepted WTG gain may require damping meridional
  low modes as well as longitudinal anomalies. Preserving the zonal mean could
  reduce the incumbent's validated MSLP and wind improvement.

## Risks

- Numerical stability: low; this is a projection before the existing bounded
  WTG increment and keeps incumbent fallback checks.
- Compute cost: low; one longitude mean and subtraction per sigma layer inside
  the existing WTG filter.
- Data leakage: none; uses only the forecast state and fixed grid geometry.
- Physical plausibility: moderate; tropical WTG motivates weak free-tropospheric
  horizontal temperature gradients, but the proposed split intentionally keeps
  zonal-mean meridional structure that may be dynamically important.
- Rollback complexity: low; one selector and one factory/registry addition.

## Evaluation Plan

- Fast gate: run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_zonanom`
  and reject on nonfinite diagnostics or broken layer-neutral tests.
- Iteration gate: compare fixed iteration against cached
  `dino_hsl2_mass_dse_wtg` metrics and require at least `+0.002` primary-score
  movement with clean diagnostics and fixed guardrails.
- Validation gate: run validation only after iteration promotion and require at
  least `+0.001` improvement over the cached incumbent.
- Outcome that would falsify the hypothesis: a clean subthreshold iteration
  result would show meridional zonal-mean WTG damping is either beneficial or
  irrelevant under the fixed WeatherBench2 score; any early `geopotential_500`
  or MSLP guardrail failure would show the projection disrupts accepted balance.

## Citations

- Sobel, A. H., J. Nilsson, and L. M. Polvani, 2001: The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences, 58, 3650-3665.
  https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Gill, A. E., 1980: Some simple solutions for heat-induced tropical
  circulation. Quarterly Journal of the Royal Meteorological Society, 106,
  447-462. https://doi.org/10.1002/qj.49710644905
- Wheeler, M. C. and G. N. Kiladis, 1999: Convectively Coupled Equatorial
  Waves: Analysis of Clouds and Temperature in the Wavenumber-Frequency Domain.
  Journal of the Atmospheric Sciences, 56, 374-399.
  https://doi.org/10.1175/1520-0469(1999)056%3C0374:CCEWAO%3E2.0.CO;2
- Code reference: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  low-mode WTG masking with `coords.horizontal.to_modal` and `to_nodal`, which
  is the natural insertion point for the zonal-anomaly projection.

## Researcher Notes

This is not a duplicate of old zonal-mean theta recentering or zonal weak-HS
proposals. Those changed global thermal means or analytic Held-Suarez
relaxation on earlier incumbents. This proposal changes only the accepted
positive-time WTG mass-DSE filter and only in the zonal-mean subspace of the
tropical low-mode anomaly.

It is also distinct from active spectral smoothing, lead filtering, and
planetary-wave preservation proposals. No saved output is filtered, no forecast
protocol changes, and no additional metrics are introduced. The single question
is whether the newly accepted WTG improvement should target longitudinal
anomalies rather than all tropical low modes.

## Evaluator Notes

### 2026-06-25T05:45:55Z

Decision: move to `staging`; ranked 2 of 3 new WTG follow-up proposals.

This is a valid bounded side-by-side model-selection idea with no forecast API,
adapter, metric, or evaluation-protocol change. It stays inside the accepted
WTG helper and uses only forecast state plus fixed grid geometry, which keeps
data-leakage and rollback risk low. The mechanism is scientifically plausible:
preserving zonal-mean meridional tropical structure could avoid damping useful
Hadley/seasonal thermal gradients while still relaxing longitudinal anomaly
structure.

It is not the best next ready candidate because it weakens the accepted WTG
operator more directly than the ocean-weighted proposal. The accepted incumbent
already produced clean MSLP/wind gains with almost neutral Z500 behavior, so
removing the zonal-mean part of the low-mode correction may simply give back
too much of that benefit. Prior zonal-mean thermal-relaxation history is not a
duplicate, but it is cautionary: broader zonal-mean preservation/weak-HS ideas
have damaged fixed metrics. Keep staged for a later WTG decomposition pass if
the ocean-weighted variant fails cleanly or if scorer diagnostics implicate
zonal-mean tropical thickness as the remaining error.
