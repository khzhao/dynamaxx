---
schema_version: 1
slug: bounded-virtual-humidity-geopotential
title: Bound Passive Humidity Only in Geopotential Diagnosis
status: scrap
created_at: 2026-06-18T13:16:06Z
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

# Bound Passive Humidity Only in Geopotential Diagnosis

## Hypothesis

The incumbent is dynamically dry but still carries humidity as a passive tracer
and uses that tracer in virtual-temperature geopotential reconstruction. Prior
history shows two constraints: removing humidity from geopotential diagnosis
damaged day-1 `geopotential_500`, while activating humidity in dynamics or
adding saturation heating degraded fixed iteration skill.

A narrower diagnostic guard can keep the beneficial virtual-temperature
correction while preventing passively advected humidity outliers from producing
unphysical hydrostatic thickness at pressure-level output time. Bounding
humidity only inside `get_geopotential_on_sigma` for output packing should
target Z500 without changing dynamics, humidity outputs, pressure initialization,
surface-pressure evolution, or near-surface residuals.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_qbound_z`.
Preserve the incumbent rollout, DFI, weak-HS forcing, near-surface residuals,
log-pressure and hydrostatic layer initialization, passive humidity tracer
transport, output variables, and fixed protocols.

Add an optional output-diagnostic guard:

- during `dinosaur_state_to_weather_state`, leave the trajectory humidity tracer
  unchanged for any emitted `specific_humidity_*` channels;
- when passing humidity into `primitive_equations.get_geopotential_on_sigma`,
  replace it with a finite, physically bounded diagnostic copy such as
  `clip(q, 0.0, 0.04)`;
- apply the bound only for the virtual-temperature geopotential calculation,
  not for pressure-level temperature, winds, surface pressure, MSLP, 2 m
  temperature, 10 m wind, DFI, or rollout tendencies;
- fall back to the incumbent no-humidity path only if the diagnostic humidity is
  absent or entirely nonfinite.

This is not a moist-dynamics proposal, not a saturation-adjustment proposal,
and not a frozen-humidity diagnostic. It retains forecast passive humidity but
guards only the scored geopotential diagnostic from nonphysical tracer tails.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, output names, shapes, leads, and metrics remain
    unchanged.
- Tests to update:
  - Unit-test that the diagnostic humidity bound is applied only before
    geopotential reconstruction.
  - Verify emitted humidity channels, pressure-level temperature, pressure-level
    winds, MSLP, surface pressure, and near-surface channels are unchanged
    before the accepted residual correction.
  - Verify finite behavior for negative, supersaturated, and nonfinite humidity
    samples.
  - Verify the candidate factory preserves all Strang incumbent flags except the
    geopotential humidity-bound option.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium and long leads if passive tracer tails are
    contaminating virtual-temperature thickness after dry rollout.
  - Primary score may improve if Z500 gains exceed the small extra diagnostic
    approximation error.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and `mean_sea_level_pressure`
    should remain effectively neutral because their output paths and the
    trajectory are unchanged.
  - Lead-zero Z500 should remain close to incumbent unless the initialized
    humidity already contains nonphysical values.
- Possible regressions:
  - If large passive humidity values are physically meaningful in the analysis
    or forecast, clipping them can make Z500 too dry and regress short-lead
    geopotential.
  - Output-only diagnostic changes can still fail guardrails, as prior Z500
    diagnostics showed.

## Risks

- Numerical stability:
  - Low. The change is output-only and bounded.
- Compute cost:
  - Negligible. It adds one local finite clip before an existing diagnostic.
- Data leakage:
  - None. The bound is fixed before scoring and uses no truth, validation
    feedback, or golden data.
- Physical plausibility:
  - Moderate. Specific humidity is nonnegative and bounded in realistic
    atmospheric columns; the approximation is that a hard diagnostic cap is
    better than trusting a dry-passive tracer tail for virtual thickness.
- Rollback complexity:
  - Low. Remove one adapter flag, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_qbound_z`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_qbound_z --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure, especially for day-1 Z500.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_qbound_z --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show passive-humidity
    outliers are not a material remaining Z500 source. Any day-1 Z500 guardrail
    failure would show the cap damages necessary virtual-temperature structure.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` passes
  trajectory humidity into `primitive_equations.get_geopotential_on_sigma`
  during output packing while the incumbent keeps `use_humidity_in_dynamics`
  false.
- History: `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
  rejected removing humidity from geopotential reconstruction after a day-1
  `geopotential_500` guardrail failure.
- History: `.logbook/history/2026-06-17_18-02-45_bounded-moist-virtual-temperature-dynamics/decision.md`
  rejected active moist virtual-temperature dynamics, so this proposal keeps
  humidity out of pressure-gradient and thermodynamic tendencies.
- History: `.logbook/history/2026-06-17_19-31-12_bounded-saturation-adjustment/decision.md`
  rejected irreversible saturation heating, so this proposal does not heat or
  change humidity tracers.
- ECMWF IFS Documentation, Part III Dynamics and Numerical Procedures, uses
  virtual temperature in the hydrostatic relation for geopotential thickness.
- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
  Survey, second edition. Academic Press.

## Researcher Notes

This is distinct from scrapped `frozen-passive-humidity-geopotential`, which
replaced forecast humidity with initialized humidity for geopotential diagnosis.
This proposal continues using forecast passive humidity and only applies a
fixed physical bound before virtual-temperature thickness.

It also avoids the rejected humidity families: it does not activate humidity in
dynamics, does not add latent heating, does not alter DFI humidity handling, and
does not remove humidity from geopotential. The only intended changed scored
channel is `geopotential_500`; non-geopotential invariance tests should be
strict.

## Evaluator Notes

### 2026-06-18T13:22:44Z

Decision: move to `scrap`.

The proposal is technically feasible and narrower than rejected moist-dynamics
or saturation-adjustment candidates. Source inspection confirms the incumbent
dry rollout carries passive humidity and passes it unbounded into
`primitive_equations.get_geopotential_on_sigma` during output packing, while
humidity remains disabled in primitive-equation dynamics. A diagnostic-only
bounded copy would therefore be source-local and low cost.

Reject it because the evidence for another humidity-only diagnostic run is too
weak. Prior passive-humidity positivity limiting was clean but essentially
neutral (`-0.0000019440828125105725` iteration delta), DFI humidity bypass was
near-roundoff negative, removing humidity from geopotential caused a day-1
`geopotential_500` guardrail failure, and active bounded moist feedbacks were
strongly negative. This cap would directly affect only `geopotential_500`, uses
an arbitrary hard upper bound without read-only evidence that q values above
the bound are materially contaminating the scored Z500 channel, and overlaps
the already-scrapped humidity-diagnostic family. The stronger output-only Z500
candidate remains the staged hypsometric diagnostic, which targets the
hydrostatic pressure-level diagnosis rather than another humidity-tracer
cleanup.
