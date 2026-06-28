---
schema_version: 1
slug: narrow-core-tropical-wtg-envelope
title: Narrow-Core Tropical WTG Envelope
status: ready
created_at: 2026-06-27T05:18:39Z
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

# Narrow-Core Tropical WTG Envelope

## Hypothesis

The accepted tropical WTG mass-DSE relaxation improved the incumbent by damping
large-scale free-tropospheric tropical thermal imbalance, but its fixed latitude
envelope reaches full strength inside 12 degrees and tapers to zero only by 27
degrees. Some recent WTG variants failed by changing relaxation timing, gating,
or filter ordering. A narrower side-by-side latitude envelope may preserve the
equatorial WTG benefit while reducing subtropical interference with baroclinic
structure and pressure gradients.

## Mechanism

Add a side-by-side candidate `dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow`.
For this candidate only, construct the WTG relaxation filter with a full-strength
latitude core inside 8 degrees and zero strength by 22 degrees. Preserve the
incumbent sigma envelope, low-mode spectral mask, relaxation timescale, mass-DSE
layer-mean removal, temperature increment cap, vertical-DSE ramp, residual
corrections, and output contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Register only the side-by-side candidate model name.
- API changes:
  - Add opt-in WTG latitude-envelope constants or a small selector that leaves
    the incumbent envelope unchanged by default.
- Tests to update:
  - Unit-test incumbent and narrow envelope values at equator, full-strength
    boundary, taper, and zero boundary.
  - Verify candidate factory preserves all incumbent flags except the WTG
    envelope selector.
  - Verify registry and non-JIT smoke forecast are finite.

## Expected Metric Movement

- Expected improvements:
  - Small improvement in `geopotential_500` and `mean_sea_level_pressure` at
    medium and late leads if subtropical WTG forcing has been over-damping
    baroclinic thermal structure.
- Expected neutral metrics:
  - Equatorial thermal stabilization should remain close to incumbent behavior.
  - Compute cost should be unchanged.
- Possible regressions:
  - Tropical `2m_temperature` or pressure skill may degrade if the accepted
    wider envelope is needed to control the full Hadley-cell thermal anomaly.

## Risks

- Numerical stability:
  - Low. The relaxation filter and caps are unchanged.
- Compute cost:
  - Negligible. The same transforms are used.
- Data leakage:
  - None. The envelope uses fixed latitude geometry only.
- Physical plausibility:
  - Moderate. WTG balance is strongest in the deep tropics, while the subtropics
    can retain stronger rotational and baroclinic balance.
- Rollback complexity:
  - Low. The candidate is side-by-side and selector-gated.

## Evaluation Plan

- Fast gate:
  - Run focused unit tests, full `uv run pytest`, and
    `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow --workers 4`.
  - Compare against cached leaderboard incumbent metrics for
    `dino_hsl2_mass_dse_wtg_vdse_ramp`.
- Validation gate:
  - Run validation only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - Any diagnostic failure, iteration primary score below the incumbent
    acceptance threshold, or variable-lead guardrail regressions beyond protocol
    limits.

## Citations

- Sobel, A. H. and Bretherton, C. S. 2000. Modeling tropical precipitation in a
  single column. Journal of Climate.
- Raymond, D. J. and Zeng, X. 2005. Modelling tropical atmospheric convection in
  the context of the weak temperature gradient approximation. Quarterly Journal
  of the Royal Meteorological Society.
- Held, I. M. and Hou, A. Y. 1980. Nonlinear axially symmetric circulations in a
  nearly inviscid atmosphere. Journal of the Atmospheric Sciences.

## Researcher Notes

This is not a duplicate of recent rejected WTG variants. It does not add
moisture-convergence gating, time tapering, ocean weighting, filter reordering,
or pressure-work coupling. It tests one fixed geometric support choice for the
already accepted WTG mechanism while leaving fixed evaluation protocols intact.

## Evaluator Notes

2026-06-27T05:18:39Z main-loop Evaluator simulation: staged. The proposal is
implementable and not a direct duplicate, but it is primarily a fixed-envelope
constant adjustment and is more likely to overfit the current WTG support than
the midpoint ramp timing candidate. Reconsider after one or more lower-tuning
vertical-DSE timing or discretization checks are exhausted.

2026-06-27T08:45:00Z main-loop Evaluator simulation: ready. The lower-tuning
midpoint vertical-DSE ramp timing idea was implemented and rejected with a clean
but subthreshold iteration delta. Among inspected WTG follow-ups, this proposal
is the only one already retargeted to the current
`dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent and it has the smallest code and
compute surface. Older staged WTG growth/timing proposals target the pre-ramp
WTG incumbent and should be retargeted separately before use.
