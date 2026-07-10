---
schema_version: 1
slug: late-ramped-skin-reservoir-coupling
title: Late-Ramped Skin Reservoir Coupling
status: history
created_at: 2026-07-05T07:09:19Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Late-Ramped Skin Reservoir Coupling

## Hypothesis

The rejected `prognostic-force-restore-skin-reservoir` candidate produced a large positive iteration primary delta of `+0.015110953201`, but it failed the fixed early `2m_temperature` RMSE guardrail. That result is useful negative evidence: the force-restore reservoir had enough physical signal to move the aggregate score, but its immediate coupling damaged early screen temperature.

A smaller side-by-side candidate that reuses the force-restore idea only after the early guardrail window should preserve the late lower-boundary memory signal while avoiding the day-1-to-day-5 T2m failure. The mechanism is not another output residual or terrain-work heat tweak; it tests whether a finite heat-capacity surface state can improve late lower-tropospheric thermal evolution once DFI, RI2m, and accepted residual-memory guards have already stabilized the first few forecast days.

## Mechanism

Add one current-incumbent descendant, for example `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_late_skin`.

For this candidate only:

- carry a minimal 2-D land skin/deep reservoir pair through the rollout wrapper, initialized from lead-zero near-surface air temperature and broad land/ocean low-mode residual information;
- keep the reservoir completely inactive through `120 h`, ramp it smoothly to full strength by `240 h`, and keep every scored early lead exactly on the incumbent reservoir-free path except for ordinary floating-point roundoff;
- couple the reservoir only to the lowest sigma-layer temperature with a capped, mean-neutral dry-static-energy exchange;
- preserve the accepted ocean bulk sensible heat flux, weak-HS relaxation, HSL/mass-DSE/WTG/vertical-DSE path, RI2m diagnostic, Ekman closure, orographic lift, terrain-work drag/heating, MSLP output, and wind diagnostics;
- leave the reservoir out of `State.tracers`, output variables, and DFI, so it is not advected as a hidden target and is not time-reversed during initialization;
- fall back to the incumbent trajectory if land-sea mask, reservoir state, temperature exchange, ramp, or finite checks fail.

This is deliberately stronger than the rejected `late-lowmode-t2m-thermal-backcoupling`, which fed a static residual back into the lowest layer and was clean but subthreshold at `+0.0004022561143662562`. The new element is a co-evolving finite-capacity reservoir, but with the early coupling removed to address the force-restore guardrail failure.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key such as `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_late_skin`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead days, metrics, and protocols stay fixed.
- Tests to update:
  - Candidate factory preserves every incumbent flag except the late skin-reservoir selector and name.
  - Reservoir exchange is exactly zero through `120 h` and bounded during the `120 h` to `240 h` ramp.
  - The air-skin exchange is finite, cap-limited, and mean-neutral in dry-static-energy units.
  - Missing or invalid land-sea mask reproduces the incumbent.
  - DFI does not carry or update the reservoir.
  - The reservoir is not emitted as an output channel and is not stored as a tracer.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 6-15 if the rejected force-restore candidate's large aggregate gain was a real late surface-memory signal.
  - Small `mean_sea_level_pressure` and `geopotential_500` gains if lower-column thermal memory improves thickness evolution after the early window.
- Expected neutral metrics:
  - Day-1-to-day-5 `2m_temperature`, because the reservoir is exactly inactive through `120 h`.
  - `10m_u_component_of_wind`, because momentum tendencies and wind diagnostics are unchanged.
- Possible regressions:
  - Late `2m_temperature` can still regress if the co-evolved reservoir drifts from the verification-relevant surface state.
  - MSLP or Z500 can regress if the lower-layer heat exchange perturbs hydrostatic thickness in a stale or spatially biased way.

## Risks

- Numerical stability:
  - Moderate. The exchange is capped and late-ramped, but it adds an auxiliary state to the rollout wrapper.
- Compute cost:
  - Low to moderate. It adds local 2-D reservoir arithmetic per inner step and no extra trajectories.
- Data leakage:
  - Low. The reservoir is initialized only from lead-zero state/static masks and evolves causally.
- Physical plausibility:
  - Moderate to high. Force-restore land-surface schemes and soil-moisture/temperature memory are established, but this is a reduced dycore surrogate.
- Rollback complexity:
  - Moderate. Remove the auxiliary carry, one selector, one factory/export, one registry key, and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_late_skin`
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_late_skin --workers 4`
  - Compare against cached `dino_ri2m_ekman_depth_orolift_lwind_twork_drag` artifacts when valid.
  - Support requires primary delta at least `+0.002`, clean diagnostics, no early day-1-to-day-5 mean RMSE guardrail failure, and no variable-lead guardrail failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_late_skin --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show that the force-restore gain cannot be recovered once early T2m damage is removed. Any early T2m guardrail failure would show the ramp or implementation is not isolating the risk.

## Citations

- Deardorff, J. W. 1978. Efficient prediction of ground surface temperature and moisture, with inclusion of a layer of vegetation. Journal of Geophysical Research. https://doi.org/10.1029/JC083iC04p01889
- Seneviratne, S. I. et al. 2010. Investigating soil moisture-climate interactions in a changing climate: A review. Earth-Science Reviews. https://doi.org/10.1016/j.earscirev.2010.02.004
- Beljaars, A. C. M. and Holtslag, A. A. M. 1991. Flux parameterization over land surfaces for atmospheric models. Journal of Applied Meteorology. https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2
- Dynamaxx history: `.logbook/history/2026-06-30_22-26-27_prognostic-force-restore-skin-reservoir/decision.md` recorded iteration delta `+0.015110953201` but rejected the candidate for early `2m_temperature` guardrail failure.
- Dynamaxx history: `.logbook/history/2026-06-28_17-32-02_late-lowmode-t2m-thermal-backcoupling/decision.md` showed a zero-through-120 h thermal ramp protected guardrails but a static residual back-coupling was too weak.

## Researcher Notes

This is not an incumbent rerun and does not propose modifying accepted cached artifacts. It avoids the recent terrain-work heat/deposition family, avoids Richardson wind reuse, and does not touch `.logbook/leaderboard.json`.

Prior-history comparison is central: the proposal keeps the scientifically promising part of the rejected force-restore candidate, but removes its known early coupling failure mode. It is distinct from the rejected `late-lowmode-t2m-thermal-backcoupling` because the reservoir co-evolves causally rather than applying a fixed residual heat source. It should be scrapped rather than retuned if the late-ramped version is clean but still below the fixed iteration promotion threshold.

## Evaluator Notes

### 2026-07-05T07:14:22Z

Decision: move to `staging`; not selected as the immediate ready candidate.

This is not an exact duplicate and should be preserved. The rejected `prognostic-force-restore-skin-reservoir` run is unusually informative: it improved iteration primary score by `+0.015110953201` but failed the fixed T2m guardrails, with day-1-to-day-5 `2m_temperature` mean RMSE regression `+0.318319` and a worst single-lead T2m regression of `+1.026170` at 240 h. The rejected `late-lowmode-t2m-thermal-backcoupling` then showed that a zero-through-120 h ramp can protect early guardrails, but the static residual back-coupling only gained `+0.0004022561143662562`, below the promotion threshold. The proposed co-evolving reservoir is a plausible attempt to combine those lessons.

The proposal stays in staging rather than ready because the implementation is larger than the DFI filter-list split and the current protocol asks for ready ideas to be small. It adds auxiliary carried lower-boundary state, finite/cap/fallback logic, DFI exclusion behavior, and a late air-skin exchange path in a family with mixed evidence: the land snow/soil reservoir was effectively neutral at `+0.0000005876598810350409`, related lower-boundary thermal refinements are often subthreshold, and the force-restore evidence includes a major target-variable guardrail failure. Active staging already includes other surface-memory or lower-boundary thermal ideas such as soil-moisture Bowen T2m memory, vegetation-canopy thermal impedance, lake-ice thermal reservoir, and stability-gated ocean heat flux.

Keep this staged as a higher-upside follow-up if the queue needs a more ambitious lower-boundary experiment after smaller candidates are exhausted. If later promoted, require exact incumbent identity through 120 h apart from roundoff, no reservoir in DFI or emitted outputs, strict dry-static-energy mean neutrality, and automatic fallback to the incumbent path when masks or reservoir diagnostics are invalid.

### 2026-07-10T04:00:21Z

Decision: move to `ready`; ranked #1 of the three compared proposals.

The queue now needs an idea with threshold-sized evidence, not another narrow
RI2m refinement. The original force-restore reservoir improved iteration
primary by `+0.015110953201186633` and improved early MSLP, Z500, and U10 RMSE
substantially, but failed because immediate lower-boundary coupling damaged
T2m. This proposal removes that identified early failure channel by making the
candidate exactly incumbent-equivalent through 120 hours, while retaining a
causally evolving finite-capacity reservoir after the guardrail window.

It ranks above `low-mode-force-restore-skin-coupling` because temporal
isolation is directly tied to the measured early failure, requires no per-step
spectral transform, and has simpler conservation/fallback behavior. It ranks
above `analysis-calibrated-ri2m-transfer-ratio` because the reservoir family
has demonstrated score leverage well above the fixed threshold, whereas recent
RI2m reference-state refinements have been small or neutral.

Implementation constraints for the current run:

- Derive from current incumbent
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m`, not the older
  terrain-work model named in the original example.
- Use candidate name
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin`.
- Reuse the fixed physical constants from the rejected reservoir; do not tune
  exchange strength, heat capacity, restore time, or caps.
- Keep atmospheric coupling exactly zero through 120 hours and use one fixed
  smooth ramp to full strength at 240 hours. The original worst T2m regression
  occurred at 240 hours, so the fixed single-lead guardrail remains the main
  risk and must not be waived.
- Keep the reservoir outside DFI, tracers, and emitted outputs. Invalid mask,
  shape, or finite checks must reproduce the incumbent path.
- Compare only with valid cached incumbent artifacts, run no golden, and scrap
  rather than retune if the fixed iteration gate fails.
