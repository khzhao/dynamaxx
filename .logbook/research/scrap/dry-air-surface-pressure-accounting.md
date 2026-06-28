---
schema_version: 1
slug: dry-air-surface-pressure-accounting
title: Separate Dry-Air Surface Pressure From Moist Total Pressure
status: scrap
created_at: 2026-06-24T11:52:46Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Separate Dry-Air Surface Pressure From Moist Total Pressure

## Hypothesis

The incumbent dry primitive-equation rollout initializes `log_surface_pressure`
from the analyzed surface pressure, but analyzed surface pressure is the weight
of moist air while the core's gas constants, mass continuity, and accepted
mass-DSE transport are dry-air formulations. Prior humidity proposals were
harmful when they fed water vapor into pressure gradients, virtual-temperature
dynamics, or latent heating. A narrower mass-accounting split may still help:
let the dry core evolve dry-air surface pressure, keep humidity passive, and
convert back to moist total pressure only for output diagnostics.

The expected benefit is small but physically specific. In humid columns,
treating total pressure as dry pressure can slightly overstate dry mass and
layer pressure thickness. Correcting that bookkeeping may reduce humid-region
MSLP and Z500 thickness bias without changing thermal tendencies, pressure
gradients, or the accepted mass-DSE HSL mechanism.

## Mechanism

Register a side-by-side candidate such as `dino_hsl2_mass_dse_dry_air_ps`
derived from `dino_hsl2_mass_dse`.

For the candidate only:

- require a complete pressure-level `specific_humidity` stack; otherwise fall
  back exactly to the incumbent initialization and output path;
- after sigma humidity has been initialized, diagnose a bounded column-mean
  vapor mass fraction from passive humidity using sigma-layer pressure
  thickness weights;
- initialize the dynamic dry-air pressure as
  `p_dry = p_total * clip(1 - q_column, 0.96, 1.0)` and store that in
  `log_surface_pressure`;
- leave temperature, winds, humidity tracer values, DFI, forcing, HSL
  departure geometry, DSE transport, and pressure-gradient coupling unchanged;
- during `dinosaur_state_to_weather_state`, reconstruct moist total surface
  pressure as `p_total = p_dry / clip(1 - q_column_forecast, 0.96, 1.0)` for
  emitted surface pressure, MSLP, and sigma-to-pressure output interpolation;
- fall back to dry pressure for output if humidity, dry-air fraction, or
  reconstructed pressure diagnostics are nonfinite or outside conservative
  bounds.

This is not a humidity dynamics proposal. Humidity remains passive and does not
enter thermal tendencies, momentum tendencies, latent heating, or virtual
pressure-gradient terms.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry key for
    `dino_hsl2_mass_dse_dry_air_ps`.
- API changes:
  - None. Forecast input/output variables, lead schedule, metrics, and
    protocols remain unchanged.
- Tests to update:
  - Verify absent humidity is an exact incumbent no-op.
  - Verify bounded dry-air pressure is lower than total pressure in humid
    columns and equal in dry columns.
  - Verify output reconstruction recovers total pressure from a synthetic
    passive humidity column.
  - Verify temperature, winds, humidity tracer arrays, and model options other
    than the new pressure-accounting flag are unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` in humid lower-tropospheric
    regimes if dry-air mass overstatement is feeding thickness and mass bias.
  - `2m_temperature` may improve weakly through corrected lower-column pressure
    placement after near-surface residual memory decays.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because prognostic momentum and the Richardson
    10 m wind diagnostic remain on the incumbent path except for downstream
    pressure-coordinate effects.
- Possible regressions:
  - MSLP could regress if the evaluation target and current output path are
    empirically better aligned with total pressure throughout the dry rollout.
  - Passive humidity phase errors can feed the output pressure reconstruction,
    so medium-lead humid columns need careful guardrail review.

## Risks

- Numerical stability:
  - Moderate. The pressure correction is bounded and small, but it changes the
    mass coordinate that all dry dynamics see.
- Compute cost:
  - Low. It adds column reductions over already-carried humidity and local
    pressure conversions.
- Data leakage:
  - None. It uses only forecast-state humidity, initialized pressure, fixed
    sigma weights, and fixed bounds.
- Physical plausibility:
  - Moderate to high. Dry-air mass is distinct from water-vapor mass, but this
    remains an approximation because the dry core does not include precipitation
    or water phase changes.
- Rollback complexity:
  - Low. Remove one adapter option, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_dry_air_ps`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_dry_air_ps --workers 4`
  - Support requires primary delta at least `+0.002` against cached
    `dino_hsl2_mass_dse`, clean diagnostics, and no fixed RMSE guardrail
    failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_dry_air_ps --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that dry/moist
    surface-pressure accounting is not a material remaining error source. Any
    early MSLP or Z500 guardrail failure would show that changing the mass
    coordinate is too disruptive for the current incumbent.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` initializes
    `log_surface_pressure` from analyzed surface pressure and carries humidity
    as a passive tracer when complete humidity channels are present.
  - Dynamaxx history:
    `.logbook/history/2026-06-17_18-02-45_bounded-moist-virtual-temperature-dynamics/decision.md`
    and
    `.logbook/history/2026-06-17_19-31-12_bounded-saturation-adjustment/decision.md`
    are negative evidence against active moist pressure-gradient and latent
    heating paths.
  - Trenberth, K. E. and Smith, L. 2005. The Mass of the Atmosphere: A
    Constraint on Global Analyses. Journal of Climate.
    https://doi.org/10.1175/JCLI-3299.1
  - Diamantakis, M. and Flemming, J. 2014. Global mass fixer algorithms for
    conservative tracer transport in the ECMWF model. Geoscientific Model
    Development. https://doi.org/10.5194/gmd-7-965-2014
  - ECMWF IFS Documentation CY49R1, Part III: Dynamics and Numerical
    Procedures, documents dry-mass and tracer mass-fixer considerations in an
    operational semi-Lagrangian model.
    https://www.ecmwf.int/en/publications/ifs-documentation

## Researcher Notes

This is not a duplicate of scrapped passive-humidity mass fixing, which only
renormalized the humidity tracer. It instead changes the dry-air pressure
coordinate and reconstructs total pressure for output. It is also distinct from
low-mode virtual-temperature pressure-gradient proposals because humidity never
enters the active pressure-gradient or thermodynamic tendencies.

The recent DSE failures argue against more aggressive DSE pressure-work
corrections. This proposal avoids the DSE-HSL branch itself and tests a
separate mass-definition assumption that the accepted dry mass-DSE incumbent
still inherits from the adapter.

## Evaluator Notes

### 2026-06-24T11:59:50Z

Decision: move to `scrap`; ranked 3 of 3 new proposals. Ready now: no.

The dry-air versus water-vapor mass distinction is physically real, and
Trenberth and Smith support separating dry-air mass from total atmospheric water
vapor mass. That evidence does not make this proposal a good next model
selection candidate. The mechanism would initialize temperature, winds, and
humidity on the incumbent total-pressure sigma mapping, then replace the
dynamic `log_surface_pressure` with a humidity-derived dry-air pressure and
later reconstruct total pressure from passively forecast humidity for MSLP and
pressure-level output. That is a coordinate and diagnostic split, not just
benign bookkeeping.

The expected benefit is small, while the risk is concentrated exactly where
recent candidates have failed: pressure, hydrostatic thickness, and early MSLP
guardrails. Hydrostatic inversion of mass-DSE produced a `-0.030209299275616164`
iteration delta and early MSLP guardrail failure, pressure-thickness correction
regressed by `-0.006172261163569502`, and DSE-consistent sigma initialization
was slightly negative. Earlier active humidity feedback also regressed badly,
and passive-humidity-only changes were essentially score-irrelevant. This
proposal would again trust passive humidity to alter a mass-coordinate path and
output pressure reconstruction.

Do not implement without stronger read-only evidence: first quantify dry/total
pressure mismatch against incumbent MSLP/Z500 errors and specify a coordinate-
consistent initialization/output path that does not use drifting passive
humidity to repair pressure diagnostics. As written, it is too likely to spend
an iteration on a high-risk pressure-coordinate perturbation with little chance
of clearing the fixed `+0.002` gate.
