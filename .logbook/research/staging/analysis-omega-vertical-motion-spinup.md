---
schema_version: 1
slug: analysis-omega-vertical-motion-spinup
title: Use Analysis Omega for a Short Vertical-Motion Spinup
status: staging
created_at: 2026-06-18T10:17:15Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/channels.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Analysis Omega for a Short Vertical-Motion Spinup

## Hypothesis

The fixed WeatherBench2 state includes pressure-level `vertical_velocity_*`
channels, but the incumbent Dinosaur adapter ignores them. The primitive
equation instead diagnoses sigma vertical motion from the initialized
horizontal wind, divergence, and surface-pressure gradient. Recent history
shows that direct wind or divergence rewrites are risky or too weak:
`helmholtz-wind-initialization` regressed badly, and
`continuity-balanced-divergence-init` was clean but still lost primary score.

A narrower use of the analyzed pressure-coordinate vertical velocity can test
whether initial vertical-motion mismatch is still a spinup error source without
changing vorticity, divergence, surface pressure, Coriolis splitting, or the
forecast contract. If ERA5 omega contains useful balanced ascent and descent
information that the coarse sigma-state projection does not reproduce, a short
decaying tendency should improve lower-tropospheric temperature, Z500, and MSLP
during the first few days while leaving the accepted long-lead trajectory mostly
unchanged.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_omega_spinup`.
Preserve the incumbent initialization, DFI, weak-HS forcing, near-surface
diagnostic residuals, horizontal diffusion, 900 s inner step, output variables,
and symmetric exact-Coriolis split.

Add an opt-in, time-decaying omega spinup term:

- add `VERTICAL_VELOCITY_VARIABLE = "vertical_velocity"` support in channel
  utilities, only for reading pressure-level input channels, not for output;
- during `weather_state_to_dinosaur_state`, interpolate pressure-level
  `vertical_velocity` from the same initial analysis to sigma centers, using
  pressure-linear interpolation and finite nearest extrapolation;
- convert pressure velocity omega, in Pa s^-1, to an approximate sigma-dot
  field with `omega / surface_pressure`, then remove boundary-inconsistent
  column offsets so the effective correction is small near the top and bottom;
- store the fixed analyzed sigma-dot anomaly in a private tracer or in an
  equation wrapper that is not emitted as a WeatherState output;
- initialize `State.sim_time` to `0.0` for this candidate, or use an equivalent
  trajectory wrapper, so the decay factor is tied to forecast model time rather
  than lead-index post-processing;
- in a candidate equation wrapper, add only the decaying vertical-advection
  tendency induced by that sigma-dot anomaly to temperature variation and
  passive tracers for the first 12 to 24 forecast hours;
- do not alter vorticity, divergence, log surface pressure, Coriolis rotation,
  horizontal scalar advection, pressure-gradient terms, or DFI state merging;
- leave DFI on the incumbent equation for the first candidate, so the test is
  positive-time spinup forcing rather than another DFI consistency experiment.

This is not a new vertical-advection discretization and not a wind
initialization correction. It uses one observed analysis field as a short-lived
vertical-motion increment in thermodynamic and tracer transport only.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/channels.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, emitted variables, target variables, lead
    steps, and fixed protocols remain unchanged.
- Tests to update:
  - Unit-test pressure-level omega stacking and pressure-to-sigma interpolation
    with finite fallback when omega channels are absent.
  - Verify the candidate factory preserves all Strang incumbent flags except
    the omega-spinup option.
  - Verify the spinup wrapper leaves vorticity, divergence, log surface
    pressure, Coriolis rotation, and horizontal diffusion unchanged.
  - Verify the added tendency decays with model time and is zero when the
    analyzed omega anomaly is zero.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 1 to 5 if missing
    analyzed ascent/descent contributes to hydrostatic and mass spinup error.
  - `2m_temperature` after the accepted residual begins to decay, if vertical
    thermal transport in the lower column is initially too weak or phase shifted.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be less exposed than in rejected wind
    initialization experiments because horizontal winds and Coriolis treatment
    are unchanged.
  - Long leads should approach the incumbent trajectory as the omega increment
    decays.
- Possible regressions:
  - ERA5 pressure-level omega may be noisy on the coarse 1.5 degree pressure
    grid or inconsistent with the model's sigma continuity relation.
  - Temperature changes from vertical-motion nudging can perturb mass fields and
    indirectly affect wind phase.
  - The primary signal may be too small if DFI and the accepted hydrostatic
    initialization already remove most spinup error.

## Risks

- Numerical stability:
  - Moderate. The change adds a transient vertical-transport tendency, so the
    amplitude must be bounded and fast diagnostics must pass before iteration.
- Compute cost:
  - Low to moderate. It adds one input interpolation and a few per-step tendency
    operations, with no resolution, lead-count, or worker-count change.
- Data leakage:
  - Low if the term uses only same-time initial analysis channels already present
    in `ForecastInput.initial_state`. It must not inspect future truth, validation
    artifacts, or constants outside the current forecast state.
- Physical plausibility:
  - Moderate. Omega is the pressure-coordinate vertical velocity in the
    hydrostatic primitive equations, but imposing an analyzed omega tendency in
    a free forecast is an approximate spinup device rather than a fully balanced
    initialization.
- Rollback complexity:
  - Low. Remove one channel constant, one option/wrapper, one factory/export,
    one registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_omega_spinup`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_omega_spinup --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    diagnostics clean, no early day 1-5 RMSE guardrail failure, and no
    variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_omega_spinup --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that analyzed omega
    is not a material remaining spinup source. Any early 10 m wind, Z500, or
    MSLP guardrail failure would show the transient vertical-motion tendency
    disrupts the accepted balance more than it helps.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` initializes
  vorticity, divergence, temperature, pressure, and humidity but does not read
  the pressure-level `vertical_velocity_*` channels present in the fixed
  WeatherBench2 state.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  diagnoses `sigma_dot_full` from horizontal divergence and surface-pressure
  gradient and uses it in vertical tendencies.
- Local metadata check: `WeatherBench2Source().state_channel_names(...)` reports
  pressure-level `vertical_velocity_*` channels in the fixed ERA5 state.
- History: `.logbook/history/2026-06-17_22-19-32_continuity-balanced-divergence-init/decision.md`
  rejected a direct divergence-only continuity correction with iteration delta
  `-0.001312899911693144`; this proposal does not edit divergence.
- History: `.logbook/history/2026-06-18_00-44-09_vorticity-preserving-dfi-increment/decision.md`
  rejected a partial DFI wind-state merge, so this proposal avoids state merging
  and keeps DFI on the incumbent path.
- ECMWF IFS Documentation CY41R2, Part III: Dynamics and Numerical Procedures,
  documents omega as pressure-coordinate vertical velocity in the hydrostatic
  primitive equations and relates it to continuity and vertical motion.
  https://www.ecmwf.int/sites/default/files/elibrary/2016/79696-ifs-documentation-cy41r2-part-iii-dynamics-and-numerical-procedures_1.pdf
- Copernicus Climate Data Store, ERA5 hourly pressure-level data documentation,
  lists pressure-level reanalysis fields from ECMWF ERA5.
  https://cds.climate.copernicus.eu/datasets/reanalysis-era5-pressure-levels
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a
  Digital Filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of active staged `upwind-vertical-advection-rollout`.
That proposal changes the vertical advection discretization for all steps. This
proposal keeps the centered operator and adds a short-lived analyzed
vertical-motion increment.

It is also not a duplicate of rejected `continuity-balanced-divergence-init`,
`helmholtz-wind-initialization`, or `vorticity-preserving-dfi-increment`. Those
ideas modified initial wind control variables or DFI state components. This
candidate leaves vorticity and divergence untouched and tests only whether the
available analyzed omega field can reduce early thermodynamic spinup.

## Evaluator Notes

### 2026-06-18T10:25:42Z

Decision: move to `staging`, current staged rank 3 behind lower-surface
diagnostic/operator-splitting fallbacks.

The mechanism is scientifically plausible but not ready for the next run. ECMWF
IFS documentation supports omega as pressure-coordinate vertical velocity
(`dp/dt`), and the incumbent source has an internally diagnosed sigma vertical
motion while the adapter currently has no pressure-level `vertical_velocity`
input path. That makes the proposal a useful test of whether same-time
analyzed ascent/descent can reduce first-day thermodynamic spinup without
editing vorticity, divergence, surface pressure, Coriolis ordering, or output
channels.

Keep it staged because the implementation surface is materially larger than
the ready interpolation candidate: it adds a new input channel family,
pressure-to-sigma omega remapping, a private anomaly state or wrapper, a
time-decaying vertical-transport tendency, and careful DFI/time-origin handling.
Recent evidence also lowers priority. DFI operator consistency was clean but
subthreshold at `+0.0008926584240389612`, sigma-native hydrostatic
initialization was negative, and prior vertical-transport changes were risky.
The proposal has low future-data leakage risk if it uses only the initial
analysis, but its imposed positive-time forcing can disturb mass and wind
balance, so it should wait behind simpler ready and fallback candidates.

### 2026-06-18T11:49:28Z

Decision: keep in `staging`, staged fallback rank 2.

The pressure-initialization rejection does not directly affect this idea
because it uses same-time analyzed omega only as a short-lived vertical-motion
spinup signal. It remains more invasive than the hypsometric diagnostic and
requires new input-channel plumbing, pressure-to-sigma remapping, a private
anomaly state or wrapper, and careful decay timing. Keep it ahead of permanent
vertical-advection and broad momentum changes because it is transient,
diagnostic as a spinup test, and avoids direct vorticity/divergence rewrites.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 2.

The flux-form continuity rejection does not directly invalidate a transient
same-time omega spinup, but it reinforces caution around mass/vertical-motion
balance changes. Keep this behind the output-only hypsometric diagnostic and
ahead of diffusion-heating and anti-aliasing fallbacks because it uses a real
analysis field and decays away, while still avoiding direct wind,
surface-pressure, and divergence rewrites.

### 2026-06-18T17:21:29Z

Decision: keep in `staging`, ranked as the strongest fallback behind the new
ready Richardson wind diagnostic.

The ready directory was empty, so this was reconsidered for promotion. Keep it
staged because it remains a broader positive-time spinup forcing with new input
channel plumbing, pressure-to-sigma omega remapping, private anomaly state or
wrapper logic, and DFI/time-origin care. It is still a good fallback because it
uses same-time analysis information and decays away, but the new ready
candidate is lower blast radius and better aligned with the accepted
near-surface residual evidence.

### 2026-06-18T18:47:01Z

Decision: keep in `staging`, ranked as the strongest fallback behind the new
ready potential-temperature thermodynamic tendency.

This file was reconsidered because `ready` was empty after the Richardson wind
diagnostic was accepted. It remains a plausible fallback: same-time ERA5 omega
could expose an initial vertical-motion spinup error without directly changing
vorticity, divergence, surface pressure, or output channels. However, it is not
the best next implementation target. It has a larger surface area than the
ready theta-tendency candidate, including new input-channel plumbing,
pressure-to-sigma omega interpolation, private anomaly or wrapper state, and
careful decay timing through DFI and positive-time rollout. Its front matter
and candidate name also predate the accepted stability-aware residual and
Richardson 10 m wind incumbent, so it would need a careful rebase before
implementation. Keep it as the top staged fallback if the theta-tendency
experiment fails cleanly.
