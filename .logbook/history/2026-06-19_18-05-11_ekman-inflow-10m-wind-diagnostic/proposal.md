---
schema_version: 1
slug: ekman-inflow-10m-wind-diagnostic
title: Add a Bounded Ekman-Inflow 10 m Wind Diagnostic
status: ready
created_at: 2026-06-19T17:59:18Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a Bounded Ekman-Inflow 10 m Wind Diagnostic

## Hypothesis

The accepted Richardson-number 10 m wind diagnostic corrected the largest
screen-wind error by rescaling the lowest sigma-layer wind speed, but it leaves
the wind direction unchanged. Surface-layer winds are not only slower than the
lowest free-atmosphere model wind; turbulent stress and Coriolis balance also
turn the wind across isobars toward lower pressure. The current incumbent still
shows increasingly negative late-lead `10m_u_component_of_wind` bias in the
accepted iteration and validation artifacts, so a bounded direction-only
Ekman-inflow adjustment may recover additional zonal-wind skill without
changing the prognostic trajectory.

## Mechanism

Preserve the incumbent rollout, DFI, weak Held-Suarez forcing, theta tendency,
theta recentering, semi-implicit off-centering, pressure-level interpolation,
near-surface residual correction, and fixed forecast contract.

Add a side-by-side option such as
`use_ekman_inflow_10m_wind_diagnostic`. When it is enabled, keep the existing
`_surface_layer_richardson_10m_wind` speed scaling as the base diagnostic, then
rotate only the 10 m vector toward the local downhill surface-pressure-gradient
direction:

- compute the raw Richardson-scaled 10 m wind vector and its speed;
- compute a nodal unit vector proportional to `-grad(log_surface_pressure)` from
  the current trajectory state, with no-op fallback where the gradient is
  nonfinite or tiny;
- compute a bounded inflow fraction, for example `0.00..0.18`, increased by
  stable lower-column Richardson number and reduced near the equator where the
  geostrophic/Ekman interpretation is weakest;
- add only the cross-isobaric component needed to turn the wind toward lower
  pressure, then rescale the final vector back to within a tight speed envelope,
  such as `0.95..1.03` of the Richardson-speed diagnostic;
- leave `10m_v_component_of_wind` consistent if requested, but score impact is
  expected through the fixed `10m_u_component_of_wind` channel.

The pressure-gradient direction should come from the same Dinosaur trajectory
state already used for output diagnostics. It must not use future truth,
validation statistics, or any additional forecast trajectory.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model name extending the incumbent with an
    `_ekman_inflow_10m_wind` suffix.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` and the output variable
    contract remain unchanged.
- Tests to update:
  - Unit-test finite no-op behavior for calm winds, tiny pressure gradients,
    missing wind channels, and near-equatorial grid points.
  - Verify the option preserves Richardson speed within the chosen envelope
    while changing direction toward lower pressure.
  - Verify non-10 m output channels are bitwise unchanged before the existing
    near-surface residual correction.
  - Add registry and non-JIT smoke tests for the side-by-side factory.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` from days 2 through 15 if part of the remaining
    wind error is directional rather than speed-only.
  - Small primary-score gain without mass-field side effects because the change
    is output-only.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, and `geopotential_500` should be
    unchanged except for aggregate bookkeeping noise.
- Possible regressions:
  - Day-1 `10m_u_component_of_wind` can regress if the pressure-gradient
    direction is noisy after sigma projection or if the direction error has the
    opposite sign from the Ekman-inflow assumption.
  - Tropical winds may degrade if the Coriolis taper is too weak.

## Risks

- Numerical stability:
  - Very low. The diagnostic is output-only and cannot feed back into DFI,
    vorticity, divergence, temperature, or log surface pressure.
- Compute cost:
  - Negligible relative to the spectral rollout; it adds one pressure-gradient
    diagnostic and vector rotation per saved lead.
- Data leakage:
  - Low. It uses only forecast-time trajectory fields and initial-state
    information already available under the fixed contract.
- Physical plausibility:
  - Moderate to high if tightly bounded. Surface-layer theory supports
    cross-isobaric flow, but the zero-orography sigma model has only an
    approximate surface-pressure-gradient diagnostic.
- Rollback complexity:
  - Low. Remove one flag/helper, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, no
    guardrail violations, and improvement or near-neutral movement in
    `10m_u_component_of_wind`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with clean
    diagnostics and no 10 m wind guardrail failure.
- Outcome that would falsify the hypothesis:
  - A clean near-zero delta would imply the accepted Richardson speed diagnostic
    has already captured the useful 10 m wind signal. Any day-1 or day-2 wind
    guardrail failure would imply the pressure-gradient rotation is too
    sensitive for the fixed protocol.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
    `_surface_layer_richardson_10m_wind`, which rescales the lowest sigma-layer
    wind speed but does not rotate direction.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/decision.md`
    accepted a bounded Richardson 10 m wind diagnostic with large 10 m wind
    gains and clean guardrails.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_08-58-52_coriolis-rotated-surface-wind-residual/decision.md`
    rejected a broader residual after a day-1 10 m wind guardrail failure,
    motivating a speed-preserving and tightly bounded output-only adjustment.
  - American Meteorological Society Glossary, "Monin-Obukhov similarity theory",
    describes the surface-layer framework for mean flow and turbulence scaling:
    https://glossary.ametsoc.org/wiki/monin-obukhov-similarity-theory/
  - ECMWF IFS Documentation Part IV, Physical Processes, documents 10 m wind and
    surface-layer exchange as diagnostic/parameterized boundary-layer quantities:
    https://www.ecmwf.int/sites/default/files/2023-06/Part-IV-Physical-Processes.pdf
  - Rasp, S. et al. 2024. WeatherBench 2: A benchmark for the next generation of
    data-driven global weather models. Journal of Advances in Modeling Earth
    Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This is not a duplicate of the staged `geostrophic-surface-wind-residual`.
That staged idea adds a bounded geostrophic residual to the 10 m wind. This
proposal preserves the accepted Richardson speed diagnostic and changes only
direction by adding a pressure-gradient inflow component, with a final speed
envelope to prevent the large day-1 wind failure seen in prior surface-wind
residual work.

It is also not another surface-layer extrapolation proposal. The rejected simple
surface-layer extrapolation changed near-surface magnitude and failed
guardrails; here the lowest-layer wind magnitude remains controlled by the
already accepted Richardson diagnostic.

## Evaluator Notes

### 2026-06-19T18:03:28Z

Decision: move to `ready`; ranked 1 of 3 fresh proposals and preferred over the
named staged alternatives for the next Orchestrator selection pool.

This is the strongest fresh candidate because it keeps the implementation
surface small and preserves the accepted trajectory. The recent Richardson
10 m wind diagnostic produced a very large accepted gain in exactly this output
family while leaving mass fields essentially unchanged, so a second bounded
wind diagnostic can plausibly produce threshold-scale movement if the remaining
wind error is directional rather than magnitude-only.

The proposal is safer than staged `geostrophic-surface-wind-residual` because
it starts from the accepted Richardson speed, changes vector direction only,
and explicitly rescales back into a tight speed envelope. That directly
addresses the rejected `surface-layer-diagnostic-extrapolation` and
`coriolis-rotated-surface-wind-residual` lessons: broad near-surface magnitude
changes and unconstrained output rotations can pass finite diagnostics while
failing early 10 m wind guardrails.

This is also a better next ready candidate than the staged T2m residual or
bulk-Richardson temperature ideas, which are single-channel output diagnostics
without the same recent accepted effect size; better than pressure-gradient
product dealiasing or diffusion variants, whose local history is clean but
weak or negative; and lower risk than prognostic boundary-layer drag, which can
perturb MSLP/Z500 balance.

Risks remain: it is still a scored-channel diagnostic, and pressure-gradient
direction can be noisy near the equator or at day 1. If selected, constants
for the inflow fraction, latitude taper, and speed envelope must be fixed
before scoring, and tests should prove non-10 m channels are unchanged while
the 10 m vector turns only under finite, non-tropical pressure-gradient
conditions.
