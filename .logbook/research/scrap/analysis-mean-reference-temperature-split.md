---
schema_version: 1
slug: analysis-mean-reference-temperature-split
title: Use an Analysis-Mean Semi-Implicit Reference Temperature
status: scrap
created_at: 2026-06-18T01:51:56Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
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

# Use an Analysis-Mean Semi-Implicit Reference Temperature

## Hypothesis

The incumbent still uses a constant 250 K semi-implicit reference temperature
for every layer, forecast time, and initial condition. That reference is used in
the gravity-wave split and in the definition of modal `temperature_variation`,
while the accepted log-pressure and hydrostatic layer-mean initialization now
provide a much more physically consistent initial sigma-column temperature.

A same-time, same-forecast analysis-mean reference profile should reduce the
explicit residual between the initialized thermal structure and the
semi-implicit linear operator without changing the absolute initialized
temperature, pressure, winds, humidity, weak Held-Suarez forcing, output
channels, or fixed protocols. The standard-atmosphere profile was safe but
essentially neutral; this proposal differs by adapting the linearization to the
actual initialized analysis rather than to a fixed climatological table.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_analysis_tref`.
Preserve the incumbent DFI span and cutoff, weak-HS coefficients and equilibrium
geometry, near-surface residual correction, log-pressure interpolation,
hydrostatic layer-mean temperature initialization, sigma grid, horizontal
diffusion, 900 s inner step, target variables, and forecast API.

For each forecast initial time independently, derive a one-dimensional reference
temperature profile from only that initial analysis:

- run the accepted pressure-level to sigma preprocessing far enough to obtain
  nodal absolute temperature on sigma layers after the incumbent log-pressure
  and hydrostatic layer-mean path;
- compute an area-weighted horizontal mean temperature for each sigma layer
  using the Dinosaur grid latitude weights;
- clip the reference profile to fixed broad physical bounds such as 180 K to
  330 K, with fallback to the 250 K incumbent profile if any layer is nonfinite;
- rebuild the Dinosaur initial state relative to this profile, so
  `reference_temperature + temperature_variation` is unchanged at initialization;
- use the same profile for the DFI initializer, the positive-time rollout, weak
  Held-Suarez absolute-temperature tendency, and output reconstruction.

This changes the numerical split of the primitive equations, not the forecast
state being initialized. It should not average across different initial times in
the same batch, because that would mix analyses from separate forecast starts.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_analysis_tref`.
- API changes:
  - None. `DycoreModel.forecast(ForecastInput) -> WeatherState` and all emitted
    variables remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent option except the new
    analysis-mean reference-temperature flag.
  - Unit-test that rebuilding a state with the analysis-mean profile preserves
    absolute nodal temperature at initialization to roundoff.
  - Verify non-temperature fields, humidity tracers, `log_surface_pressure`,
    vorticity, and divergence are unchanged by the reference-profile change.
  - Verify nonfinite or out-of-bound derived profiles fall back to the incumbent
    250 K profile.
  - Add a non-JIT finite smoke forecast and registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at early and medium leads if
    semi-implicit pressure-gradient and hydrostatic adjustment errors remain
    after the accepted hydrostatic initialization.
  - `2m_temperature` after the near-surface residual decays, if lower-column
    thermal drift is partly a linearization error.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to neutral because wind
    initialization, drag, diffusion, and output residuals are unchanged.
- Possible regressions:
  - A per-case reference profile can change the explicit/implicit partition
    enough to alter gravity-wave phase or weak-HS thermal adjustment.
  - Runtime may increase if implementation causes extra JIT compilations per
    initial time.

## Risks

- Numerical stability:
  - Low to moderate. The absolute initialized temperature is preserved, but the
    implicit operator and DFI balance path change.
- Compute cost:
  - Moderate if the implementation rebuilds a jitted trajectory per initial
    time; low if the reference profile is passed without triggering repeated
    compilation. The reported 48 CPU / 175 GiB / 4 L4 envelope is adequate for
    one side-by-side candidate.
- Data leakage:
  - Low if each reference profile uses only the same initial analysis for that
    forecast start. Do not average over validation targets, future times, or
    other initialization times.
- Physical plausibility:
  - High. Semi-implicit atmospheric models commonly use reference states to
    improve fast-wave conditioning; this proposal selects that state from the
    initialized atmosphere without changing the physical state.
- Rollback complexity:
  - Low. Remove one adapter flag, one factory, one registry entry, and focused
    tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_analysis_tref`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_analysis_tref --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the incumbent, clean diagnostics, no early day 1-5 RMSE guardrail failure,
    and no variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_analysis_tref --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the remaining
    error is not materially controlled by the semi-implicit reference profile.
    Any early MSLP/Z500 or 10 m wind guardrail failure would show that the
    adaptive split disrupts balance more than it helps.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  constructs `_reference_temperature(..., temperature_kelvin=250.0)`, subtracts
  the profile in `weather_state_to_dinosaur_state`, and adds it back in
  `dinosaur_state_to_weather_state`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  uses `PrimitiveEquationsBase.T_ref` in explicit and implicit sigma-coordinate
  pressure-gradient and temperature terms.
- History: `.logbook/history/2026-06-16_11-09-50_standard-atmosphere-reference-profile/decision.md`
  rejected a fixed standard-atmosphere reference profile with iteration delta
  `+0.00023612927630622949`, so this proposal is not another static profile.
- History: `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted layer-mean hydrostatic initialization with validation delta
  `+0.005305927605172567`, motivating a split that uses the accepted initialized
  thermal structure.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of the rejected `standard-atmosphere-reference-profile`:
that candidate used one fixed dry profile unrelated to the initialized analysis,
while this proposal preserves the initialized absolute temperature and only
changes the semi-implicit split profile for the same forecast start.

It is also distinct from rejected thermal recentering, mass-neutral weak-HS
forcing, and sigma-thickness closure. It does not add or remove heat, freeze a
thermal zero mode during rollout, change Held-Suarez tendencies, or adjust the
initialized sigma thickness; it only changes how the existing absolute
temperature is partitioned between reference and perturbation variables.

## Evaluator Notes

### 2026-06-18T01:56:57Z

Decision: move to `staging`.

The proposal is physically plausible and distinct from the rejected fixed
standard-atmosphere reference profile: it would adapt the semi-implicit split to
the same-time initialized analysis while preserving absolute initialized
temperature. Source inspection confirms the reference-temperature vector is used
both in state conversion and in the primitive-equation implicit/explicit split,
so the mechanism is real.

Do not promote it next. The adapter currently constructs one
`reference_temperature` and one jitted trajectory function before iterating over
initial times. A per-analysis profile would therefore require rebuilding the
trajectory per initial state or a broader refactor to make the reference profile
dynamic inside the equation. That increases compilation/runtime risk and the
implementation surface. The prior fixed reference-profile experiment was clean
but effectively neutral, so this remains a plausible fallback rather than the
best next run.

### 2026-06-18T03:02:30Z

Decision: keep in `staging`.

The latest exact weak-HS thermal-source split failed cleanly with only a
`+0.000047270501076557` iteration primary delta, so the loop should pivot away
from weak-HS source timing details. That result does not directly falsify this
proposal because an analysis-mean reference profile changes the semi-implicit
linearization and initialized perturbation split, not the weak-HS source
integrator.

Keep this staged rather than ready. It remains physically plausible, but the
implementation still requires either per-initial-time trajectory construction
or a larger refactor to pass a dynamic reference profile through the equation.
The earlier fixed reference-temperature profile was nearly neutral, so this
adaptive version is a reasonable fallback only after cheaper, more targeted
mechanisms have been scored.

### 2026-06-18T04:36:51Z

Decision: keep in `staging`.

The newly accepted Coriolis split changes the ranking but does not directly
falsify this idea. The proposal remains physically plausible because the
semi-implicit reference profile affects the initialized perturbation split and
linear fast-wave operator, while preserving absolute initialized temperature.
However, it still carries higher implementation and runtime risk than the
symmetric Coriolis follow-up: the current adapter builds a single reference
temperature and jitted trajectory before looping over initial times, so an
analysis-mean per-case profile likely requires per-initial-time trajectory
construction or a broader dynamic-reference refactor.

If selected later, this must be retargeted to preserve the current incumbent's
exact Coriolis split as well as DFI, weak Held-Suarez forcing, hydrostatic
layer initialization, and near-surface residual correction. Keep staged behind
the ready Coriolis-ordering experiment and the narrower hypsometric Z fallback.

### 2026-06-18T06:07:51Z

Decision: keep in `staging`.

The current incumbent is now the accepted Strang Coriolis model, so I updated
the front matter target model. The new DFI-Coriolis proposal lowers this idea's
near-term priority: both touch initialization balance, but the DFI-Coriolis
candidate is more localized and follows directly from two accepted Coriolis
rollout gains. The analysis-mean reference-temperature proposal remains
scientifically plausible, but still has the same implementation concern noted
earlier: the adapter constructs one reference profile and one jitted trajectory
before looping over initial times, so a per-analysis profile would require
per-initial-time trajectory construction or a broader dynamic-reference refactor.

Keep this as a later fallback behind DFI-Coriolis consistency, symmetric
diffusion placement, and the hypsometric geopotential diagnostic.

### 2026-06-18T07:28:25Z

Decision: keep in `staging`, ranked below the new sigma-native hydrostatic
initialization and other lower-surface fallbacks.

The latest DFI-Coriolis candidate was clean but sub-threshold, which lowers the
near-term value of operator-consistency-only balance refinements. The new
sigma-native hydrostatic proposal is a better first thermal-structure test
because it directly changes the same-time initialized sigma-layer temperature
with bounded fallbacks, while this proposal still requires either
per-initial-time trajectory construction or a broader dynamic-reference
refactor.

Do not scrap it yet because the mechanism remains distinct: it changes the
semi-implicit reference split while preserving absolute initialized
temperature. However, the fixed standard-atmosphere reference-profile result
was nearly neutral, and this adaptive version carries higher implementation
and runtime risk than the current ready idea, the targeted Z500 diagnostic, or
the explicit-tendency dealiasing fallback.

### 2026-06-18T08:53:53Z

Decision: move to `scrap`.

The latest sigma-native hydrostatic initialization is now cleanly negative
(`-0.008345744027537627`), and the older fixed standard-atmosphere reference
profile was essentially neutral (`+0.00023612927630622949`). That combination
makes this analysis-mean reference-temperature split a poor use of the next
implementation budget. It remains physically plausible, but the expected gain
is speculative while the implementation would still require per-initial-time
trajectory construction or a broader refactor to make the reference profile
dynamic inside the equation.

This is not being scrapped because reference states are unphysical; it is being
scrapped because the current code shape and scored history make the cost-risk
tradeoff worse than the newer, lower-surface residual and localized diagnostic
ideas. A future proposal would need a narrower implementation design or direct
read-only diagnostics showing that the 250 K split error materially affects the
fixed target variables.
