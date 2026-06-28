---
schema_version: 1
slug: dry-consistent-geopotential-diagnostic
title: Use Dry-Consistent Geopotential Diagnostics for the Dry Rollout
status: ready
created_at: 2026-06-17T09:06:43Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Use Dry-Consistent Geopotential Diagnostics for the Dry Rollout

## Hypothesis

The incumbent forecast dynamics are dry: `use_humidity_in_dynamics=False`.
However, when the input contains specific humidity, the adapter still carries it
as a passive tracer and passes that tracer into
`primitive_equations.get_geopotential_on_sigma` during output reconstruction.
That means `geopotential_500` can include moisture-dependent virtual-temperature
structure that did not feed back on the dry pressure-gradient, divergence, or
temperature tendencies that produced the forecast trajectory.

Using a dry hydrostatic geopotential diagnostic for the dry rollout may improve
Z500 consistency by making the pressure-level geopotential output match the
actual thermodynamic equation that was integrated. This is materially different
from enabling moist dynamics, which already failed fast with nonfinite output.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential`.
Preserve the incumbent state initialization, DFI, weak thermal Held-Suarez
relaxation, near-surface residuals, log-pressure remap, layer-mean hydrostatic
temperature initialization, passive humidity tracer transport, zero orography,
finite output interpolation, vertical advection, T80 truncation, 900 s inner
step, and public forecast API.

Add a guarded output option for geopotential reconstruction only:

- when the forward equation is dry, call
  `primitive_equations.get_geopotential_on_sigma` with
  `specific_humidity=None`;
- continue carrying and outputting specific humidity if it is requested, so this
  is not a humidity-output contract change;
- keep humidity use inside the accepted hydrostatic layer-mean initialization,
  where analyzed virtual-temperature thickness is converted to dry temperature
  before the dry forecast starts;
- leave temperature, winds, surface pressure, MSLP, near-surface residuals, and
  pressure-level interpolation unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential`.
- API changes:
  - None. Forecast input and output variables, shapes, lead times, and metrics
    remain unchanged.
- Tests to update:
  - Unit-test geopotential reconstruction with nonzero humidity and verify the
    candidate ignores humidity only for geopotential when the rollout is dry.
  - Verify humidity channels are still emitted unchanged when requested.
  - Verify temperature, winds, MSLP, surface pressure, and near-surface residual
    behavior are unchanged by the dry-geopotential option.
  - Verify the candidate factory preserves all incumbent flags and registry
    construction.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at early and medium leads if passive humidity currently
    injects output-only virtual-temperature thickness inconsistent with the dry
    trajectory.
  - Primary score may improve with little guardrail risk because only one fixed
    target channel changes.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and `mean_sea_level_pressure`
    should be exactly neutral apart from roundoff.
- Possible regressions:
  - Real-atmosphere geopotential is hydrostatically related to virtual
    temperature; removing humidity from the diagnostic could worsen tropical or
    moist-storm Z500 where moisture effects are physically important.
  - If passive humidity is already helping compensate for dry-model thermal
    biases, the candidate may regress Z500 despite being internally consistent.

## Risks

- Numerical stability:
  - Low. This is output-only and removes one diagnostic moisture factor.
- Compute cost:
  - Low. It may be marginally cheaper because output geopotential no longer
    multiplies by specific humidity for the candidate path.
- Data leakage:
  - Low. It uses no future truth, fitted coefficients, validation statistics, or
    new data sources.
- Physical plausibility:
  - Moderate. Dry consistency is numerically coherent for a dry primitive-
    equation rollout, but the real atmosphere's hydrostatic geopotential depends
    on virtual temperature.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter flag and side-by-side
    factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, no fixed RMSE guardrail failure, and improvement or
    neutrality in `geopotential_500`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_geopotential --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or sub-threshold iteration delta, especially from worse
    `geopotential_500`, would show that virtual-temperature output diagnostics
    are more useful than dry consistency for this benchmark. Any movement in
    MSLP or near-surface channels would indicate an implementation bug.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` constructs
  the incumbent with `use_humidity_in_dynamics=False` while still passing
  available humidity tracers into `get_geopotential_on_sigma` during output
  reconstruction.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  documents that `get_geopotential_on_sigma` computes dry geopotential when
  `specific_humidity` is `None` and moisture-adjusted geopotential otherwise.
- History: `.logbook/history/2026-06-16_07-36-31_moist-virtual-temperature-dynamics/decision.md`
  rejected full moist dynamics after the fast gate reported nonfinite forecasts,
  so this proposal deliberately avoids changing prognostic moist dynamics.
- History: `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted humidity-aware hydrostatic initialization converted to dry
  temperature before the dry rollout; this proposal preserves that accepted
  initialization path.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
  Survey, second edition. Elsevier. The hydrostatic relation uses virtual
  temperature for moist air, which frames the physical tradeoff in this dry
  diagnostic proposal.

## Researcher Notes

This is not a repeat of the rejected moist virtual-temperature dynamics
candidate. That candidate changed the prognostic equations and failed the fast
gate with nonfinite forecasts. This proposal changes only a geopotential output
diagnostic for the existing dry rollout and should leave all non-geopotential
fixed targets unchanged.

It is also distinct from staged `geopotential-datum-output-correction`: no
lead-zero residual, column offset, terrain datum, or MSLP change is introduced.
It is not a pressure-level output remap, conservative initialization remap,
hydrostatic derivative variant, damping/timestep/resolution tweak, or top
sponge. The core scientific question is whether a dry model should score better
when its Z500 diagnostic is reconstructed from the dry thermal state it actually
integrated.

## Evaluator Notes

2026-06-17T09:09:07Z - Move to `ready`; rank 1 of 5 active ideas.

This is the strongest next dycore iteration candidate because it is a narrow,
physically interpretable diagnostic-consistency test for the current dry
incumbent. Source inspection confirms the incumbent sets
`use_humidity_in_dynamics=False` for the rollout equation while
`dinosaur_state_to_weather_state` still passes passive humidity into
`get_geopotential_on_sigma` when reconstructing geopotential. The candidate can
therefore be implemented as a side-by-side adapter flag that changes only
geopotential reconstruction for a dry forecast and keeps humidity available for
passive output and the accepted hydrostatic layer-mean initialization.

Relevant history supports this ranking. Full moist virtual-temperature dynamics
failed the fast gate with `nonfinite_forecast`, so this proposal correctly
avoids changing prognostic moist dynamics. The accepted log-pressure,
hydrostatic-thickness, and layer-mean hydrostatic initialization sequence
improved primary score while preserving the dry rollout and current output
contract. The rejected log-pressure output interpolation and terrain-aware
orography records warn that output-path changes can damage guardrails, but this
proposal is narrower than those failures: it changes one scored channel, uses no
lead-zero truth residual, and should leave `2m_temperature`,
`10m_u_component_of_wind`, `mean_sea_level_pressure`, surface pressure, winds,
temperature, and humidity unchanged apart from roundoff.

The main risk is physical: real-atmosphere geopotential is related to virtual
temperature, so ignoring humidity may worsen Z500 even though it is internally
consistent with the dry model. If promoted, tests must prove strict invariance
for untouched variables and verify that the humidity-output contract is
unchanged. Any movement outside geopotential should be treated as an
implementation bug before a full iteration run.
