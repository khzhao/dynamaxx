---
schema_version: 1
slug: bounded-log-pressure-init-extrapolation
title: Bound Log-Pressure Initialization Extrapolation
status: ready
created_at: 2026-06-17T06:38:45Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Bound Log-Pressure Initialization Extrapolation

## Hypothesis

The accepted log-pressure initialization showed that pressure-level to sigma
remapping geometry is a useful initialization-only axis. The current
log-pressure remap still uses the same finite linear extrapolation helper as
the original pressure interpolation. Near the top or bottom of the analyzed
pressure stack, that can extend thermal and wind gradients beyond observed
levels when local sigma pressure lies just outside the available pressure-level
range.

For a short weather forecast, bounded nearest-level extrapolation at the
vertical edges is more conservative than extending the last analyzed gradient.
It should reduce spurious edge-layer thermal and momentum increments without
changing the accepted log-pressure interpolation inside the observed column.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap`.
Preserve the incumbent trajectory, DFI, layer-mean hydrostatic temperature initialization,
near-surface residual diagnostics, weak Held-Suarez relaxation, finite
sigma-to-pressure output extrapolation, spectral truncation, and inner step.

Add a guarded pressure-to-sigma initialization path that calls
`vertical_interpolation.interp_pressure_to_sigma_log_pressure` with a
nearest-extrapolation interpolation function instead of
`_linear_interp_with_safe_extrap`. Interior interpolation remains linear in
log pressure; only targets above the top source level or below the bottom source
level use the nearest analyzed pressure-level value. Apply the same bounded
edge policy to temperature, winds, and passive humidity during initialization.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_vertical_interpolation.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, and metrics are
    unchanged.
- Tests to update:
  - Unit-test log-pressure pressure-to-sigma interpolation with nearest
    extrapolation at both vertical edges and unchanged linear interpolation for
    interior targets.
  - Verify the candidate factory preserves all incumbent flags and only changes
    the initialization extrapolation mode.
  - Verify registry construction and a non-JIT finite smoke forecast if the
    existing Dinosaur smoke fixtures cover this candidate.

## Expected Metric Movement

- Expected improvements:
  - Short- and medium-lead `2m_temperature` if edge-layer thermal extrapolation
    contributes to the current incumbent's small accepted short-lead 2 m
    temperature regression.
  - `geopotential_500` and `mean_sea_level_pressure` may improve if bounded
    edge temperatures reduce spurious column-thickness noise before DFI.
  - `10m_u_component_of_wind` may improve or remain neutral if edge-level wind
    extrapolation is a small source of imbalance.
- Expected neutral metrics:
  - Interior-column pressure-level fields should remain close to the incumbent
    because interpolation inside the analyzed pressure range is unchanged.
- Possible regressions:
  - Nearest extrapolation is less vertically smooth than linear extrapolation and
    may flatten legitimate boundary-layer or stratospheric gradients.
  - If most evaluated columns never extrapolate during initialization, score
    movement may be below the fixed promotion threshold.

## Risks

- Numerical stability:
  - Low. The output path already uses finite nearest extrapolation, and this
    proposal applies the same bounded concept only at initialization edges.
- Compute cost:
  - Low. It changes the interpolation helper only during initialization.
- Data leakage:
  - Low. It uses only same-time input fields already used by the incumbent.
- Physical plausibility:
  - Moderate to high. Bounded edge extrapolation avoids inventing unobserved
    vertical gradients outside the provided pressure stack.
- Rollback complexity:
  - Low. The change can be isolated behind one interpolation option and one
    side-by-side factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean but near-zero iteration delta would show edge extrapolation is not a
    material remaining error source; any early `2m_temperature`,
    `geopotential_500`, or `10m_u_component_of_wind` guardrail failure would
    show that the incumbent's linear edge extrapolation is dynamically useful.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  implements `interp_pressure_to_sigma_log_pressure`, the current
  `_linear_interp_with_safe_extrap` default, and
  `linear_interp_with_nearest_extrap`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` uses
  log-pressure pressure-to-sigma initialization and already uses finite nearest
  extrapolation for sigma-to-pressure output packing.
- History: `.logbook/history/2026-06-17_00-55-17_log-pressure-sigma-initialization/decision.md`
  accepted log-pressure initialization with iteration primary delta
  `+0.006318821843572353` and validation primary delta
  `+0.007447672526236682`.
- History: `.logbook/history/2026-06-17_02-11-52_log-pressure-output-interpolation/decision.md`
  rejected broad log-pressure output remapping because it redistributed RMSE
  badly; this proposal does not change the output interpolation path.
- Hyman, J. M. 1983. Accurate monotonicity preserving cubic interpolation. SIAM
  Journal on Scientific and Statistical Computing. https://doi.org/10.1137/0904045
- NCAR CAM6 Scientific Guide describes monotonic vertical interpolation choices
  for dynamical-core tracers, supporting the general caution against unbounded
  interpolation artifacts at sharp vertical gradients.

## Researcher Notes

This is not a repeat of the rejected log-pressure output interpolation. That
candidate changed output remapping and caused many large `2m_temperature` RMSE
regressions. This proposal changes only initialization edge extrapolation and
keeps the accepted finite output packing unchanged.

It is also distinct from `pressure-aware-sigma-layer-grid`, which changed the
vertical grid itself and strongly degraded primary score. Here the incumbent
sigma grid, prognostic equations, DFI, weak Held-Suarez relaxation, and
layer-mean hydrostatic temperature initialization is preserved. The proposal is
deliberately small because prior accepted results favor bounded initialization
perturbations over broad coordinate or damping changes.

## Evaluator Notes

2026-06-17T06:41:34Z - Move to `staging`; rank 2 of 4 active ideas.

This proposal is implementable and low risk, but it is not the best next
iteration because the expected signal is narrower than the layer-mean
hypsometric initialization. Source inspection confirms that
`interp_pressure_to_sigma_log_pressure` accepts an interpolation function and
that `linear_interp_with_nearest_extrap` already exists. The incumbent adapter
also already uses nearest extrapolation for finite sigma-to-pressure output
packing, so a side-by-side initialization-only bounded extrapolation flag is a
small, reversible code change.

Relevant history supports staging rather than scrapping. Accepted
log-pressure initialization improved iteration primary by
`+0.006318821843572353` and validation primary by `+0.007447672526236682`
without RMSE guardrail movement, and accepted hydrostatic-thickness
initialization then produced the current much larger gain. This proposal
preserves both mechanisms and changes only the behavior outside the analyzed
pressure-level stack. It is also distinct from rejected log-pressure output
interpolation, which changed output diagnostics and produced 54 variable-lead
RMSE guardrail failures, led by medium-lead `2m_temperature` regressions above
200%.

The reason to stage is effect-size uncertainty. If few sigma targets fall
outside the source pressure range after the incumbent hydrostatic/log-pressure
initialization, the fixed iteration delta may be near zero. Nearest edge values
can also flatten legitimate boundary-layer or upper-level gradients. Revisit
after the stronger hydrostatic-estimator refinement, or sooner if diagnostics
show edge-level initialization artifacts. If promoted, keep the model
side-by-side, preserve the incumbent output path, and test both edge clipping
and unchanged interior log-linear interpolation.

2026-06-17T08:00:01Z - Keep in `staging`; retargeted to current incumbent and
rank 2 of 5 active ideas.

This remains viable but is no longer the best next experiment. I updated the
front matter, candidate name, evaluation commands, and comparison baseline from
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init` to the
current incumbent
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
Prior Evaluator notes are preserved above as historical context.

The evidence still favors staging: accepted log-pressure initialization,
hydrostatic-thickness initialization, and layer-mean hydrostatic initialization
all show that initialization geometry is productive, while rejected
log-pressure output interpolation shows the same pressure-coordinate idea is
not safe when applied to outputs. This proposal is small, reversible, and
source-supported because `interp_pressure_to_sigma_log_pressure` accepts an
interpolation function and `linear_interp_with_nearest_extrap` already exists.

It ranks behind conservative pressure-thickness remapping because its expected
effect is limited to sigma targets outside the analyzed pressure stack. The
conservative proposal changes interior remap geometry and can include bounded
edge behavior, so it has a stronger mechanism for the next full iteration. Keep
this staged as a narrower fallback if conservative remapping fails cleanly or
if diagnostics later isolate edge extrapolation artifacts.

2026-06-17T09:09:07Z - Keep in `staging`; rank 3 of 5 active ideas after the
conservative-remap rejection.

The latest conservative pressure-thickness initialization remap weakens broad
pressure-remap follow-ups but does not invalidate this narrower edge-only idea.
That candidate passed fast and iteration diagnostics, with clean guardrails,
yet regressed iteration primary by `-0.006775878375613553` and showed its
largest RMSE increases in `geopotential_500` and `mean_sea_level_pressure`
around days 4-8. The lesson is that reinterpreting all pressure-level inputs as
layer averages and remapping interior structure can hurt mass-field phase for
the current incumbent.

This proposal remains staged because it preserves the accepted interior
center-sampled log-pressure initialization and changes only extrapolated
targets above or below the analyzed pressure stack. Local source still exposes
`interp_pressure_to_sigma_log_pressure` and
`linear_interp_with_nearest_extrap`, so the implementation remains small and
reversible. The expected effect size is likely smaller than the dry
geopotential and surface-layer diagnostics, however, because it only matters
where sigma initialization currently extrapolates. Promote only if diagnostics
identify edge-level initialization artifacts or if the higher-ranked diagnostic
ideas fail cleanly.

2026-06-17T10:13:20Z - Keep in `staging`; rank 4 of 5 active ideas.

This remains a valid narrow fallback, but the new proposal set pushes it lower.
Accepted log-pressure and hydrostatic initialization history still supports
small initialization-local changes, and the rejected conservative remap does
not duplicate this edge-only mechanism. However, conservative remapping's
negative primary delta and medium-lead mass-field degradation are a warning
against additional pressure-coordinate changes unless the expected signal is
clear.

2026-06-17T13:33:51Z - Keep in `staging`; rank 3 of 4 active ideas.

This is still implementable and narrow, but recent evidence weakens the
pressure-remap family. Conservative pressure-thickness remapping was clean but
lost `-0.006775878375613553`, and the potential-temperature log-pressure
initialization also lost primary score. This proposal is safer than those
because it is edge-only, but its effect size is uncertain unless sigma targets
regularly fall outside the analyzed pressure stack.

If promoted later, keep the implementation initialization-edge-only, preserve
interior log-pressure interpolation exactly, preserve the incumbent output
path, and avoid changing pressure-level diagnostics or fixed protocols.

The current proposal only changes behavior for targets outside the analyzed
pressure stack, so effect size is probably smaller than potential-temperature
initialization and less directly supported by recent evidence than the passive
humidity DFI bypass. Keep it staged, not scrapped, because source support is
strong and rollback is simple. Promote only after higher-ranked ideas fail
cleanly or after diagnostics show edge extrapolation artifacts.

2026-06-17T11:23:24Z - Keep in `staging`; rank 5 of 6 active ideas.

This is still implementable but has weakened relative priority. Local source
continues to support a small side-by-side implementation because
`interp_pressure_to_sigma_log_pressure` accepts an interpolation function and
`linear_interp_with_nearest_extrap` already exists. The proposal is also
narrower than the rejected conservative remap because it preserves the
incumbent interior log-pressure interpolation and changes only vertical-edge
extrapolation.

Recent evidence lowers expected payoff. The conservative pressure-thickness
remap regressed iteration primary by `-0.006775878375613553`, and the
potential-temperature log-pressure initialization regressed by
`-0.0009134462392161868` despite clean diagnostics and guardrails. Those
results do not directly test edge-only nearest extrapolation, but they warn
against spending the next iteration on another pressure-coordinate
initialization change without diagnostics showing edge targets are material.
Keep this as a narrow fallback after the thermal, humidity, surface diagnostic,
and polar initialization ideas.

2026-06-17T14:41:49Z - Keep in `staging`; rank 2 of 3 active ideas.

The latest surface-layer diagnostic rejection does not directly falsify this
initialization-only edge-extrapolation idea, but it does strengthen the
preference for changes that cannot damage fixed output diagnostics. This
proposal keeps that property and remains low surface area, so it should not be
scrapped. It also remains distinct from rejected log-pressure output
interpolation and surface-layer diagnostic extrapolation because it preserves
the incumbent output path.

The reason it stays behind the polar wind taper is cumulative pressure-remap
evidence and expected effect size. Conservative pressure-thickness remapping
regressed primary by `-0.006775878375613553`, potential-temperature log-pressure
initialization regressed by `-0.0009134462392161868`, and broad output
coordinate changes have produced guardrail failures. This proposal is narrower
than those failures because it only changes targets outside the analyzed
pressure stack, but that same locality makes its likely signal small. Keep
staged as the next fallback if the ready polar-row experiment is cleanly
negative or if diagnostics specifically identify edge extrapolation artifacts.

2026-06-17T15:44:56Z - Promote to `ready`; sole ready candidate after final
fresh triage.

The Researcher search found no new proposals, `.logbook/research/proposals/`
and `.logbook/research/ready/` are empty, and the polar wind taper has now been
rejected as numerically neutral with an iteration delta of
`+1.444147295082132e-07`. The remaining active queue therefore contains only
this bounded log-pressure initialization-edge extrapolation proposal.

Recent history keeps the expected payoff modest. Conservative pressure-thickness
initialization remap regressed primary by `-0.006775878375613553`,
potential-temperature log-pressure initialization regressed by
`-0.0009134462392161868`, and surface-layer diagnostic extrapolation regressed
primary by `-0.10115079559414197` with near-surface guardrail failures. Those
failures penalize broad pressure-remap and output-diagnostic changes, but they
do not directly test this proposal's edge-only initialization mechanism.

Source inspection still supports a contained side-by-side implementation:
`interp_pressure_to_sigma_log_pressure` accepts an interpolation function, and
`linear_interp_with_nearest_extrap` already exists. The candidate should
preserve the incumbent interior log-pressure interpolation, hydrostatic
layer-mean initialization, output packing, diagnostics, and fixed protocols,
changing only extrapolated pressure-to-sigma initialization targets. That makes
it the only remaining implementable and researchable idea with a clean rollback
path.

Evaluator decision: promote to `ready` as the sole ready candidate. This does
not trigger the protocol stop condition, because one ready/researchable idea
remains after the documented search. If this candidate is implemented and fails
without generating a concrete follow-up, then the next Orchestrator pass should
treat the loop as blocked by no ready or researchable ideas remaining.
