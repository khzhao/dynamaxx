---
schema_version: 1
slug: mass-dse-remap-variance-limiter
title: Limit Variance Growth in the Mass-DSE HSL Remap
status: staging
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

# Limit Variance Growth in the Mass-DSE HSL Remap

## Hypothesis

The accepted mass-DSE branch transports `delta_p * s_prime` with a bilinear
semi-Lagrangian remap. Bilinear remapping is usually diffusive, but on a
spherical, pressure-weighted scalar it can still create localized layerwise
variance growth when departure points cross sharp thermal or mass gradients.
Those rare increments can remain finite and guardrail-clean while adding
hydrostatic noise that reduces the primary score.

A variance-nonincreasing limiter on only the accepted mass-DSE remapped scalar
should keep the useful large-scale DSE transport while rejecting remap-induced
overshoots. This is a lower-amplitude remap-quality guard, not a heat source,
not a zero-mode projection, and not a pressure-thickness product-rule
correction.

## Mechanism

Register a side-by-side candidate such as `dino_mass_dse_varlim` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- compute the incumbent weighted scalar `delta_p * s_prime`;
- call the existing accepted HSL2 midpoint remap path;
- compute layerwise spherical-area-weighted variance of the weighted scalar
  before and after the remap;
- where the remapped layer variance exceeds the pre-remap variance by more than
  a fixed small numerical tolerance, blend the remapped scalar anomaly toward
  the unremapped weighted scalar by the minimum factor needed to avoid variance
  growth;
- convert the limited remap to the mass-DSE horizontal tendency and then follow
  the incumbent `1 / delta_p` and `1 / Cp` conversion path;
- leave the layer mean, column mean, vertical theta transport, adiabatic
  tendency, momentum, pressure, forcing, filters, outputs, and protocols
  unchanged;
- fall back exactly to `dino_hsl2_mass_dse` if variance diagnostics, blending
  factors, or converted tendencies are nonfinite.

The limiter acts before the accepted local `delta_p` division. It does not
subtract a pressure-thickness tendency and does not add or remove global heat.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
- Registry changes:
  - Add one side-by-side factory and registry key for `dino_mass_dse_varlim`.
- API changes:
  - None.
- Tests to update:
  - Verify disabled selector leaves `dino_hsl2_mass_dse` unchanged.
  - Verify a synthetic remap with no variance growth is unchanged.
  - Verify a synthetic high-variance remap is blended to the pre-remap
    variance bound.
  - Verify nonfinite variance or blend diagnostics fall back to incumbent.
  - Verify candidate registration and unchanged output variables.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` if rare mass-DSE remap
    overshoots are seeding balanced thickness noise.
  - `2m_temperature` if lower-layer thermal gradients benefit from keeping the
    accepted HSL phase correction without variance growth.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because momentum and the surface wind diagnostic
    are unchanged except through downstream mass-field feedback.
- Possible regressions:
  - The accepted mass-DSE validation gain may rely on real variance growth in
    fronts or sharp baroclinic zones, so limiting it can erase useful signal.
  - A layerwise global variance criterion may be too blunt for local coastal or
    frontal structures.

## Risks

- Numerical stability:
  - Low to moderate. The limiter is a bounded convex blend, but it acts on every
    mass-DSE HSL thermal step.
- Compute cost:
  - Low. It adds two layerwise weighted reductions and local blending; no new
    remaps, outputs, or protocols are introduced.
- Data leakage:
  - None. The variance check uses only current forecast fields and fixed grid
    quadrature.
- Physical plausibility:
  - Moderate. Variance control is a standard transport-quality safeguard, but
    exact variance nonincrease is a numerical guard rather than a conservation
    law for the full primitive-equation system.
- Rollback complexity:
  - Low. Remove one limiter helper/selector, factory/export, registry key, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_mass_dse_varlim`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_mass_dse_varlim --workers 4`
  - Support requires primary delta at least `+0.002` against cached
    `dino_hsl2_mass_dse`, clean diagnostics, and no fixed RMSE guardrail
    failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_mass_dse_varlim --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that mass-DSE HSL
    variance growth is not a material remaining error source. Any early MSLP,
    Z500, or T2m guardrail failure would show the limiter removed useful
    baroclinic structure.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements the accepted mass-DSE HSL remap and exposes
  `coords.horizontal.quadrature_weights` for layerwise weighted reductions.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted the mass-DSE HSL path that this proposal limits.
- Dynamaxx history:
  `.logbook/history/2026-06-20_12-57-53_baroclinic-theta-variance-guard/decision.md`
  found a theta-variance guard stable but subthreshold, so this proposal narrows
  the variance idea to the current incumbent's transported mass-DSE remap.
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric Transport
  Schemes: Desirable Properties and a Semi-Lagrangian View on Finite-Volume
  Discretizations. In *Numerical Techniques for Global Atmospheric Models*.
  https://doi.org/10.1007/978-3-642-11640-7_8
- Thuburn, J. 2008. Some Conservation Issues for the Dynamical Cores of NWP and
  Climate Models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of staged `area-neutral-mass-dse-hsl`, which removes a
layerwise horizontal zero mode, or `column-neutral-mass-dse-increment`, which
removes a local vertical column mean from the mass-DSE increment. It also
differs from staged `semilagrangian-theta-variance-heating` and rejected
`baroclinic-theta-variance-guard`: those operate on theta and either preserve
post-step variance or add bounded heat. This candidate limits only variance
growth in the current incumbent's remapped `delta_p * s_prime` scalar before
the accepted conversion path.

The theta-variance rejection is negative evidence on expected amplitude, so
this should be treated as a low-cost remap-quality probe. It is still
decorrelated from the two latest failures because it neither subtracts
`s_prime * d(delta_p)/dt` nor applies direct hydrostatic inversion.

## Evaluator Notes

### 2026-06-24T05:16:50Z

Decision: move to `staging`; rank 3 of 3 new proposals.

This remains researchable because it acts directly on the incumbent's remapped
`delta_p * s_prime` scalar before the accepted local pressure-thickness and
`1 / Cp` conversion path. It is bounded, rollbackable, contract-preserving, and
does not repeat the rejected pressure-thickness product-rule correction or the
rejected hydrostatic inversion.

Do not promote it now because the expected signal is weaker than the other two
new proposals. The closest implemented evidence,
`baroclinic-theta-variance-guard`, was stable but effectively neutral with an
iteration delta of `-0.0000013237112340691581`, far below the fixed promotion
threshold. A layerwise global variance-nonincrease criterion is also a blunt
guard for baroclinic fronts and may remove useful variance that contributed to
the accepted mass-DSE validation gain. The staging queue already contains
related low-amplitude mass-DSE controls, especially
`area-neutral-mass-dse-hsl` and `column-neutral-mass-dse-increment`, so this
should not crowd ready unless those conservation probes fail cleanly or remap
diagnostics specifically show variance-growth outliers.

Ranked recommendation: keep as a later, low-cost remap-quality probe. Promote
behind the ready vertical-DSE transport test and behind the staged
pressure-gradient predictor unless diagnostics identify rare mass-DSE remap
overshoots as the clearest remaining error source.
