---
schema_version: 1
slug: frozen-passive-humidity-geopotential
title: Use Frozen Passive Humidity for Geopotential Diagnosis
status: scrap
created_at: 2026-06-18T04:29:16Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split
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

# Use Frozen Passive Humidity for Geopotential Diagnosis

## Hypothesis

The incumbent is a dry dynamical model: humidity is not used in the primitive
equation dynamics, but specific humidity is still advected as a passive tracer
and then used in virtual-temperature geopotential output. Prior history gives
two important constraints. Removing humidity from geopotential diagnosis was
bad, so the virtual-temperature correction matters. Passive humidity positivity
and DFI bypass experiments were effectively neutral, so small tracer-cleanup
changes do not matter by themselves.

The remaining issue may be that passively advected humidity is an incomplete
proxy for real moisture evolution and can contaminate geopotential diagnosis at
longer leads, while the initial analyzed humidity still provides a useful
virtual-temperature correction. Freezing the initialized sigma humidity only for
geopotential diagnosis tests this middle path: retain moist virtual thickness,
but avoid trusting dry passive humidity transport as forecast moisture physics.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split_frozen_q_z`.
Preserve the incumbent prognostic state, DFI, weak Held-Suarez forcing, exact
Coriolis split, near-surface residual correction, target variables, and fixed
protocols.

For each initial condition:

- keep the initialized sigma specific humidity field produced by the incumbent
  pressure-to-sigma conversion;
- run the forecast with the same passive humidity tracer behavior as the
  incumbent, so the trajectory and optional humidity outputs remain comparable;
- when computing `get_geopotential_on_sigma` for output packing, use the stored
  initialized sigma humidity broadcast over lead time instead of the advected
  passive humidity tracer;
- if humidity is absent, nonfinite, or shape-incompatible, fall back exactly to
  the incumbent path;
- leave pressure-level temperature, wind, humidity outputs, surface pressure,
  MSLP, 2 m temperature, and 10 m wind diagnostics unchanged.

This proposal does not train a moisture model, change the forecast contract, or
use future truth. It is a bounded diagnostic choice for the one output quantity
where humidity enters the dry adapter.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split_frozen_q_z`.
- API changes:
  - None. Forecast inputs, output variable names, output shapes, and fixed
    protocols remain unchanged.
- Tests to update:
  - Unit-test that geopotential diagnosis uses the supplied frozen humidity when
    the option is enabled.
  - Verify output humidity channels, if requested, still come from the trajectory
    rather than the diagnostic frozen field.
  - Verify missing humidity and nonfinite frozen humidity fall back to the
    incumbent geopotential path.
  - Verify the candidate factory preserves all incumbent flags, including exact
    Coriolis splitting.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium and long leads if dry passive humidity
    transport is degrading virtual-temperature thickness diagnosis.
  - Small primary-score improvement is possible if Z500 gains are broad and
    near-surface channels remain neutral.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and
    `mean_sea_level_pressure` should be effectively unchanged because their
    output paths and prognostic fields are unchanged.
- Possible regressions:
  - If passive humidity advection is closer to real humidity than persistence,
    Z500 may regress.
  - The effect size may be below the iteration threshold because only one target
    variable is directly affected.

## Risks

- Numerical stability:
  - Low. This is output-only and has explicit fallback behavior.
- Compute cost:
  - Low. It stores one initialized sigma humidity field per initial condition and
    broadcasts it during output packing.
- Data leakage:
  - Low. It uses only the same-time initial analysis already consumed by the
    incumbent.
- Physical plausibility:
  - Moderate. Virtual temperature is physically required for hydrostatic
    thickness, but freezing humidity is an approximation. The justification is
    that this dry model has no humidity physics, so passive humidity advection
    may be less defensible than initial-analysis persistence for this diagnostic.
- Rollback complexity:
  - Low. Remove one adapter flag, one output-packing argument, one factory/export,
    one registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split_frozen_q_z`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split_frozen_q_z --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day 1-5 RMSE guardrail failure, and no variable+lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split_frozen_q_z --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that passive
    humidity transport is not a material remaining Z500 error source. Any Z500
    guardrail failure would show that the advected passive tracer is preferable
    to initial humidity persistence for geopotential diagnosis.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` passes
  trajectory humidity to `primitive_equations.get_geopotential_on_sigma` during
  output packing while `use_humidity_in_dynamics` remains false in the incumbent.
- History: `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
  rejected removing humidity from geopotential reconstruction because it damaged
  day-1 `geopotential_500`.
- History: `.logbook/history/2026-06-17_12-29-40_passive-humidity-dfi-bypass/decision.md`
  found that preserving passive humidity through DFI changed fixed metrics only
  at near-roundoff scale, so this proposal targets the output use of humidity
  instead.
- AMS Glossary of Meteorology. Hypsometric equation.
  https://glossary.ametsoc.org/wiki/hypsometric-equation/
- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
  Survey, second edition. Academic Press.
  https://doi.org/10.1016/C2009-0-00034-8
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not another moist-dynamics proposal. It does not use humidity in
pressure-gradient tendencies, vorticity tendencies, temperature tendencies, or
weak Held-Suarez forcing, and it does not add latent heating or saturation
adjustment. Those families have strong negative evidence.

It is also not a duplicate of `dry-consistent-geopotential-diagnostic`, because
that rejected candidate removed humidity from geopotential. This proposal keeps
the virtual-temperature correction but uses the same-time initialized humidity
instead of dry-passively advected humidity for geopotential diagnosis only.

## Evaluator Notes

### 2026-06-18T04:36:51Z

Decision: move to `scrap`.

Source inspection confirms the incumbent dry rollout carries specific humidity
as a passive tracer and uses the trajectory humidity in
`primitive_equations.get_geopotential_on_sigma` during output packing, so this
is technically feasible and not an exact duplicate of the rejected dry
geopotential diagnostic. The scientific case is still too weak for the current
queue. Prior history shows that removing humidity from geopotential caused a
large day-1 `geopotential_500` guardrail failure, but passive-humidity
positivity and DFI-preservation experiments were near-roundoff, while active
moist feedback proposals were strongly negative. That evidence supports keeping
the virtual-temperature correction, not replacing passive advection with
persistence.

The proposal would directly affect only `geopotential_500`, has no read-only
evidence that initialized humidity persistence beats the dry passive tracer at
forecast leads, and could easily produce a small or adverse long-lead Z500
movement below the primary-score gate. With a stronger Coriolis follow-up and a
more physically grounded hypsometric Z diagnostic available, this is rejected as
a low-evidence humidity-only diagnostic variant.
