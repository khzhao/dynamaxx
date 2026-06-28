---
schema_version: 1
slug: layer-mass-weighted-dse-hsl
title: Transport Layer-Mass-Weighted Dry Static Energy with HSL2
status: ready
created_at: 2026-06-23T18:04:37Z
author_role: Researcher
target_model: dino_hsl2_theta_dse_hsl
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

# Transport Layer-Mass-Weighted Dry Static Energy with HSL2

## Hypothesis

The accepted incumbent shows that horizontal transport of dry static energy is
the right thermodynamic invariant to test after HSL2 theta transport. The
current implementation transports a layerwise dry-static-energy anomaly per
unit mass, then converts the horizontal tendency back to temperature through
`c_p`. In sigma coordinates, however, horizontal layer mass is proportional to
surface pressure times sigma thickness. Transporting dry static energy without
that local mass factor can underweight high-pressure columns and overweight
low-pressure columns during horizontal advection, especially for MSLP and Z500
phase errors.

The proposal is to keep the accepted HSL2 departure and fallback path but apply
it to layer-mass-weighted dry-static-energy anomalies. This tests whether the
remaining error is mass weighting of the accepted thermal invariant, not another
trajectory or pressure-work replacement.

## Mechanism

Register a side-by-side model such as `dino_hsl2_theta_mass_dse_hsl` that
inherits all options from `dino_hsl2_theta_dse_hsl`.

For the candidate only:

- diagnose nodal surface pressure and layer pressure thickness
  `delta_p = p_s * delta_sigma` in the current sigma coordinate;
- compute the incumbent dry-static-energy anomaly
  `s' = c_p T + Phi - mean_layer(c_p T + Phi)`;
- form the layer-mass-weighted scalar `delta_p * s'`;
- use the existing accepted HSL2 midpoint departure and bilinear remap to
  estimate the horizontal tendency of `delta_p * s'`;
- divide the resulting tendency by a finite guarded local `delta_p` before the
  existing `1 / c_p` conversion to temperature tendency;
- fall back exactly to `dino_hsl2_theta_dse_hsl` if pressure thickness, the
  weighted scalar, or converted tendencies are nonfinite.

The log-surface-pressure tendency remains the incumbent tendency. This is not a
flux-form pressure-continuity replacement and does not change forecast outputs,
lead times, target variables, or evaluation metrics.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add a new side-by-side model factory and registry key, leaving the incumbent
    key unchanged.
- API changes:
  - None.
- Tests to update:
  - Verify the default and incumbent DSE-HSL tendencies are unchanged when the
    option is disabled.
  - Verify mass weighting uses positive finite `delta_p` and finite-fallbacks to
    the incumbent DSE-HSL tendency.
  - Verify the candidate preserves output variables and registration.
  - Verify no metric-like source test embeds fixed evaluation acceptance
    thresholds.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500`, especially medium leads,
    if local layer mass weighting reduces thermal-thickness phase error.
  - `2m_temperature` if lower-column thermal transport currently drifts more in
    high-pressure columns than low-pressure columns.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because momentum tendencies and the 10 m wind
    diagnostic remain on the incumbent path.
- Possible regressions:
  - Short-lead MSLP if adding the mass factor without changing log-pressure
    transport introduces a new thermal/mass inconsistency.
  - Aggregate score could be neutral if the accepted DSE-HSL improvement already
    captures most useful thermal invariant information.

## Risks

- Numerical stability:
  - Moderate. The HSL trajectory is unchanged, but surface-pressure weighting
    enters every thermal horizontal tendency.
- Compute cost:
  - Low to moderate. The candidate adds one pressure-thickness diagnostic and
    one extra multiply/divide around the existing HSL remap.
- Data leakage:
  - None. It uses only prognosed state variables and fixed sigma-coordinate
    constants.
- Physical plausibility:
  - Good for a sigma-coordinate mass-weighted transport test, but incomplete
    because the mass continuity equation is deliberately unchanged.
- Rollback complexity:
  - Low. Remove one flag, helper branch, model factory/export, registry key, and
    tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_theta_mass_dse_hsl`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_theta_mass_dse_hsl --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure against the cached incumbent.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_theta_mass_dse_hsl --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, or any early MSLP/Z500
    guardrail failure, would show that the accepted unweighted DSE-HSL tendency
    is already the better empirical balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  contains the accepted `nodal_dry_static_energy_anomaly` and
  `horizontal_semilagrangian_theta_transport` paths.
- Dynamaxx history:
  `.logbook/history/2026-06-23_11-22-34_dry-static-energy-hsl-transport/decision.md`
  accepted DSE-HSL with iteration delta `+0.045455173259026704` and validation
  delta `+0.04175545761164218`.
- Dynamaxx history:
  `.logbook/history/2026-06-23_14-39-53_moist-static-energy-hsl-transport/decision.md`
  rejected passive-humidity MSE-HSL as effectively neutral, so this proposal
  keeps the dry invariant and changes mass weighting instead.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Thuburn, J. 2008. Some Conservation Issues for the Dynamical Cores of NWP
  and Climate Models. Journal of Computational Physics, 227, 3715-3730.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is not a near-duplicate of the latest rejected MSE-HSL candidate: it adds
no humidity, latent energy, or passive-tracer coupling. It is also distinct from
the rejected flux-form surface-pressure continuity experiment, because it does
not replace the log-pressure tendency or the fixed evaluation contract. It is a
narrow follow-up to the accepted DSE-HSL mechanism that tests whether the
accepted scalar should be weighted by sigma-layer mass.

## Evaluator Notes

### 2026-06-23T18:45:00Z

Decision: move to `ready`; ranked 1 of 3 current proposals.

This is the clearest next experiment because it is a narrow, contract-compatible
follow-up to the accepted `dino_hsl2_theta_dse_hsl` incumbent. The accepted
DSE-HSL candidate produced large, validated iteration and validation gains, and
the latest MSE-HSL follow-up was stable but effectively neutral. That evidence
favors probing the dry-energy transport mechanism itself rather than adding new
moisture, pressure-work, or trajectory changes.

The proposal has a specific physical and numerical mechanism: in sigma
coordinates, horizontal thermal transport can be inconsistent if the scalar
being transported ignores local layer pressure thickness. Applying the existing
HSL2 departure to `delta_p * s'`, then dividing by a guarded local `delta_p`,
is a low-surface-area way to test whether the accepted dry-static-energy
anomaly should be mass weighted. It keeps the forecast contract unchanged,
leaves log-surface-pressure and momentum tendencies on the incumbent path, and
has a clean rollback boundary through one selector, factory, registry entry,
and focused tests.

Main risk is a new thermal/mass inconsistency because the pressure-continuity
equation is deliberately unchanged. That risk is acceptable for `ready` because
the fallback can be exact, the implementation is local to the accepted
thermodynamic transport branch, and the expected signal should show up in
MSLP/Z500 guardrails early if the hypothesis is wrong. This is preferable to
the current momentum and weak-HS proposals for the immediate ready queue.
