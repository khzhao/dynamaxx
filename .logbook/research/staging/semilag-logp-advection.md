---
schema_version: 1
slug: semilag-logp-advection
title: Semi-Lagrangian Log-Pressure Horizontal Advection
status: staging
created_at: 2026-06-22T21:55:16Z
author_role: Researcher
target_model: dino_hsl2_theta
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

# Semi-Lagrangian Log-Pressure Horizontal Advection

## Hypothesis

The accepted HSL theta sequence shows that replacing Eulerian horizontal scalar
advection with a guarded semi-Lagrangian update can reduce forecast phase error.
The sigma-coordinate log-surface-pressure continuity equation still computes
its horizontal advection term explicitly from `u_dot_grad_log_sp`, while the
divergence contribution remains in the accepted semi-implicit mass/gravity-wave
operator. Applying the same bounded midpoint semi-Lagrangian treatment only to
the log-surface-pressure horizontal advection term may improve MSLP and
hydrostatic thickness phase without changing the forecast contract, the mass
split, or theta transport.

## Mechanism

Add one side-by-side model alias, `dino_hsl_logp`, extending `dino_hsl2_theta`.

For this candidate only:

- preserve all accepted `dino_hsl2_theta` thermodynamic behavior, including
  bilinear midpoint HSL theta transport, theta recentering, weak-HS analysis
  equilibrium, ocean bulk sensible heat flux, Coriolis Strang splitting,
  off-centered SIL3, residual corrections, filters, outputs, and protocols;
- add a guarded opt-in replacement for the explicit
  `nodal_log_pressure_tendency` horizontal advection term;
- for each sigma layer, use the accepted midpoint HSL displacement machinery to
  remap the two-dimensional nodal `log_surface_pressure` field backward along
  that layer's horizontal wind;
- form the layerwise advective tendency
  `(remapped_log_surface_pressure - log_surface_pressure) / step`;
- integrate those layerwise advective tendencies over sigma with the same
  weights used by the incumbent `nodal_log_pressure_tendency`;
- keep the accepted semi-implicit divergence and pressure-gradient coupling
  unchanged;
- fall back to the incumbent Eulerian `u_dot_grad_log_sp` tendency if the
  remapped log pressure, layerwise tendency, integrated tendency, step, or
  implied surface pressure is nonfinite or nonpositive;
- do not alter theta remapping, vertical advection, momentum tendencies,
  humidity, residual outputs, metric definitions, splits, or lead schedules.

This is a scalar-advection replacement for the log-pressure continuity
advection term. It is not a time-centering wrapper, pressure anchor, divergence
projection, tendency limiter, Eulerian/HSL pointwise blend, or forecast-contract
change.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model registered as `dino_hsl_logp`.
- API changes:
  - None. Forecast inputs, output variables, lead steps, target metrics,
    evaluation splits, and worker count stay fixed.
- Tests to update:
  - Verify `dino_hsl_logp` preserves every `dino_hsl2_theta` option except
    model name and the log-pressure HSL advection selector.
  - Unit-test zero wind reproduces the incumbent log-pressure tendency.
  - Unit-test a constant `log_surface_pressure` field has zero HSL advection
    tendency.
  - Verify nonfinite remapped log pressure falls back to the incumbent
    `u_dot_grad_log_sp` path.
  - Verify the candidate changes only `log_surface_pressure` explicit
    advection, not theta tendency, momentum tendencies, tracers, or output
    packing.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 2 to 15 if remaining mass-field error is
    partly horizontal phase error in log-surface-pressure advection.
  - `geopotential_500` if improved pressure evolution improves hydrostatic
    thickness and pressure-gradient balance.
- Expected neutral metrics:
  - `2m_temperature` should remain close to incumbent because theta transport,
    residual memory, and lower-boundary heat flux are unchanged.
  - `10m_u_component_of_wind` should be mostly neutral because momentum
    dynamics and the Richardson 10 m diagnostic are unchanged.
- Possible regressions:
  - Log-surface pressure is not a passive tracer; using semi-Lagrangian
    advection for only its horizontal term can disturb the accepted
    divergence/log-pressure phase relationship.
  - Early MSLP may regress if the incumbent Eulerian advection is better aligned
    with the semi-implicit mass solve.

## Risks

- Numerical stability:
  - Moderate. The candidate touches a prognostic mass variable every inner step,
    so finite and positive-pressure guards are required.
- Compute cost:
  - Low to moderate. It reuses existing displacement and bilinear remap
    machinery for one surface scalar per layer, with no extra rollout length or
    output volume. The 4-worker evaluation budget is adequate.
- Data leakage:
  - None. It uses only same-step forecast state and fixed grid geometry.
- Physical plausibility:
  - Moderate to high. Semi-Lagrangian treatment of advective mass terms is
    standard in atmospheric models, but this candidate deliberately leaves the
    divergence part in the accepted semi-implicit split.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_logp`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_logp --workers 4`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failure, and a
    primary-score improvement over cached `dino_hsl2_theta`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_logp --workers 4`
    only after iteration promotion.
  - Support requires validation improvement with unchanged guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show log-pressure
    horizontal advection is not a material remaining error source. Any early
    MSLP or Z500 guardrail failure would show the semi-Lagrangian mass-advection
    split disrupts the accepted pressure balance.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
    computes `compute_diagnostic_state_sigma`, `u_dot_grad_log_sp`, and
    `nodal_log_pressure_tendency`, and already contains bounded HSL remap
    machinery used by the accepted theta path.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` and
    `src/dynamaxx/dycore/registry.py` provide the side-by-side alias pattern
    for incumbent-derived candidates.
  - Local history:
    `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
    and `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
    show local positive evidence for guarded HSL scalar transport and midpoint
    departure estimates.
  - Local history:
    `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/decision.md`
    rejects pointwise Eulerian/HSL blending, so this proposal replaces one
    complete scalar-advection term rather than blending tendencies.
  - Active research distinction:
    `.logbook/research/staging/time-centered-log-pressure-continuity.md`
    proposes a trapezoidal continuity wrapper; this proposal instead changes
    only the horizontal advection discretization inside the explicit
    log-pressure tendency.
  - Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
    atmospheric models: a review. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
  - Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric
    transport schemes: desirable properties and a semi-Lagrangian view on
    finite-volume discretizations. In Numerical Techniques for Global
    Atmospheric Models. https://doi.org/10.1007/978-3-642-11640-7_8
  - Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
    conserving vertical finite-difference scheme and hybrid vertical
    coordinates. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2

## Researcher Notes

This proposal is decorrelated from the accepted and staged theta-remap variants:
the theta path remains exactly `dino_hsl2_theta`, and the new mechanism targets
the log-surface-pressure continuity advection term. It is also distinct from
staged `time-centered-log-pressure-continuity`, which wraps the whole
log-pressure step in a trapezoidal update, and from pressure anchors or
zero-mode projections, which impose diagnostic corrections rather than
changing a local advection discretization.

It avoids the rejected `cfl-blended-hsl-theta` pattern because the candidate
does not use spatial CFL weights or blend Eulerian and HSL tendencies. It avoids
the rejected `qmono-hsl-theta-remap` pattern because it does not introduce a
higher-order remap and does not alter theta interpolation at all.

## Evaluator Notes

### 2026-06-22T21:57:42Z

Decision: move to `staging`; do not promote for the next implementation cycle.

The proposal is plausible and source-compatible enough to keep. Local source
inspection confirms `u_dot_grad_log_sp`, `nodal_log_pressure_tendency`, and the
bounded HSL remap machinery exist near the accepted theta path, and the
proposal preserves the forecast contract, fixed metrics, and semi-implicit
divergence coupling. It is also not a duplicate of
`time-centered-log-pressure-continuity`: this idea replaces only horizontal
log-pressure advection, whereas that staged idea wraps the continuity update in
a trapezoidal step.

Keep it staged because the next cycle should spend limited evaluation budget
on the lower-risk theta trajectory refinement first. This proposal touches
prognostic surface pressure every inner step and deliberately splits the
log-pressure horizontal advection from the accepted semi-implicit mass and
divergence treatment. That is a meaningful scientific risk for early MSLP and
Z500 guardrails. Prior staged notes for mass/continuity ideas already warn that
prognostic pressure changes have had weak or negative local evidence, and the
current incumbent's positive signal is specifically in theta trajectory
handling rather than mass continuity.

If revisited later, require a short alias such as `dino_hsl_logp`, strict
fallback to the incumbent Eulerian `u_dot_grad_log_sp` path for nonfinite or
nonpositive pressure states, and tests proving theta, momentum, tracers,
outputs, and protocols remain unchanged. Do not combine this with Picard theta
departure or any pressure limiter in the same implementation cycle.
