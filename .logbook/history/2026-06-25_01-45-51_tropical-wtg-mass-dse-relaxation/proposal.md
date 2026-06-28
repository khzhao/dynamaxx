---
schema_version: 1
slug: tropical-wtg-mass-dse-relaxation
title: Tropical WTG Relaxation for Mass-DSE Thermal Anomaly
status: ready
created_at: 2026-06-25T01:38:28Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Tropical WTG Relaxation for Mass-DSE Thermal Anomaly

## Hypothesis

The accepted incumbent improved thermal transport by advecting layer-mass
weighted dry static energy, but the free tropical troposphere can still carry
unrealistic horizontal dry-static-energy gradients because the dry dycore lacks
fast convective and gravity-wave adjustment. A weak-temperature-gradient (WTG)
relaxation applied only to tropical free-tropospheric mass-DSE anomaly should
reduce large-scale tropical thickness error and downstream mass-field drift
without changing surface fluxes, humidity physics, or pressure continuity.

## Mechanism

Add one side-by-side candidate, for example `dino_hsl2_mass_dse_wtg`, derived
from `dino_hsl2_mass_dse`. During positive-time rollout only, diagnose the same
dry static energy and sigma-layer pressure thickness already used by the
incumbent mass-DSE HSL path. Apply a fixed tropical latitude envelope, a
free-tropospheric sigma envelope, and a low-mode projection to the mass-DSE
anomaly. Relax that masked anomaly toward its tropical area-weighted layer mean
on a predeclared multi-day time scale, then subtract the global layer mean of
the induced temperature tendency so the filter does not add net layer heat.

The candidate changes only the temperature tendency or a post-step
temperature-variation filter. It leaves vorticity, divergence, log surface
pressure, tracers, DFI initialization, weak-HS coefficients, ocean sensible heat
flux, HSL departure geometry, output diagnostics, and evaluation inputs
unchanged. If any pressure, DSE, mask, or tendency diagnostic is nonfinite, the
candidate must fall back to the incumbent state or incumbent tendency.

## Implementation Scope

- Expected files: add an opt-in selector and helper in `adapter.py` or
  `primitive_equations.py`, register the side-by-side factory in
  `registry.py`, and add focused tests under `tests/dycore/models/dinosaur/`.
- Registry changes: add `dino_hsl2_mass_dse_wtg`; keep
  `dino_hsl2_mass_dse` byte-for-byte equivalent when the flag is disabled.
- API changes: none to `ForecastInput`, `WeatherState`, output variables, lead
  times, or evaluation protocols.
- Tests to update: registry creation; disabled-flag incumbent equivalence;
  finite smoke forecast; exact no-op outside the tropical/free-tropospheric
  mask; layer-mean-neutral tendency on synthetic fields; fallback on nonfinite
  DSE or pressure thickness.

## Expected Metric Movement

- Expected improvements: `geopotential_500` and `mean_sea_level_pressure` at
  medium leads if tropical thickness anomalies are a remaining source of broad
  mass-field phase error; possibly `2m_temperature` in tropical ocean columns
  through improved lower-free-tropospheric temperature evolution.
- Expected neutral metrics: `10m_u_component_of_wind` should remain close
  because momentum, Coriolis splitting, drag, and surface wind diagnostics are
  unchanged.
- Possible regressions: tropical waves and convectively coupled temperature
  gradients are real forecast signal; over-relaxing them can flatten useful
  structure and degrade `geopotential_500` or early `mean_sea_level_pressure`.

## Risks

- Numerical stability: moderate; the operator is thermodynamic and bounded, but
  it must not run inside time-reversed DFI and must guard layer pressure
  thickness.
- Compute cost: low to moderate; one or two nodal diagnostics, one low-mode
  projection, and layerwise reductions per step.
- Data leakage: none; uses only forecast state, fixed latitude/sigma masks, and
  predeclared constants.
- Physical plausibility: moderate to high; WTG is a recognized tropical
  large-scale balance, but this is a dry reduced implementation without moist
  convection.
- Rollback complexity: low; one selector, one factory, one registry entry, and
  focused tests.

## Evaluation Plan

- Fast gate: run the fixed fast protocol for `dino_hsl2_mass_dse_wtg`; reject
  on nonfinite diagnostics, a failed fallback, or any early mass-field guardrail
  warning.
- Iteration gate: compare fixed iteration against cached `dino_hsl2_mass_dse`
  and require at least `+0.002` primary-score movement with clean guardrails.
- Validation gate: run fixed validation only after iteration promotion and
  require at least `+0.001` improvement.
- Outcome that would falsify the hypothesis: clean iteration below the
  promotion threshold, or any early `mean_sea_level_pressure` /
  `geopotential_500` guardrail failure, would show the simplified dry WTG
  relaxation is not a useful missing-balance term for this incumbent.

## Citations

- Sobel, A. H. and C. S. Bretherton, 2000: Modeling Tropical Precipitation in a
  Single Column. Journal of Climate, 13, 4378-4392.
  https://doi.org/10.1175/1520-0442(2000)013%3C4378:MTPIAS%3E2.0.CO;2
- Sobel, A. H., J. Nilsson, and L. M. Polvani, 2001: The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences, 58, 3650-3665.
  https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Raymond, D. J. and X. Zeng, 2005: Modelling tropical atmospheric convection
  in the context of the weak temperature gradient approximation. Quarterly
  Journal of the Royal Meteorological Society, 131, 1301-1320.
  https://doi.org/10.1256/qj.03.97

## Researcher Notes

This is not a direct variant of the recent failed DSE sigma initialization,
finite-volume mass-DSE remap, or DSE horizontal diffusion attempts. It does not
change initialization, remap order, diffusion, or the HSL departure operator;
it adds a geographically and vertically targeted tropical balance tendency on
the accepted mass-DSE scalar.

It is also not another weak-Held-Suarez or radiation proposal. The target is a
forecast-state WTG anomaly constraint, not a relaxation toward the analytic HS
equilibrium, not a solar/longwave heat source, and not a moisture or saturation
closure. The closest active files are thermal IAU and omega-spinup ideas, but
those import analyzed increments or analyzed vertical motion. This candidate
uses only the current forecast state and tests whether the tropical dry
free-tropospheric DSE gradient itself is a remaining score-scale error source.

## Evaluator Notes

### 2026-06-25T01:43:53Z

Decision: move to `ready`; ranked 1 of 3 current proposals. Recommendation:
best implementable candidate from this triage pass, if the Orchestrator wants a
single next implementation target.

The proposal has the clearest combination of mechanism, bounded implementation,
and novelty relative to the current `dino_hsl2_mass_dse` incumbent. Literature
supports the physical premise that tropical free-tropospheric horizontal
temperature gradients are weak under WTG balance, while local history shows
that the accepted mass-DSE path is the current high-leverage thermal transport
surface. This candidate uses that surface directly instead of adding a new
surface flux, changing sigma initialization, changing DSE remap algebra, or
retuning Held-Suarez relaxation.

Source inspection confirms the implementation can be kept narrow:
`PrimitiveEquationsSigma.temperature_tendency_potential_temperature_form`
already diagnoses dry static energy anomaly and guarded layer pressure
thickness for the incumbent mass-DSE branch. A side-by-side option can add a
positive-time-only, tropical/free-tropospheric, layer-mean-neutral mass-DSE
relaxation and fall back to the incumbent tendency on nonfinite diagnostics.
This is lower blast radius than the other two proposals because it changes only
a bounded thermodynamic tendency and does not edit vorticity, divergence, log
surface pressure, output variables, scoring protocols, or input channels.

The expected signal is still uncertain. WTG is a moist tropical balance, and a
dry DSE relaxation can overdamp real convectively coupled waves or flatten
useful tropical thickness structure. The implementer should keep constants
fixed before scoring, exclude DFI/time-reversed steps, cap increments, preserve
global/layer mean neutrality, prove exact no-op outside the mask, and avoid
turning this into a coefficient sweep.
