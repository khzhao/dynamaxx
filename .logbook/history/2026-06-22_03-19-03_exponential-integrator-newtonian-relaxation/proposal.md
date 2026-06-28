---
schema_version: 1
slug: exponential-integrator-newtonian-relaxation
title: Exact Exponential Integration of the Stiff Newtonian Relaxation Forcing
status: ready
created_at: 2026-06-22T02:01:10Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/held_suarez.py
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
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

# Exact Exponential Integration of the Stiff Newtonian Relaxation Forcing

## Hypothesis

The Held-Suarez forcing -- thermal relaxation `dT/dt = -kt*(T - Teq)` and
Rayleigh drag `dV/dt = -kv*V` -- is currently evaluated as an **explicit**
tendency in `HeldSuarezForcing.explicit_terms` and advanced by the explicit
partition of the IMEX Runge-Kutta stepper. Near the surface these are the
stiffest local terms (`ks = 1/4 day`, plus boundary-layer Rayleigh drag), and an
explicit update of a stiff linear relaxation is both less accurate and
stability-limited: it can only relax a bounded fraction per step and introduces
an `O(dt)` phase/amplitude error in the forced approach to equilibrium. But these
terms are **linear, local, and exactly integrable**: over a step the solution is
`T(t+dt) = Teq + (T - Teq) * exp(-kt*dt)` and `V(t+dt) = V * exp(-kv*dt)`.
Replacing the explicit relaxation update with this exact exponential
(Lie-split) integrator removes the discretization error and the stiffness
constraint, letting the near-surface temperature settle onto its
(analysis-offset) equilibrium accurately each step. Because the accepted
analysis-offset equilibrium is now a *good* target, integrating the approach to
it more exactly should sharpen `2m_temperature` and tighten the thermal field
generally.

## Mechanism

Register a side-by-side candidate named `..._landsea_surface_exprelax`. Preserve
every incumbent setting; change only **how the existing forcing terms are
time-integrated**, not their coefficients or targets.

- Split the Held-Suarez relaxation/drag out of the explicit RK tendency and
  apply it as an exact exponential (Lie/Strang) sub-step around the dynamics
  update: temperature toward `Teq` with factor `exp(-kt*dt)`, momentum with
  `exp(-kv*dt)`, using the incumbent `kt`, `kv`, and equilibrium (including the
  accepted analysis offset and land-sea diagnostic untouched).
- Use a symmetric Strang arrangement (half relaxation, dynamics, half relaxation)
  so the splitting stays second-order in time, consistent with the incumbent
  scheme order.
- Keep `Teq`, `kt`, `kv`, the off-centered semi-implicit gravity-wave solve,
  hyperdiffusion, initialization, DFI, and all diagnostics unchanged.
- Provide an exactness/consistency test: in the limit `kt*dt -> 0` the
  exponential update reproduces the incumbent explicit tendency to first order
  (bridge to the current behavior).
- Apply identically in DFI and positive-time rollout; fall back to the explicit
  treatment if the exponential update is nonfinite.

This is a **numerical discretization / stability** change, the category
RESEARCHER.md favors, and is distinct from every prior idea: the accepted
`offcentered-semi-implicit-gravity-wave` changed the implicit *gravity-wave*
solve (not the forcing); `six-hundred-second-inner-step` changed the step length;
the RK-order and dealiasing ideas changed the explicit dynamics integrator. None
changed how the stiff linear *relaxation forcing* is integrated. It is not
hyperparameter tuning: the coefficients and equilibrium are unchanged; only the
time-integration of those terms changes from explicit to exact-exponential.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/held_suarez.py` (expose an exact
    exponential update for the relaxation/drag terms);
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` /
    `adapter.py` (compose the Strang relaxation sub-step around the existing
    stepper);
  - `__init__.py`, `registry.py`, tests under `tests/dycore/`.
- Registry changes: add only the side-by-side candidate named above.
- API changes: none.
- Tests to update:
  - exact-relaxation update reproduces the analytic solution `Teq + (T-Teq)e^{-kt dt}`
    on a single linear column;
  - small-`kt*dt` limit matches the incumbent explicit tendency to first order;
  - equilibrium, coefficients, and all non-forcing terms are unchanged;
  - Strang symmetry preserves second-order accuracy on a manufactured solution;
  - nonfinite fallback reproduces the incumbent;
  - registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements: `2m_temperature` and the broader thermal field at all
  leads, from accurate (rather than `O(dt)`-biased) approach to the
  analysis-offset equilibrium near the surface where relaxation is stiffest.
- Expected neutral metrics: `geopotential_500`, `mean_sea_level_pressure`,
  `10m_u_component_of_wind` should move little, though drag exactness may slightly
  affect near-surface winds.
- Possible regressions: if the explicit treatment was already accurate at the
  inner step length, the change is neutral; an interaction between the Strang
  forcing split and the off-centered gravity-wave solve could marginally shift the
  mass field.

## Risks

- Numerical stability: improves. Exact exponential relaxation is unconditionally
  stable for the linear terms and removes their explicit stability constraint.
- Compute cost: negligible. Two elementwise `exp` evaluations per step; no extra
  transforms, resolution, leads, or workers.
- Data leakage: none. Uses only the model state and existing coefficients.
- Physical plausibility: high. Exact/exponential integration of linear
  relaxation is a standard operator-splitting technique.
- Rollback complexity: low. Restore the explicit forcing tendency.

## Evaluation Plan

- Fast gate: `uv run pytest`; `uv run dynamaxx-eval fast --model ..._exprelax`;
  finite forecasts, zero diagnostic issues.
- Iteration gate: `uv run dynamaxx-eval iteration --model ..._exprelax --workers 4`;
  support is primary-score delta at least `+0.002`, clean diagnostics, no
  guardrail failure.
- Validation gate: `uv run dynamaxx-eval validation --model ..._exprelax --workers 4`
  only after iteration promotion; require validation delta at least `+0.001`.
- Falsification: a clean near-zero iteration delta would show the explicit
  forcing update was already accurate enough at the current step length, so the
  near-surface temperature error is set by the equilibrium target, not its
  time-integration.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
    integrates `-kt*(T-Teq)` and `-kv*V` explicitly; `time_integration.py`
    provides the IMEX Runge-Kutta / Crank-Nicolson stepper this would split around.
  - Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
    dynamical cores of atmospheric general circulation models. BAMS.
    https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
  - Hochbruck, M. and Ostermann, A. 2010. Exponential integrators. Acta Numerica.
    https://doi.org/10.1017/S0962492910000048
  - Strang, G. 1968. On the construction and comparison of difference schemes.
    SIAM Journal on Numerical Analysis (operator splitting).
    https://doi.org/10.1137/0705041

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-22, paired with
`bulk-surface-sensible-heat-flux` as the orthogonal second lever. This one is a
pure numerical-method change (explicit -> exact exponential) to the stiffest
forcing terms, with very low implementation surface and improved stability -- the
profile the Evaluator has consistently favored. It is decorrelated from the
surface-flux proposal (numerical integration vs new physical process) and from all
212 prior ideas, none of which touch the time-integration of the Newtonian
relaxation. The small-`kt*dt` consistency test makes it auditable as a strict
generalization of the incumbent forcing.

## Evaluator Notes

### 2026-06-22T03:17:44Z

Decision: move to `ready`, ranked 1 of 2 fresh proposals.

This is the strongest next model-selection candidate. It is a local numerical
change to the existing accepted Held-Suarez relaxation/drag terms, not a new
forecast contract, evaluation-support change, diagnostic post-processing tweak,
or coefficient sweep. Repository inspection confirms the forcing is currently
composed through `HeldSuarezForcingSigma.explicit_terms`, while the adapter
already has step-filter and Strang-style composition hooks from prior accepted
work. That makes the proposal implementable as a side-by-side candidate with
focused tests and a clean rollback path.

The scientific claim is supported. Held-Suarez forcing is a Newtonian cooling
and lower-boundary Rayleigh-friction benchmark family, and CESM/OpenIFS
documentation describes that simplified relaxation/drag structure. Hochbruck and
Ostermann 2010 review exponential integrators for stiff systems and the exact
treatment of linear parts (`https://doi.org/10.1017/S0962492910000048`), which
matches the proposal's linear local relaxation terms. Exact exponential
relaxation should be unconditionally stable for these terms and should reduce
time-discretization error without changing equilibrium targets.

Risk is still present: if the current inner step already resolves the weak-HS
rates well enough, the measured delta may be near zero, and splitting around the
off-centered semi-implicit solve could slightly perturb MSLP/Z500. That risk is
acceptable for a `ready` experiment because the mechanism is auditable, bounded
to existing terms, compatible with the incumbent API, and likely to yield a clear
lesson even on failure. Run only the fixed gates listed in the protocol: pytest,
fast, iteration with `--workers 4`, and validation with `--workers 4` only if
iteration promotes. Do not use `golden`.
