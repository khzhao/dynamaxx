---
schema_version: 1
slug: ocean-highmode-t2m-memory
title: Ocean High-Mode 2 m Temperature Residual Memory
status: ready
created_at: 2026-06-29T17:00:36Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
expected_code_paths:
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

# Ocean High-Mode 2 m Temperature Residual Memory

## Hypothesis

The incumbent still has strongly negative `2m_temperature` skill versus
persistence at every fixed iteration lead, while recent accepted T2m gains came
from bounded output-side mechanisms: land/ocean low-mode residual memory and the
bulk Richardson 2 m diagnostic. The accepted low-mode memory deliberately keeps
only broad land/ocean structure. That leaves a different, still plausible error
source: ocean and marginal-ocean screen-temperature residuals with spatial
structure finer than the retained broad modes but slower decorrelation than
free-atmospheric weather noise because the ocean mixed layer stores thermal
anomalies.

An ocean-only, capped high-mode residual-memory component can test that missing
surface thermal inertia without touching land, soil-type partitions, prognostic
thermal back-coupling, lower-tropospheric air-mass blends, Ekman stress, or the
fixed evaluation protocol.

## Mechanism

Register a side-by-side candidate such as `dino_ri2m_ekman_ocean_t2m_himem`.
Preserve the complete incumbent rollout and output path except for the final
`2m_temperature` residual correction.

For `2m_temperature` only:

- compute the incumbent lead-zero residual after the RI2m raw diagnostic:
  analyzed T2m minus raw model T2m;
- compute the same low-mode residual component already used by the accepted
  land/ocean memory path;
- define a residual remainder by subtracting that accepted broad component from
  the total T2m residual;
- multiply the remainder by a smooth open-ocean weight from the existing
  `land_sea_mask` loader, with exact incumbent fallback if the mask is missing
  or invalid;
- filter the weighted remainder with a fixed high-mode band, for example the
  complement of the accepted low-mode mask with a broad taper to suppress
  grid-scale ringing;
- add a late-ramped, finite-decay memory of that high-mode ocean residual to
  the incumbent corrected T2m, with a strict cap such as a sub-kelvin maximum
  additional correction per lead;
- preserve lead zero exactly and leave all non-T2m channels byte-identical to
  the incumbent after output packing.

This is not a hard persistence clamp. The candidate does not bound the whole
forecast anomaly around the initial state; it carries only the initialized,
ocean-weighted, high-mode part of the raw diagnostic residual after the accepted
broad component has been removed.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused residual-correction tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory derived from `ekman_coupled_dinosaur_dycore_model()`.
- API changes:
  - None. Forecast input, forecast output variables, target variables, leads,
    metric definitions, and evaluation protocols remain fixed.
- Tests to update:
  - Verify zero-ocean and missing-mask cases reproduce the incumbent exactly.
  - Verify non-T2m channels are unchanged.
  - Verify the added residual is zero at lead zero, late-ramped, finite, capped,
    and ocean-weighted.
  - Verify a synthetic low-mode residual is removed before the high-mode memory
    path so the proposal cannot duplicate accepted low-mode memory.
  - Verify registry construction and all incumbent flags are preserved except
    the new high-mode ocean T2m option.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3-15 over ocean and coastal grid cells if the
    remaining T2m error includes slowly decorrelating mixed-layer thermal
    structure.
  - Aggregate primary score because T2m is the incumbent's clearest remaining
    fixed-score weakness.
- Expected neutral metrics:
  - `mean_sea_level_pressure`, `geopotential_500`, and
    `10m_u_component_of_wind`, because the trajectory, pressure output, Ekman
    closure, and wind diagnostics are unchanged.
- Possible regressions:
  - High-mode residuals may mostly be representativeness noise, especially near
    sharp coastlines or western boundary currents at the coarse grid.
  - Too much late memory can over-persist real synoptic air-mass changes above
    the ocean.

## Risks

- Numerical stability:
  - Low. This is a bounded output-side T2m correction after a finite rollout.
- Compute cost:
  - Low. It reuses the existing land-sea fraction loader and spectral residual
    utilities.
- Data leakage:
  - Low. It uses only lead-zero analyzed state, forecast lead, static land-sea
    mask, and fixed predeclared constants.
- Physical plausibility:
  - Moderate. Ocean mixed-layer thermal inertia supports slower decorrelation
    of marine surface temperature anomalies, but using T2m residuals as a proxy
    for missing SST/skin-temperature memory is still reduced-order.
- Rollback complexity:
  - Low. Remove one residual option/helper branch, one factory/export, one
    registry key, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_ekman_ocean_t2m_himem`.
  - Require finite forecasts and zero diagnostics issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_ocean_t2m_himem --workers 4`.
  - Compare against cached incumbent iteration primary
    `-0.16500618979404214`; support requires delta at least `+0.002`, clean
    diagnostics, no day-1-through-day-5 early RMSE guardrail failure, and no
    variable-by-lead guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_ekman_ocean_t2m_himem --workers 4`
    only after iteration promotion.
  - Compare against cached incumbent validation primary
    `-0.16591150807771451`; require validation delta at least `+0.001`.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the remaining
    T2m error is not recoverable ocean high-mode memory. Any early T2m guardrail
    failure would show the ramp or cap is too intrusive.

## Citations

- Local evidence:
  `outputs/eval/iteration_dino_ri2m_ekman_coupled.csv` reports negative
  `2m_temperature` skill versus persistence at every fixed lead, including
  `-0.25656740417490953` at 24 h and `-0.95668520337298` at 120 h.
- Local accepted evidence:
  `.logbook/history/2026-06-27_18-53-15_land-ocean-lowmode-t2m-memory/decision.md`
  accepted broad land/ocean low-mode T2m memory, and
  `.logbook/history/2026-06-27_23-08-54_bulk-richardson-2m-temperature-diagnostic/decision.md`
  accepted a bounded RI2m diagnostic.
- Local negative evidence:
  `.logbook/history/2026-06-28_02-44-14_lower-tropospheric-airmass-t2m-diagnostic`
  rejected lower-airmass output blending, and
  `.logbook/history/2026-06-28_21-00-23_soil-type-land-t2m-memory-partition`
  found static land soil class directionally useful but subthreshold.
- Deser, C., Alexander, M. A., Xie, S.-P., and Phillips, A. S. 2010. "Sea
  Surface Temperature Variability: Patterns and Mechanisms." Annual Review of
  Marine Science. https://doi.org/10.1146/annurev-marine-120408-151453
- ECMWF Newsletter 178. "Improved two-metre temperature forecasts in the 2024
  upgrade." https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade
- Rasp, S. et al. 2024. "WeatherBench 2: A benchmark for the next generation of
  data-driven global weather models." Journal of Advances in Modeling Earth
  Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This proposal uses the accepted T2m residual machinery but deliberately attacks
a component the accepted low-mode memory excluded. It is not the scrapped hard
T2m anomaly envelope, because it does not cap the total T2m forecast departure
from the initial analysis. It is not the rejected lower-tropospheric airmass
blend, because it does not use pressure-level air temperature as a final T2m
substitute. It is not the subthreshold soil-type partition, because it makes no
land static-soil change. It also avoids the latest Ekman family entirely:
stress, pumping, pressure work, and wind diagnostics are unchanged.

## Evaluator Notes

### 2026-06-29T17:05:26Z

Decision: move to `ready`; rank 1 of 2 reviewed proposals and the only ready
proposal from this batch.

This is the best next model-selection candidate. The cached incumbent artifacts
show `2m_temperature` remains worse than persistence at every fixed iteration
lead, while the proposal changes only the final T2m residual path and should
leave MSLP, Z500, U10, Ekman stress, pressure pumping, WTG, vertical-DSE, and
the fixed evaluation protocol unchanged. Local history supports this class of
bounded output-side T2m work: land-sea-aware residual memory, low-mode
land/ocean T2m memory, and the RI2m diagnostic all cleared fixed gates.

This is not an exact duplicate of the accepted land/ocean low-mode memory. The
incumbent already has land-sea-aware residual decay and a broad low-mode
land/ocean reservoir, but this proposal tests the remaining ocean-weighted
high-mode residual remainder after that broad component is removed. That makes
it a narrower follow-up to the accepted T2m lineage rather than a retry of the
same low-mode mechanism. The risk is also interpretable: if high-mode ocean
residuals are mostly weather or coastline representativeness noise, iteration
should be clean but neutral or negative, with non-T2m channels effectively
unchanged.

Implement before `helmholtz-projected-ekman-coupling`. Use one side-by-side
candidate, one fixed late ramp and cap, no parameter sweep, exact lead-zero
preservation, exact missing-mask/incumbent fallback, and tests proving non-T2m
channels are unchanged. The fixed gates should compare against the cached
`dino_ri2m_ekman_coupled` artifacts unless the Orchestrator finds a concrete
cache invalidation.
