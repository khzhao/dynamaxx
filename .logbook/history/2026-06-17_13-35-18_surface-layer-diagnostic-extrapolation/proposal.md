---
schema_version: 1
slug: surface-layer-diagnostic-extrapolation
title: Diagnose Screen-Level Fields From the Lowest Sigma-Layer Shear
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

# Diagnose Screen-Level Fields From the Lowest Sigma-Layer Shear

## Hypothesis

The incumbent still emits `2m_temperature` and `10m_u_component_of_wind` from
the lowest sigma-layer temperature and zonal wind, then applies the accepted
decaying lead-zero residual. That residual corrects the unresolved surface-layer
offset at short leads, but as it decays the forecast returns to a lowest-model-
layer proxy for screen-level quantities.

A fixed diagnostic extrapolation from the lowest two sigma layers to physical
2 m and 10 m heights should better represent screen-level temperature and wind
without changing the prognostic trajectory, pressure-level outputs, MSLP, or
fixed evaluation contract. The mechanism is strongest after the residual has
partly decayed, so it is not just a repeat of the accepted residual correction.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag`.
Preserve the incumbent DFI, weak thermal Held-Suarez relaxation, log-pressure
initialization, hydrostatic layer-mean temperature initialization, zero
orography, vertical advection, T80 truncation, 900 s inner step, finite
sigma-to-pressure output interpolation, and near-surface residual correction.

Add an optional output diagnostic for only `2m_temperature` and
`10m_u_component_of_wind`:

- estimate the geometric heights of the lowest two sigma centers from local
  surface pressure, lowest-layer temperature, dry hydrostatic scale height, and
  the fixed target heights of 2 m and 10 m;
- linearly extrapolate temperature and zonal wind from the lowest two sigma
  centers to the fixed target height;
- bound the extrapolated increment by the magnitude of the lowest-layer vertical
  difference so a noisy shear cannot dominate the diagnostic;
- apply the existing near-surface residual correction after this diagnostic so
  lead-zero matching and the accepted residual behavior are preserved.

Do not change pressure-level temperature, pressure-level winds, geopotential,
MSLP, surface pressure, humidity, the forecast trajectory, target variables,
lead times, or metric definitions.

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
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState`, emitted channel names, lead
    times, and evaluation metrics remain unchanged.
- Tests to update:
  - Unit-test the diagnostic extrapolator on a simple two-layer profile,
    including the fixed 2 m and 10 m target heights and bounded-increment rule.
  - Verify only `2m_temperature` and `10m_u_component_of_wind` change before the
    existing residual correction; pressure-level fields and MSLP must remain
    unchanged.
  - Verify the candidate factory preserves all incumbent flags and registry
    construction.
  - Add or reuse a no-JIT finite smoke forecast for the candidate.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` and `10m_u_component_of_wind` after days 2-5, where the
    accepted residual has decayed enough for the lowest-layer proxy to reappear.
  - Primary score may improve because two fixed targets are near-surface
    diagnostics and current iteration/validation artifacts still show strongly
    negative near-surface skill at most leads.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500` should be exactly neutral
    apart from roundoff because the trajectory and pressure-level output path are
    unchanged.
- Possible regressions:
  - Lowest-layer shear may be noisy during fronts or stable boundary-layer
    events, degrading `2m_temperature` or `10m_u_component_of_wind`.
  - If the accepted residual already captures most useful surface-layer
    information, the primary-score gain may be below the iteration threshold.

## Risks

- Numerical stability:
  - Low. The change is output-only and bounded, with no feedback into the dycore.
- Compute cost:
  - Low. It adds a small diagnostic calculation at output packing time.
- Data leakage:
  - Low. It uses only the forecast state, same-time initial residual path already
    accepted by history, and fixed physical target heights.
- Physical plausibility:
  - Moderate. Operational models diagnose 2 m temperature and 10 m wind through
    surface-layer post-processing rather than raw lowest-model-level values, but
    this is a simplified no-roughness, no-land-surface approximation.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter flag and one side-by-side
    factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, no fixed RMSE guardrail failure, and neutral Z500/MSLP.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean but sub-threshold iteration delta would show the remaining
    near-surface error is not a lowest-layer diagnostic-height issue. Any early
    `10m_u_component_of_wind` or `2m_temperature` guardrail failure would show
    the shear extrapolation is too noisy for the fixed benchmark.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  emits `2m_temperature` as `temperature[:, -1]` and
  `10m_u_component_of_wind` as `u_wind[:, -1]`, then optionally applies the
  accepted near-surface residual correction.
- History: `.logbook/history/2026-06-16_14-27-30_near-surface-anomaly-diagnostics/decision.md`
  accepted decaying near-surface residuals with iteration primary delta
  `+0.0353889745054945` and validation primary delta `+0.03575996912567381`.
- History: `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  shows the current incumbent passed guardrails with only small short-lead
  `10m_u_component_of_wind` regressions, so the wind guardrail remains central.
- ECMWF IFS Documentation, Part IV Physical Processes, describes 2 m
  temperature and 10 m wind as surface-layer diagnostics based on lowest-model-
  level and surface information.
- Stull, R. B. 1988. An Introduction to Boundary Layer Meteorology. Kluwer
  Academic Publishers. https://doi.org/10.1007/978-94-009-3027-8
- WeatherBench 2 identifies near-surface variables as core weather-benchmark
  targets: Rasp et al. 2023, WeatherBench 2. https://arxiv.org/abs/2308.15560

## Researcher Notes

This is not a duplicate of the accepted near-surface residual correction. The
accepted mechanism persists the initial analysis-model residual with a fixed
decay; this proposal changes the model-equivalent diagnostic at every lead using
forecast low-level vertical shear, then keeps the accepted residual layering
unchanged.

It is also not a pressure-level output remap, geopotential datum correction,
mass residual, terrain/orography experiment, damping tweak, timestep change, or
another hydrostatic initialization variant. The proposal intentionally leaves
Z500/MSLP untouched because terrain and mass-field history shows those channels
are easy to damage when surface diagnostics are coupled to pressure or
orography.

## Evaluator Notes

2026-06-17T09:09:07Z - Move to `staging`; rank 2 of 5 active ideas.

This is plausible but not the next ready candidate because it directly modifies
two fixed scored near-surface channels. Source inspection confirms the current
adapter packs `2m_temperature` and `10m_u_component_of_wind` from the lowest
sigma layer and applies the accepted near-surface residual correction
afterward, so the proposed mechanism is feasible and distinct from the existing
decaying residual. The physical motivation is also reasonable: operational
models diagnose screen-level fields from surface-layer information rather than
blindly equating them with the lowest model level.

The proposal is staged rather than scrapped because prior history shows
near-surface diagnostic mismatch is a real source of score. The accepted
near-surface residual improved iteration by `+0.0353889745054945` and
validation by `+0.03575996912567381` while leaving pressure-level and mass
channels effectively unchanged. This candidate preserves that accepted residual
layering and adds only same-time forecast-state shear information before the
residual is applied.

It stays below the dry-geopotential proposal because the simplified
two-layer extrapolation can easily inject noisy boundary-layer shear into both
temperature and wind scores, and recent history shows low-level wind guardrails
are tight. Layer-mean thermal recentering improved primary score but failed the
early `10m_u_component_of_wind` guardrail, and the current incumbent's accepted
layer-mean initialization still has small short-lead wind regressions. If this
is later promoted, require strict invariance tests for Z500/MSLP/pressure-level
fields and bounded-increment tests for stable and sharp-shear profiles.

2026-06-17T10:13:20Z - Keep in `staging`; rank 3 of 5 active ideas.

The recent dry-geopotential rejection reinforces caution around output-only
diagnostics: that candidate was localized and stable but still failed a
short-lead Z500 variable+lead guardrail. This surface-layer diagnostic is
different because it targets only `2m_temperature` and
`10m_u_component_of_wind`, and prior near-surface residual history shows those
channels contain real recoverable error. The accepted near-surface residual
improved iteration by `+0.0353889745054945` and validation by
`+0.03575996912567381` without damaging pressure-level fields.

It remains staged because it directly changes two scored near-surface channels
using a simplified two-layer shear extrapolation. Recent initialization history
keeps low-level wind risk central: layer-mean thermal recentering had attractive
primary-score gains but failed the early `10m_u_component_of_wind` guardrail,
and the current incumbent's largest accepted layer-mean initialization
regression is still short-lead `10m_u_component_of_wind`. Rank it behind the
temperature-initialization ready proposal and the passive-humidity DFI bypass,
but ahead of edge-only extrapolation and core vertical transport.

2026-06-17T11:23:24Z - Keep in `staging`; rank 3 of 6 active ideas.

This remains a plausible diagnostic-only candidate, but it is not the best next
implementation. It is source-supported and distinct from the accepted
near-surface residual correction: the adapter currently emits
`2m_temperature` and `10m_u_component_of_wind` from the lowest sigma layer, then
applies the accepted decaying residual afterward. A bounded two-layer diagnostic
could recover some remaining screen-level mismatch without touching the
forecast trajectory, pressure-level fields, Z500, or MSLP.

The risk is concentrated in exactly the guardrail that has repeatedly shaped
recent decisions. Full-column thermal recentering had large primary gains but
failed early `10m_u_component_of_wind`, and the new ready thermal limiter is
the more direct bounded follow-up to that evidence. This surface diagnostic
changes the scored near-surface channels themselves using simplified shear
physics, so it should remain behind the passive humidity DFI bypass. If
promoted later, require invariant tests for pressure-level outputs, Z500, and
MSLP; apply the existing residual after the new diagnostic; and keep the
extrapolated increment bounded by the lowest-layer vertical difference.

2026-06-17T13:33:51Z - Move to `ready`; rank 1 of 4 staged ideas after the
passive-humidity, low-level thermal-limiter, and theta-initialization
rejections.

This is now the best bounded next implementation target. The recent
passive-humidity DFI bypass was effectively neutral, the upper/mid thermal
limiter lost primary score, and the potential-temperature log-pressure remap
also lost skill. Those results weaken passive tracer and thermodynamic remap
follow-ups, while the accepted near-surface residual remains strong evidence
that screen-level diagnostic mismatch is a recoverable score source.

Promote with strict constraints: side-by-side model only; output-only
diagnostic for `2m_temperature` and `10m_u_component_of_wind`; apply the
existing near-surface residual after the new diagnostic; bound extrapolated
increments by the lowest-layer vertical difference; leave the forecast
trajectory, pressure-level output path, `geopotential_500`, `mean_sea_level_pressure`,
surface pressure, humidity, metrics, splits, and fixed protocols unchanged.
Require invariant tests for pressure-level fields, Z500, and MSLP, plus bounded
increment tests for stable and sharp-shear profiles.
