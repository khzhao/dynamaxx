---
schema_version: 1
slug: fixed-pressure-analysis-hs-equilibrium
title: Fixed Pressure Analysis HS Equilibrium
status: ready
created_at: 2026-06-21T04:30:49Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Fixed Pressure Analysis HS Equilibrium

## Hypothesis

The current incumbent gains skill from a weak Held-Suarez thermal relaxation
with an analysis-offset equilibrium. In the current Dinosaur path, the
Held-Suarez pressure coordinate is still tied to the local evolving surface
pressure. Because this no-orography dycore can initialize `surface_pressure`
from mean sea level pressure, the weak heating target can become coupled to
mass-error and MSLP-error modes rather than acting as a clean large-scale
thermal reference. Holding the Held-Suarez pressure coordinate fixed at the
standard sigma pressure `p / p0 = sigma` should keep the accepted analysis
thermal offset while reducing feedback from transient log-surface-pressure
errors into the relaxation target.

## Mechanism

Add a candidate option that leaves the incumbent rollout, residual corrections,
DFI, Coriolis split, theta tendency, theta recentering, and surface residual
decay unchanged, but changes only the pressure coordinate used by the weak
Held-Suarez equilibrium temperature calculation.

The candidate should evaluate the weak Held-Suarez equilibrium using a fixed
reference surface pressure, equivalent to `p_over_p0 = sigma`, before adding
the existing low-mode analysis equilibrium offset. The local `log_surface_pressure`
state should continue to evolve normally and should still enter the primitive
equations; it should not alter the weak thermal equilibrium coordinate for this
experiment.

## Implementation Scope

- Expected files: `src/dynamaxx/dycore/models/dinosaur/adapter.py` and, if the
  Held-Suarez helper needs a narrow parameter, the local Dinosaur forcing helper.
- Registry changes: add one registered model derived from the current incumbent
  with a suffix such as `_fixed_p_hs_eq`.
- API changes: no public API changes outside a model option or factory.
- Tests to update: add a focused construction test that the new model registers
  and that the weak Held-Suarez equilibrium can be evaluated without changing
  forecast output fields.

## Expected Metric Movement

- Expected improvements: `mean_sea_level_pressure` and `2m_temperature` at
  medium leads, especially where evolving surface-pressure errors currently
  perturb the relaxation target.
- Expected neutral metrics: `10m_u_component_of_wind`, since the wind diagnostic
  and surface residual path are unchanged.
- Possible regressions: `geopotential_500` if the current local-pressure
  dependence was compensating a real column-thickness bias.

## Risks

- Numerical stability: low, because the change modifies a weak thermal target
  and does not alter the time integrator.
- Compute cost: negligible.
- Data leakage: none; the candidate uses only forecast-state quantities and the
  existing initial analysis offset.
- Physical plausibility: moderate; Held-Suarez forcing is idealized, but its
  original benchmark is formulated as a dry dynamical-core forcing rather than
  a data-assimilative pressure-error correction.
- Rollback complexity: low; a single option can restore the incumbent behavior.

## Evaluation Plan

- Fast gate: run the fixed `fast` protocol and require finite diagnostics with
  no forecast-contract changes.
- Iteration gate: run the fixed `iteration` protocol with the standard worker
  policy and compare against the cached incumbent.
- Validation gate: run `validation` only if iteration improves the primary
  score or shows a defensible guardrail-neutral tradeoff.
- Outcome that would falsify the hypothesis: broad MSLP or T2m degradation at
  days 2 through 10, or any sign that removing local-pressure dependence
  destabilizes Z500.

## Citations

- Held, I. M., and M. J. Suarez, 1994: A proposal for the intercomparison of
  the dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Laprise, R., 1992: The Euler equations of motion with hydrostatic pressure as
  an independent variable. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1992)120%3C0197:TEEOMW%3E2.0.CO;2

## Researcher Notes

This is not a smooth analysis-HS spectral taper, a lead-decayed analysis-HS
equilibrium, or a barotropic analysis-HS offset. It leaves the accepted
analysis-offset mask and amplitude treatment unchanged and modifies only the
pressure coordinate used by the ongoing weak thermal forcing. It is also not an
initialization-only experiment, because the altered equilibrium is consulted
throughout the rollout.

## Evaluator Notes

### 2026-06-21T04:35:33Z

Decision: move to `ready`; ranked first of the three new proposals.

This is the best next model-selection experiment because it is a narrow,
implementable change to the accepted analysis-HS equilibrium path. Source
inspection confirms the current sigma Held-Suarez helper computes
`p_over_p0 = sigma * surface_pressure / p0`, and the accepted analysis-offset
wrapper adds its low-mode offset on top of that standard equilibrium. The
proposal changes only that equilibrium pressure coordinate to a fixed
`p_over_p0 = sigma` reference while preserving the incumbent primitive
equations, DFI, residual corrections, theta tendency/recentering, Coriolis
split, and surface-pressure evolution.

The recent HS lineage is mixed but still supports this as the single ready
candidate. The original analysis-offset HS equilibrium produced a large
accepted validation gain, while DFI-balanced source ordering, lead decay,
barotropic projection, and smooth horizontal taper were clean but subthreshold,
and relaxation-rate masking was harmful because it weakened stabilizing thermal
damping. This proposal is materially different from those variants: it does
not weaken the coefficient, decay the accepted offset, smooth the mask, or
project the vertical structure. It tests whether transient surface-pressure
errors should feed the weak thermal target. Keep `ready` capped to this one
candidate; if it fails cleanly, future HS follow-ups should return to staging
unless diagnostics specifically implicate the equilibrium pressure coordinate.
