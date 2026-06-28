---
schema_version: 1
slug: mass-centered-dse-anomaly-hsl
title: Mass-Centered DSE Anomaly for HSL Transport
status: ready
created_at: 2026-06-26T11:07:00Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Mass-Centered DSE Anomaly for HSL Transport

## Hypothesis

The accepted mass-DSE HSL branch multiplies an area-mean-centered dry static
energy anomaly by local sigma-layer pressure thickness. Over spatially varying
surface pressure, that weighted scalar can retain a nonzero layer mass integral
even before semi-Lagrangian remapping. A side-by-side variant that centers DSE
with the same layer-pressure mass measure used by the mass-DSE transport may
reduce slow hydrostatic thickness drift while preserving the accepted HSL
transport, WTG filter, and vertical-DSE ramp.

## Mechanism

Add one candidate such as `dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter`.

For this candidate only:

- preserve the incumbent unweighted DSE-HSL fallback, WTG relaxation,
  pressure-ramped vertical-DSE increment, vertical theta transport, adiabatic
  pressure work, residual correction, weak-HS forcing, output variables, and
  fixed protocols;
- keep `nodal_dry_static_energy_anomaly` unchanged for the unweighted DSE path
  and for the accepted pressure-ramped vertical-DSE increment, avoiding a hidden
  vertical-DSE retune;
- inside only the layer-mass-weighted horizontal HSL branch, compute a
  layerwise pressure-thickness-and-area-weighted DSE reference
  `sum(area_weight * delta_p * dse) / sum(area_weight * delta_p)`;
- form the transported scalar as
  `weighted_dse_anomaly = delta_p * (dse - mass_centered_reference)` instead of
  `delta_p * area_centered_dse_anomaly`;
- pass that scalar through the accepted HSL2 midpoint departure and the same
  finite fallback, divide by guarded `delta_p`, and convert through `1 / Cp`;
- fall back exactly to the incumbent mass-DSE tendency if pressure thickness,
  weights, centered scalar, remap outputs, or converted tendencies are nonfinite.

This is a scalar-definition experiment in the horizontal mass-DSE HSL path. It
does not change vertical-DSE timing/caps/gates, output residuals, pressure-level
diagnostics, humidity dynamics, or forecast contracts.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused primitive-equation and registry tests
- Registry changes:
  - Add one model key such as
    `dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter`.
- API changes:
  - None. Forecast inputs, output variables, target variables, metrics, and lead
    schedule remain fixed.
- Tests to update:
  - Verify the mass-centered weighted DSE scalar has zero
    area-and-pressure-thickness-weighted layer integral on synthetic fields.
  - Verify uniform surface pressure reduces to the incumbent area-centered DSE
    anomaly to tolerance.
  - Verify the unweighted DSE path and pressure-ramped vertical-DSE inputs are
    unchanged by the new selector.
  - Verify nonfinite weights or remapped fields fall back to the incumbent
    mass-DSE HSL tendency.
  - Verify candidate registration, unchanged output variables, and a finite
    non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium and late leads if
    nonzero mass-weighted DSE zero modes are contributing to thickness drift.
  - `2m_temperature` may improve modestly where lower-layer thermal drift is
    tied to the mass-DSE scalar reference rather than to surface residual decay.
- Expected neutral metrics:
  - Day-1 fields should remain close to incumbent because the accepted
    vertical-DSE ramp and all output residual paths are unchanged.
  - `10m_u_component_of_wind` should move only through downstream balanced
    mass-field feedback.
- Possible regressions:
  - The accepted area-centered scalar may be empirically compensating another
    bias; removing its mass-weighted zero mode can weaken the validated
    mass-DSE gain.
  - If pressure-thickness variation is not the active error source, this will be
    clean but subthreshold.

## Risks

- Numerical stability:
  - Low to moderate. The candidate changes an active thermodynamic scalar every
    step but keeps incumbent HSL, caps, and finite fallback.
- Compute cost:
  - Low. It adds one layerwise weighted horizontal reduction and no new remap,
    output channel, or training.
- Data leakage:
  - None. The candidate uses only current forecast pressure thickness, current
    DSE, fixed quadrature weights, and fixed constants.
- Physical plausibility:
  - Moderate to high. The transported scalar is layer-mass weighted, so defining
    its anomaly with the same mass measure is more internally consistent than
    area-centering before mass weighting.
- Rollback complexity:
  - Low. Remove one helper/selector, one factory/export, one registry key, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter`.
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    `dino_hsl2_mass_dse_wtg_vdse_ramp`, clean diagnostics, and no early
    day-1-to-day-5 or variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter --workers 4`
    only after iteration promotion.
  - Support requires validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that mass-centered
    scalar definition is not a material remaining error source. Any early
    `2m_temperature`, MSLP, or Z500 guardrail failure would show the incumbent
    area-centered scalar is part of the accepted balance.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` defines
  `nodal_dry_static_energy_anomaly`, multiplies it by sigma-layer pressure
  thickness in the mass-DSE HSL branch, and implements the accepted
  pressure-ramped vertical-DSE increment.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted layer-mass-weighted DSE HSL, establishing the value of the
  mass-weighted scalar.
- Dynamaxx history:
  `.logbook/history/2026-06-24_15-20-39_finite-volume-mass-dse-hsl-remap/decision.md`
  rejected a broader finite-volume mass-DSE remap, so this proposal changes
  only anomaly centering and keeps the accepted remap.
- Dynamaxx history:
  `.logbook/history/2026-06-25_17-17-23_baroclinic-mode-vertical-dse-spinup/decision.md`
  and `.logbook/history/2026-06-26_00-40-18_hydrostatic-work-gated-vertical-dse/decision.md`
  are negative evidence against more vertical-DSE ramp/gate variants; this
  proposal leaves the vertical-DSE branch untouched.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: A review. *Monthly Weather Review*.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric transport
  schemes: desirable properties and a semi-Lagrangian view on finite-volume
  discretizations. In *Numerical Techniques for Global Atmospheric Models*.
  https://doi.org/10.1007/978-3-642-11640-7_8
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  *Monthly Weather Review*. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2

## Researcher Notes

This is distinct from staged `area-neutral-mass-dse-hsl`, which subtracts a
layerwise area mean from the HSL tendency after remapping, and from staged
`column-neutral-mass-dse-increment`, which removes a local vertical column mean
from the incremental thermal tendency. This proposal changes the anomaly
reference before the mass-DSE scalar is transported and uses the same
pressure-thickness measure that defines the transported quantity.

It is also not a duplicate of the notable staged
`delayed-lowmode-virtual-geopotential-coupling`: no humidity, virtual
temperature, divergence tendency, or pressure-gradient increment is introduced.
The recent surface-output failures are relevant only as negative evidence
against another diagnostic patch; this proposal acts in the prognostic
horizontal thermodynamic transport while avoiding the rejected vertical-DSE
timing, cap, and gate neighborhood.

## Evaluator Notes

### 2026-06-26T11:09:59Z

Decision: move to `ready`; ranked 1 of 2 in this proposal triage.

This is the best immediate implementation candidate because it changes one
scalar definition inside the already accepted layer-mass DSE HSL branch while
preserving the incumbent WTG filter, pressure-ramped vertical-DSE increment,
vertical theta tendency, pressure work, output contract, and fixed evaluation
protocols. The source currently forms `dry_static_energy_anomaly` with a
layerwise area mean and then multiplies by local layer pressure thickness in
the mass-DSE branch, so using the same pressure-thickness-and-area measure for
the anomaly reference is a real internal-consistency test rather than a retune.

Local history supports this ranking. Layer-mass-weighted DSE HSL was accepted
with clean iteration and validation gains, and tropical WTG plus the
pressure-ramped vertical-DSE increment were also accepted on top of that path.
The nearby failures argue for this proposal's narrowness: the pressure-thickness
product-rule correction, hydrostatic inversion, finite-volume remap, and recent
vertical-DSE gate/spinup variants either regressed the primary score or damaged
early MSLP/T2m. This proposal avoids pressure-thickness tendency coupling,
hydrostatic inversion, remap replacement, humidity divergence coupling, and
output residual edits.

Relative to active staged ideas, this is stronger than
`area-neutral-mass-dse-hsl` and `column-neutral-mass-dse-increment` because it
defines the transported scalar consistently before remap rather than projecting
a tendency afterward. It is also lower-risk than the staged
`delayed-lowmode-virtual-geopotential-coupling`, which would feed passive
humidity into a prognostic divergence tendency.

Caveats: conservation-style refinements have often been clean but subthreshold,
and the accepted area-centered anomaly may be empirically compensating another
missing term. Implementation must keep `nodal_dry_static_energy_anomaly`
unchanged for the unweighted DSE path and the accepted pressure-ramped
vertical-DSE increment, must fall back exactly to the incumbent mass-DSE HSL
tendency on nonfinite diagnostics, and must not tune constants against
iteration or validation results.
