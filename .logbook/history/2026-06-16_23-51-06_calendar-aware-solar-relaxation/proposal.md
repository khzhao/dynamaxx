---
schema_version: 1
slug: calendar-aware-solar-relaxation
title: Add Calendar-Aware Solar Thermal Relaxation
status: ready
created_at: 2026-06-16T23:36:45Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/models/dinosaur/test_dependency.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add Calendar-Aware Solar Thermal Relaxation

## Hypothesis

The accepted incumbent preserves DFI, near-surface diagnostic residuals, and a
weak wind-sparing Held-Suarez thermal relaxation. That relaxation was the
largest accepted model-selection gain so far, but its equilibrium temperature is
fixed in season and symmetric about the equator. The fixed iteration and
validation protocols evaluate daily initializations across complete seasonal
cycles, so a weak thermal target that follows the calendar solar declination may
reduce seasonally locked temperature, thickness, and mass-field drift without
adding drag, changing target variables, or tuning relaxation coefficients.

This proposal is not a Held-Suarez coefficient variant. The accepted weak
relaxation rates, no-drag choice, DFI, near-surface residuals, T80 truncation,
900 s inner step, vertical advection, and horizontal diffusion remain fixed.
Only the spatial pattern of the weak thermal equilibrium becomes forecast-time
aware.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_seasonal` that preserves the incumbent
configuration and replaces the weak thermal-only forcing class with a
calendar-aware thermal-only forcing.

The implementation should:

- initialize `primitive_equations.State.sim_time` for this candidate from each
  `ForecastInput.initial_times[initial_index]`, using the existing
  `radiation.datetime_to_time` or `SolarRadiation` calendar helper with a fixed
  WeatherBench reference datetime;
- keep the DFI initializer on the accepted incumbent equation and apply the
  seasonal thermal pattern only in the scored positive-time forecast rollout, so
  date-dependent radiation is not time-reversed through the DFI filter;
- compute solar declination from the existing `radiation` module during forcing
  evaluation;
- use the existing Held-Suarez equilibrium amplitudes and the accepted weak
  thermal relaxation rates, but shift the warm-equilibrium latitude with solar
  declination rather than keeping the equilibrium symmetric about the equator;
- keep the forcing tracer-safe and wind-sparing: zero vorticity, divergence,
  log-surface-pressure, and passive-tracer tendencies; temperature tendency is
  the only added tendency.

One concrete formula is to reuse the current Held-Suarez pressure and vertical
terms while replacing the meridional `sin(latitude) ** 2` equilibrium factor
with a bounded seasonal factor centered on the solar declination, for example
`(sin(latitude) - sin(declination)) ** 2` with the same existing amplitude and
minimum-temperature bound. The Evaluator may require this exact formula before
promotion to avoid implementation-time tuning.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dinosaur_dfi_surface_residual_weak_hs_seasonal`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` remains unchanged.
- Tests to update:
  - Verify the seasonal candidate preserves DFI, near-surface residuals, weak
    thermal relaxation rates, no Rayleigh drag, default step size, default
    spectral truncation, and vertical advection.
  - Verify `sim_time` is initialized from `ForecastInput.initial_times` only for
    the seasonal forcing path.
  - Verify June and December initial times produce different equilibrium
    hemispheric thermal patterns while the incumbent factory remains unchanged.
  - Verify DFI is not passed the seasonal forcing equation.
  - Add a no-JIT finite smoke forecast test for the side-by-side candidate.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and long leads if part of the incumbent thermal
    drift is seasonally structured rather than purely zonal-mean.
  - `geopotential_500` and `mean_sea_level_pressure` through improved
    hydrostatic thickness and mass-field evolution under seasonally displaced
    weak heating/cooling.
  - Primary score may improve across both iteration and validation because both
    splits cover full annual cycles with cycled 00/06/12/18 UTC starts.
- Expected neutral metrics:
  - Early day-1 fields should stay close to the incumbent because the accepted
    DFI, residual diagnostics, step size, grid, diffusion, and relaxation rates
    are unchanged.
  - `10m_u_component_of_wind` should be less affected than in drag or damping
    proposals because the forcing remains wind-sparing.
- Possible regressions:
  - Seasonally shifting the thermal equilibrium can perturb baroclinic growth
    and pressure gradients, producing mass-field or long-lead wind regressions.
  - Without clouds, land surface, ocean coupling, or longwave radiation, a
    solar-shaped relaxation remains idealized and may add the wrong regional
    anomaly.
  - If the accepted weak Held-Suarez gain was primarily from global thermal
    drift rather than seasonal phase, the iteration effect may be sub-threshold.

## Risks

- Numerical stability:
  - Low to moderate. The candidate keeps the accepted weak relaxation rates and
    adds no momentum drag, but it changes a forecast-time thermal tendency and
    therefore must pass the fixed fast diagnostic gate before iteration.
- Compute cost:
  - Low. The added work is a calendar calculation and one nodal equilibrium
    field per tendency evaluation. The proposal assumes the reported `--workers
    4` resource budget.
- Data leakage:
  - Low. The mechanism uses only forecast initialization time and deterministic
    orbital geometry. It must not use validation scores, truth fields, learned
    climatologies, or split-specific constants.
- Physical plausibility:
  - Moderate. Solar declination is a real driver of seasonal thermal structure,
    and radiative heating is a standard physical process, but this remains a
    deliberately simple dry-dycore surrogate rather than a full radiation
    scheme.
- Rollback complexity:
  - Low. The candidate can be isolated in one forcing class, one adapter option,
    and one side-by-side registry entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_seasonal`.
  - Require finite forecasts, zero diagnostic issues, and no obvious seasonal
    branch failure across the fixed January-through-December fast starts.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_seasonal --workers 4`.
  - Compare only against exact incumbent artifacts for
    `dinosaur_dfi_surface_residual_weak_hs`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_seasonal --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean diagnostics
    and the same fixed guardrails.
- Outcome that would falsify the hypothesis:
  - Fast nonfinite behavior, an iteration primary delta below `+0.002`, an
    early mass-field RMSE guardrail failure, or a long-lead 10 m wind guardrail
    failure would show that seasonal solar relaxation is not a useful follow-up
    to the accepted weak thermal relaxation.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  composes the accepted weak thermal Held-Suarez forcing and contains the
  incumbent DFI and near-surface residual paths.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
  implements the thermal equilibrium formula and Rayleigh-drag terms; the
  accepted incumbent uses the thermal path with `kf=0.0`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/radiation.py` already
  implements orbital time, solar declination, solar hour angle, and top-of-
  atmosphere radiation helpers.
- Dynamaxx source: `src/dynamaxx/eval/protocols.py` fixes daily lead days 1..15,
  full-year iteration years 2014-2018, and held-out validation year 2019.
- Held, I. M. and Suarez, M. J. 1994. A Proposal for the Intercomparison of the
  Dynamical Cores of Atmospheric General Circulation Models. Bulletin of the
  American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Berger, A. L. 1978. Long-Term Variations of Daily Insolation and Quaternary
  Climatic Changes. Journal of the Atmospheric Sciences.
  https://doi.org/10.1175/1520-0469(1978)035%3C2362:LTVODI%3E2.0.CO;2
- ECMWF IFS Documentation CY48R1, Part IV Physical Processes, Chapter 2
  describes radiation as a core physical parametrization and radiative heating
  as a flux-divergence tendency.
  https://www.ecmwf.int/en/elibrary/81370-ifs-documentation-cy48r1-part-iv-physical-processes
- NOAA NCEI Total Solar Irradiance Climate Data Record describes total solar
  irradiance as the spectrally integrated energy input at the top of Earth's
  atmosphere.
  https://www.ncei.noaa.gov/products/climate-data-records/total-solar-irradiance

## Researcher Notes

This proposal explicitly accounts for the accepted and rejected evidence. It
preserves accepted finite pressure-level extrapolation, balanced DFI, near-
surface residual diagnostics, and weak wind-sparing Held-Suarez relaxation. It
does not duplicate the staged
`.logbook/research/staging/semi-lagrangian-vertical-transport.md`, which changes
vertical transport numerics rather than thermal forcing.

It also avoids nearby repeats of rejected mechanisms: no moist virtual-
temperature dynamics, no humidity diagnostic floor, no pressure grid or
reference-temperature profile change, no terrain/orography or MSLP reduction,
no output residual tuning, no global pressure anchor, no time-step sweep, no
divergence or hyperdiffusion damping, no vertical-advection removal, no T120
resolution change, and no dry-DFI bookkeeping split. The latest
`dry-dfi-weak-hs-split` rejection is especially relevant: splitting forcing out
of DFI alone was stable but far below threshold, so this proposal must be judged
only as a new forecast-time thermal-equilibrium mechanism, not as another DFI
branch cleanup.

The main concern is that this is still an idealized thermal forcing candidate
after an already accepted Held-Suarez improvement. The Evaluator should scrap it
if any Held-Suarez-family forecast-forcing change is considered too close to
the accepted mechanism, or stage it behind the existing semi-Lagrangian vertical
transport proposal if vertical transport is the preferred next high-risk
numerics axis.

## Evaluator Notes

2026-06-16T23:39:41Z - Move to `ready`; rank 1 of 2 for iteration 18.

This is the best next implementation candidate because it is a low-cost,
side-by-side extension of the accepted incumbent rather than a new numerics
axis. The accepted weak wind-sparing Held-Suarez candidate produced large clean
primary deltas (`+0.06357275459004397` iteration and
`+0.062227260743318746` validation), so the remaining thermal-equilibrium shape
is a credible follow-up surface. The new `dry-dfi-weak-hs-split` result does
not reject this mechanism: that experiment only proved that DFI bookkeeping
around weak-HS forcing is nearly indistinguishable from the incumbent
(`+0.0000017470501787464343` iteration delta), while this proposal changes the
positive-time thermal target seen by the scored forecast.

Feasibility is good but not zero-surface. Local source inspection confirms that
`adapter.py` already composes the incumbent weak thermal-only Held-Suarez
forcing, `held_suarez.py` contains the current symmetric
`sin(latitude) ** 2` equilibrium, `radiation.py` provides
`datetime_to_time`, `SolarRadiation`, and solar-declination helpers, and
`eval/protocols.py` fixes full-year iteration and validation initializations
with January-through-December fast starts. The current adapter builds one
trajectory function before the per-initial-time loop and does not set
`primitive_equations.State.sim_time` from `ForecastInput.initial_times`, so the
implementation must explicitly thread each initialization datetime into the
positive-time rollout state without changing the public forecast API.

Implementation constraints for promotion: keep this side-by-side as
`dinosaur_dfi_surface_residual_weak_hs_seasonal`; preserve finite
pressure-level extrapolation, DFI, near-surface residual diagnostics, T80,
900 s inner steps, default diffusion, vertical advection, and the accepted weak
relaxation rates; keep `kf=0.0` and all non-temperature forcing tendencies zero;
use the fixed seasonal formula described in the proposal rather than tuning a
new amplitude or coefficient; do not pass the seasonal forcing through the
time-reversed DFI initializer; and do not use validation scores, truth fields,
learned climatologies, or split-specific constants.

Negative evidence is accounted for. This does not duplicate rejected moist
virtual-temperature dynamics, passive humidity floors, reference-profile or
pressure-grid changes, terrain/orography changes, mass residuals, pressure
anchors, time-step sweeps, divergence or hyperdiffusion damping, vertical
advection removal, T120 truncation, or dry-DFI bookkeeping splits. The main
risks are that the accepted weak-HS gain may already be mostly global drift
correction, that an idealized seasonal thermal target can perturb long-lead
winds where the incumbent has limited guardrail margin, and that a small
formula change may still fail the `+0.002` iteration threshold.

Literature and source checks support the mechanism enough for one fixed-gate
experiment. NASA describes the seasonal distribution of direct sunlight as a
consequence of Earth's axial tilt, NOAA NCEI defines total solar irradiance as
top-of-atmosphere energy input, ECMWF IFS documentation treats radiation as a
core physical process, and CESM documentation describes Held-Suarez as
temperature relaxation toward a zonally symmetric equilibrium plus lower-boundary
drag following Held and Suarez (1994). These sources justify a calendar-aware
thermal-relaxation surrogate, but they do not guarantee WeatherBench2 score
movement; the fixed fast and iteration gates remain decisive.
