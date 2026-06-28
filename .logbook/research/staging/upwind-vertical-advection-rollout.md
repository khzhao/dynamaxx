---
schema_version: 1
slug: upwind-vertical-advection-rollout
title: Use the Existing Upwind Vertical-Advection Operator
status: staging
created_at: 2026-06-18T07:23:54Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
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

# Use the Existing Upwind Vertical-Advection Operator

## Hypothesis

The incumbent uses centered sigma-coordinate vertical advection. Prior vertical
transport history gives negative evidence against broad changes: suppressing
vertical advection failed the fast gate, and a split semi-Lagrangian remap was
scrapped as too broad. Those results do not test the existing upwind operator,
which preserves vertical transport while adding sign-aware numerical
monotonicity along sigma.

Replacing centered vertical advection with the vendored upwind vertical
advection may reduce vertical ringing in temperature, wind, and passive tracer
transport without changing the accepted Strang Coriolis split, DFI window,
weak-HS forcing, horizontal diffusion, output diagnostics, lead times, or fixed
evaluation protocols.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_upwind_vadv`.
Preserve every incumbent option except the vertical-advection discretization.

Add a small adapter option for vertical advection:

- keep `sigma_coordinates.centered_vertical_advection` as the default incumbent
  path;
- pass `sigma_coordinates.upwind_vertical_advection` into
  `PrimitiveEquations` and `PrimitiveEquationsSigma` for the candidate;
- use the same upwind operator in DFI and positive-time rollout because this is
  a model-equation change, not a DFI-only consistency experiment;
- preserve vertical advection as enabled, avoiding the nonfinite behavior seen
  when vertical advection was suppressed;
- do not add a split remap, departure-point search, new time step, or new
  diffusion coefficient.

The mechanism is a vertical transport discretization test with a lower
implementation surface than semi-Lagrangian transport.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, emitted variables, shapes, leads, target
    variables, metrics, and protocols remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves all Strang incumbent flags except
    the vertical-advection scheme selector.
  - Unit-test that `_primitive_equation` receives the requested vertical
    advection callable for dry and humidity-carrying equation paths.
  - Verify the incumbent default remains centered vertical advection.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if
    centered vertical transport creates dispersive thermal or mass-field
    oscillations.
  - `2m_temperature` after the accepted residual decays if lower-column
    vertical thermal transport becomes less noisy.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should not change at lead zero and may be near
    neutral at early leads because initialization, Coriolis splitting, and
    near-surface residual correction are unchanged.
- Possible regressions:
  - First-order upwinding may be too diffusive, weakening baroclinic structure
    and degrading Z500 or wind phase.
  - If vertical ringing is not a material remaining error source, score movement
    may be small or negative despite clean diagnostics.

## Risks

- Numerical stability:
  - Moderate. Upwinding is usually stabilizing for transport, but it changes all
    vertically advected prognostic and tracer tendencies each step.
- Compute cost:
  - Low. The source operator already exists and does not change resolution,
    output volume, lead count, or expected worker count.
- Data leakage:
  - None. The scheme uses only forecast state and fixed grid geometry.
- Physical plausibility:
  - Moderate. Upwind advection is a standard monotone transport discretization,
    but its numerical diffusion may be excessive for a spectral primitive
    equation core.
- Rollback complexity:
  - Low. Remove one selector, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_upwind_vadv`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_upwind_vadv --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`
    against the Strang incumbent, clean diagnostics, no early day 1-5 RMSE
    guardrail failure, and no variable+lead guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_upwind_vadv --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A fast nonfinite result, a clean negative iteration delta, or an early Z500,
    MSLP, or 10 m wind guardrail failure would show that upwind vertical
    transport is either unstable, too diffusive, or not relevant to the
    incumbent's remaining error.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py`
  already defines both `centered_vertical_advection` and
  `upwind_vertical_advection`; `primitive_equations.py` accepts a
  `vertical_advection` callable.
- History: `.logbook/history/2026-06-16_20-56-11_vertical-advection-suppression/decision.md`
  rejected removing vertical advection after fast nonfinite behavior, so this
  proposal preserves vertical transport.
- Research scrap: `.logbook/research/scrap/semi-lagrangian-vertical-transport.md`
  rejected a split semi-Lagrangian remap as a broad transport rewrite; this
  proposal uses the existing in-equation upwind operator instead.
- LeVeque, R. J. 2002. Finite Volume Methods for Hyperbolic Problems.
  Cambridge University Press.
  https://www.cambridge.org/core/books/finite-volume-methods-for-hyperbolic-problems/CB7B0A27A6D37AE3B906D4AE7C60A87E
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of vertical-advection suppression because it retains a
vertical transport tendency. It is not a duplicate of scrapped
semi-Lagrangian vertical transport because it does not add an operator-split
remap, disable centered advection to avoid double counting, or change trajectory
contract. It also does not overlap active staged RK4, diffusion-split, reference
temperature, or hypsometric-output proposals.

The proposal uses prior failures as negative evidence: broad transport rewrites
are risky, so this candidate is intentionally limited to a source-supported
callable swap inside the existing primitive equation.

## Evaluator Notes

### 2026-06-18T07:28:25Z

Decision: move to `staging`; low-to-middle fallback, not ready.

This is narrower than the scrapped split semi-Lagrangian vertical-transport
proposal and is not a duplicate of vertical-advection suppression. Source
inspection confirms `sigma_coordinates.upwind_vertical_advection` exists and
`PrimitiveEquationsSigma` accepts a `vertical_advection` callable, so the
implementation can be a side-by-side callable selector rather than an
operator-split remap or a removal of vertical transport.

The risk is still high enough to keep it out of `ready`. The nearest direct
history is severe: vertical-advection suppression failed the fast gate with
nonfinite forecasts and metrics beginning at lead hour 264. The broader
numerics family is also mostly negative or sub-threshold, including T120
truncation, 600 s stepping, divergence damping, hyperdiffusion, and the latest
DFI operator-consistency refinement. First-order upwinding may be stabilizing,
but it changes all vertically advected tendencies every inner step and may add
too much numerical diffusion to baroclinic structure. Revisit only after
lower-surface hydrostatic/output/filter-placement ideas are scored or if new
diagnostics specifically implicate centered vertical transport.

### 2026-06-18T08:53:53Z

Decision: keep in `staging`, low priority.

The new proposals do not duplicate this existing-callable swap, and source
inspection still confirms `sigma_coordinates.upwind_vertical_advection` can be
passed through the primitive-equation constructor. It is narrower than the
scrapped split semi-Lagrangian vertical-transport proposal and does not repeat
the rejected vertical-advection suppression ablation.

The scientific priority remains low. The nearest direct history is still the
fast-gate failure from removing vertical advection, and the broader transport
and damping family has mostly failed or moved scores only below threshold.
First-order upwinding may stabilize vertical transport, but it may also add too
much numerical diffusion to baroclinic temperature and wind structure. Revisit
only if future diagnostics specifically implicate centered vertical advection.

### 2026-06-18T10:25:42Z

Decision: keep in `staging`; current staged rank 8 and lowest active priority.

The existing upwind callable makes this implementable, and it is narrower than
the scrapped semi-Lagrangian vertical-transport rewrite. It is still the least
attractive active staged idea because it changes all vertically advected
tendencies every inner step and the closest direct evidence is severe:
vertical-advection suppression failed the fast gate with nonfinite forecasts.

The new omega-spinup proposal is also vertical-motion-related, but it is a
short-lived analyzed forcing test rather than a permanent first-order upwind
scheme. Keep this upwind rollout candidate only as a later diagnostic follow-up
if centered vertical transport becomes the clearest remaining failure mode.

### 2026-06-18T11:49:28Z

Decision: keep in `staging`, staged fallback rank 9 and lowest active priority.

No new evidence improves the risk profile. The existing callable keeps the
implementation surface small, but a permanent first-order upwind vertical
transport scheme can add too much numerical diffusion to thermal and wind
structure. Keep it behind the transient omega-spinup idea and all horizontal
continuity, diagnostic, split-ordering, and anti-aliasing candidates.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 10 and lowest active
priority.

The new log-sigma proposal is a narrower thermodynamic vertical-balance test
than permanently switching all vertical advection to first-order upwind. The
nearest direct evidence remains severe because vertical-advection suppression
failed fast, and broader transport changes remain risky. Keep this only as a
late diagnostic follow-up if centered vertical advection becomes the clearest
remaining failure mode.
