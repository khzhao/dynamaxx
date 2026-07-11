---
schema_version: 1
slug: ocean-anchor-ri2m-lower-boundary
title: Ocean-Anchor Richardson 2 m Lower Boundary
status: ready
created_at: 2026-07-11T05:34:39Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Ocean-Anchor Richardson 2 m Lower Boundary

## Hypothesis

The accepted incumbent now has a physically informed late 2 m observer over
land: its prognostic skin is initialized from lead-zero analyzed T2m and used
as the lower endpoint of a bounded Richardson interpolation after day 5. That
change improved days 6-15 T2m RMSE by about 4.95% on both fixed splits, yet T2m
mean skill remains about `-0.78` on iteration and `-0.80` on validation.

Ocean points still use the atmospheric-only RI2m observer even though the
incumbent already carries a causal, finite lead-zero ocean thermal anchor for
its accepted bulk sensible heat flux. Using that existing anchor as the ocean
lower endpoint of the same bounded, forecast-state-dependent RI2m observation
operator may recover additional marine T2m skill without changing dynamics,
the accepted flux, land behavior, or early guardrails.

## Mechanism

Register one side-by-side descendant, tentatively suffixed `_ori`, that
preserves the complete incumbent and adds only an ocean output-observer path.

- Retain the existing
  `_ocean_bulk_sensible_heat_flux_temperature_anchor` for each initial
  condition. Do not change how the anchor is extracted, validated, or used by
  the accepted ocean heat-flux forcing.
- During output packing, compute the incumbent pressure-thickness atmospheric
  RI2m result first.
- Where the land fraction is valid and the ocean fraction is positive, use the
  existing lead-zero ocean anchor as the surface potential-temperature
  endpoint and the accepted pressure-thickness lower atmospheric reference as
  the upper endpoint. Reuse the incumbent skin-aware Richardson number, shear
  floor, hydrostatic reference height, stability limiter, finite fallback, and
  `+/-1.5 K` departure cap.
- Blend this ocean estimate with the incumbent output using ocean fraction and
  the already accepted zero-through-120-hour, full-at-240-hour smooth ramp.
- Preserve the accepted prognostic-skin observer over land exactly. Fractional
  coastal cells receive complementary land and ocean weights whose sum cannot
  exceed one.
- Missing, invalid, nonpositive, or shape-incompatible anchor/mask/pressure
  fields; unsupported vertical geometry; nonfinite intermediate values; and
  zero ocean fraction reproduce the exact incumbent output cell by cell.
- Leave the ocean heat-flux equation, land reservoir, T2m residual memory,
  atmospheric trajectory, MSLP, Z500, U10, target variables, lead schedule,
  metrics, and deterministic forecast contract unchanged.

This is a state-dependent surface-layer observation operator. It is not an
additive persistence residual, an ocean flux retune, a second prognostic
trajectory, or a new surface-temperature input.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for one selector,
    candidate-only private anchor retention, the complementary ocean observer,
    and the factory.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` for export.
  - `src/dynamaxx/dycore/registry.py` for one side-by-side key.
  - Focused Dinosaur, dependency, and registry tests.
- Registry changes:
  - Suggested key:
    `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori`.
- API changes:
  - None. The existing deterministic `ForecastInput -> WeatherState`
    contract, trajectory count, and emitted variables remain unchanged.
- Tests to update:
  - Exact factory parity except name and selector.
  - Exact land, early-lead, zero-ocean, missing-anchor, invalid-mask, invalid
    pressure, and unsupported-geometry fallback.
  - Complementary coastal weighting without double counting.
  - Bounded ocean endpoint interpolation and unchanged land skin observer.
  - Bitwise non-T2m output parity and unchanged atmospheric trajectory.
  - Registry/dependency coverage and a finite forecast smoke test.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` after day 5 over ocean and coastal cells, particularly
    where the accepted ocean thermal anchor contains unresolved marine
    boundary-layer memory.
  - A plausible iteration primary gain is `+0.002` to `+0.008`; the land
    analogue produced `+0.0168874870225921` while affecting only land.
- Expected neutral metrics:
  - MSLP, Z500, U10, and every atmospheric trajectory field are exactly
    incumbent because this is output-only.
  - All emitted variables through 120 hours and all pure-land cells are exact
    incumbent.
- Possible regressions:
  - Lead-zero T2m is an air-temperature proxy, not SST, and may become stale
    under marine fronts.
  - The accepted ocean heat flux already moves the lower atmosphere toward the
    same anchor, so the output observer may duplicate that signal.

## Risks

- Numerical stability:
  - Low. The arithmetic is output-only, bounded, finite-guarded, and has an
    exact incumbent fallback.
- Compute cost:
  - Low. The anchor already exists; the candidate adds local output arithmetic
    and no extra rollout.
- Data leakage:
  - None. Only the causal lead-zero T2m already consumed by the accepted ocean
    forcing is used. No future target, validation statistic, or golden result
    enters the observer.
- Physical plausibility:
  - Moderate. Marine 2 m diagnostics use a surface thermal endpoint and
    stability-aware interpolation, but T2m is a reduced proxy for SST because
    the fixed input exposes no SST channel.
- Rollback complexity:
  - Low. Remove one selector, private output-plumbing branch, factory/export,
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run focused/full tests and fixed candidate fast. Require finite output,
    zero issues, exact non-T2m parity, and no contract change.
- Iteration gate:
  - Run fixed candidate-only iteration with four workers against the valid
    cached incumbent. Require delta at least `+0.002`, clean diagnostics, and
    all fixed RMSE guardrails.
- Validation gate:
  - Run candidate validation once only after iteration promotion. Require delta
    at least `+0.001`, clean diagnostics, and the same guardrails.
- Outcome that would falsify the hypothesis:
  - A subthreshold iteration delta, any marine-driven T2m guardrail failure, or
    evidence that the observer merely duplicates the accepted ocean forcing.
    Scrap without changing the ramp, cap, anchor, or Richardson constants.

## Citations

- Fairall, C. W., Bradley, E. F., Hare, J. E., Grachev, A. A., and Edson,
  J. B. 2003. Bulk Parameterization of Air-Sea Fluxes: Updates and
  Verification for the COARE Algorithm. *Journal of Climate*.
  https://doi.org/10.1175/1520-0442(2003)016%3C0571:BPOASF%3E2.0.CO;2
- Beljaars, A. C. M. and Holtslag, A. A. M. 1991. Flux parameterization over
  land surfaces for atmospheric models. *Journal of Applied Meteorology*.
  https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2
- ECMWF Newsletter 178, Improved two-metre temperature forecasts in the 2024
  upgrade, describes stability-aware interpolation between surface and
  lowest-model-level temperatures.
  https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade
- Local accepted evidence:
  `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/decision.md`,
  `.logbook/history/2026-07-10_09-06-37_prognostic-skin-ri2m-lower-boundary/decision.md`,
  and
  `.logbook/history/2026-07-10_23-59-52_analysis-2m-initialized-land-skin-memory/decision.md`.

## Researcher Notes

This is not the rejected `ocean-highmode-t2m-memory`: that candidate retained
an additive high-wavenumber analysis residual and regressed iteration by
`-0.00033790813261483366`. This proposal instead applies a bounded
forecast-state Richardson operator to an already accepted physical anchor.

It is not `sst-sea-ice-ocean-flux-anchor`, pressure-thickness ocean heat-cap,
Richardson-wind ocean flux, or exact ocean-flux splitting: the accepted forcing
path and its anchor are untouched. It is also not a land-skin retune; land
initialization, reservoir evolution, exchange, and observer remain exact.

## Evaluator Notes

### 2026-07-11T05:38:11Z

Decision: move to `ready`; ranked #1 for the next implementation.

Scientific rationale: a bounded surface-to-lowest-layer Richardson diagnostic
is a defensible reduced screen-temperature operator, and this candidate extends
the already accepted land-endpoint structure to ocean cells without modifying
the atmospheric state. The lead-zero T2m anchor is only a proxy for ocean skin
temperature and can become stale, but the existing forcing demonstrates that
it carries useful causal lower-boundary information. The fixed post-120-hour
ramp, endpoint bracket, `+/-1.5 K` cap, and exact fallbacks contain that risk.

Novelty rationale: this is not the rejected ocean high-mode residual memory,
which added an evolving spatial residual and moved iteration by
`-0.00033790813261483366`. It is also not a retune of the accepted ocean heat
flux. It tests one new question: whether the existing anchor improves the
bounded RI2m output endpoint over ocean while the accepted forcing and
trajectory remain bitwise unchanged.

Feasibility rationale: the current incumbent already extracts and validates
the per-initial-condition ocean anchor, retains the pressure-thickness RI2m
references, land/ocean weights, forecast clock, and accepted ramp, and exposes
the output packing location needed for a candidate-only observer. The change
fits the deterministic forecast contract and has a small, reversible source
and test surface. Implementation must plumb the existing anchor to output
packing without changing its extraction or prognostic forcing use.

Risk rationale: the main scientific risk is duplicate use of a static T2m
anchor after the ocean forcing has already relaxed the lowest layer toward it.
That can make the result stale or subthreshold over marine fronts. Do not tune
the ramp, cap, Richardson constants, anchor, masks, or blend after seeing the
iteration score. Require complementary coastal weights with no land/ocean
double counting, exact incumbent behavior through 120 hours, exact pure-land
and non-T2m parity, and per-cell fallback for every invalid dependency.

Prior-evidence rationale: the accepted ocean bulk sensible heat flux gained
`+0.0714278996861683` on iteration, the accepted land skin RI2m endpoint gained
`+0.0037114563296446745`, and analyzed land-skin initialization then gained
`+0.0168874870225921` with reproducible late T2m improvement. Those results do
not guarantee an ocean observer gain, but together they provide stronger
threshold-scale evidence than the staged alternatives. T2m remains the only
negative mean-skill target, while MSLP, Z500, and U10 are positive, so an
isolated T2m observer is preferable to spending balance margin on a new
prognostic mixing or terrain-momentum closure.

Implement exactly one `_ori` descendant of accepted source commit
`603f44a9b052557bd3bf3a16a9dcd9c05f343449`. Compare candidate iteration and,
only after promotion, validation against the valid cached incumbent artifacts.
Preserve all fixed protocols and the deterministic forecast contract; do not
run golden.
