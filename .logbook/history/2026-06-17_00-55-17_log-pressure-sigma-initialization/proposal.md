---
schema_version: 1
slug: log-pressure-sigma-initialization
title: Use Log-Pressure Sigma Initialization
status: ready
created_at: 2026-06-17T00:43:25Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
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

# Use Log-Pressure Sigma Initialization

## Hypothesis

The incumbent initializes an equidistant sigma-coordinate primitive-equation
state from WeatherBench2 pressure-level analyses by interpolating temperature,
horizontal wind, and passive humidity linearly in pressure. Atmospheric
pressure-level profiles are often smoother in `log(p)` than in `p`, and
hydrostatic layer thickness depends on pressure ratios rather than pressure
differences. A log-pressure pressure-to-sigma remap may therefore reduce the
initial vertical-structure error that DFI has to filter, while leaving the
accepted equidistant sigma grid, forecast equations, DFI, near-surface residuals,
and weak wind-sparing Held-Suarez relaxation unchanged.

This is not a pressure-grid or reference-profile proposal. The candidate keeps
the same sigma layer centers, same 250 K semi-implicit reference temperature,
same output pressure interpolation, same finite output extrapolation, same
vertical advection, and same fixed evaluation contract. Only the coordinate used
to sample the input pressure-level analysis during initialization changes from
linear pressure to log pressure.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init` that preserves the incumbent
configuration with one additional initialization option.

During `weather_state_to_dinosaur_state`, build the usual target pressures
`sigma_center * surface_pressure` in hPa, but interpolate pressure-level fields
against `log(pressure_hpa)` instead of `pressure_hpa`:

- source coordinates are `log(pressure_coords.centers)`
- target coordinates are `log(max(sigma_center * surface_pressure_hpa, eps))`
- temperature, `u_component_of_wind`, `v_component_of_wind`, and passive
  `specific_humidity` use the same log-pressure remap
- surface pressure itself, vorticity/divergence conversion, DFI, weak
  Held-Suarez forcing, near-surface residual diagnostics, and output packing are
  unchanged

The implementation should keep the current bounded extrapolation behavior at the
top and bottom of the input pressure stack. If a helper is added to
`vertical_interpolation.py`, it should be deterministic, JAX-compatible, and
used only by the side-by-side candidate unless the Orchestrator later accepts it.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dinosaur_dfi_surface_residual_weak_hs_logp_init`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` remains unchanged.
- Tests to update:
  - Verify the candidate preserves DFI, near-surface residuals, weak thermal-only
    Held-Suarez relaxation, default T80 truncation, 900 s inner step, default
    diffusion, vertical advection, and the incumbent output path.
  - Add a focused helper test showing that log-pressure interpolation differs
    from linear-pressure interpolation on a curved pressure profile and matches
    it for profiles that are linear in `log(p)`.
  - Verify the default incumbent still uses the current linear-pressure
    initialization path.
  - Add a no-JIT finite smoke forecast test for the side-by-side candidate.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at early to medium leads if
    log-pressure remapping reduces hydrostatic thickness or pressure-gradient
    imbalance introduced by pressure-to-sigma initialization.
  - `2m_temperature` at medium leads if lower-tropospheric thermal structure is
    initialized with less vertical interpolation bias before the accepted
    near-surface residual decays.
  - Primary score may improve without spending the long-lead 10 m wind guardrail
    margin because no momentum drag, diffusion, or wind diagnostic correction is
    added.
- Expected neutral metrics:
  - Day-1 near-surface fields should remain close to the incumbent because DFI,
    the near-surface residual correction, weak Held-Suarez rates, and the
    forecast stepper are unchanged.
  - Runtime should be nearly identical to the incumbent.
- Possible regressions:
  - The current linear-pressure remap may be acting as useful vertical smoothing
    of pressure-level analysis noise; a log-pressure remap could sharpen upper
    tropospheric gradients and worsen Z500 or wind.
  - If the accepted DFI already removes the relevant initialization imbalance,
    the effect may be below the iteration promotion threshold.
  - Any change to initialized temperature and wind can alter baroclinic growth,
    so clean fast diagnostics are necessary but not sufficient.

## Risks

- Numerical stability:
  - Low to moderate. The candidate does not change the time step, equations,
    grid, vertical advection, forcing strength, or filters, but it does perturb
    the balanced initial state seen by the forward rollout.
- Compute cost:
  - Low. The candidate adds logarithms during pressure-to-sigma initialization
    only and assumes the reported `--workers 4` evaluation budget.
- Data leakage:
  - Low. The remap uses only the input analysis, surface pressure, and fixed
    pressure coordinates; it does not use truth fields, validation scores,
    learned climatologies, or split-specific constants.
- Physical plausibility:
  - Moderate to high. Log-pressure interpolation is a standard pressure-coordinate
    choice in atmospheric data assimilation and observation-operator contexts,
    and hydrostatic thickness depends on pressure ratios.
- Rollback complexity:
  - Low. The side-by-side option can be removed from one factory, one registry
    entry, and a small initialization branch.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init`.
  - Require finite forecasts and zero diagnostic issues. Inspect the fast artifact
    for any early Z500 or MSLP drift before spending an iteration run.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init --workers 4`.
  - Compare only against exact incumbent records for
    `dinosaur_dfi_surface_residual_weak_hs`.
  - Support for the hypothesis is primary-score delta at least `+0.002` with
    clean diagnostics and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean diagnostics
    and the same fixed guardrails.
- Outcome that would falsify the hypothesis:
  - Fast nonfinite behavior, an iteration primary delta below `+0.002`, an early
    `geopotential_500` or `mean_sea_level_pressure` guardrail failure, or a
    broad worsening of long-lead wind would show that log-pressure initialization
    is not useful for this incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  initializes Dinosaur sigma states from pressure-level WeatherState fields with
  `vertical_interpolation.interp_pressure_to_sigma`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  provides the current linear pressure-to-sigma interpolation helper and the
  bounded extrapolation behavior that this proposal should preserve.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  reconstructs hydrostatic geopotential on sigma levels and uses pressure-ratio
  terms in the primitive-equation vertical discretization.
- JCSDA JEDI UFO documentation, "Vertical Interpolation", describes pressure
  vertical interpolation defaults in `log(air pressure)` for `air_pressure` and
  `air_pressure_levels`.
  https://jcsda-jedi-docs.readthedocs-hosted.com/en/8.0.0/inside/jedi-components/ufo/obsops.html#vertical-interpolation
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEABAC%3E2.0.CO;2

## Researcher Notes

This proposal preserves all accepted evidence: finite pressure-level output
extrapolation, balanced digital-filter initialization, near-surface anomaly
diagnostics, and weak wind-sparing Held-Suarez relaxation. It does not duplicate
the staged `.logbook/research/staging/semi-lagrangian-vertical-transport.md`,
which changes forward vertical transport numerics; this proposal changes only
the initialization remap from pressure levels to the existing sigma grid.

The relevant negative evidence is pressure-related, so this should be triaged
skeptically. It is distinct from `pressure-aware-sigma-layer-grid` because it
does not change sigma interfaces, layer thicknesses, vertical finite
differences, output interpolation targets, or the DFI trajectory geometry. It is
distinct from `standard-atmosphere-reference-profile` because it keeps the
constant 250 K semi-implicit reference state and only changes how analyzed
fields are sampled onto the incumbent grid. It is distinct from finite
pressure-level extrapolation because that accepted change affected sigma-to-
pressure output packing, while this candidate affects pressure-to-sigma
initialization.

The latest `calendar-aware-solar-relaxation` rejection is also negative evidence
against further thermal-equilibrium changes: it was finite and diagnostic-clean
but regressed primary score by `-0.040271379533892704` and failed 2 m
temperature guardrails. This proposal avoids that family entirely: no seasonal
thermal target, no Held-Suarez coefficient or geometry change, no new forcing,
and no validation-tuned constants.

Avoid implementing this as a general evaluation or forecast-contract change. If
the Evaluator promotes it, keep it side-by-side, use fixed log-pressure
initialization for all evaluation splits, and let the existing fast, iteration,
and validation protocols decide whether the small remap improvement is real.

## Evaluator Notes

2026-06-17T00:46:27Z - Move to `ready`; rank 1 of 2 for iteration 19.

This is the strongest current next experiment because it has the smallest
implementation and runtime surface among the live ideas while still targeting a
real physical/numerical mechanism. Local source inspection confirms that the
incumbent builds the sigma initial state by calling
`vertical_interpolation.interp_pressure_to_sigma` from
`weather_state_to_dinosaur_state`, so this can be isolated to the pressure-level
to sigma initialization remap plus a side-by-side factory and registry entry.
The current helper already accepts an interpolation function, and the bounded
extrapolation behavior can be preserved by applying the existing safe
interpolator to `log(pressure)` coordinates.

Scientific support is adequate but not decisive. The JCSDA JEDI UFO
documentation for `VertInterp` states that pressure-coordinate interpolation is
done in the logarithm of air pressure for `air_pressure` and
`air_pressure_levels`, which supports log-pressure remapping as a standard
observation/operator choice. Local Dinosaur source also uses pressure-ratio and
log-sigma terms in the sigma primitive-equation hydrostatic machinery. These
checks support plausibility, not a guaranteed score improvement, so the
candidate should remain side-by-side and be judged strictly by the fixed gates.

Negative evidence was weighed heavily. Pressure-aware sigma-layer grids were
clean but much worse on iteration primary score; the standard-atmosphere
reference profile and global pressure anchor had effects that were too small or
slightly negative; terrain-aware surface pressure improved aggregate score but
failed early Z500/MSLP guardrails; mass diagnostic residuals were safe but too
small. This proposal is distinct because it does not change the sigma grid,
surface pressure, output packing, semi-implicit reference temperature, or
forecast equations. It also preserves all accepted mechanisms: finite
pressure-level output extrapolation, balanced DFI, near-surface anomaly
diagnostics, and wind-sparing weak Held-Suarez relaxation. The recent
calendar-aware solar relaxation rejection is further evidence against thermal
forcing variants, but this proposal does not tune Held-Suarez forcing or add a
thermal-equilibrium target.

Implementation constraints: keep the candidate registered only as
`dinosaur_dfi_surface_residual_weak_hs_logp_init`; keep the incumbent default on
linear pressure initialization; apply the log-pressure remap to temperature,
horizontal winds, and passive humidity only during initialization; do not alter
sigma-to-pressure output interpolation or finite extrapolation; do not change
DFI, weak Held-Suarez coefficients, near-surface residuals, vertical advection,
time step, spectral truncation, or evaluation protocols. The fast artifact
should be inspected for early Z500/MSLP drift before spending an iteration run.
