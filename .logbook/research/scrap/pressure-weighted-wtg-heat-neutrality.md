---
schema_version: 1
slug: pressure-weighted-wtg-heat-neutrality
title: Pressure-Weighted WTG Heat Neutrality
status: scrap
created_at: 2026-06-27T01:48:57Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Pressure-Weighted WTG Heat Neutrality

## Hypothesis

The accepted tropical WTG mass-DSE relaxation changes temperature through a
mass-DSE anomaly but removes the post-clipping layer heat offset with horizontal
area weights only. In sigma coordinates, the layer heat content is proportional
to layer pressure thickness, so an area-neutral temperature increment can still
leave a nonzero mass-weighted thermal increment when surface pressure varies.
Replacing the offset calculation with pressure-thickness weights should make the
WTG correction better aligned with the mass-DSE variable that it relaxes, while
preserving the accepted WTG mask, low-mode projection, ramped vertical-DSE path,
and deterministic forecast contract.

## Mechanism

Register a side-by-side candidate named
`dino_hsl2_mass_dse_wtg_vdse_ramp_pwwtg`. Preserve the accepted incumbent
factory and add one selector that changes only the heat-neutrality correction
inside `_tropical_wtg_mass_dse_relaxation_step_filter`.

For the candidate:

- keep the current tropical latitude envelope, sigma envelope, low-mode mask,
  WTG relaxation fraction, and per-step temperature cap;
- after clipping the raw WTG temperature increment, compute the layer offset
  with weights proportional to `quadrature_weights * layer_pressure_thickness`
  inside the existing WTG support;
- subtract that offset through the same WTG mask so the pressure-thickness
  weighted layer heat increment is zero, or fall back to the incumbent
  area-weighted offset when pressure thickness is nonfinite or degenerate;
- leave vorticity, divergence, log surface pressure, humidity tracers, forecast
  outputs, evaluation protocols, and target variables unchanged.

This is distinct from the recent rejected WTG support variants: it does not
weaken, taper, shift, or humidity-gate where WTG acts. It changes only the
conservation weighting of the existing WTG thermal offset.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dino_hsl2_mass_dse_wtg_vdse_ramp_pwwtg`.
- API changes:
  - None.
- Tests to update:
  - Factory parity with `dino_hsl2_mass_dse_wtg_vdse_ramp` except for the new
    selector and name.
  - Unit test showing the candidate preserves pressure-thickness weighted layer
    heat neutrality after clipping.
  - Unit test showing fallback to incumbent behavior for nonfinite or
    degenerate layer pressure thickness.
  - Registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500`, if small mass-weighted
    thermal imbalances from WTG are feeding pressure/thickness errors.
  - `2m_temperature` at early-to-medium leads through better lower-tropospheric
    heat-content consistency.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because wind diagnostics and momentum tendencies
    are unchanged.
- Possible regressions:
  - If the existing area-neutral offset accidentally compensates surface-pressure
    biases, the mass-weighted version could reduce that compensation.
  - The effect may be small because pressure-thickness variations are moderate
    inside the tropical WTG support.

## Risks

- Numerical stability:
  - Low. The candidate remains bounded by the existing temperature-increment cap
    and finite diagnostics.
- Compute cost:
  - Negligible. It adds a few reductions over arrays already available inside
    the WTG filter.
- Data leakage:
  - None. The filter uses only forecast state and fixed weights.
- Physical plausibility:
  - High. Heat-content conservation in pressure/sigma coordinates should be
    pressure-thickness weighted rather than pure area weighted.
- Rollback complexity:
  - Low. Remove one selector, one helper path if added, one factory/export,
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_pwwtg`
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_pwwtg --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure against the cached incumbent.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_pwwtg --workers 4`
    only after iteration promotion.
  - Support requires validation delta at least `+0.001`, clean diagnostics, and
    fixed guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that WTG
    heat-neutrality weighting is not a material remaining error source.

## Citations

- Sobel, A. H., Nilsson, J., and Polvani, L. M. 2001. The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences, 58, 3650-3665.
  https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review, 109, 758-766.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Arakawa, A. and Lamb, V. R. 1977. Computational design of the basic dynamical
  processes of the UCLA general circulation model. Methods in Computational
  Physics, 17, 173-265.
  https://doi.org/10.1016/B978-0-12-460817-7.50009-4

## Researcher Notes

Recent rejected WTG variants changed the spatial or temporal support of the WTG
relaxation and produced clean but negative primary deltas. This proposal keeps
the accepted support fixed and targets a narrower conservation mismatch between
the mass-DSE mechanism and the area-weighted heat offset. It should be cheaper
and more diagnostic than another WTG mask experiment.

## Evaluator Notes

### 2026-06-27T01:52:04Z

Decision: move to `scrap`.

This is scientifically coherent, but it is too close to the already implemented
and rejected `mass-neutral-clipped-wtg-dse` experiment. That candidate changed
the WTG post-clipping conservation closure toward pressure-thickness neutrality
and scored `-0.2589338868909309` versus the then-incumbent
`-0.25851235493825614`, an iteration delta of `-0.0004215319526747474`.
The decision record explicitly concluded that the accepted area-neutral WTG
closure was empirically better and that future WTG closure refinements need a
larger documented error mode to justify another iteration slot.

The current proposal keeps WTG support fixed, which avoids the recent negative
evidence from support tapering and moisture-convergence gating. However, its
expected signal is another small conservation-weighting correction inside a
WTG operator whose closure variant has already been tested and rejected under
fixed gates. It is unlikely to clear the `+0.002` iteration threshold against
the stronger `dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent.
