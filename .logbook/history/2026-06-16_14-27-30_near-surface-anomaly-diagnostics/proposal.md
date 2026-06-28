---
schema_version: 1
slug: near-surface-anomaly-diagnostics
title: Add Decaying Near-Surface Diagnostic Anomalies
status: ready
created_at: 2026-06-16T07:21:43Z
author_role: Researcher
target_model: dinosaur_dfi
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add Decaying Near-Surface Diagnostic Anomalies

## Hypothesis

The incumbent adapter emits `2m_temperature` as the lowest sigma-layer temperature and `10m_u_component_of_wind` as the lowest sigma-layer zonal wind. Those are not prognostic screen-level variables, and the model has no surface layer, skin temperature, land-sea roughness, or turbulent exchange parameterization. A simple decaying initial diagnostic anomaly should preserve analyzed unresolved surface-layer structure at short leads while letting the dynamical core control the synoptic evolution.

## Mechanism

For each initialization, compute the model-equivalent near-surface diagnostics at lead 0 from the converted Dinosaur state, then compare them with the actual initial `2m_temperature` and `10m_u_component_of_wind` channels if present. During output packing, add a lead-dependent residual correction to the corresponding forecast diagnostics:

`corrected = dynamic_diagnostic + initial_residual * exp(-lead_hours / decay_hours)`

Use one physically conservative decay time, such as 48 hours, for both 2 m temperature and 10 m zonal wind. This treats screen-level and 10 m fields as unresolved diagnostic departures from the lowest resolved layer, not as new prognostic variables. It does not alter pressure-level dynamics or use future truth.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Registry changes:
  - None expected for an in-place candidate evaluated as `dinosaur`.
- API changes:
  - None. The required initial channels are already present in `ForecastInput.initial_state`, and the correction is applied only when the corresponding requested output channel is supported.
- Tests to update:
  - Add a unit test confirming exact lead-0 matching for corrected near-surface channels when lead 0 is requested.
  - Add a unit test confirming the correction decays with lead time and is skipped when the initial diagnostic channel is absent.
  - Ensure pressure-level outputs and MSLP are unchanged by the correction.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 1-3, especially over land and stable boundary-layer regimes where the lowest resolved model layer is a poor screen-level diagnostic.
  - `10m_u_component_of_wind` at days 1-3 where the unresolved surface layer creates a persistent offset between 10 m wind and the lowest sigma-level wind.
  - Primary score may improve because two of the four fixed target variables are near-surface diagnostics.
- Expected neutral metrics:
  - `geopotential_500` and `mean_sea_level_pressure` should be neutral because the correction is output-only.
- Possible regressions:
  - A fixed decay may retain stale surface anomalies too long during frontal passages or strong diurnal transitions.
  - If the incumbent already wins through dynamic near-surface evolution at later leads, residual persistence could hurt days 4-7.

## Risks

- Numerical stability:
  - Very low. This is an output diagnostic transform and does not feed back into the dycore state.
- Compute cost:
  - Negligible compared with the spectral rollout.
- Data leakage:
  - Low. The correction uses only forecast-time initial analysis channels, the same information used by the persistence baseline.
- Physical plausibility:
  - Moderate. Operational models diagnose 2 m temperature and 10 m winds through surface-layer relationships; this proposal is a simple unresolved-anomaly surrogate, not a full Monin-Obukhov surface-layer scheme.
- Rollback complexity:
  - Low. The correction can be isolated to output packing and guarded by a dataclass option.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur`.
  - Confirm no diagnostic failures and inspect whether near-surface RMSE improves without pressure-level side effects.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur --workers 4`.
  - Support for the hypothesis is lower primary score driven by `2m_temperature` or `10m_u_component_of_wind` at early leads, with Z500 and MSLP neutral.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur --workers 4` only if the iteration gate improves.
  - Validation should preserve early-lead gains without producing a broad day 4-15 regression.
- Outcome that would falsify the hypothesis:
  - If near-surface improvements are absent or are outweighed by later-lead stale-anomaly errors, the diagnostic residual should be rejected or revised with a shorter decay.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently maps `2m_temperature` to `temperature[:, -1]` and `10m_u_component_of_wind` to `u_wind[:, -1]`.
- Dynamaxx source: `src/dynamaxx/eval/protocols.py` scores `2m_temperature`, `mean_sea_level_pressure`, `geopotential_500`, and `10m_u_component_of_wind` at daily leads 1 through 15.
- ECMWF IFS documentation, Part IV Physical Processes: describes 2 m temperature and 10 m wind as surface-layer post-processing diagnostics based on interpolation between the lowest model level and the surface. https://www.ecmwf.int/sites/default/files/2023-06/Part-IV-Physical-Processes.pdf
- ECMWF Newsletter 178: notes that 2 m temperature is a diagnostic variable derived from surface and lowest-model-level quantities using Monin-Obukhov similarity theory. https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade
- WeatherBench 2 paper: identifies near-surface variables as impact-relevant benchmark targets. https://ar5iv.labs.arxiv.org/html/2308.15560

## Researcher Notes

The logbook has no existing proposals or history to duplicate. A WeatherBench2 metadata check confirmed the fixed source includes both `2m_temperature` and `10m_u_component_of_wind` initial channels. This proposal intentionally avoids changing the forecast contract and leaves the fixed evaluation protocol untouched.

## Evaluator Notes

2026-06-16T07:24:59Z - Move to `staging`.

This is plausible and low risk, but it is too target-specific to be the top ready candidate. Source inspection confirms the current adapter emits `2m_temperature` and `10m_u_component_of_wind` directly from the lowest sigma layer, while ECMWF IFS documentation treats 2 m temperature and 10 m wind as surface-layer post-processing diagnostics using surface and lowest-model-level information. A decaying initial residual is therefore a reasonable surrogate for unresolved surface-layer structure and should be easy to roll back.

The main penalty is metric-gaming risk. The change is output-only, affects two fixed scored variables, and introduces a hand-chosen decay constant without improving the prognostic dynamics. It may improve days 1-3 but is unlikely to help mass fields or longer leads, and stale residuals could harm fronts, diurnal transitions, and rapidly changing boundary layers. This is not leakage because it uses only forecast-time analysis channels, but it is closer to calibrated persistence than to a dycore improvement.

Keep staged as a later diagnostic-output experiment, preferably after a dynamics candidate has been evaluated or after residual autocorrelation evidence justifies the decay timescale. It should not be selected before the moist virtual-temperature proposal.

2026-06-16T07:47:01Z - Keep in `staging` after incumbent fast-gate evidence.

The broken incumbent gate further weakens this as a next implementation target.
The proposal is a target-specific output diagnostic correction for 2 m
temperature and 10 m wind; it does not address non-finite values in the full
emitted forecast tensor, which are checked before target selection. Reconsider
only after pressure-level output validity is repaired and a finite incumbent
baseline exists, preferably with residual-autocorrelation evidence to justify
the decay constant.

2026-06-16T08:46:22Z - Keep in `staging`.

The finite incumbent baseline makes this proposal evaluable, but it remains a
lower-ranked follow-up. Baseline skill is poor for both scored near-surface
channels, so the proposal could improve the primary score at short leads.
However, the mechanism is output-only, affects exactly two fixed target
variables, and depends on a hand-selected decay constant without residual
autocorrelation evidence in the logbook. It also would be expected to leave Z500
and MSLP unchanged, limiting both scientific learning and robustness against
validation overfit.

Keep staged for later consideration after a broader dynamics candidate has been
scored, or if a Researcher adds evidence constraining the decay time from
forecast-time residual behavior only. It must continue to preserve the existing
forecast API, target variables, fixed gates, splits, and metrics.

2026-06-16T09:37:10Z - Keep in `staging`.

The new evidence does not justify promotion. Hyperdiffusion's early
`10m_u_component_of_wind` regression makes a near-surface correction relevant,
but it also reinforces the need to avoid hand-tuned changes that directly touch
the sensitive fixed target. This proposal remains low-cost and likely
diagnostic-clean because it is output-only, yet it still improves at most two
near-surface targets and is unlikely to teach much about the broad long-lead
thermal and mass-field drift in the incumbent.

Keep staged below digital filter initialization and Held-Suarez. Reconsider only
with forecast-time residual autocorrelation evidence that constrains the decay
timescale without using validation truth or changing the fixed protocols.

2026-06-16T10:58:43Z - Keep in `staging` after re-triage against
`dinosaur_dfi`.

This remains low-cost and likely diagnostic-clean, but the DFI incumbent does
not change the earlier ranking concern. Existing `dinosaur_dfi` artifacts still
show strongly negative near-surface skill, so a decaying forecast-time residual
could improve short-lead 2 m temperature or 10 m zonal wind. However, the
mechanism is output-only, directly targets two fixed scored variables, and
still lacks residual-autocorrelation evidence for the decay timescale.

Keep below all currently staged dynamics or geometry proposals. It is a useful
fallback if broader physical candidates fail, but it should not be the next
ready item while a small numerical-balance experiment is available. If revived,
the proposal should be revised as a side-by-side candidate that preserves DFI
and compares against `dinosaur_dfi`, not as an in-place change to canonical
`dinosaur`.

2026-06-16T12:04:45Z - Keep in `staging` after re-triage against
`dinosaur_dfi`.

This remains implementable and likely diagnostic-clean, but it is still the
lowest-ranked active idea. The accepted DFI incumbent does not remove the
near-surface diagnostic mismatch: the adapter still emits 2 m temperature and
10 m winds directly from the lowest sigma layer, while operational models
diagnose those quantities with surface-layer information. The fixed target
variables also still include both near-surface channels, so the idea may be a
useful fallback.

Do not move to ready while broader numerical or physical mechanisms remain. The
proposal is output-only, directly targets two scored variables, and depends on
an unconstrained decay time without residual-autocorrelation evidence in the
logbook. It should stay behind pressure-grid, terrain, and Held-Suarez ideas.
If revived, revise it for a side-by-side `dinosaur_dfi_*` candidate and require
forecast-time-only evidence for any decay timescale before implementation.

2026-06-16T13:02:50Z - Keep in `staging` after Iteration 7 re-triage
against `dinosaur_dfi`.

Rank this third among the active staged ideas. It remains the lowest-risk and
smallest implementation, and ECMWF documentation supports treating 2 m
temperature and 10 m winds as near-surface diagnostics influenced by surface and
boundary-layer modeling rather than raw lowest-model-layer fields. However, the
proposal is still output-only, directly targets two fixed scored variables, and
has no forecast-time residual autocorrelation evidence to justify the decay
timescale.

Do not promote while terrain/orography remains available as a broader physical
candidate. This should stay as a fallback diagnostic experiment, and if revived
it should be revised for a side-by-side `dinosaur_dfi_*` candidate that
preserves the accepted DFI incumbent and constrains any decay constant without
using validation truth or changing fixed protocols.

2026-06-16T14:16:35Z - Move to `ready` after Iteration 8 re-triage against
`dinosaur_dfi` at `cfdc344723cee1f267b892ddd924fc5d07b89f2d`.

Rank this first among the two remaining staged ideas and cap `ready` at this
single proposal. The recent terrain-aware surface-pressure/orography rejection
changed the tradeoff: it substantially improved aggregate primary score and
early near-surface RMSE, but failed the fixed mass-field guardrails badly for
`geopotential_500` and `mean_sea_level_pressure`. That makes the safest next
experiment a narrowly scoped output-diagnostic correction that can be required
to leave pressure-level fields and MSLP bitwise or roundoff unchanged.

The scientific premise remains supportable but bounded. Source inspection
confirms the adapter currently emits `2m_temperature` and
`10m_u_component_of_wind` from the lowest sigma layer, while ECMWF
documentation treats screen-level temperature and 10 m wind as surface-layer
diagnostics involving lowest-model-level and surface information. This proposal
still has metric-targeting risk and lacks residual-autocorrelation evidence for
the decay time, so promote only under these implementation constraints:
preserve DFI, use a side-by-side candidate such as `dinosaur_dfi_near_surface`,
use one fixed pre-declared decay constant rather than validation-tuned
coefficients, and add tests proving `geopotential_500` and
`mean_sea_level_pressure` outputs are unchanged by the diagnostic correction.
Validation remains protocol-gated by iteration.
