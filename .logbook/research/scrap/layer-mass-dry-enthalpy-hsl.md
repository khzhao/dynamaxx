---
schema_version: 1
slug: layer-mass-dry-enthalpy-hsl
title: Layer-Mass Dry-Enthalpy HSL Transport
status: scrap
created_at: 2026-06-24T15:41:00Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
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

# Layer-Mass Dry-Enthalpy HSL Transport

## Hypothesis

The accepted layer-mass DSE transport may have won partly because it mass-weights
the horizontal thermodynamic scalar, not necessarily because the hydrostatic
geopotential component should be converted directly into local temperature
tendency. A bounded layer-mass dry-enthalpy HSL branch, transporting
`delta_p * Cp * T_anomaly`, can test that separation: it keeps the accepted
mass-weighted HSL numerics while removing the geopotential part of dry static
energy from the transported scalar.

## Mechanism

Register a side-by-side candidate, for example `dino_hsl2_mass_enthalpy`.
Preserve the incumbent HSL2 departure estimates, local pressure-thickness
division, vertical theta tendency, adiabatic tendency, weak-HS forcing, ocean
bulk sensible heat flux, residual corrections, and output contract.

For the candidate only:

- compute absolute nodal temperature on sigma levels using the same reference
  temperature and `temperature_variation` diagnostics as the incumbent;
- remove the area-weighted layer mean of `Cp * T` to form a dry-enthalpy
  anomaly;
- transport `weighted_enthalpy_anomaly = delta_p * Cp * T_anomaly` with the
  same HSL2 midpoint remap used by the incumbent mass-DSE branch;
- divide the remapped tendency by guarded local `delta_p` and by `Cp` to obtain
  the horizontal temperature tendency;
- retain incumbent vertical theta transport and adiabatic compression terms;
- fall back to the accepted `dino_hsl2_mass_dse` temperature tendency if
  temperature, pressure thickness, or remap diagnostics are nonfinite.

This is not a DSE pressure-thickness correction, hydrostatic inversion, DSE
initialization, vertical DSE transport, or deeper ocean heat-flux variant. It is
a side-by-side scalar-choice test inside the already accepted HSL2 thermal
transport hook.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and one short registry alias.
- API changes:
  - None. Forecast state, outputs, targets, and evaluation protocols stay fixed.
- Tests to update:
  - Verify layer-mean removal under spherical quadrature.
  - Verify constant temperature produces no added horizontal HSL tendency.
  - Verify invalid pressure thickness or nonfinite temperature falls back to the
    accepted mass-DSE tendency.
  - Verify candidate factory differs from `dino_hsl2_mass_dse` only by the new
    thermodynamic scalar selector.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` if the accepted DSE scalar sometimes overconverts
    geopotential displacement into local thermal tendency.
  - `geopotential_500` and `mean_sea_level_pressure` may improve if the
    mass-weighted enthalpy tendency is less prone to short-lead pressure shocks
    than more aggressive DSE variants.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to incumbent except through
    thermal-gradient feedback.
- Possible regressions:
  - Removing the geopotential component may give back some of the accepted
    mass-DSE gain if dry static energy, rather than mass weighting alone, was
    the important physical signal.

## Risks

- Numerical stability:
  - Low to moderate. The branch is finite-guarded and bounded by the existing
    HSL2 displacement caps, but it changes an active thermal tendency.
- Compute cost:
  - Low. It reuses the incumbent mass-DSE transport machinery and avoids any new
    pressure or hydrostatic solve.
- Data leakage:
  - None. It uses only forecast-state temperature and pressure thickness.
- Physical plausibility:
  - Moderate. Dry enthalpy is not a materially conserved adiabatic invariant
    like dry static energy, but the proposal isolates a plausible numerical
    source of the incumbent gain: layer-mass-weighted horizontal heat transport.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_enthalpy`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_enthalpy --workers 4`.
  - Compare against cached `dino_hsl2_mass_dse` incumbent metrics only.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_enthalpy --workers 4`
    only after fixed iteration promotion.
- Outcome that would falsify the hypothesis:
  - A negative or subthreshold clean iteration result would show that the
    geopotential part of dry static energy is needed for the accepted gain. Any
    early T2m, MSLP, or Z500 guardrail failure would show the scalar swap
    disrupts the incumbent balance.

## Citations

- Chavas, D. R. and Peters, J. M. 2023. Static energy deserves greater emphasis
  in the meteorology community. *Bulletin of the American Meteorological
  Society*. https://doi.org/10.1175/BAMS-D-22-0013.1
- Lorenz, E. N. 1955. Available potential energy and the maintenance of the
  general circulation. *Tellus*. https://doi.org/10.3402/tellusa.v7i2.8796
- Lin, S.-J. and Rood, R. B. 1996. Multidimensional flux-form
  semi-Lagrangian transport schemes. *Monthly Weather Review*.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2

## Researcher Notes

This proposal deliberately contrasts with the accepted mass-DSE incumbent rather
than editing it with a pressure-thickness correction. It does not rerun or
invalidate incumbent metrics. It is not the recent rejected hydrostatic
inversion, vertical-DSE transport, or DSE-consistent initialization path.

It is also not a duplicate of staged `mass-flux-theta-transport` or
`full-state-theta-thermodynamic-tendency`: the transported scalar is dry
enthalpy in temperature units, with the same layer-mass weighting and HSL2
machinery as the accepted mass-DSE branch. The result should answer a narrow
question left by the incumbent gain: whether mass-weighted heat transport is
enough, or whether hydrostatic dry static energy itself is essential.

## Evaluator Notes

### 2026-06-24T15:18:56Z

Decision: move to `scrap`; rank 3 of 3 new proposals; ready now: no.

This is a clean ablation question, but it is not a good optimization candidate
against the current incumbent. Dry enthalpy `Cp * T` lacks the dry adiabatic
invariant argument that supported the accepted DSE and mass-DSE HSL steps, and
removing the hydrostatic geopotential component likely discards part of the
signal that produced the large DSE-HSL gain and the later mass-DSE validation
gain. The proposal's own expected upside is mostly that DSE may overconvert
geopotential displacement into temperature; recent history tested more direct
DSE conversion fixes and found them unfavorable, especially the hydrostatic
inversion (`-0.030209299275616164` iteration delta with early MSLP guardrail
failure) and pressure-thickness correction (`-0.006172261163569502` iteration
delta).

It is also too close to existing staged thermodynamic scalar/transport
questions to keep in the active queue. `full-state-theta-thermodynamic-tendency`
and `mass-flux-theta-transport` already cover more physically defensible
temperature/theta alternatives, while the new dry-entropy proposal is a better
mass-weighted scalar-choice follow-up because entropy is tied to potential
temperature for dry adiabatic flow. If the loop later needs an ablation study
for interpretability, this can be rewritten from scratch with diagnostic
evidence that the geopotential term is harmful; as written it is unlikely to
beat `dino_hsl2_mass_dse` under the fixed metrics.
