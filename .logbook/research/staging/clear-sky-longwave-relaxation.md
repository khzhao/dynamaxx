---
schema_version: 1
slug: clear-sky-longwave-relaxation
title: Add Bounded Clear-Sky Longwave Temperature Relaxation
status: staging
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

# Add Bounded Clear-Sky Longwave Temperature Relaxation

## Hypothesis

The incumbent has weak Held-Suarez thermal relaxation and an ocean sensible heat
flux, but no explicit longwave cooling or temperature-dependent radiative
relaxation. Prior solar and humidity-radiation ideas were risky because they
added local insolation or coupled thermal tendencies to passive humidity. A dry,
area-mean-neutral longwave anomaly relaxation is more bounded: warm columns
cool slightly faster than layer-mean columns and cold columns warm slightly
relative to the same layer mean, with no humidity, clouds, or new global heat
source.

Because the accepted mass-DSE HSL path improved thermal transport, remaining
medium-lead error may include lower- and middle-tropospheric thermal-amplitude
drift rather than transport phase alone. A weak Stefan-Boltzmann-inspired
temperature-anomaly relaxation may reduce `2m_temperature` and Z500 thickness
drift while leaving mass continuity and DSE transport unchanged.

## Mechanism

Register a side-by-side candidate such as `dino_hsl2_mass_dse_lw_relax` derived
from `dino_hsl2_mass_dse`.

For the candidate only:

- compose an explicit thermal forcing with the incumbent primitive equation and
  existing weak-HS/ocean forcing path;
- diagnose nodal full temperature `T = T_ref + temperature_variation`;
- compute a layerwise area-weighted anomaly of `T**4`, convert it to a
  temperature tendency using a fixed linearization scale `4 * T0**3`, and apply
  the tendency with negative sign so locally warm anomalies cool and locally
  cold anomalies relax back;
- use a fixed vertical taper concentrated between about `sigma=0.25` and
  `sigma=0.9`, with little or no forcing at the model top and no special
  near-surface residual changes;
- cap the local tendency magnitude to a predetermined weak value such as
  `0.15 K day^-1`;
- subtract the layerwise area mean exactly before converting to modal space so
  the new forcing does not duplicate the accepted global weak-HS heat source;
- leave vorticity, divergence, `log_surface_pressure`, humidity tracers,
  DFI, HSL geometry, DSE transport, ocean heat-flux amplitude, residual
  corrections, outputs, and protocols unchanged;
- fall back to zero added longwave tendency if temperature, anomaly, or modal
  forcing diagnostics are nonfinite.

This is a reduced clear-sky radiative damping proxy, not a full radiation
scheme and not a retuning of Held-Suarez equilibrium temperatures.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry key for
    `dino_hsl2_mass_dse_lw_relax`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, metrics, and
    protocols stay fixed.
- Tests to update:
  - Verify horizontally uniform temperature produces zero added tendency.
  - Verify the tendency cools warm anomalies and warms cold anomalies with zero
    area mean by layer.
  - Verify the cap and vertical taper are finite, deterministic, and unchanged
    by DFI or output variable selection.
  - Verify the forcing changes only `temperature_variation` tendency.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and long leads if lower-tropospheric thermal
    anomaly drift remains after the accepted residual and ocean heat-flux paths.
  - `geopotential_500` if weak thermal-amplitude relaxation reduces column
    thickness drift without mass-field shocks.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because momentum
    tendencies and the 10 m diagnostic are unchanged.
  - `mean_sea_level_pressure` should be mostly neutral if the layerwise
    area-mean removal protects global thermal mass balance.
- Possible regressions:
  - Real longwave radiation depends on humidity, clouds, trace gases, and
    vertical flux divergence; a dry anomaly proxy can damp useful baroclinic
    structure.
  - Even weak thermal damping can alter storm-track phase and indirectly harm
    MSLP or Z500 guardrails.

## Risks

- Numerical stability:
  - Low to moderate. The tendency is bounded and mean-neutral, but applies every
    positive-time step.
- Compute cost:
  - Low. It adds local temperature algebra and layerwise weighted reductions.
- Data leakage:
  - None. It uses only forecast temperature, fixed grid weights, and fixed
    physical constants.
- Physical plausibility:
  - Moderate. The Stefan-Boltzmann nonlinearity motivates stronger relaxation
    of warm anomalies, but this is not a spectrally resolved radiative transfer
    calculation.
- Rollback complexity:
  - Low. Remove one forcing wrapper/flag, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_lw_relax`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_lw_relax --workers 4`
  - Support requires primary delta at least `+0.002` against cached
    `dino_hsl2_mass_dse`, clean diagnostics, and no fixed RMSE guardrail
    failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_lw_relax --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that missing dry
    longwave anomaly relaxation is not a material remaining error source. Any
    early MSLP, Z500, or 10 m wind guardrail failure would show that the thermal
    damping disrupts accepted balance.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` composes
    weak Held-Suarez and ocean sensible-heat forcing but has no longwave
    radiative tendency.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_23-51-06_calendar-aware-solar-relaxation/decision.md`
    is negative evidence against broad solar equilibrium changes; this proposal
    uses no calendar or solar geometry.
  - Dynamaxx research:
    `.logbook/research/scrap/humidity-weighted-radiative-temperature-relaxation.md`
    is negative evidence against humidity-coupled radiation proxies; this
    proposal uses temperature only.
  - Manabe, S. and Strickler, R. F. 1964. Thermal Equilibrium of the Atmosphere
    with a Convective Adjustment. Journal of the Atmospheric Sciences.
    https://doi.org/10.1175/1520-0469(1964)021%3C0361:TEOTAW%3E2.0.CO;2
  - Mlawer, E. J., Taubman, S. J., Brown, P. D., Iacono, M. J., and Clough,
    S. A. 1997. Radiative transfer for inhomogeneous atmospheres: RRTM, a
    validated correlated-k model for the longwave. Journal of Geophysical
    Research. https://doi.org/10.1029/97JD00237
  - Stephens, G. L. 1984. The Parameterization of Radiation for Numerical
    Weather Prediction and Climate Models. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1984)112%3C0826:TPORFN%3E2.0.CO;2

## Researcher Notes

This proposal is intentionally not another DSE-HSL correction, pressure-work
branch, vertical transport change, humidity activation, or solar-phase forcing.
It targets a separate physical-process gap with a bounded, dry, mean-neutral
thermal relaxation.

The recent vertical-DSE candidate showed that thermal changes can improve
aggregate score while failing MSLP guardrails. This proposal therefore caps the
added tendency tightly and removes layer means so the first evaluation signal
should be a broad thermal-amplitude effect, not an immediate pressure shock.

## Evaluator Notes

### 2026-06-24T11:59:50Z

Decision: move to `staging`; ranked 2 of 3 new proposals. Ready now: no.

The proposal is plausible enough to preserve because it targets a real missing
process with a bounded, dry, area-mean-neutral temperature tendency and avoids
coupling the rollout to passive humidity. Literature checks support the broad
premise that longwave radiative transfer is a core atmospheric temperature
process, but they do not directly justify this reduced `T**4` anomaly forcing:
real clear-sky longwave cooling depends on vertical flux divergence, humidity,
clouds, trace gases, and pressure-temperature structure, not only local
temperature anomaly relative to a layer mean.

This is lower priority than the ocean-flux taper because its constants, taper,
and cap are more empirical and the current history is cautionary for broad
thermal forcing. Calendar-aware solar relaxation strongly regressed
`2m_temperature`, humidity-weighted radiation is already scrapped as too crude,
and staged weak-HS/tropopause thermal variants show that thermal-relaxation
changes need a more specific implementation path or bias diagnostic before
spending the next fixed iteration slot.

Keep staged as a later thermal-amplitude experiment if read-only diagnostics
show systematic lower- or mid-tropospheric temperature-amplitude drift in the
incumbent. If promoted, require zero layer-mean forcing, a short candidate name,
strict tendency caps, no humidity/cloud proxy, no coefficient sweep, and tests
showing uniform-temperature no-op behavior plus unchanged non-temperature
tendencies.
