---
schema_version: 1
slug: global-mean-pressure-anchor
title: Anchor the Global-Mean Surface-Pressure Mode
status: ready
created_at: 2026-06-16T17:39:18Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs
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

# Anchor the Global-Mean Surface-Pressure Mode

## Hypothesis

The accepted incumbent has strong aggregate improvement from weak thermal
relaxation, but mean sea-level pressure and 500 hPa geopotential still carry
large absolute RMSE at medium and long leads. A dry hydrostatic primitive-equation
dycore should conserve global dry-air mass in the absence of sources and sinks.
Preserving only the global spectral-mean mode of `log_surface_pressure` during
time stepping may reduce avoidable mass-field drift while leaving balanced
spatial pressure anomalies, temperature evolution, and low-level winds mostly
unchanged.

## Mechanism

Add an optional Runge-Kutta step filter that copies the previous state's
zero-wavenumber `log_surface_pressure` coefficient into the next state after each
inner step. The filter should preserve all nonzero pressure modes and all other
state leaves. Applied inside the existing `step_with_filters` path, this keeps
the candidate close to a dry-mass conservation constraint throughout the rollout
and during digital-filter initialization, without using analysis residuals or
future truth.

The candidate should preserve all accepted incumbent mechanisms: digital filter
initialization, near-surface residual diagnostics, and wind-sparing weak
Held-Suarez thermal relaxation. A side-by-side registered model name such as
`dinosaur_dfi_surface_residual_weak_hs_pressure_anchor` is appropriate.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add a side-by-side factory for
    `dinosaur_dfi_surface_residual_weak_hs_pressure_anchor`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` and output variables remain
    unchanged.
- Tests to update:
  - Add a unit test for the pressure-anchor filter showing only the
    zero-wavenumber `log_surface_pressure` coefficient is copied from the
    previous state.
  - Add a trajectory-construction test showing the filter is included only when
    the candidate flag is enabled.
  - Add factory and registry tests showing the candidate preserves DFI,
    near-surface residual correction, and weak Held-Suarez relaxation.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at medium and long leads if part of the remaining
    error is global pressure drift rather than synoptic anomaly error.
  - `geopotential_500` at medium and long leads through improved pressure-level
    interpolation and column-thickness consistency.
- Expected neutral metrics:
  - `2m_temperature` should remain close to the incumbent because the thermal
    tendency and near-surface residual correction are unchanged.
  - `10m_u_component_of_wind` should remain close to the incumbent because the
    candidate does not add momentum damping or change vorticity/divergence
    tendencies directly.
- Possible regressions:
  - If the incumbent's global pressure drift compensates another model bias,
    anchoring the mean could worsen MSLP or Z500 despite being conservative.
  - If `log_surface_pressure` mean is not a close proxy for global dry mass on
    the packed sigma grid, score movement may be too small to clear the
    iteration threshold.

## Risks

- Numerical stability:
  - Low. The filter only edits one existing modal coefficient and does not add
    new tendencies, transforms, or divisions.
- Compute cost:
  - Negligible relative to the incumbent. The filter is a small modal-array
    update inside existing stepping.
- Data leakage:
  - Low. The preserved value comes only from the model state carried from the
    initial condition and previous step, not from evaluation targets or future
    truth.
- Physical plausibility:
  - Moderate to high for a dry global primitive-equation selection experiment.
    The mechanism enforces a mass-like invariant but does not attempt full
    energy or angular-momentum conservation.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter flag and one side-by-side
    registry entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_pressure_anchor`.
  - Require `diagnostics.failed=false` and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_pressure_anchor --workers 4`.
  - Support for the hypothesis is a primary-score gain of at least `+0.002`
    versus `dinosaur_dfi_surface_residual_weak_hs`, ideally led by MSLP or Z500,
    with all fixed RMSE guardrails passing.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_pressure_anchor --workers 4`
    only after iteration promotion.
  - Acceptable validation evidence is a primary-score gain of at least `+0.001`
    with clean diagnostics and guardrails.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with sub-threshold primary movement, MSLP or
    Z500 regression, or any early mass-field guardrail failure would indicate
    that global pressure anchoring is not useful for this incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` constructs
  the incumbent trajectory with DFI, near-surface residual correction, weak
  Held-Suarez thermal relaxation, and `time_integration.step_with_filters`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  defines `State.log_surface_pressure` as a modal prognostic field.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  exposes step filters that receive the previous and next Runge-Kutta states.
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics, 227, 3715-3730.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Jablonowski, C. and Williamson, D. L. 2006. A baroclinic instability test case
  for atmospheric model dynamical cores. Quarterly Journal of the Royal
  Meteorological Society, 132, 2943-2975. https://doi.org/10.1256/qj.06.12
- NOAA/NCAR Global Atmospheric Dynamical Core Assessment, 2008, identifies mass
  conservation as a necessary attribute for global atmospheric solvers.
  https://www2.mmm.ucar.edu/projects/global_cores/core_assessment.pdf

## Researcher Notes

This is not a duplicate of `mass-diagnostic-analysis-residuals`, which applied
decaying output-time analysis residuals to MSLP and Z500 and produced only a
`+0.00042505322207886387` iteration delta. This proposal uses no analysis
residual and instead constrains one global prognostic mode through the existing
time-step filter interface.

It is also distinct from `terrain-aware-surface-pressure-orography`, which
introduced spatial orography and badly failed early MSLP/Z500 guardrails despite
large aggregate score gains. The proposed anchor is spatially uniform in modal
space, so it should not introduce the terrain pressure-gradient imbalance that
caused that rejection. It is not a Held-Suarez variant and does not spend more of
the long-lead 10 m wind guardrail margin through additional damping.

## Evaluator Notes

2026-06-16T17:42:01Z - Move to `ready` for Iteration 11 triage against
`dinosaur_dfi_surface_residual_weak_hs` at
`4756cc9a4b69c41eec60e2177fb03a73974f0e2d`.

Ranked recommendation: 1 of 2, strongest next implementation candidate.

The proposal is implementable under the fixed forecast contract. Source
inspection confirms `time_integration.step_with_filters` passes both the
previous and next Runge-Kutta states to each filter, so a side-by-side adapter
flag can preserve the previous state's zero-wavenumber
`log_surface_pressure` coefficient while leaving other prognostic fields and
nonzero pressure modes unchanged. This keeps the implementation surface limited
to the Dinosaur adapter, exports, registry entry, and focused tests.

The scientific risk is acceptable for one fixed-gate experiment. Prior
mass-field attempts provide mixed negative evidence: the terrain/orography
candidate showed that spatial pressure changes can hide severe early MSLP and
Z500 guardrail failures behind aggregate score gains, while the output-only
mass diagnostic residual was safe but too small to promote. This proposal is
narrower than terrain/orography because it constrains only a global modal
pressure mode and uses no analysis residuals, future targets, validation
feedback, or altered evaluation protocol. It is also preferable to another
damping or time-stepping change immediately after the accepted weak
Held-Suarez candidate, because the latest validation guardrail margin is
tightest for long-lead `10m_u_component_of_wind`.

Implementation should be side-by-side as
`dinosaur_dfi_surface_residual_weak_hs_pressure_anchor`, preserving DFI,
near-surface residual correction, and weak thermal Held-Suarez relaxation.
Reject before validation if iteration movement is sub-threshold or if early
MSLP/Z500 RMSE guardrails regress, since that would indicate the global
pressure-mode constraint is either compensating the wrong bias or too small to
matter under the fixed WeatherBench2 metrics.
