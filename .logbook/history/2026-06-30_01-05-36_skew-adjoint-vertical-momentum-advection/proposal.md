---
schema_version: 1
slug: skew-adjoint-vertical-momentum-advection
title: Skew-Adjoint Mass-Weighted Vertical Momentum Advection
status: ready
created_at: 2026-06-30T00:57:29Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py
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

# Skew-Adjoint Mass-Weighted Vertical Momentum Advection

## Hypothesis

The current sigma vertical-advection operator is the centered advective form
`-sigma_dot * d x / d sigma`. That is a reasonable scalar advection operator, but
for momentum it does not make the vertical-transport contribution skew-adjoint in
the layer-mass inner product on the model's uneven sigma layers. The result can be
a small artificial source or sink of vertically redistributed kinetic energy,
which can project onto `10m_u_component_of_wind`, `geopotential_500`, and
`mean_sea_level_pressure` over 1-15 day WeatherBench2 rollouts.

The staged proposal
`.logbook/research/staging/mass-weighted-energy-conserving-vertical-advection.md`
was correctly held because it claimed pure advective conservation for a generally
divergent `sigma_dot`. This revised mechanism does not make that claim. It
explicitly uses the skew-symmetric split

`A(x) = -0.5 * [sigma_dot * d_sigma x + d_sigma(sigma_dot * x)]`

for the momentum vertical-advection term only. This split contains the
`-0.5 * d_sigma(sigma_dot) * x` compression term needed for an exact quadratic
identity. Scalar tracers and temperature vertical advection should remain on the
incumbent centered operator so constants and scalar transport behavior are not
altered by a momentum-energy fix.

## Mechanism

Add a side-by-side candidate, for example `dino_ri2m_skewvadv`, derived from
`dino_ri2m_ekman_coupled`.

Define a local helper in `sigma_coordinates.py` that operates on interface
`sigma_dot` with zero top and bottom boundary velocities. For layer thickness
`Delta_i`, centered values `x_i`, and interface velocities `w_{i+1/2}`, use

`(A x)_i = -(w_{i+1/2} x_{i+1} - w_{i-1/2} x_{i-1}) / (2 Delta_i)`

with missing boundary neighbor terms omitted because boundary `w` is zero. This
is the discrete skew split, not the conservative flux form. Its testable
identity is exact for any finite `x`, any finite interface `w`, and any positive
unequal layer thicknesses:

`sum_i Delta_i * x_i * (A x)_i = 0`.

The cancellation is by pairwise antisymmetry:

`Delta_i A_{i,i+1} = -0.5 w_{i+1/2}` and
`Delta_{i+1} A_{i+1,i} = +0.5 w_{i+1/2}`.

Thread the option only into `PrimitiveEquationsSigma.curl_and_div_tendencies`
where the vertical momentum terms `sigma_dot_u` and `sigma_dot_v` are formed.
Leave `nodal_temperature_vertical_tendency`, tracer tendencies, pressure
continuity, weak-HS forcing, WTG, vertical-DSE increment, accepted Ekman
stress-pumping, residual memory, and output diagnostics unchanged. If the new
operator produces any nonfinite tendency, fall back exactly to the incumbent
centered vertical momentum tendency for that step.

## Implementation Scope

- Expected files:
  - `sigma_coordinates.py`: add the skew-adjoint helper and boundary handling.
  - `primitive_equations.py`: add a boolean selector for momentum-only skew
    vertical advection and use it only in `curl_and_div_tendencies`.
  - `adapter.py`: add a default-false flag and a factory derived from
    `ekman_coupled_dinosaur_dycore_model()`.
  - `__init__.py` and `registry.py`: export/register one short candidate name.
  - tests: focused operator identity, no-op/fallback, and registry tests.
- Registry changes: one new side-by-side key such as `dino_ri2m_skewvadv`.
- API changes: none.
- Tests to update:
  - On unequal synthetic sigma layers, verify
    `sum(Delta * x * A(x))` is zero to tight tolerance for random finite `x`
    and `sigma_dot`.
  - Verify the incumbent centered operator does not generally satisfy that same
    identity, so the test guards against a no-op.
  - Verify scalar/tracer and temperature vertical tendencies are unchanged by
    the option.
  - Verify nonfinite inputs fall back to the incumbent centered momentum term.
  - Verify the candidate factory preserves all `dino_ri2m_ekman_coupled` flags
    except the new momentum-advection selector.

## Expected Metric Movement

- Expected improvements: `10m_u_component_of_wind` and `geopotential_500` at
  medium-to-long leads if vertical momentum transport is injecting small
  unresolved kinetic-energy errors; `mean_sea_level_pressure` may improve
  secondarily through better balanced wind evolution.
- Expected neutral metrics: `2m_temperature`, since the lower-boundary thermal
  path, RI2m diagnostic, residual memory, and temperature vertical advection
  remain incumbent.
- Possible regressions: the compression term may disturb momentum-pressure
  balance if the incumbent advective form is empirically compensating another
  error; early `10m_u_component_of_wind` and MSLP guardrails are the main risks.

## Risks

- Numerical stability: moderate. The operator is nondissipative and touches
  momentum every inner step, but it is local, bounded by finite fallback, and
  does not alter scalar transport.
- Compute cost: negligible; one local vertical stencil for `u` and `v`.
- Data leakage: none.
- Physical plausibility: high as a structure-preserving momentum-transport
  experiment; deliberately not applied to passive scalars because the skew split
  is not a conservative tracer operator.
- Rollback complexity: low to moderate; one helper, one selector, one factory,
  and tests.

## Evaluation Plan

- Fast gate: run `uv run pytest`, then
  `uv run dynamaxx-eval fast --model dino_ri2m_skewvadv`; require clean
  diagnostics and finite forecasts.
- Iteration gate: run
  `uv run dynamaxx-eval iteration --model dino_ri2m_skewvadv --workers 4`;
  support requires at least `+0.002` over cached incumbent iteration primary
  `-0.16500618979404214`, with all fixed RMSE guardrails clean.
- Validation gate: only after iteration promotion, run
  `uv run dynamaxx-eval validation --model dino_ri2m_skewvadv --workers 4`;
  require at least `+0.001` over cached incumbent validation primary
  `-0.16591150807771451`.
- Outcome that would falsify the hypothesis: a clean subthreshold or negative
  iteration delta, or an early wind/MSLP guardrail regression, would indicate
  that the incumbent vertical momentum form is already better balanced in this
  model despite lacking the discrete skew identity.

## Citations

- Simmons, A. J. and Burridge, D. M. 1981. "An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates."
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Arakawa, A. and Lamb, V. R. 1981. "A Potential Enstrophy and Energy
  Conserving Scheme for the Shallow Water Equations." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0018:APEAEC%3E2.0.CO;2
- Morinishi, Y., Lund, T. S., Vasilyev, O. V., and Moin, P. 1998. "Fully
  Conservative Higher Order Finite Difference Schemes for Incompressible Flow."
  Journal of Computational Physics, 143, 90-124. https://doi.org/10.1006/jcph.1998.5962
- Thuburn, J. 2008. "Some Conservation Issues for the Dynamical Cores of NWP
  and Climate Models." Journal of Computational Physics, 227, 3715-3730.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Local evidence:
  `.logbook/research/staging/mass-weighted-energy-conserving-vertical-advection.md`
  was staged because its operator did not prove the advertised identity; this
  proposal supplies the corrected skew-adjoint identity and limits scope to
  momentum.

## Researcher Notes

This is not a repeat of first-order upwind vertical advection, sigma-dot
smoothing, theta-only upwinding, semi-Lagrangian vertical remap, or the staged
uncorrected energy-conserving proposal. It directly resolves the Evaluator's
objection by acknowledging that pure advective vertical transport is not
quadratically conservative for divergent `sigma_dot`, then using the
skew-symmetric split with an exact mass-weighted identity. It also narrows the
blast radius by keeping temperature and tracers on the incumbent operator.

## Evaluator Notes

### 2026-06-30T01:04:27Z

Decision: move to `ready`; ranked first and recommended as the next
implementation target.

This proposal directly addresses the reason
`mass-weighted-energy-conserving-vertical-advection` was staged. The new
interface-stencil proof is the relevant discrete identity:
`Delta_i A_{i,i+1} = -0.5 w_{i+1/2}` and
`Delta_{i+1} A_{i+1,i} = +0.5 w_{i+1/2}`, so the layer-mass quadratic form
`sum_i Delta_i x_i A(x)_i` cancels pairwise on unequal sigma layers with zero
top and bottom interface velocity. That is a concrete, testable improvement over
the earlier flux-form derivation, which reconstructed an advective operator
without proving skew-adjointness for divergent `sigma_dot`.

The source surface is acceptable for one iteration. The current code localizes
vertical momentum advection in `PrimitiveEquationsSigma.curl_and_div_tendencies`
through `sigma_dot_u` and `sigma_dot_v`, while `sigma_coordinates.py` already
houses the centered and upwind vertical operators. A momentum-only selector can
therefore leave scalar, tracer, temperature, pressure-continuity, lower-boundary
memory, RI diagnostics, and the accepted Ekman closure unchanged. The required
tests are also sharply defined: exact skew identity on unequal layers, incumbent
non-identity, unchanged scalar/thermal paths, finite fallback, and factory flag
preservation.

Risk remains moderate. The skew split intentionally changes the velocity
equation for vertically uniform wind when `sigma_dot` is vertically divergent,
so it is a structure-preserving numerical experiment rather than a guaranteed
closer approximation to the incumbent advective PDE. Recent
`momentum-only-sl-vertical-advection` history also warns that vertical momentum
transport changes can become unstable over the full iteration split. This
proposal is still the best current ready candidate because it is Eulerian,
local, non-remapping, finite-guarded, and fixes a precise mathematical defect
instead of adding broad diffusion or another lower-boundary coefficient tweak.
