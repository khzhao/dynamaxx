---
schema_version: 1
slug: balanced-digital-filter-initialization
title: Add Lanczos Digital Filter Initialization
status: ready
created_at: 2026-06-16T07:21:43Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add Lanczos Digital Filter Initialization

## Hypothesis

WeatherBench2 initial states are pressure-level analyses that are interpolated into Dinosaur sigma-coordinate spectral state variables. That conversion can leave small gravity-wave and pressure-divergence imbalance, especially because the adapter uses a simplified dry or moist primitive-equation system and zero orography. A short Lanczos digital filter initialization should damp high-frequency imbalance before the forecast while preserving the balanced synoptic components that dominate daily lead scores.

## Mechanism

Apply `time_integration.digital_filter_initialization` to each converted Dinosaur initial state before the main trajectory rollout. Use the same equation, IMEX SIL3 stepper, and step filters as the forecast, with a short symmetric window such as 6 hours and a cutoff period equal to the window. With the default 900 second inner step, this adds 12 backward and 12 forward initialization steps per initial state before the 15 day forecast. The normal forecast contract and output variables remain unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Registry changes:
  - None expected for an in-place candidate evaluated as `dinosaur`.
- API changes:
  - None. Add adapter fields such as `apply_digital_filter_initialization`, `digital_filter_time_span_seconds`, and `digital_filter_cutoff_seconds`, but keep `forecast(ForecastInput) -> WeatherState` unchanged.
- Tests to update:
  - Add a deterministic unit test with `jit_forecast=False` showing that enabling the filter still preserves output shape, variables, and finite values.
  - Add a small helper test that the filter setup uses the same equation and filters as the main step function.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `10m_u_component_of_wind` at days 1-3 if the current adapter is launching spurious divergence or inertia-gravity noise.
  - `geopotential_500` at early and medium leads if filtered balance reduces fast-wave contamination in the mass field.
- Expected neutral metrics:
  - Later leads may be neutral because slow balanced errors and missing physics dominate after the initial adjustment period.
- Possible regressions:
  - `2m_temperature` and `10m_u_component_of_wind` could lose useful small-scale analyzed structure if the filter is too aggressive.
  - If the converted initial state is already balanced enough, the filter adds cost without improving the primary score.

## Risks

- Numerical stability:
  - Low to moderate. The code path exists, but it uses time-reversed dynamics and therefore needs fast-gate confirmation under the exact adapter equation.
- Compute cost:
  - Low for 15 day forecasts. A 6 hour window at 900 seconds adds 24 short steps, roughly 1.7 percent of a 15 day rollout with 900 second inner steps.
- Data leakage:
  - Low. The filter uses only model dynamics initialized from the analysis at the forecast time.
- Physical plausibility:
  - Good. Digital filter initialization is a standard way to reduce high-frequency imbalance without fitting to target data.
- Rollback complexity:
  - Low. The change can be guarded by one adapter flag.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur`.
  - Inspect diagnostics for non-finite forecasts or obvious over-filtering regressions.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur --workers 4`.
  - Support for the hypothesis is lower primary score, with the strongest per-lead improvement at days 1-3 for MSLP, Z500, or 10 m wind.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur --workers 4` only after an iteration improvement.
  - Validation should show the same early-lead direction without a compensating loss at days 7-15.
- Outcome that would falsify the hypothesis:
  - Primary-score regression with no early-lead MSLP/Z500/wind improvement, or instability in the time-reversed filter path, would reject this idea.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py` already implements `digital_filter_initialization` with Lanczos weights and cites Lynch and Huang.
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a Digital Filter. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Lynch, P. 1997. The Dolph-Chebyshev Window: A Simple Optimal Filter. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1997)125%3C0655:TDCWAS%3E2.0.CO;2
- Whitaker, J. S. and Kar, S. K. 2013. Implicit-Explicit Runge-Kutta Methods for Fast-Slow Wave Problems. Monthly Weather Review. https://doi.org/10.1175/MWR-D-13-00132.1

## Researcher Notes

The logbook contains no prior history or active proposals. This is not a timestep-tuning proposal: it uses the existing forecast scheme and filters, but adds a physically motivated balanced-initialization pass before the scored rollout.

## Evaluator Notes

2026-06-16T07:24:59Z - Move to `staging`.

This is scientifically credible but not the best next experiment. Digital-filter initialization is a standard NWP technique for reducing high-frequency imbalance, and source inspection confirms Dynamaxx already vendors a Lanczos `digital_filter_initialization` helper with a reversible equation wrapper. The proposal is therefore implementable without changing the public dycore API.

The ranking concern is expected signal-to-surface-area. The fixed protocols score daily leads from day 1 through day 15, while DFI primarily damps sub-daily inertia-gravity adjustment noise. The current adapter already uses a stable IMEX SIL3 stepper and horizontal diffusion, so the proposal needs the pressure-level-to-sigma initialization imbalance to be large enough to survive into daily RMSE. It also introduces a more delicate path than the moist proposal: backward integration through the same equation, filter reuse in both directions, and decisions about whether lead-0 outputs should represent the raw or filtered analysis.

Keep staged as a good follow-up if iteration diagnostics show early-lead MSLP, divergence, or wind noise. It should not displace the moist virtual-temperature candidate unless new evidence shows the incumbent has a clear spin-up imbalance.

2026-06-16T07:47:01Z - Keep in `staging` after incumbent fast-gate evidence.

The new evidence changes the priority, not the scientific assessment. Digital
filter initialization remains a plausible model-selection dynamics candidate,
but it does not target the full-output finite diagnostic that currently fails
for canonical `dinosaur` before target metrics are considered. Defer until a
finite-output infrastructure repair establishes a comparable incumbent
baseline. After that, keep it as a lower-ranked follow-up focused on early-lead
spin-up and balance.

2026-06-16T08:46:22Z - Keep in `staging`.

The accepted finite baseline removes the previous diagnostic blocker, and the
proposal remains scientifically credible. Source inspection confirms the
Lanczos digital filter initialization helper exists and can reuse the same
equation, solver, and filters as the forecast path. The expected benefit is
mainly early-lead reduction of initialization imbalance in MSLP, Z500, and wind.

Do not promote it ahead of scale-selective hyperdiffusion for this iteration.
The implementation surface is more delicate because it adds backward and
forward initialization integrations, filter application in both directions, and
new adapter configuration choices. Its signal may also be concentrated in days
1-3 while the fixed primary score spans days 1-15. Keep staged as the next
dynamics follow-up if hyperdiffusion is rejected or if diagnostics show a clear
spin-up imbalance.

2026-06-16T09:37:10Z - Move to `ready`.

The rejected hyperdiffusion experiment changes this proposal's relative rank.
The finite baseline is now established, the prior higher-ranked diffusion
candidate failed despite clean diagnostics, and the failure specifically
highlighted early low-level wind sensitivity. Digital filter initialization is
now the best implementable next target because it addresses initialization
imbalance without adding persistent forcing or target-specific output
corrections.

Source inspection confirms `time_integration.digital_filter_initialization`
already implements a Lanczos-weighted backward/forward initialization path and
can reuse the existing equation, solver, and filters. The mechanism is standard
in numerical weather prediction for reducing high-frequency imbalance in short
forecasts, and its expected signal in early MSLP, Z500, and wind is scientifically
cleaner than an output residual while lower-risk than Held-Suarez relaxation.
It remains a moderate implementation risk because backward integration must be
tested under the exact adapter equation and filters, but it preserves the
forecast API and fixed evaluation contract.

Recommended implementation shape: register a side-by-side candidate model for
scoring so the canonical `dinosaur` incumbent and leaderboard artifacts remain
comparable. Keep the window short and fixed before scoring; do not tune the
filter against iteration or validation outputs.
