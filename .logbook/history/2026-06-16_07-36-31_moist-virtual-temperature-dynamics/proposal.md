---
schema_version: 1
slug: moist-virtual-temperature-dynamics
title: Enable Moist Virtual-Temperature Dynamics
status: ready
created_at: 2026-06-16T07:21:43Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Enable Moist Virtual-Temperature Dynamics

## Hypothesis

The incumbent Dinosaur adapter carries specific humidity as an optional tracer but disables humidity feedbacks in the primitive-equation dynamics by default. Enabling the existing moist equation path should improve hydrostatic thickness, pressure-gradient, geopotential, and mass-field evolution because water vapor changes virtual temperature and therefore the density and geopotential relationship. The fixed WeatherBench2 score includes mean sea-level pressure and 500 hPa geopotential, so this is aimed at two directly scored large-scale fields while remaining physically interpretable.

## Mechanism

Use the existing `PrimitiveEquationsSigma` moist branch by setting `use_humidity_in_dynamics=True` when a complete pressure-level specific-humidity stack is present. The adapter already detects complete humidity stacks, stores humidity as a tracer during pressure-to-sigma initialization, and passes a `humidity_key` into the equation constructor when this option is enabled. The candidate would make that path active for the default Dinosaur candidate, so virtual-temperature corrections enter geopotential and pressure-gradient terms during the rollout.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Registry changes:
  - None expected for an in-place candidate evaluated as `dinosaur`. If the Orchestrator wants a side-by-side registered variant, add a small factory only after selection.
- API changes:
  - None. The full WeatherBench2 initial state already includes pressure-level `specific_humidity_*` channels, and the adapter already accepts them through `ForecastInput.initial_state`.
- Tests to update:
  - Add or extend a helper test showing that the default trajectory constructor selects a moist equation when humidity channels are available.
  - Preserve the dry path for states without a complete humidity stack.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500`, especially at days 1-7 where virtual-temperature corrections affect thickness and balanced pressure gradients.
  - `mean_sea_level_pressure`, especially in humid tropical and storm-track cases where moisture changes column density.
  - Secondary improvement in `2m_temperature` if lower-tropospheric thermal evolution becomes less dry-biased.
- Expected neutral metrics:
  - `10m_u_component_of_wind` may be mostly neutral except where pressure-gradient changes alter synoptic wind.
- Possible regressions:
  - If humidity is passively advected without condensation, precipitation, radiation, or boundary-layer sinks, the moisture field may drift and over-correct virtual temperature at longer leads.
  - Numerical stiffness may increase in very humid columns if pressure-gradient residuals become larger than in the dry split.

## Risks

- Numerical stability:
  - Moderate. The moist equation code path exists upstream, but it has not been the default in this adapter. Fast gate should catch non-finite rollouts.
- Compute cost:
  - Low to moderate. One extra tracer is transformed and advected, increasing spectral transforms and memory modestly.
- Data leakage:
  - Low. The proposal uses only initial specific humidity channels, not future targets.
- Physical plausibility:
  - Mixed. Moist virtual-temperature dynamics are physically justified, but moisture has no modeled phase changes or sources in this candidate.
- Rollback complexity:
  - Low. The change can be isolated to one adapter default and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur`.
  - Require finite forecasts and no diagnostic issue increase relative to the incumbent.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur --workers 4`.
  - Support for the hypothesis is a lower primary score with improvement in `geopotential_500` or `mean_sea_level_pressure` that is not offset by a larger near-surface regression.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur --workers 4` only if the iteration gate improves.
  - Acceptability depends on validation primary-score improvement under the fixed protocol.
- Outcome that would falsify the hypothesis:
  - Any repeatable non-finite forecasts, or an iteration primary-score regression dominated by MSLP/Z500 degradation, would indicate that passive-moist dynamics are harming this benchmark setup.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently defaults `use_humidity_in_dynamics=False` and routes to the moist equation only when enabled.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` implements humidity corrections through virtual temperature and moist pressure-gradient tendencies.
- NeuralGCM paper, Nature 2024: describes the Dinosaur-backed dycore as hydrostatic primitive equations with moisture and a horizontal pseudo-spectral discretization. https://www.nature.com/articles/s41586-024-07744-y
- Dinosaur upstream README: notes that Dinosaur supports dry and moist primitive equations on sigma coordinates. https://github.com/neuralgcm/dinosaur/blob/main/README.md

## Researcher Notes

The logbook history and active research directories are empty, so there is no prior duplicate or failed result. A metadata check of the WeatherBench2 source found 82 state channels, including complete pressure-level `specific_humidity_*` stacks for the same pressure levels used by temperature and winds, so the proposal does not require changing the forecast contract.

## Evaluator Notes

2026-06-16T07:24:59Z - Move to `ready`.

This is the strongest next implementation candidate. Source inspection confirms the adapter already loads complete pressure-level humidity stacks, stores humidity as a tracer, and gates moist primitive-equation dynamics behind `use_humidity_in_dynamics=False`. The expected implementation is therefore a low-surface-area default change plus focused tests, with no forecast API or registry change required.

The scientific mechanism is well supported: the local `primitive_equations.py` moist path uses specific humidity in virtual-temperature/geopotential and pressure-gradient tendencies, ECMWF IFS dynamics define virtual temperature from temperature and specific humidity in the governing equations, and the upstream Dinosaur/NeuralGCM documentation describes moist hydrostatic primitive equations on sigma coordinates. This targets mass and thickness evolution, so the expected effects plausibly touch more than one fixed metric (`mean_sea_level_pressure`, `geopotential_500`, and possibly low-level temperature/wind through changed dynamics).

Main risk is that the humidity tracer is passive here, without condensation, precipitation, radiation, or boundary-layer sinks. That could introduce long-lead humid-column bias, but the rollback path is simple and the fast/iteration gates should expose instability or broad degradation. Compared with the other proposals, this has the best balance of mechanistic physical benefit, small implementation scope, and low leakage risk.
