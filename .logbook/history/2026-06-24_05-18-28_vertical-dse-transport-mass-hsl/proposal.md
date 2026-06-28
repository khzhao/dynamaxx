---
schema_version: 1
slug: vertical-dse-transport-mass-hsl
title: Use Dry Static Energy for Vertical Thermal Transport
status: ready
created_at: 2026-06-24T05:12:55Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Dry Static Energy for Vertical Thermal Transport

## Hypothesis

The incumbent `dino_hsl2_mass_dse` horizontally transports a layer-mass-weighted
dry-static-energy anomaly, but the vertical thermal transport still follows the
older theta vertical tendency path. The accepted DSE results suggest that `Cp T
+ Phi` is the more useful thermal invariant for this sigma core. A remaining
imbalance may come from mixing DSE horizontal transport with theta vertical
transport before the adiabatic pressure-work term is added.

Using dry static energy for the vertical thermal-advection part should improve
hydrostatic column coherence without changing HSL departure geometry,
pressure-thickness tendencies, log-surface-pressure continuity, or the
DSE-to-temperature conversion that the current incumbent empirically supports.

## Mechanism

Register a side-by-side candidate such as `dino_mass_dse_vdse` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- preserve the accepted mass-DSE horizontal HSL branch exactly;
- compute the same nodal dry-static-energy anomaly already used by the DSE-HSL
  path;
- compute the vertical tendency of that DSE anomaly with the existing centered
  `sigma_dot_full` vertical-advection operator;
- convert the DSE vertical tendency to temperature through `1 / Cp` and use it
  in place of the incumbent theta-derived vertical thermal transport;
- keep the incumbent adiabatic tendency, pressure tendency, momentum tendency,
  weak-HS forcing, surface residuals, ocean bulk heat flux, and output packing
  unchanged;
- fall back exactly to `dino_hsl2_mass_dse` if DSE, sigma-dot, converted
  vertical tendency, or selected modal temperature tendency is nonfinite.

This is not a vertical-advection suppression or upwind replacement. It keeps the
same vertical velocity and stencil and changes only the scalar supplied to the
vertical thermal transport inside the accepted mass-DSE thermal branch.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
- Registry changes:
  - Add one side-by-side factory and registry key for `dino_mass_dse_vdse`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, and protocols
    stay fixed.
- Tests to update:
  - Verify the default and `dino_hsl2_mass_dse` paths are unchanged when the
    selector is disabled.
  - Verify zero `sigma_dot` leaves the candidate equal to the incumbent
    mass-DSE thermal tendency.
  - Verify synthetic finite DSE vertical tendencies are converted through `Cp`.
  - Verify nonfinite diagnostics fall back to the incumbent mass-DSE path.
  - Verify candidate registration and unchanged output variables.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` if mixed horizontal DSE
    and vertical theta transport is a remaining thickness-balance error.
  - `2m_temperature` at medium leads if lower-column vertical thermal transport
    becomes more consistent with the accepted DSE horizontal transport.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because momentum and the 10 m diagnostic remain
    on the incumbent path except through balanced mass-field feedback.
- Possible regressions:
  - The incumbent theta vertical transport may be a useful empirical
    compensation for the sigma pressure-work split.
  - DSE vertical transport can alter upper-column thermal structure and show up
    as early Z500 or MSLP regression.

## Risks

- Numerical stability:
  - Moderate. The vertical advection operator is unchanged, but the scalar in a
    core thermal tendency changes every inner step.
- Compute cost:
  - Low. DSE is already diagnosed for the horizontal branch; this adds one
    vertical-advection call and local algebra.
- Data leakage:
  - None. The mechanism uses only current forecast state and fixed model
    constants.
- Physical plausibility:
  - High as a dry-adiabatic scalar-consistency test, with the caveat that the
    pressure-work term remains the incumbent sigma-coordinate approximation.
- Rollback complexity:
  - Low. Remove one selector, one branch, one factory/export, one registry key,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_mass_dse_vdse`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_mass_dse_vdse --workers 4`
  - Support requires primary delta at least `+0.002` against cached
    `dino_hsl2_mass_dse`, clean diagnostics, and no fixed RMSE guardrail
    failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_mass_dse_vdse --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show that the
    incumbent theta vertical transport is not a material remaining error source.
    Any early Z500 or MSLP guardrail failure would show DSE vertical transport
    disrupts the accepted sigma balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  contains the accepted `use_layer_mass_weighted_dse_hsl_transport` branch and
  the existing `nodal_temperature_vertical_tendency` / theta vertical path.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted `dino_hsl2_mass_dse` with iteration delta `+0.005725334705943053`
  and validation delta `+0.00546393735603079`.
- Dynamaxx history:
  `.logbook/history/2026-06-16_20-56-11_vertical-advection-suppression/decision.md`
  showed that removing vertical advection is unstable, so this proposal
  preserves vertical advection and changes only its thermal scalar.
- Holton, J. R. and Hakim, G. J. 2012. *An Introduction to Dynamic
  Meteorology*, fifth edition. Academic Press.
- Durran, D. R. 2010. *Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics*, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2

## Researcher Notes

This is distinct from staged `smoothed-sigma-dot-vertical-advection`,
`theta-upwind-vertical-advection`, and `upwind-vertical-advection-rollout`.
Those proposals change the advective vertical velocity or stencil. This one
keeps the incumbent centered vertical-advection operator and tests scalar
consistency with the now-accepted DSE horizontal transport.

It also avoids the two latest negative mechanisms: it does not compute a
pressure-thickness product-rule correction and does not invert the DSE tendency
through a hydrostatic operator. The risk is the older vertical-transport
negative evidence, so the proposal is framed as a narrow scalar substitution
with exact incumbent fallback rather than a vertical-dynamics rewrite.

## Evaluator Notes

### 2026-06-24T05:16:50Z

Decision: move to `ready`; rank 1 of 3 new proposals and the only current
ready recommendation.

This is the strongest next experiment because it tests a precise inconsistency
introduced by the accepted incumbent: horizontal thermal transport now uses
layer-mass-weighted dry static energy, while the vertical thermal transport
still uses the older theta-derived scalar. The source has a narrow hook at the
mass-DSE thermal branch, the implementation can be side-by-side with exact
incumbent fallback, and the expected cost is only one additional vertical
advection call plus local algebra.

The prior vertical-advection suppression failure is important negative
evidence, but this proposal does not remove vertical transport or change the
vertical velocity/stencil. It also avoids both latest rejected mechanisms:
`pressure-thickness-corrected-mass-dse-hsl` broadly degraded the primary score
by `-0.006172261163569502`, and `hydrostatic-inverted-mass-dse-hsl` degraded by
`-0.030209299275616164` with an early MSLP guardrail failure. This proposal is
less aggressive than either because it preserves pressure thickness,
hydrostatic conversion, momentum, pressure tendency, forcing, filters, and
outputs.

Ranked recommendation: implement first if the Orchestrator wants the next
candidate from this proposal batch. Keep the fixed fast and iteration gates
strict; any early Z500/MSLP guardrail issue should be treated as evidence that
theta vertical transport is part of the accepted sigma-coordinate balance
rather than a remaining inconsistency.
