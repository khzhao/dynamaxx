---
schema_version: 1
slug: hydrostatic-thickness-initialization
title: Initialize Temperature From Hydrostatic Geopotential Thickness
status: ready
created_at: 2026-06-17T02:00:00Z
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

# Initialize Temperature From Hydrostatic Geopotential Thickness

## Hypothesis

The incumbent initializes the sigma-coordinate primitive-equation state from
pressure-level temperature, wind, surface pressure, and passive humidity. It
does not use the full pressure-level geopotential stack that is present in the
WeatherBench2 initial state, even though the model later diagnoses geopotential
hydrostatically from temperature, humidity, and surface pressure. This can leave
the initialized thermal structure and the evaluated `geopotential_500` field
slightly inconsistent before DFI.

The newly accepted log-pressure initialization showed that bounded,
initialization-only vertical-coordinate changes can improve primary score while
preserving RMSE guardrails. A hydrostatic-thickness initialization projects the
input temperature onto the analyzed geopotential thickness relation before the
existing log-pressure pressure-to-sigma remap, which may reduce hydrostatic
imbalance without changing forecast equations or output contracts.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init`. When the
initial WeatherState contains a complete `geopotential_<level>` stack matching
the inferred temperature, wind, and humidity pressure levels:

- compute layer-mean virtual temperature estimates from adjacent pressure-level
  geopotential differences using the hypsometric relation in log pressure
- convert virtual temperature to dry temperature with passive specific humidity
  when a complete humidity stack is available; otherwise use the dry estimate
- use one-sided finite differences at the top and bottom levels and centered
  differences at interior levels, all in `log(p)`
- use this hydrostatic-consistent pressure-level temperature only for Dinosaur
  state initialization before the incumbent log-pressure pressure-to-sigma remap
- leave pressure-level winds, surface pressure, passive humidity tracers, DFI,
  weak Held-Suarez, near-surface residuals, time stepping, and output packing
  unchanged

If the required geopotential stack is absent or incomplete, the candidate should
fall back to incumbent temperature initialization rather than changing the
forecast contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init`.
- API changes:
  - None. Preserve deterministic `forecast(ForecastInput) -> WeatherState`.
- Tests to update:
  - Add a helper test showing that an isothermal synthetic atmosphere with
    geopotential linear in `log(p)` reconstructs the expected temperature.
  - Add a helper test confirming fallback to incumbent temperature when the
    geopotential stack is incomplete.
  - Verify the candidate factory preserves DFI, near-surface residuals, weak
    Held-Suarez, log-pressure initialization, default step size, default
    spectral wavenumbers, and incumbent output interpolation.
  - Add a non-JIT finite smoke forecast test for the candidate.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at early and medium leads if the initial hydrostatic
    relation between temperature and analyzed geopotential is currently a source
    of diagnostic mismatch.
  - `mean_sea_level_pressure` may improve modestly if DFI starts from a thermal
    profile more consistent with pressure-gradient and thickness terms.
  - Primary score may improve even when fixed RMSE guardrail changes are small,
    similar to the accepted log-pressure initialization result.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because winds and low-level
    momentum tendencies are not modified directly.
- Possible regressions:
  - `2m_temperature` can regress if the analyzed pressure-level temperature is
    more useful for near-surface forecast skill than the hydrostatic thickness
    reconstruction.
  - Noisy geopotential differences near the top or bottom pressure levels could
    introduce vertical thermal noise unless the implementation uses bounded,
    finite arithmetic and existing DFI.
  - If the fixed score benefits mostly from raw analyzed temperature rather than
    hydrostatic consistency, the iteration delta may be negative.

## Risks

- Numerical stability:
  - Moderate. This is initialization-only and keeps DFI, but it changes the
    thermal profile passed to the primitive equations.
- Compute cost:
  - Low. The calculation is a local vertical finite difference before existing
    interpolation and does not increase trajectory length or output size.
- Data leakage:
  - Low. The mechanism uses only same-time initial geopotential and humidity
    fields already included in `ForecastInput.initial_state`; it does not use
    future truth, validation statistics, or target-specific fitting.
- Physical plausibility:
  - Moderate to high. Hydrostatic primitive-equation models diagnose
    geopotential from temperature and pressure thickness; initializing the
    thermal field consistently with analyzed thickness is a direct balance
    projection.
- Rollback complexity:
  - Low to moderate. The candidate can be removed by deleting one initialization
    option, one factory, one registry entry, and associated tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init --workers 4`.
  - Compare against exact incumbent records for
    `dinosaur_dfi_surface_residual_weak_hs_logp_init`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - Fast nonfinite behavior, early `2m_temperature` guardrail failure, early
    `geopotential_500` or `mean_sea_level_pressure` guardrail failure, or a clean
    but negative iteration delta would show that hydrostatic-thickness
    initialization is not beneficial for this incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` initializes
  Dinosaur temperature from pressure-level `temperature_<level>` channels and
  currently ignores pressure-level `geopotential_<level>` during initialization.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  diagnoses geopotential hydrostatically on sigma levels from temperature,
  passive humidity, surface pressure, and sigma coordinates.
- ECMWF IFS documentation gives a discrete hydrostatic relation in which layer
  geopotential differences depend on dry gas constant, virtual temperature, and
  logarithms of pressure ratios.
  https://www.ecmwf.int/sites/default/files/elibrary/112024/81625-ifs-documentation-cy49r1-part-iii-dynamics-and-numerical-procedures.pdf
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://ui.adsabs.harvard.edu/abs/1981MWRv..109..758S
- NOAA/AOML hydrostatic and hypsometric notes derive the relationship between
  geopotential thickness, virtual temperature, and the logarithm of pressure.
  https://www.aoml.noaa.gov/ftp/hrd/annane/prelim_notes/hypsometric_equation.pdf

## Researcher Notes

This proposal explicitly uses the accepted log-pressure initialization as
positive evidence for narrow initialization projections, while accounting for
negative evidence from broader vertical-coordinate experiments. It does not
change the sigma grid, terrain/orography, surface-pressure prognosis, output
residuals, time step, spectral truncation, diffusion, divergence damping,
vertical-advection scheme, or Held-Suarez equilibrium geometry.

It is not a revival of the rejected moist virtual-temperature dynamics
candidate. That candidate enabled humidity in the dynamical tendencies and
failed the fast gate with nonfinite forecasts. This proposal keeps humidity
passive and uses it only to convert a same-time hydrostatic virtual-temperature
estimate into a dry temperature for initialization. It is also distinct from the
standard-atmosphere reference-profile rejection: that changed the semi-implicit
reference split but left the analyzed thermal profile unchanged, while this
changes the initialized physical temperature profile and leaves the
semi-implicit reference temperature alone.

The risk is that analyzed temperature may already be the better predictor for
the fixed near-surface and pressure-level metrics. The Evaluator should rank
this behind lower-risk output-only diagnostics if avoiding thermal-profile
perturbations is preferred.

## Evaluator Notes

2026-06-17T02:02:53Z - Move to `staging`; rank 2 of 3 active ideas for iteration 20.

This proposal is plausible and worth retaining, but it should not be the next
implementation target while the lower-risk log-pressure output remap is ready.
The mechanism is physically meaningful: local source confirms initialization
currently stacks pressure-level temperature, winds, optional passive humidity,
and surface pressure, then ignores the pressure-level geopotential stack. Local
source also confirms output geopotential is diagnosed hydrostatically from
sigma-level temperature, humidity, surface pressure, and sigma coordinates.
Using same-time initial geopotential thickness to construct a hydrostatically
consistent thermal profile is therefore a real balance-projection idea rather
than a duplicate of the accepted log-pressure interpolation.

Scientific support is adequate for staging. Hypsometric and hydrostatic
references support deriving layer-mean virtual temperature from geopotential
thickness divided by a logarithmic pressure ratio, and the Dinosaur code uses
log sigma ratios in its hydrostatic geopotential weights. This supports the
direction of the proposal, but it does not establish that replacing analyzed
temperature with a finite-difference thickness estimate will improve the fixed
WeatherBench2 targets.

The main reason to stage it is risk. Unlike the output-remap proposal, this
changes the initialized thermal state passed into DFI and the primitive
equations. That can affect `2m_temperature`, pressure-gradient balance, MSLP,
and winds, and it could introduce vertical noise at the top or bottom pressure
levels. Prior history warns that plausible mass/pressure/thermal balance ideas
can be either too weak or harmful: standard-atmosphere reference profile gained
only `+0.00023612927630622949`, mass diagnostic residuals gained only
`+0.00042505322207886387`, and terrain-aware surface pressure/orography failed
major Z500/MSLP guardrails despite a large primary-score gain. The accepted
log-pressure initialization is positive evidence for narrow initialization
changes, but this proposal has a larger behavioral surface.

Keep this staged as a follow-up if the ready output-remap candidate fails cleanly
or is exhausted. If promoted later, require a side-by-side model only, fallback
to incumbent temperature when the geopotential stack is incomplete, bounded
finite arithmetic for layer differences, no validation tuning, and close
inspection of early `2m_temperature`, `geopotential_500`, and
`mean_sea_level_pressure` guardrails before any validation run.

2026-06-17T03:11:14Z - Keep in `staging`; rank 3 of 4 active ideas.

The new Helmholtz wind and layer-mean thermal-recentering proposals change this
idea's relative rank downward, not its scientific plausibility. This proposal
still has a clear hydrostatic mechanism and remains implementable, but it
replaces the analyzed pressure-level thermal profile with finite-difference
temperatures inferred from geopotential thickness before DFI. That is a larger
thermal initialization perturbation than the Helmholtz wind projection and a
less direct response to the current measured long-lead `2m_temperature` cold
bias than the thermal zero-mode constraint.

The positive evidence from accepted log-pressure sigma initialization still
applies: narrow initialization projections can move primary score while keeping
RMSE guardrails clean. The caution also still applies: rejected standard
atmosphere, pressure-grid, terrain/orography, and diagnostic mass experiments
show that plausible hydrostatic or mass-field changes often fail by small
effect size or by early `geopotential_500` / `mean_sea_level_pressure`
guardrails. Keep this staged as the next initialization follow-up if the two
ready candidates fail cleanly or if new diagnostics specifically implicate
temperature-geopotential inconsistency at initialization.

2026-06-17T05:24:11Z - Move to `ready`; rank 1 of 2 active staged ideas after
the ready queue was exhausted.

The three most recent rejected candidates change the risk profile but leave this
as the best current implementable option. `log-pressure-output-interpolation`
shows that the accepted log-pressure initialization result should not be
generalized to output diagnostics; this proposal remains initialization-only and
does not alter output interpolation. `helmholtz-wind-initialization` is strong
negative evidence against wind control-variable projections because it damaged
mass and geopotential balance, but this proposal does not change wind
initialization directly. `layer-mean-thermal-recentering` is mixed evidence: it
improved iteration primary by `+0.010479318541482652` but failed the early
`10m_u_component_of_wind` RMSE guardrail by a narrow margin. That makes wind
guardrail inspection mandatory, but it also shows that thermal-state changes can
still move the fixed score materially.

This is promoted because it has the clearest remaining physical mechanism at
the lowest implementation surface: use same-time analyzed geopotential thickness
to initialize a temperature profile that is more consistent with the
hydrostatic geopotential diagnostic already used by the model, then keep DFI,
weak Held-Suarez, near-surface residuals, log-pressure sigma initialization,
forecast equations, and output packing unchanged. It is not a constant tune, it
uses no future data or validation statistics, and it should be easy to roll back
as a side-by-side registry entry.

Implementation constraints for the Orchestrator and Implementer are tightened in
light of the recent guardrail failures: preserve the current incumbent as the
comparison target, add only a side-by-side model, do not blend or tune the
hydrostatic projection strength, fall back exactly to incumbent temperature
initialization when the required geopotential stack is incomplete, and inspect
early `10m_u_component_of_wind`, `geopotential_500`, and
`mean_sea_level_pressure` RMSE before any validation run. A wind guardrail
failure like the thermal-recentering run should reject the candidate rather than
prompting within-run tuning.
