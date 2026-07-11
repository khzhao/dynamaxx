---
schema_version: 1
slug: analysis-2m-initialized-land-skin-memory
title: Initialize Land-Skin Memory from the Lead-Zero 2 m Analysis
status: ready
created_at: 2026-07-10T23:53:16Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri
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

# Initialize Land-Skin Memory from the Lead-Zero 2 m Analysis

## Hypothesis

The accepted land reservoir initializes both auxiliary skin and deep
temperatures from the post-DFI lowest sigma layer, then holds those memories
unchanged until the day-5 ramp begins. The forecast input already contains the
lead-zero analyzed 2 m temperature, which is a more direct lower-boundary
observation than a coarse atmospheric layer. Initializing the land skin/deep
pair from that available analysis may improve the late thermal memory that has
already produced two threshold-sized gains, while preserving the complete
early forecast and every accepted exchange and observer constant.

## Mechanism

Add one candidate-only initialization source for the existing external skin
carry.

- Read the lead-zero `2m_temperature` channel from each initial `WeatherState`.
  Validate shape, finite positive Kelvin values, and the existing land fraction.
- Convert the field only to Dinosaur latitude order and nondimensional Kelvin.
  At active land points, initialize both `skin_temperature` and
  `deep_temperature` to the analyzed 2 m value. Using the same value for both
  prevents an artificial initial deep-restore gradient.
- Over ocean, fractional cells below the accepted land threshold, a missing 2 m
  channel, incompatible shape, or any invalid value, initialize exactly from
  the incumbent post-DFI lowest-layer temperature.
- Do not blend the analysis with the model layer, smooth it, bias-correct it,
  retain a second memory, or tune by land class. The choice is the single
  direct analysis endpoint or exact incumbent fallback.
- Leave the accepted skin/deep evolution, heat exchange, transfer coefficient,
  wind dependence, cap, heat-capacity ratio, deep restore, mask, 120-to-240 h
  ramp, mixed-layer behavior, and prognostic-skin RI2m observer unchanged.

Because both exchange and skin-aware output blending are zero through 120 h,
the atmospheric trajectory and all emitted targets must remain bitwise
incumbent through day 5 even though the unexposed auxiliary initial memory is
different.

## Implementation Scope

- Expected files: `adapter.py` for one selector, validated lead-zero T2m
  extraction, optional initializer input, and factory; Dinosaur exports,
  registry, and focused tests.
- Registry changes: one side-by-side descendant, for example
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si`.
- API changes: none. `2m_temperature` is already part of the fixed initial
  `WeatherState`; no new input, output, target, trajectory, or public shape is
  introduced.
- Tests to update: factory parity; exact missing/invalid/ocean fallback; land
  initialization equality; identical skin/deep start; no analysis smoothing;
  exact atmospheric/output parity through 120 h; unchanged post-ramp evolution
  code and forecast contract.

## Expected Metric Movement

- Expected improvements: late T2m from a better initialized land boundary;
  secondary MSLP and Z500 through accepted causal heat exchange; possible U10
  improvement through lower-column thermal phasing. A plausible iteration
  delta is `+0.002` to `+0.006` because the accepted late reservoir and skin
  observer together retained more than `+0.011` iteration signal.
- Expected neutral metrics: every emitted target through 120 h, all ocean
  points, and forecasts whose initial T2m is unavailable or invalid.
- Possible regressions: the day-zero 2 m field may be too shallow or stale when
  first activated at day 5, and existing low-mode T2m residual memory already
  carries some of the same analysis information.

## Risks

- Numerical stability: low. Only finite initial auxiliary values change; all
  accepted caps and delayed coupling remain.
- Compute cost: negligible. One existing channel extraction and mask blend per
  initial condition, with no inner-step work.
- Data leakage: none. Lead-zero analyzed T2m is part of the causal forecast
  input and is already used by accepted initial-residual logic; no future lead
  or validation label is read.
- Physical plausibility: moderate to high. Land surface state initialization is
  a standard forecast concern, but 2 m air temperature is not identical to
  radiometric skin or deep soil temperature. Setting skin and deep equal is a
  deliberately reduced initialization that avoids inventing an unobserved
  gradient.
- Rollback complexity: low. Remove one selector/initializer path, factory,
  registry entry, and focused tests.

## Evaluation Plan

- Fast gate: initialization/fallback/early-parity tests, full pytest, and fixed
  candidate fast with clean diagnostics.
- Iteration gate: fixed candidate-only iteration against the valid cached
  incumbent; require `+0.002`, clean diagnostics, and unchanged guardrails.
- Validation gate: run once only after promotion; require `+0.001`, clean
  diagnostics, and consistent late T2m behavior.
- Outcome that would falsify the hypothesis: a subthreshold iteration result or
  late T2m/MSLP regression should scrap this direct initialization. Do not add
  blending, smoothing, land-class parameters, or a different activation ramp.

## Citations

- Deardorff, J. W. 1978. Efficient prediction of ground surface temperature
  and moisture, with inclusion of a layer of vegetation. Journal of
  Geophysical Research 83, 1889-1903.
  https://doi.org/10.1029/JC083iC04p01889
- Koster, R. D. et al. 2004. Realistic initialization of land surface states:
  impacts on subseasonal forecast skill. Journal of Hydrometeorology.
  https://doi.org/10.1175/JHM-387.1
- Candy, B. et al. 2017. The impact of satellite-derived land surface
  temperatures on numerical weather prediction analyses and forecasts.
  Journal of Geophysical Research: Atmospheres.
  https://doi.org/10.1002/2016JD026417
- Local positive evidence:
  `.logbook/history/2026-07-10_04-01-39_late-ramped-skin-reservoir-coupling/decision.md`
  and
  `.logbook/history/2026-07-10_09-06-37_prognostic-skin-ri2m-lower-boundary/decision.md`.

## Researcher Notes

No active proposal or scored history initializes the new accepted skin carry
from lead-zero analyzed T2m. This is not residual-memory retuning: the existing
residual path is untouched, and this analysis enters only an external land
state whose accepted effects remain delayed. It is not a flux, stress,
deposition, RI2m, or ramp variant. It competes with, rather than combines with,
the pressure-thickness initialization proposal in the same batch; the Evaluator
should keep only the better-supported endpoint.

## Evaluator Notes

### 2026-07-10T23:57:10Z

Decision: move to `ready`; ranked #1 of the five bounded candidates and leave
it as the sole ready file.

Code feasibility and causality are established against source commit
`3fb32ff048b00b779d7e16a2c72e728866a4f4ba`. The worktree source and tests are
identical to that commit. The fixed WeatherBench2 source metadata includes
`2m_temperature` throughout the 2014-2019 fast, iteration, and validation
periods. Each evaluation batch loads all initial channels, and the runner must
select initial T2m to construct persistence for every initial state. More
directly, the accepted residual-memory lineage has already consumed that
lead-zero field across the complete fixed protocols with clean diagnostics.
It is therefore a causal initial analysis, not a future verification value.

The model can pass one validated T2m array from the existing per-initial-state
`WeatherState` into its private trajectory closure, run the unchanged DFI, and
then use the array only to initialize the external carry. This changes no
public `ForecastInput`, `WeatherState`, output channel, trajectory count, or
forecast shape. The incumbent reservoir step and skin observer both apply an
exact zero ramp through 120 h, so a different hidden carry can preserve exact
atmospheric and emitted-output parity through that endpoint.

Analyzed 2 m air temperature is not literally radiometric skin temperature or
deep soil temperature. Setting both reduced states equal is defensible only as
a neutral-gradient initialization when no analyzed soil profile is available:
it avoids inventing a skin-to-deep restore impulse and tests one observable
endpoint. Do not present the pair as a physically resolved land state.

This proposal substantially overlaps the accepted initial-residual memory.
That path forms `analyzed T2m - raw lead-zero T2m`, retains broad land/ocean
low-mode means with the same 120-to-240 h activation window, and gained
`+0.003330329353020467` on iteration and `+0.003344284472691278` on validation.
The proposed carry change is approximately `analyzed T2m - post-DFI
lowest-layer air`, so it is not independent information. It is not an exact
duplicate, however: the accepted extra memory is an output-only land/ocean
broad mean, while this candidate is a full-resolution land-only private state
that can affect the accepted skin observer and bounded prognostic heat exchange
after day 5. Readiness is for one experiment testing whether that distinct
local/prognostic route adds value beyond the accepted broad correction.

Bounded ranking:

1. `analysis-2m-initialized-land-skin-memory`
2. `energy-neutral-boundary-layer-entrainment-mixing`
3. `stability-gated-katabatic-slope-flow`
4. `symmetric-exact-land-skin-exchange-split`
5. `pressure-thickness-initialized-land-skin-memory`

The ready scope is frozen:

- Derive one side-by-side candidate from exact commit
  `3fb32ff048b00b779d7e16a2c72e728866a4f4ba` and the exact named incumbent.
- Fix one endpoint: at finite, positive, active-land cells, initialize both
  skin and deep to lead-zero analyzed T2m after only unit and latitude-order
  conversion. Add no blend, smoothing, bias correction, land class, second
  memory, or alternate endpoint.
- At ocean and below-threshold land cells, use the incumbent post-DFI
  lowest-layer value. A missing channel, incompatible shape, invalid mask, or
  each nonfinite/nonpositive T2m cell must use the same exact incumbent
  fallback; invalid input must never partially contaminate another cell.
- Preserve exact atmospheric and all emitted-output parity through 120 h.
  Keep the residual path, DFI, dynamics, exchange coefficient, exchange depth,
  heat-capacity ratio, deep restore, caps, land threshold, ramp, RI2m observer,
  and every other accepted constant unchanged.
- Combine no other idea and change no evaluation protocol or forecast
  contract. If iteration delta is below `+0.002`, scrap this endpoint without
  tuning, blending, smoothing, changing fallback, or trying another ramp.
