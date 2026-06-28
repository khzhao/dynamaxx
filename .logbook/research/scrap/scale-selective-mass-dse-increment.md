---
schema_version: 1
slug: scale-selective-mass-dse-increment
title: Apply Mass-DSE HSL Only to Large-Scale Thermal Increments
status: scrap
created_at: 2026-06-24T01:38:14Z
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

# Apply Mass-DSE HSL Only to Large-Scale Thermal Increments

## Hypothesis

The accepted DSE-HSL and mass-DSE-HSL path shows that changing the transported
thermal invariant can materially improve the fixed score. In contrast, several
nearby HSL trajectory or remap refinements were neutral, negative, or unstable,
and the latest pressure-thickness product-rule correction degraded the
incumbent. This suggests the robust signal may live in the large-scale balanced
thermal increment introduced by mass-DSE weighting, while small-scale HSL
increment details are more likely to add interpolation noise or phase error.

A side-by-side candidate should keep the unweighted DSE-HSL fallback at all
scales and add only a fixed low-wavenumber part of the accepted mass-DSE
increment. This tests whether mass-DSE's value is primarily synoptic and
planetary-scale hydrostatic structure rather than grid-scale thermal detail.

## Mechanism

Register a side-by-side model such as `dino_mass_dse_lowmode` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- compute the unweighted DSE-HSL temperature tendency and accepted mass-DSE HSL
  temperature tendency exactly as in the incumbent branch;
- form the modal increment
  `mass_dse_temperature_tendency - dse_temperature_tendency`;
- apply a fixed smooth total-wavenumber taper to that modal increment, for
  example full weight through a conservative low mode and zero weight beyond a
  predeclared transition band;
- return `dse_temperature_tendency + tapered_increment`;
- keep vertical theta tendency, adiabatic tendency, pressure tendency, momentum,
  weak-HS forcing, ocean bulk flux, residuals, diagnostics, output variables,
  and fixed evaluation protocols unchanged;
- fall back exactly to `dino_hsl2_mass_dse` if the taper or selected tendency is
  nonfinite.

The taper is applied only to the extra mass-DSE increment, not to the whole
state and not to the fixed evaluation outputs. It does not retune the rejected
pressure-thickness product-rule correction.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry key for
    `dino_mass_dse_lowmode`.
- API changes:
  - None.
- Tests to update:
  - Verify the candidate preserves all incumbent settings except the new
    selector and model name.
  - Verify zero increment returns the unweighted DSE-HSL tendency exactly.
  - Verify a synthetic low-mode increment is retained and a high-mode increment
    is strongly attenuated by the fixed taper.
  - Verify nonfinite taper diagnostics fall back to the incumbent mass-DSE
    branch.
  - Verify registration and unchanged output variables.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and late leads if
    large-scale mass-DSE structure carries the accepted gain while high modes
    add noise.
  - `2m_temperature` may remain close to incumbent if low-level synoptic thermal
    structure is retained.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because momentum and surface wind diagnostics are
    unchanged except through balanced mass-field feedback.
- Possible regressions:
  - The accepted mass-DSE branch may rely on smaller-scale frontal or coastal
    thermal increments, so tapering the increment could lose the validation
    gain.
  - If the taper is too sharp, it can introduce spectral ringing in the thermal
    tendency; the implementation should use a smooth fixed transition.

## Risks

- Numerical stability:
  - Low. The candidate is a modal linear filter on an already finite thermal
    increment with exact incumbent fallback.
- Compute cost:
  - Low. The mass-DSE and DSE-HSL tendencies are already modal at selection
    time; the new work is a fixed modal mask multiply.
- Data leakage:
  - None. The taper uses fixed spectral indices and no evaluation statistics.
- Physical plausibility:
  - Moderate. Scale-selective filtering is common in spectral dycores, but this
    variant is an empirical split between balanced large scales and smaller
    thermal increments.
- Rollback complexity:
  - Low. Remove one selector/mask helper, factory/export, registry key, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_mass_dse_lowmode`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_mass_dse_lowmode --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure against cached `dino_hsl2_mass_dse`.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_mass_dse_lowmode --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that the accepted
    mass-DSE benefit is not confined to low modes. A `2m_temperature` regression
    with neutral MSLP/Z500 would indicate useful lower-tropospheric thermal
    detail was filtered away.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  already computes modal temperature tendencies for both DSE-HSL and mass-DSE
  HSL paths, making an increment-only modal taper local to the candidate.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted the mass-DSE branch, providing the increment to isolate.
- Dynamaxx history:
  `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/decision.md`,
  `.logbook/history/2026-06-22_21-59-29_picard-hsl-theta-departure/decision.md`,
  and `.logbook/history/2026-06-23_06-13-46_coriolis-centered-hsl-theta-departure/decision.md`
  caution against more HSL trajectory or pointwise blend variants.
- Boer, G. J., McFarlane, N. A., and Lazare, M. 1992. Greenhouse Gas-Induced
  Climate Change Simulated with the CCC Second-Generation General Circulation
  Model. Journal of Climate. https://doi.org/10.1175/1520-0442(1992)005%3C1045:GGICCS%3E2.0.CO;2
- Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
  Atmospheric Models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric Transport
  Schemes: Desirable Properties and a Semi-Lagrangian View on Finite-Volume
  Discretizations. In Numerical Techniques for Global Atmospheric Models.
  https://doi.org/10.1007/978-3-642-11640-7_8

## Researcher Notes

This is not a duplicate of staged `lead-dependent-spectral-smoothing`,
`planetary-wave-preserving-horizontal-diffusion`, or
`smooth-analysis-hs-spectral-taper`: those proposals filter broader state,
forcing, or rollout structures. This proposal filters only the incremental
thermal tendency added by the accepted mass-DSE branch relative to unweighted
DSE-HSL.

It is also distinct from the latest rejected
`pressure-thickness-corrected-mass-dse-hsl` candidate. The rejected mechanism
added a product-rule pressure-thickness correction and degraded the incumbent
primary score. This proposal keeps pressure thickness as in the accepted
incumbent and asks whether the mass-DSE increment should be limited by
horizontal scale instead of coupled more tightly to mass continuity.

## Evaluator Notes

### 2026-06-24T01:43:04Z

Decision: move to `scrap`; rank 3 of 3 new proposals.

The mechanism is implementable, but it is too empirical for the next search
slot. Scale-selective filtering is a standard dycore tool, and filtering only
the mass-DSE increment is narrower than filtering the full state. The proposal
still depends on an arbitrary fixed low-mode cutoff and transition band without
diagnostic evidence that high-wavenumber mass-DSE increments are the remaining
error source. That makes it mostly a cutoff experiment rather than a targeted
physical correction.

Prior local evidence is unfavorable for this neighborhood. HSL trajectory and
remap refinements were neutral, negative, or unstable; broader spectral and
diffusion ideas are already staged as low-priority fallbacks; and the accepted
mass-DSE validation gain may rely on smaller-scale frontal or lower-column
thermal increments that this taper would attenuate. The latest
pressure-thickness rejection is negative evidence for over-coupling mass
continuity, but it does not by itself justify suppressing high-mode mass-DSE
structure.

Ranked recommendation: do not implement. Revive only if a future diagnostic
artifact shows the accepted mass-DSE increment has harmful high-wavenumber
noise, and only with a predeclared mask that is not tuned after iteration or
validation scores.
