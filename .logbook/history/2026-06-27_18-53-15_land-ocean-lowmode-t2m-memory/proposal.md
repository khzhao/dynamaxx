---
schema_version: 1
slug: land-ocean-lowmode-t2m-memory
title: Land-Ocean Low-Mode 2 m Temperature Residual Memory
status: ready
created_at: 2026-06-25T20:29:05Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
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

# Land-Ocean Low-Mode 2 m Temperature Residual Memory

## Hypothesis

The cached current incumbent still has strongly negative
`2m_temperature` skill versus persistence and a growing cold bias at long
leads: iteration mean skill is about `-0.955`, validation mean skill is about
`-0.984`, and the day-15 bias is near `-1.5 K` in both splits. The accepted
near-surface residual machinery already improves early screen variables, but it
lets broad T2m bias decay away. A low-order land/ocean residual reservoir can
retain only the slowly varying surface-memory component while allowing
synoptic and high-wavenumber residuals to decay as the incumbent currently
does.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`, derived from the current incumbent.

In the post-rollout near-surface residual correction:

- compute the incumbent raw lead-zero `2m_temperature` residual exactly as
  today;
- split that residual into land and ocean portions using the existing
  land-sea fraction when available, with the exact incumbent fallback when the
  mask is missing or invalid;
- retain only a broad low-order component, for example land and ocean
  area means plus an optional very-low-wavenumber spectral residual, while
  leaving high-wavenumber residuals on the incumbent scale-separated decay;
- apply the retained broad residual with a long but finite decay and a smooth
  late-lead activation so day-1 through day-5 guardrails are not spent on a
  purely diagnostic correction;
- cap the added broad correction per lead and preserve lead zero exactly;
- apply the correction only to `2m_temperature`; do not change 10 m wind, MSLP,
  Z500, prognostic state variables, WTG, vertical-DSE, or fixed protocols.

This is an output-side residual-memory candidate, not a new surface flux or
forecast-contract change.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused adapter residual-correction tests
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key such as
    `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`.
- API changes:
  - None. Forecast inputs, outputs, lead steps, and target variables stay
    unchanged.
- Tests to update:
  - Verify the correction leaves non-T2m variables bitwise unchanged.
  - Verify lead zero remains exactly the analyzed initial `2m_temperature`.
  - Verify the correction falls back to incumbent behavior when land-sea data,
    spectral splitting, or broad residual diagnostics are invalid.
  - Verify synthetic land-only, ocean-only, and mixed masks produce bounded
    land/ocean broad residuals.
  - Verify early-lead activation is zero or near zero through the documented
    guardrail window and bounded at late leads.
  - Verify factory/dependency and registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 5-15, especially the cold-bias component visible
    in cached incumbent artifacts.
  - Iteration primary score should improve by roughly `+0.003` to `+0.012` if
    the negative T2m skill is dominated by broad surface-memory bias rather
    than unpredictable high-wavenumber weather noise.
  - Validation primary score should improve by roughly `+0.0015` to `+0.008`
    if the broad residual memory is split-stable.
- Expected neutral metrics:
  - `mean_sea_level_pressure`, `geopotential_500`, and
    `10m_u_component_of_wind` should be unchanged except through metric
    aggregation, because their output fields are not modified.
- Possible regressions:
  - Early `2m_temperature` RMSE can fail guardrails if the late activation is
    not conservative enough.
  - Broad residual persistence can hurt regions where the initial raw residual
    is an interpolation artifact rather than a surface-memory signal.

## Risks

- Numerical stability:
  - Low. This operates after rollout on finite output fields and has an exact
    incumbent fallback.
- Compute cost:
  - Low. It reuses existing land-sea and spectral residual utilities and adds
    only low-order reductions and broadcasts.
- Data leakage:
  - Low if implemented strictly from lead-zero initial-state residuals and
    fixed masks. It must not inspect future truth, validation errors, or cached
    metric outcomes beyond this proposal's documented motivation.
- Physical plausibility:
  - Moderate. Land soil moisture/thermal inertia and ocean mixed-layer memory
    support broad near-surface temperature anomaly persistence, but this is
    still a reduced residual-memory approximation.
- Rollback complexity:
  - Low. Remove one residual option, one helper path, one factory/export,
    one registry key, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem --workers 4`.
  - Support requires primary delta at least `+0.002`, clean diagnostics, no
    early day-1-through-day-5 mean RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem --workers 4`
    only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` and clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that broad T2m
    residual memory is not a remaining error source. Any early T2m guardrail
    failure would show the reservoir is too strong or activates too early.

## Citations

- Dynamaxx cached metrics:
  `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv` and
  `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv` show
  `2m_temperature` as the weakest target variable by skill versus persistence,
  with a persistent late cold bias near `-1.5 K`.
- Dynamaxx code:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` already implements
  scale-separated near-surface residual memory, land-sea T2m residual decay,
  and land-sea mask loading; this proposal reuses those mechanisms rather than
  adding new data dependencies.
- Dynamaxx history:
  `.logbook/history/2026-06-21_23-32-41_land-sea-contrast-surface-temperature`
  accepted land-sea-aware T2m residual memory, and
  `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux`
  accepted a surface-energy addition with large validation gain.
- Seneviratne, S. I. et al. 2010. Investigating soil moisture-climate
  interactions in a changing climate: a review. Earth-Science Reviews.
  https://doi.org/10.1016/j.earscirev.2010.02.004
- Deser, C., Alexander, M. A., Xie, S.-P., and Phillips, A. S. 2010. Sea
  surface temperature variability: patterns and mechanisms. Annual Review of
  Marine Science. https://doi.org/10.1146/annurev-marine-120408-151453
- Stull, R. B. 1988. An Introduction to Boundary Layer Meteorology. Springer.
  https://link.springer.com/book/10.1007/978-94-009-3027-8

## Researcher Notes

This is distinct from the accepted `land-sea-contrast-surface-temperature`
change, which changed land/ocean residual decay behavior for the full T2m
residual. This proposal preserves only a broad low-order land/ocean residual
reservoir while high modes continue to decay through the incumbent path. It is
not staged `diurnal-surface-residual-memory`, because it does not fit or
persist a local diurnal phase. It is not staged
`lead-bounded-screen-temperature-anomaly`, because it does not clamp the full
forecast anomaly toward the initial state. It is not staged
`bulk-richardson-2m-temperature-diagnostic`, because it does not change the raw
diagnosed screen-temperature formula. It is also decorrelated from WTG and
vertical-DSE follow-ups: prognostic state evolution is unchanged, and only the
T2m output residual path changes.

## Evaluator Notes

### 2026-06-25T20:33:00Z

Decision: move to `staging`; ranked 3 of 4 current proposals.

This is feasible now and stays inside accepted local patterns: the adapter
already has scale-separated near-surface residual memory, land-sea T2m residual
logic, finite fallbacks, and side-by-side registration coverage. It does not
change target variables, lead times, evaluation protocols, or the forecast API.

Stage rather than ready because the mechanism is mostly output-side and would
improve only one scored channel. The land/ocean low-mode reservoir has plausible
surface-memory support and should not be rejected merely for using an accepted
residual path, but it is more metric-facing than a trajectory-level numerical
limiter. Keep it as a high-priority surface-temperature fallback if the next
vertical-DSE candidate is neutral or negative.

### 2026-06-27T15:02:44Z

Decision: move to `ready`; ranked 1 of 3 reviewed current-incumbent options.

The just-rejected `boundary-layer-sheltered-vertical-dse` candidate showed that
damping the lower-column part of the accepted vertical-DSE increment severely
damages `2m_temperature`, so the next experiment should avoid vertical-DSE
sheltering, gating, or retiming. This proposal is decorrelated from that failed
family: it changes only the output-side `2m_temperature` residual-memory path,
preserves the current `dino_hsl2_mass_dse_wtg_vdse_ramp` dynamics, and should
leave MSLP, Z500, U10, WTG, vertical-DSE, and fixed evaluation protocols
unchanged. It is more metric-facing than a trajectory-level mechanism, but T2m
is the incumbent's clearest remaining scored weakness and the codebase already
has accepted scale-separated and land-sea residual machinery with finite
fallbacks.

Implement as exactly one side-by-side candidate, with one fixed low-mode
land/ocean residual-memory schedule and no parameter sweep. Keep lead zero
exact, apply only to `2m_temperature`, cap any additional late-lead correction,
and compare only against the valid cached incumbent artifacts unless the cache
is concretely invalid.
