---
schema_version: 1
slug: ekman-balanced-spinup-ramp
title: Ekman-Balanced Positive-Time Spinup Ramp
status: ready
created_at: 2026-06-30T05:34:31Z
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

# Ekman-Balanced Positive-Time Spinup Ramp

## Hypothesis

The accepted `dino_ri2m_ekman_coupled` incumbent gained strongly from adding a
bounded surface-stress plus Ekman-pumping closure, but that closure is applied
only as a positive-time rollout filter after the initialized state is produced.
That means the DFI-balanced initial mass/wind state is immediately exposed to a
new frictional stress-pumping pair at full strength. A short, fixed
incremental-analysis-style activation of the accepted Ekman increments should
reduce early inertial and mass-adjustment shock while preserving the high-signal
full-strength Ekman closure for most of the 15-day forecast.

This is not a drag retune, roughness redistribution, pressure-work thermal
coupling, or exact mass-neutral projection. The stress formula, wind caps,
pressure caps, equatorial taper, area-neutral pressure projection, and fallback
logic remain those of the accepted incumbent; only the first positive-time
activation schedule changes.

## Mechanism

Register a side-by-side candidate such as `dino_ri2m_ekman_spinup`, derived from
`ekman_coupled_dinosaur_dycore_model()`.

Inside `_ekman_coupled_surface_step_filter` for the candidate only:

- compute the incumbent wind and log-pressure increments exactly as today;
- diagnose a smooth time multiplier from `State.sim_time`, using the existing
  time path already required by the pressure-ramped vertical-DSE incumbent;
- use a fixed schedule chosen before scoring, for example `0.35` at forecast
  time zero, smoothstep to `1.0` by 24 h, and `1.0` thereafter;
- multiply the already capped wind and log-pressure increments by the same
  scalar time factor, then perform the same modal/nodal finite checks before
  accepting the corrected state;
- if `sim_time` is absent, nonfinite, or negative, fall back exactly to the
  incumbent full-strength Ekman filter rather than inventing a new state clock;
- keep DFI, WTG, vertical-DSE, T2m memory, RI2m diagnostic, output variables,
  lead schedule, worker policy, and all fixed evaluation protocols unchanged.

The implementation should be one opt-in flag plus one helper returning the
bounded ramp. The candidate should not change the incumbent registry entry.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side key, for example `dino_ri2m_ekman_spinup`.
- API changes:
  - None. `DycoreModel.forecast`, emitted variables, target variables, lead
    times, and evaluation protocols stay fixed.
- Tests to update:
  - Verify the ramp is finite, monotone, bounded between the fixed initial
    fraction and one, and equals one after the declared spinup window.
  - Verify missing or nonfinite `sim_time` reproduces incumbent Ekman output.
  - Verify an all-one ramp reproduces the accepted filter exactly.
  - Verify wind and log-pressure caps still hold after modal projection.
  - Verify candidate factory parity with `dino_ri2m_ekman_coupled` except for
    the new spinup-ramp selector and model name.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` and `mean_sea_level_pressure` at days 1-5 if full
    first-step Ekman forcing is exciting a small adjustment transient.
  - `geopotential_500` if a cleaner early mass/wind adjustment improves
    balanced medium-lead height evolution.
- Expected neutral metrics:
  - Later leads should remain close to incumbent because the accepted Ekman
    closure reaches full strength after 24 h.
  - `2m_temperature` should be nearly neutral because no thermal tendency,
    residual memory, or RI2m diagnostic is changed.
- Possible regressions:
  - If the accepted full-strength first-day Ekman impulse is itself responsible
    for the large score gain, even a short ramp may give back useful U10 and
    MSLP skill.

## Risks

- Numerical stability:
  - Low. The change only reduces accepted, already capped increments during a
    fixed early window and falls back to incumbent behavior on invalid time
    diagnostics.
- Compute cost:
  - Negligible. It adds scalar time arithmetic inside an existing filter.
- Data leakage:
  - None. The ramp uses only forecast model time and fixed constants.
- Physical plausibility:
  - Moderate to high. Gradually inserting a new analysis or forcing increment
    is standard spinup control, and the underlying stress-pumping closure is the
    accepted physical mechanism.
- Rollback complexity:
  - Low. Remove one flag/helper, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_ekman_spinup`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_spinup --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    incumbent iteration primary `-0.16500618979404214`, clean diagnostics, and
    no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_ekman_spinup --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` against cached validation
    primary `-0.16591150807771451`.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show that the
    incumbent full-strength first-day Ekman forcing is already preferable. Any
    early U10, MSLP, or Z500 guardrail failure would show the ramp disrupts the
    accepted balance rather than reducing spinup shock.

## Citations

- Local positive evidence:
  `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/decision.md`
  accepted `dino_ri2m_ekman_coupled` with iteration delta
  `+0.04799113626142959` and validation delta `+0.04683104652127085`.
- Local negative evidence:
  `.logbook/history/2026-06-30_01-49-51_exact-mass-neutral-ekman-pumping/decision.md`
  showed exact Ekman mass neutrality was clean but slightly negative, so this
  proposal changes temporal balance rather than another invariant projection.
- Local negative evidence:
  `.logbook/history/2026-06-29_21-03-42_static-roughness-weighted-ekman-coupling/decision.md`
  found roughness weighting effectively neutral; this proposal keeps the
  accepted spatial stress distribution.
- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. "Data
  Assimilation Using Incremental Analysis Updates." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
- Lynch, P. and Huang, X.-Y. 1992. "Initialization of the HIRLAM Model Using a
  Digital Filter." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Tan, B. 2000. "Ekman Pumping for Stratified Planetary Boundary Layers
  Adjacent to a Free Surface or Topography." Journal of the Atmospheric
  Sciences. https://doi.org/10.1175/1520-0469(2000)057%3C3334:EPFSPB%3E2.0.CO;2
- de Roode, S. R. and Siebesma, A. P. 2020. "A Bound on Ekman Pumping."
  Journal of Advances in Modeling Earth Systems. https://doi.org/10.1029/2019MS001976

## Researcher Notes

This is deliberately close to the accepted model surface while avoiding the
recent rejected Ekman variants. It is not the staged Coriolis-scaled Ekman depth
idea, which changes vertical stress geometry; not Helmholtz-projected Ekman,
which changes the wind-component split; and not the rejected exact
mass-neutrality idea, which changed a pressure projection invariant. The
proposal asks only whether a physically accepted closure should enter the
positive-time forecast with a standard spinup window.

## Evaluator Notes

### 2026-06-30T06:09:00Z

Decision: move to `ready`; ranked 1 of 2 in this triage pass.

This is the strongest next experiment because it changes only the temporal
activation of the accepted coupled Ekman stress-pumping increment. It preserves
the incumbent drag law, caps, equatorial taper, area-neutral pressure
projection, output contract, fixed protocols, and cached incumbent comparison.
Source inspection confirms the required `sim_time` path already exists through
the pressure-ramped vertical-DSE option, and the coupled Ekman filter is
localized enough for a side-by-side selector plus focused tests.

The scientific mechanism is credible. Incremental analysis update literature
supports gradual insertion of increments to reduce model spinup, and digital
filter initialization literature supports reducing early imbalance/noise. The
local history is also favorable for a narrow timing test: the accepted
`dino_ri2m_ekman_coupled` closure produced the current large gain, while
roughness redistribution, exact mass-neutral pumping, pressure-work thermal
coupling, and output wind veering either regressed or failed the promotion
threshold. This proposal avoids those duplicate mechanisms and asks a distinct
question: whether the accepted full-strength closure is too abrupt during the
first positive-time rollout day.

Risk remains that the incumbent's first-day full-strength Ekman impulse is part
of the skill gain, in which case the candidate should fail cleanly with a
subthreshold or negative iteration delta. That risk is acceptable because the
implementation surface is small, the expected cost is negligible, and the result
would give a useful answer about spinup timing without changing evaluation
protocols. If selected, fix the ramp constants before scoring, initialize
`sim_time` only for the candidate path as needed, and require tests for bounded
monotone ramp behavior, invalid-time fallback to exact incumbent output, cap
preservation, and factory/registry parity.
