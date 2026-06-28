---
schema_version: 1
slug: static-stability-gated-ocean-heat-flux
title: Static-Stability-Gated Ocean Heat Flux
status: staging
created_at: 2026-06-23T08:48:19Z
author_role: Researcher
target_model: dino_hsl2_theta
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

# Static-Stability-Gated Ocean Heat Flux

## Hypothesis

The accepted ocean bulk sensible heat flux was a large positive step, while the
later SST/sea-ice anchor and snow/soil reservoir refinements were effectively
neutral. The current incumbent still shows a growing negative `2m_temperature`
bias in cached iteration and validation artifacts, but another unconditional
lower-boundary flux is unlikely to move the score. A stronger mechanism is to
apply the existing ocean heat-exchange tendency preferentially when the lowest
model column is statically stable, where weak vertical exchange can trap
near-surface cold bias over ocean. This changes the *coupling regime* rather
than adding a new anchor or reservoir.

## Mechanism

Register a side-by-side model such as `dino_hsl2_theta_ocean_stabflux`.
Preserve the accepted ocean bulk sensible heat-flux formulation and every
`dino_hsl2_theta` option, but multiply the ocean-only flux by a bounded
stability factor diagnosed from the lowest two sigma layers:

- compute dry potential temperature in the lowest two sigma layers using the
  current forecast state and sigma pressure;
- diagnose a bulk lower-column static-stability measure, such as positive
  lower-minus-upper potential temperature difference or a simple Brunt-Vaisala
  proxy in model coordinates;
- increase the existing ocean heat-flux exchange rate only under stable
  near-surface stratification, with a conservative cap such as at most `2x` the
  accepted rate and the same per-step temperature increment cap already used by
  `_OceanBulkSensibleHeatFluxForcingSigma`;
- leave unstable or neutral columns on the accepted ocean bulk path;
- retain ocean mask weighting, finite fallback, HSL2 theta transport, pressure
  tendencies, residual corrections, and output variables unchanged.

This is still a forecast-state-only physical parameterization. It does not use
future truth, validation statistics, new target variables, or changed lead
times.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for `dino_hsl2_theta_ocean_stabflux`.
- API changes:
  - None. Forecast contract, target variables, split definitions, and metrics
    stay fixed.
- Tests to update:
  - Verify neutral/unstable lower-column cases exactly reproduce accepted ocean
    bulk heat flux.
  - Verify stable columns increase exchange rate only up to the fixed cap.
  - Verify the existing maximum per-step temperature increment is still
    enforced after stability scaling.
  - Verify missing ocean mask or nonfinite stability diagnostics fall back to
    the accepted flux.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3-15 over ocean-dominated regions if stable
    boundary layers are under-coupled in the accepted flux.
  - `geopotential_500` may improve slightly through warmer lower-column
    thickness where cold bias is systematic.
- Expected neutral metrics:
  - `mean_sea_level_pressure` should remain close because the same per-step heat
    cap and ocean weighting are preserved.
  - `10m_u_component_of_wind` should be nearly neutral because momentum and the
    Richardson wind diagnostic are unchanged.
- Possible regressions:
  - Extra ocean heating can worsen warm biases or MSLP if the lower-column cold
    bias is not caused by stable boundary-layer decoupling.
  - If stability diagnostics are noisy, the factor can add spatial texture to
    the lower thermal field.

## Risks

- Numerical stability:
  - Low to moderate. The existing heat-flux cap remains the main stability
    guard; the new multiplier is bounded and finite-guarded.
- Compute cost:
  - Low. It adds local potential-temperature diagnostics in an already active
    forcing path.
- Data leakage:
  - None. It uses only forecast state, the existing land-sea/ocean mask path,
    and fixed constants.
- Physical plausibility:
  - Moderate. Static stability controls boundary-layer coupling, but this is a
    simple bulk surrogate rather than a full turbulent ocean-atmosphere scheme.
- Rollback complexity:
  - Low. Remove one flag/helper, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_theta_ocean_stabflux`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_theta_ocean_stabflux --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-to-5 RMSE guardrail failure, and no variable-lead guardrail
    failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_theta_ocean_stabflux --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero delta would show the accepted ocean bulk flux already
    captures the useful lower-boundary signal. Any early MSLP or Z500 guardrail
    failure would show the added thermal coupling is too aggressive.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/decision.md`
  accepted ocean-only bulk sensible heat exchange with iteration delta
  `+0.0714278996861683` and validation delta `+0.07032535118514627`.
- Dynamaxx history:
  `.logbook/history/2026-06-22_07-54-50_sst-sea-ice-ocean-flux-anchor/decision.md`
  and `.logbook/history/2026-06-22_10-08-39_snow-soil-land-thermal-reservoir/decision.md`
  rejected later lower-boundary refinements as clean but nearly neutral.
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_OceanBulkSensibleHeatFluxForcingSigma`, ocean mask weighting, and the fixed
  maximum per-step temperature increment.
- Holtslag, A. A. M. and Boville, B. A. 1993. Local versus nonlocal boundary-layer
  diffusion in a global climate model. Journal of Climate.
  https://doi.org/10.1175/1520-0442(1993)006%3C1825:LVNBLD%3E2.0.CO;2
- Large, W. G., McWilliams, J. C., and Doney, S. C. 1994. Oceanic vertical
  mixing: A review and a model with a nonlocal boundary layer parameterization.
  Reviews of Geophysics. https://doi.org/10.1029/94RG01872
- ECMWF IFS Documentation Part IV, Physical Processes, describes stability-
  dependent turbulent diffusion and surface exchange.
  https://www.ecmwf.int/en/elibrary/81368-ifs-documentation-cy48r1-part-iv-physical-processes

## Researcher Notes

This is not a duplicate of the accepted ocean bulk sensible heat-flux candidate:
that candidate used one fixed exchange-rate formula wherever ocean weight was
available. This proposal changes only the stability dependence of that accepted
source while preserving the same anchor, mask, cap, and fallback.

It is also not another SST/sea-ice anchor or land reservoir variant. Those
recent follow-ups changed boundary-condition information and were nearly
neutral. This proposal changes coupling strength only in stable near-surface
ocean columns, which is a different physical mechanism and is decorrelated from
the pressure-work and momentum proposals in this batch.

## Evaluator Notes

### 2026-06-23T08:52:24Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

The idea is physically plausible and implementable without changing the
forecast contract. Boundary-layer literature supports stability-dependent
turbulent exchange, and source inspection confirms the accepted ocean-bulk heat
flux is isolated behind `_OceanBulkSensibleHeatFluxForcingSigma` with an ocean
weight, wind-dependent exchange rate, per-step temperature cap, and finite
fallback. A stability multiplier could therefore be tested as a local
side-by-side candidate while keeping target variables, splits, metrics, and
lead times unchanged.

Do not put it in `ready` for the next run. After the accepted ocean bulk heat
flux, two lower-boundary refinements were clean but effectively neutral:
SST/sea-ice anchoring moved iteration by only
`+0.0000030296370109317294`, and the snow/soil reservoir moved by only
`+0.0000005876598810350409`. This proposal has a better mechanism than those
anchor/reservoir variants, but it is still another capped lower-layer thermal
addition and is less likely than the pressure-work candidate to clear the
fixed `+0.002` iteration gate.

Keep staged as a later, independent thermal-coupling fallback. If promoted,
use one fixed conservative stability factor, no coefficient sweep, no new
boundary-condition data, no incumbent rerun unless the leaderboard cache is
invalid, and tests proving unstable/neutral columns reproduce the accepted
ocean-bulk path exactly.
