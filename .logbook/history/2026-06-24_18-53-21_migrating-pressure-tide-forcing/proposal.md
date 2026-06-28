---
schema_version: 1
slug: migrating-pressure-tide-forcing
title: Add a Mass-Neutral Migrating Surface-Pressure Tide
status: ready
created_at: 2026-06-24T18:46:33Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/radiation.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a Mass-Neutral Migrating Surface-Pressure Tide

## Hypothesis

The fixed WeatherBench2 protocols score 6-hourly `mean_sea_level_pressure`, and
ERA5 analyses contain regular solar atmospheric tides in surface pressure. The
incumbent dry dycore includes weak thermal relaxation and surface residual
corrections, but it does not explicitly carry the migrating diurnal or
semidiurnal pressure tide. A small deterministic, globally mass-neutral
log-surface-pressure tide could reduce systematic MSLP phase error without
changing mass-DSE transport, hydrostatic initialization, ocean heat-flux
distribution, or output residual decay.

## Mechanism

Add one side-by-side model, for example `dino_hsl2_mass_dse_pressure_tide`.

Implement the tide as an incremental positive-time filter on `log_surface_pressure`:

- use forecast initialization time, model time, longitude, and latitude to build
  a fixed migrating solar-time pressure pattern;
- include only predeclared wave components, for example a semidiurnal westward
  wavenumber-2 component and a smaller diurnal westward wavenumber-1 component;
- use fixed literature-scale amplitudes, expressed in pascals and converted to
  nondimensional `delta log(surface_pressure)` with a surface-pressure guard;
- apply the increment as
  `tide_pattern(next_time) - tide_pattern(previous_time)` so lead zero is not
  changed and the forecast carries only tide phase evolution from the analysis
  initial state;
- subtract the area-weighted global mean from each pattern before applying it,
  keeping total surface mass unchanged to quadrature precision;
- use a smooth tropical-to-subtropical latitude envelope, because the largest
  solar pressure tides are tropical, with fixed zero taper into high latitudes;
- preserve vorticity, divergence, temperature, tracers, residual corrections,
  DFI, weak-HS forcing, ocean sensible heat flux, and HSL/DSE branches;
- exclude the tide filter from DFI and fall back to the incumbent state if the
  time conversion, pressure guard, or pattern is nonfinite.

This is a physical external pressure-tide tendency, not a learned MSLP bias
correction. It uses no verification fields and no split-specific amplitude
tuning.

## Implementation Scope

- Expected files:
  - `adapter.py` for the step filter, signed model-time plumbing, and candidate
    factory.
  - `radiation.py` only if a shared local-solar-time helper is needed.
  - `__init__.py`, `registry.py`, and focused tests.
- Registry changes:
  - Add one side-by-side candidate, `dino_hsl2_mass_dse_pressure_tide`.
- API changes:
  - None. The forecast contract, target variables, lead times, worker policy,
    and protocols remain fixed.
- Tests to update:
  - Verify lead-zero preservation by applying zero net increment from initial
    time to initial time.
  - Verify the tide pattern is area-mean zero and finite.
  - Verify semidiurnal phase advances with solar time and longitude.
  - Verify only `log_surface_pressure` is directly changed.
  - Verify disabled or nonfinite time conversion reproduces the incumbent.
  - Add registry and finite non-JIT smoke coverage.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure`, especially at all leads sampled on 6-hour UTC
    cycles, if a missing migrating tide contributes coherent pressure error.
  - Small aggregate primary-score improvement if MSLP gains do not disturb other
    fields.
- Expected neutral metrics:
  - `2m_temperature`, `geopotential_500`, and `10m_u_component_of_wind`, because
    the tendency is small, mass-neutral, and only applied to log-surface-pressure.
- Possible regressions:
  - Any direct pressure edit can perturb pressure gradients and feed back into
    wind and height evolution after several inner steps.
  - If ERA5 tidal phase is already implicitly present in the initialized
    pressure and the dycore preserves it well enough, adding phase evolution can
    double-count or dephase the tide.

## Risks

- Numerical stability:
  - Low to moderate. The applied pressure amplitude is small and capped, but the
    mass field is dynamically sensitive.
- Compute cost:
  - Low. The pattern is local grid algebra and a global area mean.
- Data leakage:
  - Low if amplitudes and phases are fixed from literature before evaluation and
    never selected from iteration or validation metrics.
- Physical plausibility:
  - Moderate. Solar atmospheric tides are real and visible in surface pressure,
    but this reduced pattern omits full vertical tidal heating and propagation.
- Rollback complexity:
  - Low. Remove one filter/flag, one helper if added, one factory/export, one
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_pressure_tide`
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_pressure_tide --workers 4`
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    guardrail failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_pressure_tide --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001`.
- Outcome that would falsify the hypothesis:
  - A neutral or negative iteration delta with clean diagnostics would show the
    missing pressure tide is not a material error source. Any MSLP or wind
    guardrail failure would show that direct pressure-tide insertion disrupts
    the accepted mass-wind balance.

## Citations

- Chapman, S. and Lindzen, R. S. 1970. Atmospheric Tides: Thermal and
  Gravitational. D. Reidel. MIT atmospheric-dynamics lecture notes cite this as
  the standard reference for atmospheric tides.
  https://ocw.mit.edu/courses/12-810-dynamics-of-the-atmosphere-spring-2008/resources/chapter_9/
- Dai, A. and Wang, J. 1999. Diurnal and semidiurnal tides in global surface
  pressure fields. Journal of the Atmospheric Sciences, 56, 3874-3891.
  https://doi.org/10.1175/1520-0469(1999)056%3C3874:DASTIG%3E2.0.CO;2
- Covey, C., Dai, A., Lindzen, R. S. and Marsh, D. R. 2011. The
  surface-pressure signature of atmospheric tides in modern reanalyses. Journal
  of the Atmospheric Sciences, 68, 495-514.
  https://doi.org/10.1175/2010JAS3560.1
- Forbes, J. M. and Garrett, H. B. 1978. Thermal excitation of atmospheric tides
  due to insolation absorption by O3 and H2O. Geophysical Research Letters, 5,
  1013-1016. https://doi.org/10.1029/GL005i012p01013

## Researcher Notes

This is not the staged `diurnal-surface-residual-memory`: it modifies the
prognostic mass field through a mass-neutral physical pressure-tide increment,
not a scored-output residual. It is not the staged `solar-weighted-thermal-
tendency` or rejected `calendar-aware-solar-relaxation`: it adds no heat source
and does not move the weak-HS equilibrium. It is also not a pressure-thickness
DSE correction, hydrostatic inversion, vertical DSE transport, DSE-consistent
initialization, deeper ocean heat-flux distribution, or global mass-DSE remap.

## Evaluator Notes

### 2026-06-24T18:51:46Z

Decision: move to `ready`; rank 1 of 3 new proposals; ready now: yes.

This is the strongest next experiment because it is the most novel relative to
the current research queue and has a clear, fixed physical target. The cited
atmospheric-tide literature supports coherent diurnal and semidiurnal
surface-pressure tides in analyses and reanalyses, and the proposal keeps the
mechanism deterministic, lead-zero preserving, and globally mass neutral rather
than learned from the fixed WeatherBench2 splits.

The local duplicate check is favorable. It is not the staged
`diurnal-surface-residual-memory`, which only changes corrected
`2m_temperature`; it is not the staged `solar-weighted-thermal-tendency`, which
adds thermal forcing; and it is not the rejected `calendar-aware-solar-relaxation`,
which moved the weak-HS thermal equilibrium. It does sit near the pressure/mass
family, where direct pressure-continuity and mass-DSE edits have often been
negative, so the implementation must stay small: one predeclared tide pattern,
one fixed amplitude set from literature, exact area-mean removal, no validation
tuning, DFI exclusion, finite fallback, and tests proving only
`log_surface_pressure` is directly changed.

Ready status is conditional only in the ordinary Evaluator sense: the
Orchestrator may select it for implementation now, but scoring must still use
the fixed gates and cached `dino_hsl2_mass_dse` incumbent artifacts unless
concretely invalid.
