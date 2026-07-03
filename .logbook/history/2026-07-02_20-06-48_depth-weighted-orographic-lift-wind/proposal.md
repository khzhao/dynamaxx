---
schema_version: 1
slug: depth-weighted-orographic-lift-wind
title: Depth-Weighted Orographic Lift Wind
status: ready
created_at: 2026-07-02T20:00:04Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth_orolift_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Depth-Weighted Orographic Lift Wind

## Hypothesis

The accepted terrain-lift tendency estimates mountain-following vertical motion from the single lowest Dinosaur wind layer. At this resolution, the lowest layer also carries boundary-layer drag, near-surface diagnostic corrections, and local noise, so it can misrepresent the resolved lower-tropospheric flow impinging on broad terrain. A shallow depth-weighted wind estimate should preserve the terrain-lift mechanism while making the forcing more synoptically coherent and less sensitive to one layer.

## Mechanism

Add an opt-in branch in `_orographic_lift_theta_tendency_step_filter` that replaces `lowest_u_wind` and `lowest_v_wind` in the `w_terrain` calculation with a normalized weighted mean over the lower part of the existing orographic-lift sigma envelope. The weights should emphasize the lowest two or three layers, ignore invalid columns through the existing finite diagnostics, and leave the weak-flow taper based on the same effective wind speed. Existing low-mode terrain, latitude taper, forecast-time ramp, area-neutral projection, and temperature cap remain unchanged. The candidate model can be registered as `dino_ri2m_ekman_depth_orolift_lwind`.

## Implementation Scope

- Expected files: `adapter.py` for a boolean flag, lower-column wind helper, and factory; `__init__.py` and `registry.py` for side-by-side registration.
- Registry changes: add one model name derived from the incumbent factory.
- API changes: none.
- Tests to update: focused unit tests for normalized lower-layer weights, exact incumbent behavior when the flag is off, finite fallback if the weighted mean is invalid, and registry construction.

## Expected Metric Movement

- Expected improvements: `mean_sea_level_pressure` and `geopotential_500` at days 1-10 through more coherent mountain forcing in synoptic flow; possible `2m_temperature` improvement near terrain by reducing noisy lowest-layer overcorrections.
- Expected neutral metrics: global wind scores should be close to neutral because the proposal changes only a thermal tendency filter.
- Possible regressions: if the lowest layer carries the most relevant terrain-blocked flow information, depth averaging may weaken useful localized lift and reduce the accepted orographic benefit.

## Risks

- Numerical stability: low; the tendency still passes through existing caps and finite checks.
- Compute cost: low; wind fields are already transformed to nodal space.
- Data leakage: none; only forecast-state winds are used.
- Physical plausibility: medium-high; broad orographic response depends on incoming low-level flow, and a shallow layer mean is less noisy than a single model level.
- Rollback complexity: low; the branch is opt-in and side-by-side.

## Evaluation Plan

- Fast gate: `uv run pytest` and `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind`.
- Iteration gate: `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind --workers 4`.
- Validation gate: `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind --workers 4` only after iteration promotion.
- Outcome that would falsify the hypothesis: iteration primary delta below `+0.002`, diagnostics showing invalid weighted winds, or a broad loss in MSLP/Z500 indicating the single lowest layer was the better forcing estimate.

## Citations

- Teixeira, M. A. C., 2014: "The physics of orographic gravity wave drag." Frontiers in Physics. https://www.frontiersin.org/journals/physics/articles/10.3389/fphy.2014.00043/full
- Hughes, O. K., and C. Jablonowski, 2023: "A mountain-induced moist baroclinic wave test case for the dynamical cores of atmospheric general circulation models." Geoscientific Model Development, 16, 6805-6831. https://gmd.copernicus.org/articles/16/6805/2023/
- Durran, D. R., and J. B. Klemp, 1982: "On the Effects of Moisture on the Brunt-Vaisala Frequency." Journal of the Atmospheric Sciences, 39, 2152-2158. https://journals.ametsoc.org/view/journals/atsc/39/10/1520-0469_1982_039_2152_oteomo_2_0_co_2.xml
- Current code reference: `src/dynamaxx/dycore/models/dinosaur/adapter.py`, `_orographic_lift_theta_tendency_step_filter`.

## Researcher Notes

This is not a duplicate of `barotropic-envelope-orography-tendency`, which added a separate mass-divergence terrain tendency and was nearly neutral. This proposal keeps the accepted thermal terrain-lift form but changes the resolved incoming wind estimate that drives it. It is also not constant tuning of the accepted orographic lift: the mechanism is a representational change from one layer to a lower-column flow estimate, with the same fixed evaluation gates and cached incumbent policy.

## Evaluator Notes

### 2026-07-02T20:05:23Z

Decision: move to `ready`; ranked 1 of 3 proposals in this triage.

This is the strongest next implementation candidate because it changes the resolved incoming-flow estimate that drives the accepted terrain-lift tendency, rather than only adding another cap to the same increment. The incumbent already computes nodal low-level winds, terrain gradients, a sigma envelope, weak-flow taper, area-neutral projection, and per-step temperature caps inside `_orographic_lift_theta_tendency_step_filter`, so a shallow normalized lower-column wind is a small, side-by-side implementation with no forecast-contract or evaluation-protocol change.

Prior history supports trying one more focused orographic-lift refinement: `orographic-lift-adiabatic-tendency` was accepted with strong iteration and validation gains, while `strang-split-orographic-lift-filter` was stable but below promotion. This proposal is more mechanistically distinct than Strang ordering because it changes the flow sample used for mountain forcing. Literature check: Teixeira 2014 and Hughes/Jablonowski 2023 support the importance of incoming flow over terrain and mountain-triggered waves in dynamical-core tests; Durran/Klemp 1982 is only background for stratification and is not the core justification here.

Implementation concerns: keep the weights hard-coded and conservative, derived from existing sigma coordinates rather than tuned to scores; preserve exact incumbent behavior when the selector is off; use the same effective wind for the weak-flow taper; and add finite fallback tests so invalid weighted winds reproduce the incumbent lowest-layer path.
