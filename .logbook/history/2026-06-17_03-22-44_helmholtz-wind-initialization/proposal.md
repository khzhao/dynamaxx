---
schema_version: 1
slug: helmholtz-wind-initialization
title: Initialize Sigma Winds Through Helmholtz Wind Diagnostics
status: ready
created_at: 2026-06-17T03:07:20Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Initialize Sigma Winds Through Helmholtz Wind Diagnostics

## Hypothesis

The incumbent initializes sigma-level winds by first interpolating pressure-level
`u_component_of_wind` and `v_component_of_wind` to local sigma pressures, then
transforming the resulting vector wind into Dinosaur's spectral vorticity and
divergence prognostic variables. Because the interpolation weights vary
horizontally through surface pressure, vertical interpolation of vector
components does not commute with the horizontal Helmholtz transform. That can
inject small rotational/divergent imbalance before the accepted DFI filter.

Initializing vorticity and divergence as scalar diagnostics on pressure levels,
then remapping those scalar fields to sigma levels with the same accepted
log-pressure interpolation, should better match the prognostic variables
actually evolved by the spectral primitive-equation model. This targets wind
balance without changing thermal initialization, pressure initialization,
vertical coordinates, forcing, residual diagnostics, or output interpolation.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind`. During
`weather_state_to_dinosaur_state`, keep the incumbent log-pressure
initialization for temperature, humidity, and log surface pressure, but replace
the wind initialization path:

- compute pressure-level vorticity and divergence from the analyzed pressure-
  level `u` and `v` winds using the existing spherical-harmonic transform
- convert those pressure-level modal diagnostics back to nodal scalar stacks
- remap nodal vorticity and divergence stacks from pressure to sigma using the
  incumbent log-pressure pressure-to-sigma interpolation and local surface
  pressure
- transform the sigma-level scalar vorticity and divergence back to modal space
  and use them directly in the initial Dinosaur state
- preserve accepted DFI, near-surface residual diagnostics, weak Held-Suarez
  thermal relaxation, log-pressure temperature/humidity initialization, default
  T80 truncation, 900 s inner step, and finite pressure-level output packing

If the required pressure-level wind stack is absent, the adapter already cannot
construct a Dinosaur initial state, so no fallback or forecast-contract change is
needed.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind`.
- API changes:
  - None. Preserve deterministic `forecast(ForecastInput) -> WeatherState`.
- Tests to update:
  - Add a factory and registry test confirming the candidate preserves all
    incumbent flags and enables only Helmholtz wind initialization.
  - Add a synthetic solid-body or nondivergent-wind initialization test showing
    the candidate preserves a nearly nondivergent pressure-level wind field
    through sigma initialization.
  - Add a divergent synthetic wind test showing divergence is remapped through
    the new scalar path rather than silently zeroed.
  - Add a non-JIT finite smoke forecast test for the side-by-side candidate.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at early and medium leads if part of the remaining
    low-level wind error comes from component-wise vertical remapping of sheared
    winds.
  - `geopotential_500` and `mean_sea_level_pressure` may improve modestly if
    the initial divergent adjustment is cleaner before DFI.
  - Primary score may move even with small target RMSE changes, as observed for
    accepted log-pressure initialization.
- Expected neutral metrics:
  - `2m_temperature` should be mostly neutral because temperature, weak thermal
    relaxation, and near-surface residual correction are unchanged.
  - Pressure-level temperature and humidity diagnostics should remain close to
    the incumbent because only wind initialization changes.
- Possible regressions:
  - `10m_u_component_of_wind` can regress if component-wise wind interpolation is
    currently compensating another adapter bias.
  - Interpolating vorticity and divergence as scalar diagnostics can smooth or
    phase-shift vertically sheared jets differently than vector interpolation.
  - Polar derivative noise or transform roundoff could appear in the pressure-
    level vorticity/divergence stacks if tests do not cover latitude ordering
    and finite arithmetic carefully.

## Risks

- Numerical stability:
  - Low to moderate. This is initialization-only and keeps accepted DFI, but it
    changes the initial vorticity/divergence partition used by the dynamical
    core.
- Compute cost:
  - Low. It adds a small number of spectral transforms during initialization
    only; rollout length, resolution, output volume, and worker count are
    unchanged.
- Data leakage:
  - Low. The mechanism uses only same-time initial pressure-level winds already
    present in `ForecastInput.initial_state`.
- Physical plausibility:
  - Moderate to high. Spectral primitive-equation models commonly prognose
    vorticity and divergence, and initializing those fields directly is aligned
    with the model's control variables.
- Rollback complexity:
  - Low. The candidate can be removed by deleting one adapter option, one
    factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind --workers 4`.
  - Compare against exact incumbent records for
    `dinosaur_dfi_surface_residual_weak_hs_logp_init`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - Fast nonfinite behavior, early `10m_u_component_of_wind` guardrail failure,
    or a clean but sub-threshold iteration delta would show that Helmholtz wind
    initialization does not improve this incumbent.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
    interpolates pressure-level vector winds to sigma before converting to modal
    vorticity and divergence; it already exposes the accepted log-pressure
    initialization flag.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py`
    provides `uv_nodal_to_vor_div_modal` and `vor_div_to_uv_nodal`, making the
    proposed Helmholtz wind path locally implementable.
  - ECMWF IFS Documentation Part III describes spectral-transform hydrostatic
    primitive-equation dynamics and vorticity-divergence formulations used in
    operational atmospheric models.
    https://www.ecmwf.int/sites/default/files/elibrary/112024/81625-ifs-documentation-cy49r1-part-iii-dynamics-and-numerical-procedures.pdf
  - NOAA/GFDL spectral core notes formulate the primitive-equation spectral core
    with prognostic vorticity, divergence, temperature, and log surface pressure.
    https://www.gfdl.noaa.gov/wp-content/uploads/files/user_files/pjp/spectral_core.pdf
  - Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
    digital filter. Monthly Weather Review. The accepted incumbent already uses
    DFI; this proposal changes the wind control variables passed into that
    balance filter rather than replacing it.
    https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2

## Researcher Notes

This proposal is intentionally separate from the staged
`hydrostatic-thickness-initialization`, which changes temperature using analyzed
geopotential thickness. Here temperature and geopotential are untouched; only
the wind control-variable projection changes. It is also separate from staged
`semi-lagrangian-vertical-transport`, which changes the rollout transport
scheme rather than initialization.

Negative evidence is accounted for. The rejected divergence-damping candidate
changed ongoing forecast dissipation and was slightly negative; this proposal
does not damp divergence and acts only before DFI. The rejected vertical-
advection suppression and T120 candidates failed fast due to broad stability
changes; this candidate preserves vertical transport, resolution, filters, and
time step. The log-pressure output interpolation result warns that remapping
can move RMSE guardrails, so this proposal should be scrutinized for early wind
regressions before validation.

## Evaluator Notes

2026-06-17T03:11:14Z - Move to `ready`; rank 1 of 4 active ideas and recommended next implementation target.

This is the strongest next candidate because it is a narrow initialization-only
projection onto the variables the Dinosaur primitive-equation state actually
uses. Local source inspection confirms the current incumbent stacks
pressure-level `u_component_of_wind` and `v_component_of_wind`, applies the
pressure-to-sigma remap to those vector components, and only then calls
`spherical_harmonic.uv_nodal_to_vor_div_modal`. Local source also confirms the
accepted log-pressure initialization switch is already isolated in this path and
that `uv_nodal_to_vor_div_modal` / `vor_div_to_uv_nodal` are available, so the
implementation surface is mostly adapter plumbing plus focused tests.

Scientific support is adequate for ready. The cited GFDL spectral-core notes
and ECMWF IFS documentation support spectral-transform primitive-equation
formulations using vorticity/divergence control variables. That does not prove
this projection will improve WeatherBench2 skill, but it supports the mechanism
that initializing the prognostic scalar diagnostics directly can be a cleaner
state projection than vertically remapping vector components through
horizontally varying surface pressure and then taking horizontal derivatives.

Prior history favors trying this before broader rollout changes. Accepted DFI
and accepted log-pressure sigma initialization show that small initialization
balance/projection changes can clear both iteration and validation gates. The
rejected divergence-selective damping result is relevant but not a duplicate:
that candidate damped ongoing divergent motion and slightly degraded primary
score, while this proposal changes only the initial vorticity/divergence
partition before the accepted DFI filter. The most recent log-pressure output
interpolation rejection warns that remapping changes can produce hidden
variable+lead RMSE failures, so this candidate should be stopped before
validation if early or medium-lead `10m_u_component_of_wind`,
`geopotential_500`, or `mean_sea_level_pressure` guardrails fail.

Implementation constraints for the Orchestrator/Implementer: keep this
side-by-side only; preserve DFI, near-surface residuals, weak Held-Suarez,
log-pressure temperature/humidity initialization, T80, 900 s inner step, and
finite output packing; do not add fallbacks that change the forecast contract;
add nondivergent and divergent synthetic wind tests so the transform path is
not accidentally zeroing divergence or introducing latitude-order mistakes.
