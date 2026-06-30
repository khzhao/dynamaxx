---
schema_version: 1
slug: snow-albedo-shortwave-shield
title: Snow-Albedo Shortwave Thermal Shield
status: staging
created_at: 2026-06-30T13:38:54Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
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

# Snow-Albedo Shortwave Thermal Shield

## Hypothesis

The current `dino_ri2m_ekman_coupled` incumbent still has strongly negative
`2m_temperature` skill versus persistence across the fixed 1-15 day leads.
Recent T2m followups show that simple output blends, high-mode ocean residuals,
humidity-aware RI2m, and lower-tropospheric air-mass diagnostics are not enough.
The accepted model also has no explicit surface albedo process.

Snow cover is a high-albedo lower boundary that strongly reduces daytime
shortwave absorption and changes near-surface thermal evolution. A weak,
daytime-only, snow-gated shortwave cooling tendency in the lowest sigma layers
tests a different land-surface mechanism from the rejected snow/soil thermal
reservoir: it does not relax air toward a soil or snow temperature reservoir,
and it does not alter residual-memory decay. It instead uses snow depth or snow
cover as an albedo shield on incoming solar energy.

## Mechanism

Register one side-by-side candidate such as `dino_ri2m_snow_sw`, derived from
`ekman_coupled_dinosaur_dycore_model()`.

For the candidate only:

- keep the incumbent DFI, HSL, mass-DSE, WTG, vertical-DSE ramp, ocean sensible
  heat flux, land/ocean low-mode T2m memory, RI2m 2 m temperature diagnostic,
  coupled Ekman closure, MSLP path, and wind diagnostics unchanged;
- use `ForecastInput.initial_times`, lead/model time, longitude, and latitude
  with existing radiation utilities to diagnose local positive daytime
  shortwave availability;
- read lead-zero `snow_depth` and, if available, `snow_cover` or an equivalent
  single-level snow field from the initial state; use exact incumbent fallback
  when snow fields are absent, nonfinite, negative, or grid-incompatible;
- form a bounded snow-albedo shield weight that is zero over snow-free points,
  increases smoothly with snow depth or snow fraction, and saturates for
  sufficiently snow-covered grid cells;
- apply a negative temperature tendency only in the lowest one or two sigma
  layers, only under positive local solar illumination, and only where the
  snow shield is active;
- subtract the area-weighted layer mean of the tendency before application so
  the candidate tests snow-covered spatial contrast rather than a global
  cooling retune;
- cap the local cooling per inner step and per forecast day, keep DFI on the
  incumbent equation, and finite-fallback to the incumbent state if the
  corrected lower-layer temperature is invalid;
- leave vorticity, divergence, `log_surface_pressure`, tracers, `sim_time`,
  target variables, lead days, metrics, and worker budget unchanged.

The first implementation should use one fixed albedo-shield amplitude and one
fixed snow-depth saturation scale chosen before scoring. It should not tune
constants against iteration output.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/radiation.py` only if a small reusable
    daylight helper is needed
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key such as `dino_ri2m_snow_sw`.
- API changes:
  - None. Forecast inputs, output variables, target variables, lead days, and
    fixed evaluation protocols remain unchanged.
- Tests to update:
  - Verify nighttime, zero solar angle, and snow-free cases reproduce the
    incumbent exactly.
  - Verify missing, negative, nonfinite, or misaligned snow fields reproduce
    the incumbent exactly.
  - Verify the snow shield is bounded, monotone with snow amount, and saturated
    above the declared snow-depth scale.
  - Verify the added tendency is lower-layer confined, nonpositive before
    layer-mean removal, area-mean neutral after layer-mean removal, and capped.
  - Verify DFI uses the incumbent equation and only positive-time rollout uses
    the snow shortwave tendency.
  - Verify candidate factory parity with `dino_ri2m_ekman_coupled` except for
    the new snow-shortwave selector and model name.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2-15 in snow-covered land and marginal snow
    regimes if missing snow-albedo shielding contributes to warm daytime
    lower-boundary errors after residual memory decays.
  - Small secondary `geopotential_500` or `mean_sea_level_pressure` gains are
    possible if lower-column thermal contrast improves synoptic thickness.
- Expected neutral metrics:
  - Snow-free tropical and ocean regions should be near incumbent.
  - `10m_u_component_of_wind` should remain close because momentum and final
    wind diagnostics are unchanged directly.
- Possible regressions:
  - If the incumbent is cold-biased over snow or the accepted T2m residual
    already compensates snow-albedo errors, extra daytime cooling can worsen
    T2m.
  - Area-mean neutrality can create compensating weak warming outside snow
    regions, potentially affecting pressure or height fields.
  - The global score may be insensitive if snow-covered daytime cases occupy
    too little of the fixed evaluation sample.

## Risks

- Numerical stability:
  - Low to moderate. The tendency is capped and lower-layer only, but it changes
    prognostic temperature during positive-time rollout.
- Compute cost:
  - Low. It adds solar-angle algebra, snow-field validation, and local
    elementwise tendency arithmetic.
- Data leakage:
  - Low. It uses only lead-zero snow fields, forecast time, grid geometry, and
    fixed constants. It must not use future snow, validation errors, or golden
    results.
- Physical plausibility:
  - Moderate to high. Snow albedo is a first-order land-surface radiative
    control, but this is a reduced atmospheric tendency rather than a full snow
    energy-balance or land-surface model.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry key, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_snow_sw`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_snow_sw --workers 4`.
  - Compare against cached `dino_ri2m_ekman_coupled` incumbent artifacts when
    valid. Support requires primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_snow_sw --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean diagnostics
    and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show snow-albedo
    shortwave shielding is not a material remaining fixed-score source. A T2m,
    MSLP, or Z500 guardrail failure would show the thermal contrast source is
    too intrusive for the accepted balance.

## Citations

- Local metric evidence:
  `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` and
  `outputs/eval/validation_dino_ri2m_ekman_coupled.json` show
  `2m_temperature` remains negative versus persistence at all fixed leads,
  while MSLP and U10 are much stronger after the accepted Ekman closure.
- Local negative evidence:
  `.logbook/history/2026-06-22_10-08-39_snow-soil-land-thermal-reservoir/decision.md`
  rejected a snow/soil thermal-reservoir tendency as effectively neutral; this
  proposal tests daytime radiative albedo shielding instead of reservoir
  relaxation.
- Local negative evidence:
  `.logbook/history/2026-06-29_17-06-47_ocean-highmode-t2m-memory/decision.md`,
  `.logbook/history/2026-06-29_00-43-59_virtual-richardson-2m-temperature/decision.md`,
  and `.logbook/history/2026-06-28_02-44-14_lower-tropospheric-airmass-t2m-diagnostic/decision.md`
  discourage nearby output-only T2m diagnostic variants.
- Local source:
  `src/dynamaxx/dycore/models/dinosaur/radiation.py` provides solar-geometry
  utilities, and `src/dynamaxx/dycore/models/dinosaur/xarray_utils.py` lists
  snow-related WeatherBench2 single-level channels used by prior local
  proposals.
- Dutra, E., Balsamo, G., Viterbo, P., Miranda, P. M. A., Beljaars, A.,
  Schar, C., and Elder, K. 2010. "An Improved Snow Scheme for the ECMWF Land
  Surface Model: Description and Offline Validation." Journal of
  Hydrometeorology. https://doi.org/10.1175/2010JHM1249.1
- Noilhan, J. and Planton, S. 1989. "A Simple Parameterization of Land Surface
  Processes for Meteorological Models." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1989)117%3C0536:ASPOLS%3E2.0.CO;2
- Viterbo, P. and Beljaars, A. C. M. 1995. "An Improved Land Surface
  Parameterization Scheme in the ECMWF Model and Its Validation." Journal of
  Climate. https://doi.org/10.1175/1520-0442(1995)008%3C2716:AILSPS%3E2.0.CO;2

## Researcher Notes

This proposal is decorrelated from the recent Ekman followups and from the
post-DFI thickness recenter. It is also not a duplicate of the rejected
snow/soil reservoir, because it does not use deep soil temperature, does not
relax toward a stored reservoir, and does not change snow insulation of a heat
storage process. It is distinct from staged generic solar and cloud-shortwave
ideas because the mask is snow-albedo-specific, daytime-only, and active only
where lead-zero snow fields support a high-albedo surface.

## Evaluator Notes

### 2026-06-30T13:43:15Z

Decision: move to `staging`; ranked 2 of 2 new proposals.

The physical mechanism is plausible and the proposal is not an exact duplicate
of the rejected `snow-soil-land-thermal-reservoir`: this tests a daytime,
snow-gated shortwave cooling contrast rather than relaxation toward a soil or
snow heat reservoir. It is also more specific than staged
`solar-weighted-thermal-tendency` and staged
`daytime-low-cloud-shortwave-shield` because the activation mask is tied to
lead-zero snow fields rather than generic insolation or a diagnosed low-cloud
proxy.

Keep it staged rather than ready because the fixed global primary score has
repeatedly been hard to improve with narrow lower-boundary thermal and T2m
followups. The snow/soil reservoir was clean but effectively neutral, ocean
high-mode T2m memory regressed, humidity-aware RI2m was neutral to slightly
negative, and the lower-tropospheric airmass T2m diagnostic regressed
substantially. This proposal may improve a physically important subset, but
snow-covered daytime land points may occupy too little of the fixed
WeatherBench2 sample to clear the expensive iteration threshold, and any
area-mean-neutral compensating warming could perturb MSLP or Z500.

If promoted later, implement exactly one fixed-amplitude side-by-side candidate
derived from `dino_ri2m_ekman_coupled`; keep DFI, residual memory, RI2m,
Ekman, target variables, leads, and metrics unchanged; require exact no-op
behavior for nighttime, snow-free, missing, nonfinite, negative, or
shape-incompatible snow fields; and prove lower-layer confinement, bounded
cooling, and layerwise area-mean neutrality in focused tests. Do not tune the
snow-depth saturation scale or cooling amplitude against iteration output.
