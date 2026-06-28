---
schema_version: 1
slug: ozone-layer-upper-thermal-relaxation
title: Ozone-Layer Upper-Thermal Relaxation
status: scrap
created_at: 2026-06-27T19:00:21Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/radiation.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Ozone-Layer Upper-Thermal Relaxation

## Hypothesis

The current incumbent has strong lower- and middle-tropospheric thermodynamic
machinery, but the dry Dinosaur stack still lacks an explicit stratospheric or
upper-tropospheric radiative structure. A very weak, prescribed ozone-layer
thermal relaxation in the upper sigma levels may reduce large-scale height and
wind drift through better upper-column thermal balance while avoiding the lower
boundary, T2m residual, WTG, and vertical-DSE mechanisms that have dominated
recent experiments.

## Mechanism

Add one side-by-side candidate, for example `dino_vdse_t2m_ozone`, derived from
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`.

For this candidate only:

- keep the incumbent weak Held-Suarez equilibrium, WTG mass-DSE relaxation,
  pressure-ramped vertical-DSE increment, land/ocean T2m memory, ocean flux,
  HSL transport, DFI, residual correction, and output variables unchanged;
- use the existing model time path already required by the vertical-DSE ramp to
  compute day-of-year and solar declination, with positive-time rollout only;
- build a fixed ozone-like upper-level thermal target: a smooth vertical
  envelope centered above roughly `sigma=0.15-0.35`, a broad latitude envelope
  that strengthens poleward of the subtropics, and a small seasonal hemispheric
  shift following solar declination;
- apply a weak temperature tendency toward that target only in the upper
  thermal state, with no forcing below a fixed sigma cutoff such as `0.45`;
- remove the global layer mean of the added tendency and cap the per-step
  increment to a small value such as `0.03-0.05 K` so the term cannot become a
  hidden large heat source;
- do not use ozone observations, future truth, validation statistics, learned
  climatologies, or new target variables;
- fall back to zero added tendency if the seasonal factor, vertical mask, or
  temperature diagnostics are nonfinite.

This is narrower than broad clear-sky longwave relaxation and different from
seasonally shifting the Held-Suarez equilibrium: it applies only an upper-level,
mean-neutral, ozone-layer-like thermal term and leaves the incumbent lower
troposphere and accepted HS geometry intact.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/radiation.py` only if a small
    vectorized declination helper is needed
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one short side-by-side key such as `dino_vdse_t2m_ozone`.
- API changes:
  - None. Forecast inputs, target variables, lead times, metric definitions,
    and output shapes stay fixed.
- Tests to update:
  - Verify the candidate preserves all incumbent selectors except the
    upper-thermal option and name.
  - Verify the vertical mask is zero below the chosen cutoff and bounded above.
  - Verify layerwise area-mean tendency removal and per-step cap.
  - Verify June and December initial dates produce opposite hemispheric
    seasonal weighting while the incumbent remains unchanged.
  - Verify nonfinite seasonal or temperature diagnostics produce a zero added
    tendency.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium and late leads if upper-column thermal drift
    is aliasing into 500 hPa height through hydrostatic thickness.
  - `10m_u_component_of_wind` and `mean_sea_level_pressure` may improve slightly
    if the upper-level thermal wind structure becomes less biased.
- Expected neutral metrics:
  - `2m_temperature` should be close to neutral because the forcing is zero in
    the lower troposphere and the accepted T2m residual-memory path is
    unchanged.
- Possible regressions:
  - Upper-level thermal forcing can still alter baroclinic wave phase and
    pressure gradients, so Z500 and MSLP guardrails must be watched.
  - The effect may be too weak to clear the iteration threshold if the current
    score is dominated by lower-tropospheric T2m skill.

## Risks

- Numerical stability:
  - Low to moderate. The forcing is weak, upper-level, mean-neutral, and capped,
    but it is applied every positive step.
- Compute cost:
  - Low. It adds local mask arithmetic and no new transforms, resolution,
    workers, or output volume.
- Data leakage:
  - Low. It uses only deterministic date/latitude geometry, sigma coordinates,
    and forecast-state temperature.
- Physical plausibility:
  - Moderate. Stratospheric ozone radiative heating affects stratospheric
    temperatures and winds, but this is a reduced prescribed thermal surrogate,
    not interactive chemistry or full radiation.
- Rollback complexity:
  - Low. Remove one forcing wrapper/flag, one factory/export, one registry key,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_vdse_t2m_ozone`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_vdse_t2m_ozone --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem` incumbent, clean diagnostics, and
    no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_vdse_t2m_ozone --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show that missing
    upper ozone-like radiative structure is not a material remaining error
    source. Any early Z500, MSLP, or wind guardrail failure would show the upper
    thermal forcing disrupts accepted balance.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently initializes model
  time for the pressure-ramped vertical-DSE incumbent path and composes the
  accepted forcing/filter stack that this proposal leaves unchanged.
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/radiation.py` contains deterministic
  orbital-time and solar-geometry helpers that can provide a fixed seasonal
  phase without new data.
- Dynamaxx history:
  `.logbook/history/2026-06-16_23-51-06_calendar-aware-solar-relaxation/decision.md`
  rejected seasonally displacing the weak-HS equilibrium after `2m_temperature`
  regressions; this proposal avoids lower-level HS geometry changes.
- Dynamaxx research:
  `.logbook/research/staging/clear-sky-longwave-relaxation.md` covers broad
  dry longwave anomaly damping; this proposal is narrower, upper-level, and
  ozone-layer-shaped.
- de F. Forster, P. M. and Shine, K. P. 1997. Radiative forcing and temperature
  trends from stratospheric ozone changes. *Journal of Geophysical Research*.
  https://doi.org/10.1029/96JD03510
- Monge-Sanz, B. M. et al. 2022. A stratospheric prognostic ozone for seamless
  Earth-system models. *Atmospheric Chemistry and Physics*.
  https://doi.org/10.5194/acp-22-4277-2022
- ECMWF. Evaluating the impact of prognostic ozone in IFS NWP forecasts.
  https://www.ecmwf.int/en/elibrary/81266-evaluating-impact-prognostic-ozone-ifs-nwp-forecasts

## Researcher Notes

This proposal is decorrelated from the recent vertical-DSE failures because it
does not change vertical-DSE amplitude, timing, sheltering, hydrostatic-work
gates, or WTG support. It is also intentionally not another T2m residual-memory
extension. The main scientific question is whether a missing upper-level
radiative structure can move Z500/MSLP/wind skill without spending the
lower-boundary guardrail margin.

## Evaluator Notes

### 2026-06-27T19:07:18Z

Decision: move to `scrap`.

The physical premise is real but mismatched to the current selection problem.
Literature checks support that radiatively interactive stratospheric ozone can
affect stratospheric temperature and winds, but the current incumbent's weakest
validation channel is still `2m_temperature` with mean skill near `-0.9706`.
`geopotential_500` and `10m_u_component_of_wind` are already positive, and
`mean_sea_level_pressure` is only mildly negative relative to T2m.

This proposal would add a new upper-column thermal forcing with empirical
vertical/latitude/seasonal envelopes. That overlaps the staged clear-sky and
tropopause thermal-relaxation family while targeting channels that are not the
dominant bottleneck. Recent WTG, vertical-DSE, and thermal-forcing variants were
mostly clean but subthreshold or harmful when they perturbed accepted balance.
Under the fixed metrics, this is a lower-probability experiment than isolated
T2m or MSLP diagnostics and should not remain in the active queue.
