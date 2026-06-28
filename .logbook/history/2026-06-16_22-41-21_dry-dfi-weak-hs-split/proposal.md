---
schema_version: 1
slug: dry-dfi-weak-hs-split
title: Run DFI on Dry Dynamics Before Weak HS Forecast Forcing
status: ready
created_at: 2026-06-16T22:26:22Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Run DFI on Dry Dynamics Before Weak HS Forecast Forcing

## Hypothesis

The accepted incumbent combines three useful pieces: balanced digital-filter
initialization, near-surface diagnostic residuals, and weak wind-sparing
Held-Suarez thermal relaxation. In the current adapter, the DFI forward and
time-reversed integrations use the same composed equation that includes the
weak thermal relaxation. Newtonian relaxation is not a reversible balanced-wave
dynamics term; in the backward branch of DFI it is effectively anti-relaxing.

Running DFI on the dry primitive-equation dynamics and then applying weak
Held-Suarez only during the scored forward forecast should preserve the accepted
thermal-drift correction while avoiding a small nonphysical initialization bias.
The expected gain is modest but low-risk because the forecast forcing,
near-surface residuals, grid, step size, diffusion, variables, and protocols
stay fixed.

## Mechanism

Add a side-by-side incumbent variant that separates the equation used for
initialization from the equation used for forecast rollout:

- candidate model name: `dinosaur_dfi_surface_residual_weak_hs_dry_dfi`
- DFI equation: dry sigma-coordinate primitive equations with the incumbent
  vertical advection, horizontal diffusion filter, reference temperature, grid,
  and DFI span/cutoff
- forecast equation: the current incumbent equation, including weak
  wind-sparing Held-Suarez thermal relaxation
- diagnostics: the accepted near-surface residual correction remains unchanged

The implementation should not change the `ForecastInput` or `WeatherState`
contract. It should only let `_trajectory_function` build a separate
initialization equation when both DFI and weak Held-Suarez are enabled for this
candidate. The accepted incumbent entry must remain byte-for-byte equivalent in
behavior unless the selected implementation deliberately registers a new
side-by-side factory.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only a side-by-side factory for
    `dinosaur_dfi_surface_residual_weak_hs_dry_dfi`.
- API changes:
  - None.
- Tests to update:
  - Verify the candidate preserves DFI, weak Held-Suarez, and near-surface
    residual flags.
  - Add a focused test or monkeypatch proving DFI receives an equation without
    weak Held-Suarez while the forward stepper still receives the forced
    equation.
  - Verify the incumbent factory still uses the current single-equation path.

## Expected Metric Movement

- Expected improvements:
  - Small gains in `2m_temperature`, `geopotential_500`, and
    `mean_sea_level_pressure` at early to medium leads if the current forced
    backward DFI introduces thermal imbalance before the forecast starts.
  - Primary score improvement should be broad but likely smaller than the
    original weak-Held-Suarez acceptance.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be nearly unchanged because the accepted
    forcing remains wind-sparing and no drag, damping, or residual wind change
    is introduced.
  - Long leads should retain the accepted weak-Held-Suarez thermal-drift
    benefit because the rollout forcing is unchanged.
- Possible regressions:
  - The current forced DFI may be providing useful extra thermal smoothing; if
    so, removing the relaxation from DFI can slightly worsen near-surface
    temperature or mass fields.
  - Any gain may be below the fixed iteration promotion threshold.

## Risks

- Numerical stability:
  - Low. Both equations use already accepted pieces, and the candidate removes a
    nonreversible tendency from the DFI branch rather than adding a new source.
- Compute cost:
  - Same order as the incumbent. DFI still runs over the same window and the
    forecast rollout length is unchanged.
- Data leakage:
  - Low. No future truth, validation statistics, climatology, or new data are
    used.
- Physical plausibility:
  - Moderate to high. DFI is intended to reduce gravity-inertia imbalance in the
    analyzed mass and wind fields; keeping diabatic Newtonian relaxation out of
    the backward initialization branch is physically cleaner than time-reversing
    it.
- Rollback complexity:
  - Low. The change can be isolated behind one candidate factory and one adapter
    option.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_dry_dfi`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_dry_dfi --workers 4`.
  - Compare against exact incumbent records for
    `dinosaur_dfi_surface_residual_weak_hs`.
  - Support for the hypothesis is a primary-score delta of at least `+0.002`
    with clean diagnostics and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_dry_dfi --workers 4`
    only if iteration promotes.
  - Require validation primary delta of at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean iteration run with neutral or negative primary movement would show
    that the forced DFI branch is not an important remaining error source.
  - Any nonfinite fast artifact would falsify the implementation approach
    before iteration.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  composes weak Held-Suarez into the equation before creating the DFI
  initializer, so the time-reversed DFI branch includes the relaxation tendency.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements DFI by applying forward and `TimeReversedImExODE` integrations over
  the Lanczos filter window.
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a
  Digital Filter. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Polavarapu, S., Ren, S., Clayton, A. M., Sankey, D., and Rochon, Y. 2004. On
  the Relationship between Incremental Analysis Updating and Incremental Digital
  Filtering. Monthly Weather Review. https://doi.org/10.1175/1520-0493(2004)132%3C2495:OTRBIA%3E2.0.CO;2
- Held, I. M. and Suarez, M. J. 1994. A Proposal for the Intercomparison of the
  Dynamical Cores of Atmospheric General Circulation Models. Bulletin of the
  American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2

## Researcher Notes

This is not a Held-Suarez coefficient variant. The accepted weak thermal
relaxation coefficients, wind-sparing choice, and forecast rollout forcing
remain fixed; only the initialization equation is split from the forecast
equation.

This is also not a conservation-only one-mode tweak, time-step sweep, damping
variant, vertical-advection removal, pressure-grid/reference-profile/orography
change, output residual extension, resolution change, or humidity diagnostic
floor. The negative evidence from pressure anchor, 600 s step, divergence
damping, vertical-advection suppression, passive humidity floor, and T120
therefore does not directly duplicate this mechanism.

The expected effect size may be small. That is acceptable only because the code
surface and compute cost are low, the fixed protocols are unchanged, and the
idea directly targets a plausible inconsistency introduced by the latest
accepted incumbent.

## Evaluator Notes

2026-06-16T22:29:56Z - Move to `ready`; rank 1 of 2 for iteration 17.

This is the best next experiment because it has a clear local mechanism, small
implementation surface, no new data, no new protocol, and low rollback cost.
Source inspection confirms the incumbent adapter builds one primitive-equation
object, composes weak Held-Suarez relaxation into it, and then passes that same
equation into digital-filter initialization. The DFI helper documents that the
equation should be reversible dynamics only, while `TimeReversedImExODE` flips
the equation's explicit tendencies during the backward branch. Keeping weak
thermal relaxation in the scored forecast but removing it from the DFI equation
therefore targets a concrete nonreversible initialization inconsistency in the
current accepted incumbent.

Prior evidence supports this ranking. The finite pressure-level extrapolation
repair made diagnostics comparable; balanced DFI was accepted with iteration
delta `+0.004385840377088002` and validation delta
`+0.004498416027438834`; near-surface residual diagnostics were accepted with
iteration delta `+0.0353889745054945` and validation delta
`+0.03575996912567381`; weak wind-sparing Held-Suarez relaxation was accepted
with iteration delta `+0.06357275459004397` and validation delta
`+0.062227260743318746`. This proposal preserves those accepted mechanisms and
only changes how the latest accepted forcing interacts with initialization.

Negative evidence was checked explicitly. This is not a duplicate of rejected
moist virtual-temperature dynamics, pressure-grid/reference-profile/orography,
mass-residual, global-pressure-anchor, time-step, damping, vertical-advection
suppression, humidity-limiter, T120, or hyperdiffusion experiments. The closest
caution is the standard-atmosphere reference-profile rejection, which shows
some balance-partition changes are too small; the expected gain here may also
fall below the promotion threshold. The risk is still acceptable for `ready`
because the proposal removes a nonreversible tendency from DFI rather than
altering forecast dynamics, coordinates, resolution, drag, diffusion, or target
diagnostics. Because weak Held-Suarez already spends some long-lead
`10m_u_component_of_wind` guardrail margin, the implementation must preserve
the accepted wind-sparing thermal-only forcing and must not add drag or damping.

Citations and evidence checked: local source
`src/dynamaxx/dycore/models/dinosaur/adapter.py`, local DFI implementation in
`src/dynamaxx/dycore/models/dinosaur/time_integration.py`, the incumbent
leaderboard entry, and relevant history decisions/scoring notes for accepted
DFI, accepted near-surface residuals, accepted weak Held-Suarez relaxation, and
the listed rejected experiments. The proposal's DFI and Held-Suarez literature
citations support the general framing, but the decisive evidence for triage is
the verified local code path and fixed-protocol history.

Implementation constraints for Orchestrator: keep this side-by-side as
`dinosaur_dfi_surface_residual_weak_hs_dry_dfi`; do not change the incumbent
factory behavior; build a dry initialization equation that uses the same grid,
reference temperature, humidity choice, vertical advection, diffusion filters,
step size, DFI span, and DFI cutoff as the incumbent; keep the forecast equation
identical to `dinosaur_dfi_surface_residual_weak_hs`; add focused tests proving
DFI receives the dry equation while the forward stepper receives the weak-HS
equation.
