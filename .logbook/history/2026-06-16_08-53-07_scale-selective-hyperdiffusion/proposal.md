---
schema_version: 1
slug: scale-selective-hyperdiffusion
title: Use Scale-Selective Fourth-Order Horizontal Diffusion
status: ready
created_at: 2026-06-16T07:45:01Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Scale-Selective Fourth-Order Horizontal Diffusion

## Hypothesis

The incumbent Dinosaur adapter uses a T80 pseudo-spectral dry primitive-equation
model with a second-order horizontal diffusion step filter. Second-order
Laplacian diffusion damps broad resolved scales more strongly than necessary
when the main numerical need is to control truncation-scale noise, aliasing, and
spectral ringing. A fourth-order horizontal diffusion filter with the same
top-wavenumber e-folding time should be more scale selective: it damps the
highest resolved modes while preserving larger synoptic modes that dominate the
daily WeatherBench2 targets.

This is a model-selection candidate only after the incumbent finite-output
diagnostic issue is repaired. It should not be used to mask or reinterpret the
current `nonfinite_forecast` failure, because that failure is already present in
the dry incumbent.

## Mechanism

Change the Dinosaur default horizontal diffusion order from 2 to 4 while keeping
the existing default top-mode damping timescale formula. The implementation
should leave the IMEX SIL3 stepper, inner step length, output channels, metrics,
and evaluation protocols unchanged.

The current helper computes the diffusion scale so the highest total wavenumber
has the configured e-folding time for any order. Raising the order therefore
changes the shape of the damping curve rather than simply making all diffusion
stronger or weaker. Synoptic wavenumbers should experience less artificial
damping, while near-truncation modes remain controlled after each Runge-Kutta
step.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Registry changes:
  - None expected for an in-place candidate evaluated as `dinosaur`. If the
    Orchestrator requires side-by-side scoring, add a small registered factory
    only after selection.
- API changes:
  - None. Do not alter `ForecastInput`, emitted channel names, metric code, or
    diagnostic behavior.
- Tests to update:
  - Update the default-configuration test to expect
    `horizontal_diffusion_order == 4`.
  - Add or extend a helper test showing that the horizontal diffusion filter
    still matches `time_integration.horizontal_diffusion_step_filter` with the
    configured order.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if the
    incumbent is over-damping balanced synoptic waves.
  - `10m_u_component_of_wind` if less broad diffusion preserves large-scale wind
    gradients while controlling grid-scale noise.
- Expected neutral metrics:
  - `2m_temperature` may be mostly neutral because the dry dycore lacks boundary
    layer and surface physics.
- Possible regressions:
  - If second-order diffusion is currently suppressing dynamically important
    small-scale noise, fourth-order diffusion may under-damp intermediate
    wavenumbers and worsen MSLP or wind at later leads.
  - If non-finite output diagnostics have not been repaired first, this proposal
    cannot be evaluated cleanly and should be deferred.

## Risks

- Numerical stability:
  - Moderate. The highest modes keep the same nominal damping time, but
    intermediate modes receive less damping than before.
- Compute cost:
  - Negligible. The existing filter already supports arbitrary order and applies
    the damping in spectral space.
- Data leakage:
  - Low. No future truth or validation statistics are used.
- Physical plausibility:
  - Good. Scale-selective diffusion is a standard numerical closure for
    pseudo-spectral atmospheric models, but the exact order must be verified
    empirically under the fixed protocols.
- Rollback complexity:
  - Low. The change is one adapter default plus tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur`.
  - This gate is meaningful only after `dinosaur` itself has a finite-output fast
    baseline. Require `diagnostics.failed=false`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur --workers 4`.
  - Support for the hypothesis is a lower primary score or higher
    skill-vs-persistence than the finite incumbent baseline, led by Z500, MSLP,
    or 10 m wind improvements.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur --workers 4` only if
    iteration improves.
  - Validation should preserve medium-lead mass-field improvements without a
    broad near-surface degradation.
- Outcome that would falsify the hypothesis:
  - A finite fast and iteration run with worse primary score and no Z500/MSLP
    improvement would indicate that the current second-order damping is more
    appropriate for this dry adapter.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements `horizontal_diffusion_step_filter` so the top wavenumber e-folding
  time is held fixed as the diffusion order changes.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/filtering.py` documents
  spectral filters for Gibbs phenomena and nearly singular pseudo-spectral
  solutions.
- Gottlieb, D. and Shu, C.-W. 1997. On the Gibbs Phenomenon and Its Resolution.
  SIAM Review. https://doi.org/10.1137/S0036144596301390
- Hou, T. Y. and Li, R. 2007. Computing nearly singular solutions using
  pseudo-spectral methods. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2007.04.014
- Kochkov et al. 2024. Neural general circulation models for weather and
  climate. Nature. The Dinosaur-backed dycore uses a horizontal pseudo-spectral
  discretization. https://www.nature.com/articles/s41586-024-07744-y

## Researcher Notes

This proposal is distinct from the staged balanced digital-filter initialization
idea: it changes ongoing spectral dissipation throughout the forecast, not only
the initial balanced state. It is also distinct from the near-surface diagnostic
proposal because it changes prognostic dynamics rather than output residuals.
The rejected moist-history lesson is that fast diagnostic failures must be
interpreted carefully; this candidate should not be scored until the incumbent
full-output non-finite issue has been repaired or otherwise resolved by an
accepted infrastructure change.

## Evaluator Notes

2026-06-16T07:47:01Z - Move to `staging`.

The mechanism is credible and low surface area. Source inspection confirms the
adapter default is currently `horizontal_diffusion_order == 2`, and the existing
helper passes that order into `time_integration.horizontal_diffusion_step_filter`.
Fourth-order diffusion is a legitimate scale-selective spectral closure and
should be easy to test once the fixed gates are meaningful.

Do not move this to `ready` in this iteration because it cannot repair the
current `nonfinite_forecast` fast failure shared by the incumbent and the
rejected moist candidate. Reconsider after an accepted infrastructure repair
creates a finite `dinosaur` fast and iteration baseline. Until then, any score
from this candidate would be confounded by the pre-existing output-diagnostics
failure.

2026-06-16T08:46:22Z - Move to `ready`.

The accepted finite pressure-level extrapolation repair has removed the prior
triage blocker. The current leaderboard points to a finite canonical
`dinosaur` baseline at commit `4beb6c221f8655f80b6530713ffc75697e9c654e`, with
fast, iteration, and validation diagnostics passing with zero issues. That makes
this a clean model-selection experiment under the unchanged fixed protocols.

This is the strongest next candidate among staged ideas. Source inspection
confirms the adapter default remains `horizontal_diffusion_order == 2`, and the
helper computes the scale from the top-mode damping time for the requested
order. Changing the default to 4 is therefore a small, reversible change to the
damping spectrum rather than a forecast-contract, metric, split, or output
target change. The mechanism can plausibly affect Z500, MSLP, and 10 m wind
across more than only the earliest leads, which gives it broader learning value
than the output-only near-surface residual and a lower implementation risk than
digital filter initialization.
