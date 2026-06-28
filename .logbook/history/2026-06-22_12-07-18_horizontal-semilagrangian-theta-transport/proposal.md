---
schema_version: 1
slug: horizontal-semilagrangian-theta-transport
title: Apply Horizontal Semi-Lagrangian Theta Transport
status: ready
created_at: 2026-06-22T12:02:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Apply Horizontal Semi-Lagrangian Theta Transport

## Hypothesis

The incumbent already improved thermodynamics by transporting potential
temperature, but the horizontal scalar transport still uses the Eulerian
spectral product form. A single positive-time candidate that semi-Lagrangian
advects only the dry theta anomaly horizontally can reduce phase and Courant
errors in baroclinic thermal structures while preserving the accepted
semi-implicit gravity-wave damping, Coriolis split, vertical transport,
surface residuals, and ocean bulk sensible heat flux.

## Mechanism

Add one side-by-side candidate with short alias `dino_hsl_theta`. For the
candidate only, replace the horizontal part of the theta-anomaly tendency with a
bounded backward-departure remap:

- diagnose nodal horizontal wind from the current vorticity/divergence state;
- compute one-step departure points on the sphere using the existing inner-step
  size and a conservative displacement cap;
- bilinearly interpolate the current theta anomaly to those departure points
  and convert the implied increment back to a modal temperature tendency;
- keep the incumbent centered vertical advection, pressure-work term,
  log-surface-pressure tendency, momentum tendencies, DFI, weak-HS forcing, theta
  mean recentering, diffusion, residuals, and ocean heat-flux source unchanged;
- fall back to the incumbent theta tendency if the departure remap or converted
  tendency is nonfinite.

This is a horizontal thermodynamic transport experiment, not a vertical
semi-Lagrangian transport rewrite, residual advection, output filter, or
lower-boundary thermal reservoir.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one registered side-by-side model, preferably using evaluation
    alias `dino_hsl_theta`.
- API changes:
  - None.
- Tests to update:
  - Verify zero wind reproduces incumbent theta transport.
  - Verify finite bounded departure points on polar and equatorial rows.
  - Verify only the theta horizontal transport selector changes candidate flags.
  - Add a non-JIT finite forecast smoke test and registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if thermal
    phase error is feeding hydrostatic thickness and mass-field drift.
  - `2m_temperature` after accepted residual memory decays if lower-column theta
    advection is a remaining error source.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because momentum,
    Coriolis splitting, and the Richardson diagnostic are unchanged.
- Possible regressions:
  - The remap can be more diffusive than the incumbent spectral tendency.
  - Thermal phase changes can indirectly perturb pressure gradients and trigger
    early Z500/MSLP guardrail movement.

## Risks

- Numerical stability:
  - Moderate. The change affects every positive-time step but is bounded and has
    an incumbent fallback.
- Compute cost:
  - Moderate. Adds nodal interpolation work per inner step without changing
    worker count, lead range, or grid size.
- Data leakage:
  - None. Uses only current forecast state and fixed geometry.
- Physical plausibility:
  - High. Semi-Lagrangian horizontal transport is standard in atmospheric models.
- Rollback complexity:
  - Low. Remove one selector, helper path, factory/export, registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_theta`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_theta --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failures, and
    iteration primary delta at least `+0.002` against cached incumbent artifacts.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_theta --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, or early Z500/MSLP guardrail
    failure, would show horizontal theta transport is not a useful remaining
    error source for this incumbent.

## Citations

- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lin, S.-J. and Rood, R. B. 1996. Multidimensional flux-form semi-Lagrangian
  transport schemes. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of staged vertical-transport ideas, `mass-flux-theta-
transport`, or `skew-symmetric-horizontal-scalar-advection`: it changes the
horizontal theta transport operator through a backward-departure remap rather
than flux-form mass weighting, skew-symmetric algebra, or vertical advection.
It is also decorrelated from the last two rejected lower-boundary thermal
reservoir variants and does not require incumbent reruns or protocol changes.

## Evaluator Notes

### 2026-06-22T12:06:03Z

Decision: move to `ready`; ranked 1 of 2 fresh proposals.

The proposal is implementable now and is the best current candidate for the
empty ready queue. Source inspection shows that the incumbent theta path is
localized in `PrimitiveEquationsSigma.temperature_tendency_potential_temperature_form`,
where dry theta anomaly already passes through `horizontal_scalar_advection`.
That gives a concrete side-by-side hook for replacing only the horizontal theta
transport contribution while preserving the accepted vertical advection,
pressure-work term, DFI path, semi-implicit off-centering, theta mean
recentering, residual diagnostics, and ocean bulk sensible heat flux.

The scientific support is adequate. Staniforth and Cote 1991 support
semi-Lagrangian advection as a standard atmospheric-model transport family, and
Lin and Rood 1996 support semi-Lagrangian transport on the sphere. This proposal
is not flux-form conservative, so it should be treated as a bounded phase/Courant
error experiment rather than as a conservation fix.

Local evidence is mixed but still favorable relative to alternatives. The
accepted theta-form thermodynamic tendency improved iteration by
`+0.015447942083573918`, and theta mean recentering added
`+0.003997358805283291`, showing the theta family has produced real signal.
The rejected skew-symmetric scalar advection was clean but slightly negative
(`-0.000439921242894048`), so a mere algebraic scalar-product identity is not
enough; this proposal is stronger because it changes the actual horizontal
transport operator. The recent SST/sea-ice anchor and snow/soil reservoir
rejections are weak evidence only against narrow lower-boundary thermal
variants, not against this non-thermal transport discretization.

Implementation constraints for the Orchestrator/Implementer: use a short alias
such as `dino_hsl_theta`; keep the change strictly side-by-side; apply it only
to the horizontal dry-theta anomaly transport; preserve the incumbent path for
zero wind and all non-theta tendencies; cap departure displacements; use finite
fallback to the incumbent theta tendency; and rely on the cached incumbent
artifacts supplied in the task for scoring unless a concrete protocol
incompatibility appears.
