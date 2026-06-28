---
schema_version: 1
slug: lead-decayed-analysis-hs-equilibrium
title: Decay the Analysis-Offset Held-Suarez Equilibrium During Rollout
status: ready
created_at: 2026-06-20T20:51:54Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Decay the Analysis-Offset Held-Suarez Equilibrium During Rollout

## Hypothesis

The accepted incumbent gained skill by adding a bounded low-mode analysis
offset to the weak Held-Suarez equilibrium, showing that the raw analyzed
large-scale thermal state is a useful relaxation anchor. That offset is
currently persistent for the full 15-day rollout. If part of the remaining
day-4 and long-lead mass-field error comes from over-anchoring the model toward
the initial analyzed thermal anomaly after synoptic evolution has moved on, a
fixed lead-time decay of only the offset should retain the accepted early
thermal balance while reducing later MSLP and Z500 bias.

This preserves the weak-HS relaxation rates. It is materially different from
the rejected analysis-offset relaxation-rate mask, which weakened stabilizing
thermal damping where the offset was large and caused severe 2 m temperature
and pressure regressions.

## Mechanism

Register a side-by-side candidate with a suffix such as
`_analysis_hs_eq_decay`. Keep DFI, log-pressure and hydrostatic layer
initialization, exact Coriolis Strang splitting, Richardson 10 m wind,
theta-form tendency, theta mean recentering, off-centered SIL3, horizontal
diffusion, and scale-separated near-surface residual correction unchanged.

For this candidate only:

- compute the accepted low-mode clipped equilibrium offset from the raw
  initialized state exactly as the incumbent does;
- use the full offset during DFI, matching the accepted balanced initialization
  path rather than revisiting the rejected DFI-balanced anchor;
- initialize positive-time rollout `sim_time` at zero and multiply the offset
  by a fixed decay factor `exp(-t / tau)` inside the weak-HS forcing, with
  `tau = 10 days` and no data-dependent tuning;
- apply the decay to the equilibrium offset only, not to `kt`, `ka`, `ks`, or
  any residual-diagnostic decay;
- keep the offset low-mode mask and Kelvin cap identical to the incumbent;
- fall back to the incumbent constant offset if `sim_time` is absent or any
  decayed offset is nonfinite.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate factory and registry entry only.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, and metrics
    remain fixed.
- Tests to update:
  - Verify full offset is used at positive-time `t = 0` and decays
    monotonically for later `sim_time`.
  - Verify DFI still uses the accepted incumbent offset behavior.
  - Verify relaxation rates and near-surface residual decays are unchanged.
  - Verify missing or nonfinite `sim_time` falls back to the incumbent.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` around days 3 to 8 if constant offset memory
    over-constrains evolving low-mode thickness.
  - `geopotential_500` at medium and long leads through less stale thermal
    anchoring.
- Expected neutral metrics:
  - Day-1 to day-2 `2m_temperature` should remain close to incumbent because
    the accepted initial offset and residual correction are preserved.
  - `10m_u_component_of_wind` should be near neutral because no wind diagnostic
    or momentum tendency changes.
- Possible regressions:
  - If the constant analysis offset remains beneficial through day 15, the
    taper will remove useful thermal anchoring and regress T2m, MSLP, or Z500.
  - A badly handled `sim_time` path could accidentally change DFI or all
    candidates, so tests must isolate the option.

## Risks

- Numerical stability:
  - Low. The candidate reduces a bounded thermal-equilibrium offset over time
    and keeps damping rates unchanged.
- Compute cost:
  - Negligible. One scalar exponential multiplies an existing nodal field.
- Data leakage:
  - None. It uses only the same initial analysis already used by the incumbent
    and a fixed lead-time decay.
- Physical plausibility:
  - Moderate. IAU and nudging methods commonly taper analysis increments in
    time, but this applies the idea to an idealized equilibrium offset rather
    than a full data-assimilation increment.
- Rollback complexity:
  - Low. Remove one adapter option, one forcing argument, one factory/export,
    one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_name> --workers 4`.
  - Support requires primary delta at least `+0.002` against the cached
    incumbent, clean diagnostics, and no fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_name> --workers 4`
    only after iteration promotion.
  - Support requires validation delta at least `+0.001` with the same
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta, especially with early
    T2m/MSLP regression, would show that persistent offset memory is still
    useful or that the decay removes it too quickly.

## Citations

- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
  assimilation using incremental analysis updates. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
  digital filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2

## Researcher Notes

This proposal accounts for the accepted analysis-HS evidence but changes a
different control knob from the two latest rejected follow-ups: it does not
compute the offset from the DFI-balanced state and does not reduce local
thermal damping where the offset is large.

## Evaluator Notes

### 2026-06-20T20:56:31Z

Decision: move to `ready`; ranked first of the three new proposals.

This is the best next experiment because it builds directly on the accepted
analysis-offset Held-Suarez equilibrium without repeating the two failed
follow-ups. The accepted raw analysis-HS offset produced large positive
iteration and validation deltas, while the DFI-balanced variant was
near-neutral/slightly negative and the relaxation-rate mask strongly failed
with severe `2m_temperature` and `mean_sea_level_pressure` guardrail
regressions. This proposal preserves the raw-state offset at initialization and
keeps weak-HS rates unchanged, so it does not weaken the stabilizing thermal
damping that the rate-mask result showed is important.

The main risk is that the accepted constant offset may remain useful through
day 15, making any decay negative or subthreshold. That risk is acceptable for
a ready slot because the implementation surface is small, the mechanism is
localized to a bounded low-mode equilibrium offset, and the expected failure
mode is a clean score regression rather than broad numerical instability. The
Implementer should keep DFI on the incumbent full-offset path, initialize
positive-time `sim_time` only after DFI, and prove that relaxation rates and
surface residual memory are unchanged.
