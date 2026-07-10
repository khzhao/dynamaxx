---
schema_version: 1
slug: prognostic-skin-ri2m-lower-boundary
title: Prognostic Skin Lower Boundary for RI2m
status: history
created_at: 2026-07-10T08:59:45Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin
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

# Prognostic Skin Lower Boundary for RI2m

## Hypothesis

The accepted late-ramped land skin reservoir improved validation T2m RMSE by
about `0.149 K` on average after day 5, but the emitted pressure-thickness RI2m
diagnostic still uses only atmospheric layer-band temperatures and winds. The
new prognostic skin state therefore affects T2m only indirectly through its
lowest-layer heat exchange. Operational surface-layer diagnostics instead
interpolate between skin temperature and the lowest atmospheric model level,
with stability dependence. Using the accepted, causally evolved skin as the
land lower boundary of RI2m after its existing 120-hour inactive window should
recover additional screen-temperature structure without changing dynamics or
early guardrails.

## Mechanism

Add one candidate-only output branch that preserves the accepted forecast
trajectory and public `WeatherState` contract.

- Retain the already computed skin-temperature trajectory inside the adapter
  until output packing. It remains outside `primitive_equations.State`, DFI,
  tracers, and emitted channels.
- Over valid land cells only, form a bounded skin-to-lower-layer 2 m estimate
  using the existing pressure-thickness lower atmospheric reference, its
  diagnosed geometric height, the existing wind/shear floor, and a bulk
  Richardson number whose lower thermal endpoint is the prognostic skin.
- Reuse the incumbent RI2m `3 K` departure cap, finite fallback, pressure
  guards, and stability limiter. Introduce no fitted residual or new thermal
  amplitude.
- Blend from the incumbent pressure-thickness RI2m output to the skin-aware
  estimate with exactly the accepted reservoir ramp: weight zero through
  `120 h`, smoothstep to full at `240 h`. Multiply by valid land fraction, so
  ocean and invalid-mask points reproduce the incumbent exactly.
- Return only the existing deterministic forecast variables and one trajectory
  per initialization. The model contract, metrics, splits, targets, and lead
  times remain unchanged; no evaluation infrastructure change is required.

## Implementation Scope

- Expected files:
  - `adapter.py`: one selector, internal skin-trajectory retention, an optional
    skin argument in output conversion, the bounded skin-aware RI2m helper,
    and one side-by-side factory derived from the current incumbent.
  - `__init__.py` and `registry.py`: export and register one candidate such as
    `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri`.
  - Focused tests under `tests/dycore/`.
- Registry changes:
  - One additive candidate key; no incumbent mutation before acceptance.
- API changes:
  - None. Skin remains an internal rollout auxiliary and is never emitted.
- Tests to update:
  - Candidate factory differs from the incumbent only by the new observer
    selector and name.
  - Output is exactly incumbent through 120 h and at ocean/invalid-mask points.
  - Skin-aware output remains within the existing departure cap and finite.
  - Dynamics are byte-identical between candidate and incumbent for a supplied
    trajectory; only T2m packing may differ after the ramp begins.
  - No skin variable appears in `WeatherState.variables`.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` after day 5, especially over land under stable or weak-wind
    conditions where a skin-to-air gradient contains information absent from
    the atmospheric-only RI2m bands.
- Expected neutral metrics:
  - MSLP, Z500, and U10 are identical because the trajectory is unchanged.
  - All targets through 120 h are identical apart from roundoff.
- Possible regressions:
  - The accepted reservoir skin may be a useful heat-memory state but a poor
    instantaneous screen-temperature endpoint. Direct use can double-count the
    same signal already transferred to the lowest air layer or exaggerate
    stable nocturnal departures.

## Risks

- Numerical stability:
  - Low. This is bounded output arithmetic with exact incumbent fallback.
- Compute cost:
  - Low to moderate. Retaining the 2-D skin trajectory increases temporary
    memory but adds no integration or spectral transforms.
- Data leakage:
  - None. Skin is initialized from lead-zero forecast state and evolves
    causally; no verification data or future boundary fields are used.
- Physical plausibility:
  - Moderate to high. Skin and lowest-model-level interpolation is standard,
    but this dycore's reduced reservoir is not a full surface energy model.
- Rollback complexity:
  - Low. Remove one output branch, selector, factory/export, registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run focused tests, full `uv run pytest`, and candidate `fast`; require clean
    diagnostics and exact early/ocean parity tests.
- Iteration gate:
  - Run the fixed candidate-only iteration protocol with four workers and
    compare with the valid cached incumbent. Require delta at least `+0.002`,
    clean diagnostics, no days 1-5 mean RMSE regression over `2%`, and no
    variable/lead regression over `10%`.
- Validation gate:
  - Run once only after iteration promotion. Require delta at least `+0.001`,
    clean diagnostics, and the fixed early guardrail.
- Outcome that would falsify the hypothesis:
  - A subthreshold iteration result, any late T2m guardrail failure, or evidence
    that the skin endpoint duplicates rather than complements RI2m should scrap
    the idea without blend or cap tuning.

## Citations

- ECMWF, "Improved two-metre temperature forecasts in the 2024 upgrade."
  The IFS diagnoses T2m by stability-dependent interpolation between skin and
  lowest-model-level temperature. https://doi.org/10.21957/bi49s20qa8
- ECMWF/Copernicus CARRA2 Data User Guide, section 5.4. It gives an explicit
  skin-to-lowest-level surface-layer T2m formulation.
  https://confluence.ecmwf.int/spaces/CKB/pages/583771203/Copernicus+pan-Arctic+Regional+Reanalysis+CARRA2+Data+User+Guide
- Deardorff, J. W. 1978. Efficient prediction of ground surface temperature
  and moisture, with inclusion of a layer of vegetation. Journal of
  Geophysical Research 83(C4), 1889-1903.
  https://doi.org/10.1029/JC083iC04p01889
- Dynamaxx history:
  `.logbook/history/2026-07-10_04-01-39_late-ramped-skin-reservoir-coupling/decision.md`
  accepted the causal skin state and measured its late-lead benefit.

## Researcher Notes

This was impossible before `late-ramped-skin-reservoir-coupling`: earlier RI2m
and screen-temperature proposals had no prognostic surface endpoint and either
used only atmospheric bands or frozen analysis residuals. It is not another
RI2m band-averaging refinement like `hypsometric-centroid-ri2m-temperature`,
`theta-consistent-ri2m-reference-states`, or staged
`stability-adaptive-ri2m-temperature-bands`; the new information is the
accepted causal skin state. It is also not thermal back-coupling because it
does not change the atmospheric trajectory.

The direct target exposure is a real model-selection risk. Use one fixed
published-style observer, the existing cap and ramp, and no tuning. A clean
subthreshold result should move directly to scrap.

## Evaluator Notes

### 2026-07-10T09:04:18Z

Decision: move to `ready`; ranked #1 of the three reviewed ideas.

This is the strongest next experiment because it uses information that did not
exist before the new incumbent: the accepted, causally evolved land-skin state.
The local evidence is threshold-sized. Late-ramped reservoir coupling improved
iteration by `+0.007475791275368793` and validation by
`+0.007538212012404538`, with validation T2m RMSE improving by about `0.149 K`
on average after day 5. The proposed observer tests whether that demonstrated
late surface-memory signal can improve the scored T2m diagnostic directly,
while making MSLP, Z500, U10, and the atmospheric trajectory invariant.

The cited mechanism is supported: ECMWF documents stability-dependent T2m
interpolation between skin temperature and the lowest model level, including
measured T2m RMSE improvement from revising that interpolation. This proposal
is materially different from recent subthreshold RI2m reference-state variants
because its lower endpoint is a new prognostic surface state rather than
another rearrangement of the same atmospheric layers.

Implementation constraints for the selected candidate:

- Derive from
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin` and
  change only the output observer path; the atmospheric and skin trajectories
  must be identical to the incumbent for the same input.
- Retain the already evolved skin trajectory after rollout without placing it
  in `primitive_equations.State`, DFI, tracers, or emitted variables.
- Use the accepted zero-through-120-hour and 120-to-240-hour smooth ramp
  exactly. Do not tune the ramp, reservoir constants, transfer amplitudes,
  Richardson thresholds, or departure cap.
- Apply the branch only at valid land points. Ocean points, invalid masks,
  nonfinite diagnostics, unavailable skin state, and unsupported geometry must
  reproduce the incumbent T2m output exactly.
- Reuse the incumbent pressure-thickness RI2m references, finite guards, and
  final departure bound. Do not add an analysis residual, future truth,
  surface-type fit, or split-specific coefficient.
- Prove exact T2m parity through 120 hours and exact non-T2m parity at all
  leads in focused tests. The deterministic one-trajectory forecast contract
  and fixed evaluation protocols must remain unchanged.
- Treat a clean iteration gain below `+0.002` as falsification; do not revise
  caps, blend weights, or stability constants against evaluation results.
