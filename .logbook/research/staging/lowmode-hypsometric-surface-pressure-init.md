---
schema_version: 1
slug: lowmode-hypsometric-surface-pressure-init
title: Initialize Surface Pressure with a Bounded Low-Mode Hypsometric Correction
status: staging
created_at: 2026-06-21T21:34:31Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Initialize Surface Pressure with a Bounded Low-Mode Hypsometric Correction

## Hypothesis

The adapter initializes Dinosaur `log_surface_pressure` from `surface_pressure`
when available, otherwise from `mean_sea_level_pressure`, and otherwise from a
constant fallback. The terrain-aware surface-pressure/orography experiment
showed that a broad terrain coupling can improve primary score while failing
mass-field guardrails, so a prognostic terrain retry is unsafe. A smaller
candidate can instead correct only the large-scale initialized surface pressure
when both MSLP and lower-column thermal/geopotential information imply a
bounded sea-level reduction mismatch.

If the incumbent still carries a low-wavenumber surface-pressure initialization
bias, correcting it before the accepted log-pressure and hydrostatic
temperature initialization may improve MSLP and Z500 without adding orography,
changing pressure gradients over terrain, or altering the output contract.

## Mechanism

Register a side-by-side candidate extending the incumbent name with
`_lowmode_hyp_sp_init`. Preserve the incumbent zero-orography rollout,
log-pressure remap, hydrostatic layer-mean temperature initialization, DFI,
weak-HS analysis equilibrium, theta tendency, Coriolis split, off-centering,
surface residuals, and output paths.

For this candidate only:

- before `weather_state_to_dinosaur_state` constructs `log_surface_pressure`,
  compute the incumbent surface-pressure field using `_surface_pressure_values`;
- if both `mean_sea_level_pressure` and enough low-level pressure-level
  temperature/geopotential channels are available, infer a dry hypsometric
  surface-pressure estimate from MSLP and a bounded effective terrain height;
- retain only the low horizontal modes of the logarithmic correction
  `log(sp_hypsometric) - log(sp_incumbent)`, using a conservative mask such as
  total wavenumber no higher than 6 to 8;
- clip the correction to a small fixed range, for example no more than a few
  hPa equivalent in surface pressure, and blend it into the incumbent
  initialization with a fixed fraction;
- do not change orography, pressure-level output interpolation, MSLP output
  diagnosis, or any valid-time forecast post-processing;
- fall back to the incumbent surface pressure exactly when inputs are missing,
  nonfinite, or outside physical bounds.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate with suffix `_lowmode_hyp_sp_init`.
- API changes:
  - None. Forecast input variables, output variables, lead times, metrics, and
    fixed protocols stay unchanged.
- Tests to update:
  - Unit-test finite fallback, low-mode mask construction, correction clipping,
    and exact no-op behavior when MSLP or required pressure-level channels are
    absent.
  - Verify the candidate changes only initialized `log_surface_pressure` and not
    raw pressure-level temperature/wind initialization helpers.
  - Verify the factory preserves all incumbent flags except the new surface
    pressure initialization selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` if a broad initial mass-field bias remains from
    MSLP/surface-pressure ambiguity.
  - `geopotential_500` if corrected initial surface pressure improves
    hydrostatic column placement before rollout.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should remain mostly governed
    by accepted residual paths, though they can move indirectly through the
    changed mass field.
- Possible regressions:
  - Even a low-mode surface-pressure correction can perturb balanced winds and
    mass fields. Early MSLP/Z500 guardrails are the main risk.
  - If `surface_pressure` is already correct in the fixed WeatherBench2 input,
    the correction should be skipped or nearly neutral; a nonzero correction
    would be harmful.

## Risks

- Numerical stability:
  - Moderate. The correction changes an initialized prognostic mass variable,
    but it is bounded, low-mode, and fallback guarded.
- Compute cost:
  - Low. The added work is one same-time diagnostic and one spectral mask per
    initial state.
- Data leakage:
  - Low. It uses only same-time analysis fields available in the forecast input.
- Physical plausibility:
  - Moderate. The hypsometric relation links pressure reduction, temperature,
    and height, but the inferred terrain height is a simplified diagnostic and
    must remain tightly bounded.
- Rollback complexity:
  - Low to moderate. Remove one initialization helper/flag, one factory/export,
    one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    incumbent, clean diagnostics, no early day-1-through-day-5 RMSE guardrail
    failure, and no variable-by-lead guardrail failure.
- Validation gate:
  - Run fixed validation only after iteration promotion and require validation
    delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A negative iteration delta, early MSLP/Z500 guardrail regression, or a unit
    test showing the fixed data already supplies consistent surface pressure
    would falsify this mechanism.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` initializes
    `log_surface_pressure` through `_surface_pressure_values` before pressure to
    sigma remapping.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography/decision.md`
    showed that terrain and surface-pressure handling can improve primary score
    but fail early mass-field guardrails, motivating a bounded low-mode
    initialization-only variant.
  - Dynamaxx history:
    `.logbook/history/2026-06-17_00-55-17_log-pressure-sigma-initialization/decision.md`
    accepted log-pressure initialization, so this proposal preserves that remap
    and changes only the surface-pressure field supplied to it.
  - Pauley, P. M. 1998. An Example of Uncertainty in Sea Level Pressure
    Reduction. Weather and Forecasting.
    https://doi.org/10.1175/1520-0434(1998)013%3C0833:AEOUIS%3E2.0.CO;2
  - Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
    Survey, second edition. Academic Press.

## Researcher Notes

This is not a duplicate of the staged persistent or dynamic MSLP output
diagnostics: it does not change emitted MSLP after rollout. It is also not a
terrain/orography retry: orography remains zero and no terrain term is inserted
into pressure gradients. The correction is same-time, low-mode, clipped, and
initialization-only. The terrain-aware guardrail failure is strong negative
evidence, so the Evaluator should rank this only if it believes the low-mode
bound materially changes the risk profile.

## Evaluator Notes

### 2026-06-21T21:38:13Z

Moved to `staging`. The mechanism is physically coherent and preserves the
forecast contract, but it changes initialized prognostic mass and therefore
inherits meaningful early MSLP/Z500 guardrail risk from the rejected
terrain-aware surface-pressure/orography experiment. The low-mode clipping and
initialization-only scope make it materially safer than the failed terrain run,
so it is not scrapped, but it is not the best immediate candidate while a
narrower output-side wind residual test is available. Rank 2 of 3.

### 2026-06-28T07:01:40Z

Decision: keep in `staging`; rank 4 of 4.

This is the least attractive candidate in the current MSLP/pressure set. It is
bounded and initialization-only, but it still edits initialized prognostic
`log_surface_pressure`, so it can perturb the mass field, balanced winds, Z500,
T2m, and MSLP through the full rollout. That violates the current preference
for output-only or tightly isolated diagnostics when a simpler MSLP-only test
is available. Do not promote it ahead of the persistent offset or hypsometric
output diagnostics. Keep staged rather than scrapping because a future
read-only residual analysis could still show a true low-mode initialization
bias, but require strong evidence before spending an iteration on a prognostic
mass change.
