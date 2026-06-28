---
schema_version: 1
slug: late-tapered-tropical-wtg-relaxation
title: Late-Taper the Tropical WTG Mass-DSE Relaxation
status: ready
created_at: 2026-06-26T18:26:20Z
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

# Late-Taper the Tropical WTG Mass-DSE Relaxation

## Hypothesis

The accepted tropical WTG mass-DSE relaxation improved the current model family,
but it applies the same relaxation timescale from spinup through day 15. WTG is
a large-scale tropical balance approximation, while the free forecast's passive
humidity, lower-boundary thermal state, and phase errors become less analysis-
anchored at later leads. A small late-lead taper can preserve the accepted early
tropical balance while reducing overconstraint of medium- and late-lead MSLP and
Z500.

## Mechanism

Add one opt-in candidate, for example `dino_hsl2_mass_dse_wtg_vdse_wtg_taper`.
Keep the incumbent HSL mass-DSE, pressure-ramped vertical-DSE increment, ocean
bulk heat flux, residual corrections, DFI, SIL3 settings, and output paths
unchanged.

Inside `_tropical_wtg_mass_dse_relaxation_step_filter`, multiply the existing
`relaxation_fraction` by a forecast-age taper read from `next_state.sim_time`.
Use a fixed schedule such as full strength through 120 h, smoothly tapering to
`0.70` by 240 h, then held at `0.70`. If `sim_time` is missing, nonfinite, or
outside finite bounds, fall back exactly to the incumbent untapered WTG filter.
Do not change the WTG latitude envelope, sigma envelope, low-mode mask,
temperature increment cap, or mass-neutral layer heat offset.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key, `dino_hsl2_mass_dse_wtg_vdse_wtg_taper`.
- API changes:
  - None. Forecast inputs, outputs, lead times, metrics, and protocols stay
    fixed.
- Tests to update:
  - Unit-test WTG taper weights at 0 h, 120 h, 240 h, and a late lead.
  - Verify missing or nonfinite `sim_time` reproduces incumbent WTG behavior.
  - Verify all existing WTG masks, caps, and layer heat offsets are preserved.
  - Verify the candidate factory differs from the incumbent only by the new WTG
    taper selector and model name.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 6-15 if fixed WTG
    strength is overconstraining late tropical mass-height adjustment.
  - Small aggregate primary-score gain, plausibly `+0.002` to `+0.006`, if late
    tropical height/pressure errors are a remaining source.
- Expected neutral metrics:
  - Days 1-5 should remain near incumbent because the taper is full strength
    through 120 h.
  - `10m_u_component_of_wind` should be mostly neutral because momentum and the
    wind diagnostic are unchanged.
- Possible regressions:
  - Tropical `2m_temperature` can worsen if the accepted WTG relaxation remains
    beneficial at all leads.
  - A subthreshold result is likely if late WTG overconstraint is not a material
    error source.

## Risks

- Numerical stability:
  - Low. The candidate weakens an existing capped thermal filter and has an
    exact incumbent fallback.
- Compute cost:
  - Negligible. It adds scalar lead-time arithmetic inside an existing filter.
- Data leakage:
  - None. The taper uses only model forecast age and fixed constants, not truth
    or validation results.
- Physical plausibility:
  - Moderate. WTG is physically grounded in tropical gravity-wave adjustment,
    but a forecast-age taper is a pragmatic reduced-model guard.
- Rollback complexity:
  - Low. Remove one selector, helper, factory/export, registry entry, and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_wtg_taper`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_wtg_taper --workers 4`.
  - Compare against the cached `dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent
    artifacts from `.logbook/leaderboard.json`; candidate source edits do not
    invalidate those artifacts.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-lead
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_wtg_taper --workers 4` only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, especially with worse late
    MSLP/Z500, would show fixed-strength WTG is not a remaining bottleneck.

## Citations

- Sobel, A. H., Nilsson, J., and Polvani, L. M. 2001. The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences. https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Raymond, D. J. and Zeng, X. 2005. Modelling tropical atmospheric convection
  in the context of the weak temperature gradient approximation. Quarterly
  Journal of the Royal Meteorological Society. https://doi.org/10.1256/qj.03.97
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_tropical_wtg_mass_dse_relaxation_step_filter` as a capped, low-mode,
  mass-neutral thermal filter.
- Dynamaxx history:
  `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg/decision.md`
  accepted the current incumbent with cached iteration and validation gains.

## Researcher Notes

This is not a duplicate of `late-lead-vertical-dse-cap-release`,
`hydrostatic-work-gated-vertical-dse`, or
`baroclinic-mode-vertical-dse-spinup`: it leaves the accepted vertical-DSE
increment, cap, pressure ramp, and spatial guard untouched. It is also distinct
from `time-centered-tropical-wtg-mass-dse` and
`incremental-tropical-wtg-mass-dse`, which change WTG time placement or
application form rather than only reducing late-lead relaxation strength.

## Evaluator Notes

### 2026-06-26T18:29:29Z

Decision: move to `ready`; ranked 1 of 2 evaluated proposals.

This is implementation-ready and the stronger next experiment. The accepted
WTG mass-DSE relaxation produced a clean positive score movement, and the
current incumbent's pressure-ramped vertical-DSE addition was also accepted
with large iteration and validation gains. Recent follow-ups that altered the
vertical-DSE mechanism directly were clean but subthreshold or harmful, so the
best remaining low-surface-area question is whether the accepted WTG component
is too strong at late lead times.

The proposed schedule is conservative: it is exactly incumbent-equivalent
through 120 h, so it should protect the fixed day-1-through-day-5 guardrail,
and then only weakens an existing capped thermal relaxation to 70 percent by
240 h. The mechanism is physically plausible as a reduced-model guard because
WTG balance is well supported for tropical free-tropospheric large-scale flow,
while free-running forecast humidity, lower-boundary thermal state, and phase
errors become less analysis-anchored at later leads. Literature checks support
the broad WTG basis, but not the exact taper constants; those constants are a
single fixed side-by-side hypothesis, not a sweep.

Implementation surface is small and compatible with the incumbent code:
`next_state.sim_time` already exists for the vertical-DSE ramp path, and the
WTG filter is isolated behind `_tropical_wtg_mass_dse_relaxation_step_filter`.
Require the implementer to preserve the existing WTG latitude envelope, sigma
envelope, low-mode mask, cap, mass-neutral heat offset, finite fallback, and
all output/evaluation contracts. Do not rerun the incumbent unless the cached
leaderboard artifacts are concretely invalid under `roles/PROTOCOL.md`.
