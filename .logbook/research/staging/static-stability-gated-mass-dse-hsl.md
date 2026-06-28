---
schema_version: 1
slug: static-stability-gated-mass-dse-hsl
title: Static-Stability Gate for Mass-DSE HSL Increments
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

# Static-Stability Gate for Mass-DSE HSL Increments

## Hypothesis

The accepted mass-DSE HSL branch produced clean, validated gains, but it also
adds a pressure-thickness-weighted thermal increment in every layer. Rare
columns with strong vertical thermal gradients or thin upper layers may receive
mass-DSE horizontal increments that weaken dry static stability more than the
accepted unweighted DSE-HSL branch would. Those columns can remain finite while
seeding hydrostatic thickness and pressure-gradient phase errors.

A local dry-static-stability gate should keep the accepted mass-DSE benefit in
most columns while reverting only risky columns to the accepted DSE-HSL
fallback tendency.

## Mechanism

Register a side-by-side model such as `dino_mass_dse_stabgate` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- compute the incumbent unweighted DSE-HSL temperature tendency and the accepted
  mass-DSE HSL temperature tendency already available in
  `temperature_tendency_potential_temperature_form`;
- estimate the explicit horizontal thermal update implied by the mass-DSE
  horizontal term over the current inner step;
- diagnose dry potential temperature before and after that mass-DSE horizontal
  update using the current sigma pressure;
- for columns that are initially statically stable, detect whether any adjacent
  layer separation would be reduced below a fixed conservative fraction, such
  as `0.25`, or inverted by the mass-DSE increment;
- in those flagged columns, use the unweighted DSE-HSL tendency for all layers;
- use the accepted mass-DSE tendency everywhere else;
- fall back exactly to `dino_hsl2_mass_dse` if pressure, theta conversion,
  stability differences, masks, or selected tendencies are nonfinite.

This is a selector between two already implemented finite thermal paths. It
does not add another HSL trajectory correction, change remap order, alter
vertical advection, edit pressure work, modify log-surface pressure, or change
forecast outputs.

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
    `dino_mass_dse_stabgate`.
- API changes:
  - None.
- Tests to update:
  - Verify the candidate preserves all `dino_hsl2_mass_dse` settings except the
    new selector and model name.
  - Verify stable columns with acceptable mass-DSE increments select the
    incumbent mass-DSE tendency exactly.
  - Verify synthetic increments that erode dry static stability select the
    unweighted DSE-HSL fallback for the whole column.
  - Verify initially neutral or inverted columns do not receive an artificial
    stability repair beyond the existing incumbent fallback chain.
  - Verify nonfinite diagnostics fall back to the incumbent mass-DSE behavior.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 1-8 if rare
    mass-DSE increments perturb hydrostatic column structure.
  - `2m_temperature` at medium leads if lower-column static stability is better
    preserved in frontal or high-gradient regions.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because momentum tendencies and wind diagnostics
    are unchanged.
- Possible regressions:
  - The accepted mass-DSE increment may be beneficial even in columns that this
    gate marks as risky, so reverting to unweighted DSE-HSL can remove useful
    phase correction.
  - A columnwise selector can introduce small horizontal discontinuities in the
    thermal tendency near the gate threshold.

## Risks

- Numerical stability:
  - Low to moderate. The selector chooses between two finite-guarded incumbent
    thermal paths, but the mask must not propagate nonfinite values.
- Compute cost:
  - Low. It adds theta conversion and adjacent-layer differences on existing
    nodal arrays; no extra remap or rollout step is required.
- Data leakage:
  - None. It uses only the current forecast state, current-step tendencies, and
    fixed sigma geometry.
- Physical plausibility:
  - Moderate to high. Dry static stability is a core hydrostatic balance
    constraint, and the fallback is the previously accepted DSE-HSL thermal
    transport rather than an artificial clipping source.
- Rollback complexity:
  - Low. Remove one selector/helper, one adapter flag, one factory/export, one
    registry key, and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_mass_dse_stabgate`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_mass_dse_stabgate --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure against cached `dino_hsl2_mass_dse`.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_mass_dse_stabgate --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that local
    mass-DSE static-stability erosion is not a material remaining error source.
    Any early MSLP, Z500, or 2 m temperature guardrail failure would show the
    selector disrupts the accepted mass-DSE balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements the accepted DSE-HSL and mass-DSE HSL fallback chain.
- Dynamaxx history:
  `.logbook/history/2026-06-23_11-22-34_dry-static-energy-hsl-transport/decision.md`
  accepted unweighted DSE-HSL with iteration delta `+0.045455173259026704`.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted mass-DSE HSL on top of DSE-HSL, providing the two finite tendency
  paths used by this selector.
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Arakawa, A. and Suarez, M. J. 1983. Vertical Differencing of the Primitive
  Equations in Sigma Coordinates. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1983)111%3C0034:VDOTPE%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This proposal is not a duplicate of staged `static-stability-gated-hsl-theta`.
That staged idea targets `dino_hsl2_theta` and chooses between midpoint and
first-order theta HSL tendencies. This proposal targets the current
`dino_hsl2_mass_dse` incumbent and chooses between two accepted dry-static-
energy thermal paths: mass-weighted DSE-HSL and its unweighted DSE-HSL
fallback.

It also differs from rejected `charney-phillips-interface-theta-advection`,
which changed vertical transport and failed fast with nonfinite forecasts. This
candidate does not alter vertical advection or interface reconstruction. The
main negative evidence is that low-amplitude theta stability selectors may be
subthreshold; the reason to keep this proposal researchable is that the new
mass-DSE branch is now the incumbent and has a stronger pressure-thickness
coupling than the older theta-only transport path.

## Evaluator Notes

### 2026-06-23T21:59:49Z

Decision: move to `staging`; rank 3 of 3 new proposals.

This is not a duplicate of the staged theta-HSL stability gate because it acts
on the current `dino_hsl2_mass_dse` incumbent and selects between two accepted
dry-static-energy thermal paths. The fallback design is source-compatible, the
implementation should be rollbackable, and dry static stability is a legitimate
hydrostatic balance concern.

Keep it staged because the expected benefit depends on undocumented rare
columns where mass-DSE increments erode stability, while the mechanism adds a
fixed threshold and a columnwise tendency mask every thermodynamic step. That
creates more empirical-tuning and horizontal-discontinuity risk than either
conservation proposal. Local history also argues for caution: the older
`static-stability-gated-hsl-theta` idea was staged for the same reason, and
broad dry static-stability adjustment was scrapped without diagnostics showing
frequent incumbent instability.

Recommendation: do not implement this in the next slot. Promote only after a
diagnostic pass or failed conservation follow-ups justify static-stability
erosion as a material remaining error source. If promoted, fix the threshold
before iteration scoring, preserve exact `dino_hsl2_mass_dse` behavior for
already neutral or inverted columns, and skip validation unless the fixed
iteration gate promotes it.
