---
schema_version: 1
slug: midpoint-semilagrangian-theta-departure
title: Use a Midpoint Departure Estimate for Horizontal Semi-Lagrangian Theta
status: ready
created_at: 2026-06-22T14:33:04Z
author_role: Researcher
target_model: dino_hsl_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Use a Midpoint Departure Estimate for Horizontal Semi-Lagrangian Theta

## Hypothesis

The current incumbent `dino_hsl_theta` won strongly by replacing the Eulerian
horizontal dry-theta anomaly tendency with a bounded one-step backward
semi-Lagrangian remap. Its departure point is still a first-order estimate from
arrival-grid winds at the current step. That can leave trajectory phase error in
curved or sheared flow, especially near jets and high latitudes, even though the
semi-Lagrangian transport mechanism itself is now proven useful in this codebase.

A midpoint departure estimate should preserve the accepted horizontal-theta
transport mechanism while reducing trajectory error. The expected benefit is a
cleaner thermal phase for baroclinic structures, which can improve
`geopotential_500`, `mean_sea_level_pressure`, and decaying `2m_temperature`
skill without changing the fixed evaluation protocol or adding a new physical
forcing.

## Mechanism

Add one side-by-side candidate with short alias `dino_hsl2_theta`.

For the candidate only:

- keep the accepted theta anomaly variable, bilinear scalar remap, finite
  fallback, CFL cap, vertical theta transport, pressure-work term,
  layer-mean theta recentering, weak-HS forcing, ocean bulk sensible heat flux,
  residual diagnostics, DFI, and all output packing unchanged;
- compute the incumbent first half-step backward displacement from the
  arrival-grid horizontal wind;
- remap the nodal horizontal wind components to the half-step location with the
  existing bounded horizontal remap machinery;
- compute the full backward departure from that midpoint wind, with the same
  displacement and finiteness caps as the incumbent;
- use the resulting departure point only for the horizontal dry-theta anomaly
  remap;
- fall back exactly to the accepted `dino_hsl_theta` first-order departure path
  if midpoint wind interpolation, displacement, or converted tendency is
  nonfinite or shape-incompatible.

This is a trajectory-accuracy experiment for the accepted theta transport path.
It is not a new scalar variable, vertical advection change, pressure-continuity
change, diffusion-strength change, or lower-boundary thermal reservoir.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model registered as `dino_hsl2_theta`.
- API changes:
  - None. `DycoreModel.forecast`, emitted variables, lead times, metrics, and
    protocols remain fixed.
- Tests to update:
  - Verify zero wind and spatially uniform wind reproduce the accepted
    `dino_hsl_theta` departure to tolerance.
  - Verify midpoint departure remains bounded and finite on equatorial and
    polar rows.
  - Verify only the theta horizontal semi-Lagrangian selector changes candidate
    behavior; non-theta tendencies and output residual branches preserve
    incumbent flags.
  - Verify nonfinite midpoint diagnostics fall back to the first-order
    `dino_hsl_theta` transport.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and late leads if
    remaining thermal phase error comes from first-order theta departure
    geometry.
  - `2m_temperature` after the accepted residual memory decays, if lower-column
    theta transport still has phase/Courant error.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because momentum,
    Coriolis splitting, Richardson 10 m wind diagnosis, and residual correction
    are unchanged.
- Possible regressions:
  - Midpoint interpolation can add numerical smoothing or alter the empirical
    balance that made the first-order `dino_hsl_theta` candidate strong.
  - If the current first-order cap is acting as useful diffusion, a more accurate
    trajectory could increase small-scale thermal variance and hurt early
    Z500/MSLP guardrails.

## Risks

- Numerical stability:
  - Moderate. The change touches the accepted thermodynamic transport each inner
    step, but it is bounded and has an exact incumbent fallback.
- Compute cost:
  - Moderate. It adds remaps for horizontal wind components per theta transport
    step; no extra leads, workers, grid size, or evaluation passes are needed.
- Data leakage:
  - None. It uses only current forecast state and fixed grid geometry.
- Physical plausibility:
  - High. Semi-Lagrangian methods commonly emphasize accurate departure-point
    trajectories, and midpoint estimates are a standard way to reduce trajectory
    error.
- Rollback complexity:
  - Low. Remove one selector/helper path, one factory/export, one registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_theta`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_theta --workers 4`.
  - Support requires clean diagnostics, fixed RMSE guardrails passing, and
    iteration primary delta at least `+0.002` against cached `dino_hsl_theta`
    incumbent metrics.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_theta --workers 4`
    only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with clean
    diagnostics and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that first-order
    departure error is not a material remaining source for the accepted
    horizontal theta transport. Any early Z500/MSLP guardrail failure would show
    the midpoint trajectory disrupts the incumbent balance.

## Citations

- Local evidence:
  - `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
    accepted `dino_hsl_theta` with iteration delta `+0.1070074439676863` and
    validation delta `+0.10295803136629866`.
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` implements
    `_horizontal_semilagrangian_theta_departure_displacement`,
    `_horizontal_semilagrangian_remap_layer`, and
    `horizontal_semilagrangian_theta_transport`, giving a localized hook for
    improving only the departure estimate.
  - `outputs/eval/iteration_dino_hsl_theta.csv` shows remaining negative mean
    skill for `2m_temperature`, `mean_sea_level_pressure`, and late
    `10m_u_component_of_wind`, so trajectory-level gains still have room to
    matter.
- Literature:
  - Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
    atmospheric models: a review. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
  - Temperton, C. and Staniforth, A. 1987. An efficient two-time-level
    semi-Lagrangian semi-implicit integration scheme. Quarterly Journal of the
    Royal Meteorological Society. https://doi.org/10.1002/qj.49711347714
  - ECMWF, 2014. The semi-Lagrangian technique in atmospheric modelling:
    current status and future challenges.
    https://www.ecmwf.int/sites/default/files/elibrary/2014/74225-semi-lagrangian-technique-atmospheric-modelling-current-status-and-future-challenges_0.pdf

## Researcher Notes

This is not a duplicate of the accepted horizontal-semi-Lagrangian theta
transport proposal: the accepted mechanism is retained as the fallback and
baseline, while this proposal changes only the departure-point time accuracy.
It is not active staged `mass-flux-theta-transport`, `theta-upwind-vertical-
advection`, `full-state-theta-thermodynamic-tendency`, or
`skew-symmetric-horizontal-scalar-advection`; those change conservation form,
vertical stencil, theta variable content, or scalar-product algebra.

It also avoids the two recent rejected lower-boundary thermal ideas
`sst-sea-ice-ocean-flux-anchor` and `snow-soil-land-thermal-reservoir`. The
candidate uses no new external boundary data, no evaluation-protocol changes,
and no golden run for iterative selection.

## Evaluator Notes

### 2026-06-22T14:36:17Z

Decision: move to `ready`; rank 1 of 2 new proposals; recommend as the sole
next implementation idea.

This is the strongest immediate follow-up to the incumbent `dino_hsl_theta`.
The accepted horizontal semi-Lagrangian theta transport produced a large,
validated gain, and this proposal preserves that mechanism while changing only
the departure-point time accuracy for the theta horizontal remap. The source
hook is localized in the existing bounded remap path, the fallback is exactly
the incumbent first-order departure, and the registry/API surface remains
side-by-side and reversible.

The literature check supports the numerical premise: semi-Lagrangian schemes
are standard in atmospheric models, and improving departure-point estimates by
centering the advecting velocity is a recognized trajectory-accuracy strategy.
That does not guarantee a score gain, but it makes this a better experiment
than another broad forcing or reservoir change after the recent lower-boundary
ideas were clean but score-neutral.

Risks are moderate rather than low because midpoint wind interpolation adds
extra remaps and may perturb the empirical smoothing/balance that made
`dino_hsl_theta` strong. Those risks are acceptable for one ready slot because
the change is mechanistic, bounded, local to theta transport, and likely to
teach whether first-order trajectory phase error remains a material source
under the fixed iteration/validation protocols.
