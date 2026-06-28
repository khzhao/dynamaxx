---
schema_version: 1
slug: area-neutral-mass-dse-hsl
title: Preserve Layer-Integrated Mass-DSE During HSL Remap
status: staging
created_at: 2026-06-23T21:55:20Z
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

# Preserve Layer-Integrated Mass-DSE During HSL Remap

## Hypothesis

The accepted mass-DSE branch uses interpolation-form semi-Lagrangian transport.
That transport is stable and accurate enough to improve the score, but it is
not exactly conservative under spherical area quadrature. Because the candidate
now transports a layer-mass-weighted thermodynamic scalar, any spurious
layer-integral tendency in `delta_p * s_prime` can project onto global thermal
thickness, MSLP, and Z500 drift.

The proposal is to preserve the layer-integrated mass-DSE anomaly during the
HSL remap by removing the spherical-area-weighted zero mode from the
mass-weighted DSE horizontal tendency before converting it back to temperature.

## Mechanism

Register a side-by-side model such as `dino_mass_dse_areaneutral` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- preserve all incumbent options, including the accepted HSL2 departure,
  bilinear scalar remap, direct mass-DSE branch, vertical theta tendency,
  adiabatic tendency, weak-HS forcing, ocean bulk flux, pressure/momentum
  tendencies, residuals, output variables, and fixed protocols;
- after computing the finite HSL tendency of `delta_p * s_prime`, compute its
  layerwise spherical-area-weighted mean using the existing latitude weights;
- subtract that layerwise zero mode from the mass-weighted DSE horizontal
  tendency;
- divide the neutralized tendency by guarded local `delta_p` and convert
  through `1 / c_p` exactly as the incumbent branch does;
- fall back exactly to `dino_hsl2_mass_dse` if the area weights, layer means,
  neutralized tendency, or converted temperature tendency are nonfinite.

This is an HSL conservation projection for the transported scalar. It does not
anchor pressure, modify log-surface pressure, retune weak-HS relaxation, change
the remap order, or add forecast outputs.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add one short side-by-side factory and registry key for
    `dino_mass_dse_areaneutral`.
- API changes:
  - None.
- Tests to update:
  - Verify the incumbent mass-DSE tendency is unchanged when the option is
    disabled.
  - Verify the neutralized mass-DSE tendency has zero spherical-area-weighted
    layer mean on a synthetic finite field.
  - Verify a tendency that already has zero weighted mean is unchanged.
  - Verify invalid weights or nonfinite neutralized fields fall back to the
    incumbent branch.
  - Verify candidate registration and unchanged output variables.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and long leads
    if interpolation nonconservation of layer mass-DSE is a remaining slow
    drift source.
  - `2m_temperature` may improve modestly if lower-layer thermal zero-mode
    drift is reduced after the accepted surface residuals decay.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because no momentum or 10 m diagnostic path is
    changed.
- Possible regressions:
  - The zero-mode in the accepted mass-DSE tendency may be compensating for
    missing forcing or pressure-work effects.
  - If the integral drift is already numerical-noise scale, the proposal may be
    clean but subthreshold.

## Risks

- Numerical stability:
  - Low to moderate. The projection is a bounded linear correction on an
    already finite tendency, but it acts every thermodynamic step.
- Compute cost:
  - Low. It adds one weighted horizontal reduction per layer and no new remaps,
    transforms, outputs, or lead times.
- Data leakage:
  - None. It uses only current forecast fields and fixed grid quadrature.
- Physical plausibility:
  - Moderate to high. Conservation of transported scalar integrals is a
    desirable dycore property, but the projection is global-per-layer rather
    than locally flux-form.
- Rollback complexity:
  - Low. Remove one projection helper, one selector, one factory/export, one
    registry key, and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_mass_dse_areaneutral`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_mass_dse_areaneutral --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure against cached `dino_hsl2_mass_dse`.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_mass_dse_areaneutral --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that HSL
    layer-integral drift in mass-DSE is not a material remaining error source.
    Any early MSLP or Z500 guardrail failure would show the removed zero mode
    was part of the accepted empirical balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  contains the accepted HSL remap and mass-DSE branch.
- Dynamaxx history:
  `.logbook/history/2026-06-23_00-41-09_mean-neutral-hsl-theta-transport/decision.md`
  found a theta zero-mode HSL projection stable but subthreshold.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted mass-DSE transport, making the transported scalar more physically
  relevant than theta for a conservation projection retest.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric
  Transport Schemes: Desirable Properties and a Semi-Lagrangian View on
  Finite-Volume Discretizations. In Numerical Techniques for Global Atmospheric
  Models. https://doi.org/10.1007/978-3-642-11640-7_8
- Thuburn, J. 2008. Some Conservation Issues for the Dynamical Cores of NWP and
  Climate Models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is not a duplicate of rejected `mean-neutral-hsl-theta-transport`: that
candidate acted on theta before the accepted DSE and mass-DSE transport
discoveries. This proposal acts on the current incumbent's transported
mass-weighted dry-static-energy tendency, where a nonconservative zero mode is
more directly tied to hydrostatic thickness.

It is also distinct from staged `column-dry-static-energy-recentering`, which
would apply a post-step thermodynamic state filter. Here the correction is
inside the horizontal HSL transport tendency and only removes the remap-induced
layer-integral component. The prior theta result is negative evidence on
expected amplitude, so this should be treated as a low-cost conservation probe,
not as a guaranteed high-signal candidate.

## Evaluator Notes

### 2026-06-23T21:59:49Z

Decision: move to `staging`; rank 2 of 3 new proposals.

This is scientifically coherent and cheap enough to keep researchable. The
accepted mass-DSE branch makes layer-integrated conservation more relevant than
the older theta-only zero-mode test, and the proposed projection is a bounded
linear correction with no new remap, no metric contract change, no data
leakage, and straightforward fallback to `dino_hsl2_mass_dse`.

Keep it staged rather than ready because the nearest implemented evidence is
weak. `mean-neutral-hsl-theta-transport` was stable and slightly positive, but
its iteration delta was only `+0.00009292283211348451`, far below the fixed
promotion threshold. A mass-DSE zero-mode projection may have a stronger
hydrostatic connection, but it still mostly removes a global layer mean rather
than addressing local pressure-system structure. It could also subtract an
empirical compensation that the newly accepted mass-DSE tendency uses to hold
MSLP/Z500 balance.

Recommendation: keep as the next conservation backup if the pressure-thickness
product-rule correction fails cleanly or if diagnostics show a meaningful
layer-integral mass-DSE drift. Do not choose it ahead of the rank-1 ready
candidate unless the Orchestrator specifically wants a lower-amplitude,
lower-risk probe.
