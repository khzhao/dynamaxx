---
schema_version: 1
slug: damped-courant-limited-vertical-momentum-transport
title: Damped Courant-Limited Vertical Momentum Transport
status: staging
created_at: 2026-06-30T01:45:03Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
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

# Damped Courant-Limited Vertical Momentum Transport

## Hypothesis

The recent `skew-adjoint-vertical-momentum-advection` candidate failed the fixed
fast gate with nonfinite forecasts even though its implementation had local
nonfinite tendency fallback. The failure argues that a purely skew-adjoint
vertical momentum operator can still inject excessive full-step wind energy
before diagnostics catch it. That does not rule out vertical momentum transport
as a missing process, but any follow-up must make boundedness and damping part
of the proposed operator rather than an after-the-fact rescue.

A Courant-limited blend between the incumbent centered vertical momentum
tendency and a first-order upwind diffusive tendency, with a kinetic-energy and
per-step wind-increment backstop, should test vertical momentum transport while
guaranteeing that the new part of the operator cannot create unbounded local
wind increments. The hypothesis is that a small amount of vertically consistent
momentum redistribution can improve `10m_u_component_of_wind` and balanced
pressure evolution if the previous fast failure was caused by missing damping,
not by the vertical transport idea itself.

## Mechanism

Register one side-by-side candidate such as `dino_ri2m_damped_vmom` derived from
`ekman_coupled_dinosaur_dycore_model()`. Preserve the accepted Ekman closure,
mass-DSE HSL, WTG, pressure-ramped vertical-DSE increment, T2m memory, RI2m
diagnostic, DFI, filters, output variables, and fixed protocols.

For the candidate only, add an opt-in vertical momentum tendency path inside
`PrimitiveEquationsSigma.curl_and_div_tendencies`:

- compute the incumbent centered vertical momentum tendencies for `u` and `v`;
- compute a same-shape first-order upwind vertical momentum tendency using the
  sign of `sigma_dot_full` and fixed no-flux top/bottom boundaries;
- pass the nondimensional inner-step length from the adapter into the equation
  option and diagnose a local vertical Courant number
  `C = abs(sigma_dot_full) * dt / max(delta_sigma, tiny)`;
- blend toward the upwind tendency only where `C` exceeds a conservative start
  threshold, for example zero blend below `C = 0.25` and full upwind by
  `C = 0.75`;
- apply an explicit per-step wind-increment cap, for example no more than
  `1.0 m s^-1` per 900 s inner step from this replacement tendency after unit
  conversion;
- compute nodal kinetic-energy change attributable to the candidate vertical
  term and no-op to the incumbent centered tendency wherever the candidate term
  would raise local column kinetic energy by more than a fixed small tolerance;
- fall back exactly to the incumbent centered vertical momentum tendency if any
  candidate tendency, Courant number, energy diagnostic, or projected wind
  increment is nonfinite.

This is not a repeat of the failed skew-adjoint proposal. The central design
property is dissipative boundedness: the upwind branch is monotone, the blend is
Courant-triggered, and the final candidate increment is capped before entering
the curl/divergence tendency. It also leaves scalar vertical-DSE transport and
thermal pressure work unchanged, so it is not another vertical-DSE ramp or WTG
timing variant.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side key such as `dino_ri2m_damped_vmom`.
- API changes:
  - None. The forecast input/output contract and fixed target variables remain
    unchanged.
- Tests to update:
  - Unit-test the vertical Courant blend: centered below the lower threshold,
    upwind above the upper threshold, and smooth bounded interpolation between.
  - Verify no-flux top and bottom behavior for synthetic `sigma_dot_full`.
  - Verify per-step wind-increment caps in SI units after nondimensional unit
    conversion.
  - Verify the kinetic-energy backstop no-ops to the incumbent centered
    tendency when the candidate term is locally energy-increasing beyond the
    tolerance.
  - Verify nonfinite candidate diagnostics fall back exactly to incumbent
    vertical momentum tendencies.
  - Verify the candidate factory preserves all `dino_ri2m_ekman_coupled` flags
    except the new damped vertical momentum selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` if lower-tropospheric vertical momentum exchange
    is a remaining missing process after the accepted Ekman closure.
  - `mean_sea_level_pressure` and `geopotential_500` if bounded vertical
    momentum transport reduces spurious shear-driven convergence without
    destabilizing the pressure-gradient balance.
- Expected neutral metrics:
  - `2m_temperature`, because no T2m memory, RI2m diagnostic, vertical-DSE
    scalar transport, WTG, or thermal forcing branch is changed directly.
- Possible regressions:
  - Added vertical momentum diffusion may overdamp baroclinic shear and weaken
    synoptic development.
  - If the failed skew-adjoint result reflects a deeper incompatibility between
    vertical momentum transport and this sigma-grid rollout, even the damped
    path may be clean but score-negative.

## Risks

- Numerical stability:
  - Moderate. This touches core momentum tendencies, but the proposal includes
    explicit Courant damping, per-step wind-increment caps, kinetic-energy
    no-op fallback, and finite guards to address the previous nonfinite fast
    failure.
- Compute cost:
  - Low to moderate. It adds local vertical finite differences, Courant
    diagnostics, and reductions; no new forecast outputs or model-selection
    protocols are required.
- Data leakage:
  - None. It uses only current forecast-state winds, `sigma_dot_full`, sigma
    geometry, fixed constants, and the fixed inner-step length.
- Physical plausibility:
  - Moderate. Upwinded vertical momentum transport is more dissipative than a
    centered or skew-adjoint discretization, but the damping is physically
    interpretable as unresolved vertical shear mixing under large vertical
    Courant stress.
- Rollback complexity:
  - Medium. The equation option must be isolated in `primitive_equations.py`,
    threaded through the adapter, and registered as one side-by-side model.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_damped_vmom`.
  - Require finite forecasts and zero diagnostic issues. Any nonfinite fast
    output is a direct falsification because boundedness is the main design
    claim.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_damped_vmom --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    incumbent iteration primary `-0.16500618979404214`, clean diagnostics, and
    no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_damped_vmom --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` against cached incumbent
    validation primary `-0.16591150807771451` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - Any fast nonfinite failure would show the boundedness argument is
    insufficient. A clean negative or subthreshold iteration delta would show
    damped vertical momentum transport is not a material improvement over the
    accepted incumbent. Early U10, MSLP, or Z500 guardrail failure would show
    the damping damages balanced shear or pressure evolution.

## Citations

- Lin, S.-J. and Rood, R. B. 1996. "Multidimensional Flux-Form
  Semi-Lagrangian Transport Schemes." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Thuburn, J. 1996. "Multidimensional Flux-Limited Advection Schemes." Journal
  of Computational Physics. https://doi.org/10.1006/jcph.1996.0006
- Simmons, A. J. and Burridge, D. M. 1981. "An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates."
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to
  Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Local negative evidence:
  `.logbook/history/2026-06-30_01-05-36_skew-adjoint-vertical-momentum-advection/decision.md`
  rejected the prior vertical momentum advection candidate after fast diagnostics
  reported `nonfinite_forecast` and `nonfinite_metric`.
- Local negative evidence:
  `.logbook/history/2026-06-27_14-55-51_boundary-layer-sheltered-vertical-dse/decision.md`
  showed that suppressing accepted lower-column vertical-DSE behavior damaged
  T2m; this proposal leaves vertical-DSE scalar transport unchanged.
- Local positive evidence:
  `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/decision.md`
  accepted the current surface-stress incumbent, so this proposal preserves that
  closure and only tests a bounded core-momentum transport change.

## Researcher Notes

This proposal deliberately accounts for the most recent fast failure. The old
skew-adjoint candidate had a local nonfinite tendency fallback but no global
boundedness or damping guarantee; this proposal makes the bounded, dissipative
branch the experiment. It is still a higher-risk idea than a diagnostic-only
candidate, so the fast gate should be treated as decisive.

It is distinct from staged vertical-DSE and WTG variants because it does not
change scalar thermal redistribution, pressure-ramped vertical-DSE increments,
or WTG relaxation. It is also distinct from staged `vertical-courant-limited-advection`
if that proposal targets scalar or broad vertical advection generally; this one
is momentum-only, Courant-triggered, and includes a kinetic-energy no-op
backstop specifically motivated by the failed skew-adjoint momentum run.

## Evaluator Notes

### 2026-06-30T01:48:49Z

Decision: move to `staging`; plausible bounded follow-up, but not ready after
the latest vertical-momentum failure.

The proposal correctly reacts to the rejected
`skew-adjoint-vertical-momentum-advection` candidate: boundedness and damping
are built into the experiment instead of being added after a nonfinite fast
failure. First-order upwind transport under a Courant constraint is a standard
stabilizing numerical pattern, and the explicit wind-increment cap plus finite
fallback make this stronger than the failed skew-adjoint proposal's local
nonfinite tendency fallback.

Do not promote it now. The recent local evidence is sharply negative for
prognostic vertical momentum transport: `momentum-only-sl-vertical-advection`
became nonfinite during iteration, and the latest skew-adjoint vertical momentum
candidate failed the fast gate with `nonfinite_forecast` and
`nonfinite_metric`. This proposal touches
`PrimitiveEquationsSigma.curl_and_div_tendencies`, so any local boundedness
claim must survive curl/div projection, spectral truncation, pressure-gradient
coupling, and the full fixed rollout. A nodal per-step cap and local
kinetic-energy no-op reduce risk, but they are not a full proof that the modal
state update cannot seed later nonfinite pressure or wind growth.

It is also lower priority than the single ready Ekman mass-neutral proposal.
That candidate changes one projection invariant inside an accepted high-signal
closure; this one changes core momentum tendencies and overlaps the broader
staged vertical-numerics family, including `vertical-courant-limited-advection`,
`upwind-vertical-advection-rollout`, and lower-column momentum-mixing ideas.

Keep staged because the boundedness argument is materially better than the
failed skew-adjoint run and the mechanism is not an exact duplicate of scalar
vertical-Courant limiting. Promotion would require either exhaustion of lower
risk ready ideas or new diagnostics showing vertical momentum transport is a
dominant remaining U10/MSLP/Z500 error source. Before promotion, the proposal
should specify how the per-step cap is measured after nondimensional unit
conversion, how the kinetic-energy no-op is applied without creating shape or
projection inconsistencies, and what exact test demonstrates incumbent-equivalent
fallback when any candidate diagnostic is nonfinite.
