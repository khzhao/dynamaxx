---
schema_version: 1
slug: offcentered-semi-implicit-gravity-wave
title: Off-Centered Semi-Implicit Gravity-Wave Treatment
status: ready
created_at: 2026-06-19T06:23:10Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
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

# Off-Centered Semi-Implicit Gravity-Wave Treatment

## Hypothesis

The incumbent integrates the linear gravity-wave and geopotential terms with a
**centered** Crank-Nicolson semi-implicit average (the
`crank_nicolson` / IMEX path in `time_integration.py`, equivalent to an implicit
weight of `0.5`). A centered average is neutrally stable for the fast
gravity-inertia modes: it neither grows nor damps them. Imbalance injected by
initialization, weak-HS forcing, and the surface diagnostics therefore radiates
as long-lived spurious gravity waves that add noise to the mass field
(`mean_sea_level_pressure`, `geopotential_500`). **Off-centering** the implicit
average toward the future state (implicit weight `0.5 + epsilon`) introduces a
controlled, frequency-selective `O(dt)` damping that preferentially attenuates
the fastest gravity modes while leaving the slow balanced Rossby modes nearly
untouched. This is the standard ECMWF/IFS decentering technique and should
reduce mass-field noise and improve early-to-medium balance without adding a
separate explicit filter.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter`.
Preserve incumbent initialization, DFI, weak-HS forcing, exact symmetric
Coriolis split, horizontal diffusion, potential-temperature tendency, theta mean
recentering, stability-aware residual decay, Richardson 10 m wind diagnostic,
output variables, WeatherBench2 splits, lead times, metrics, and deterministic
gates.

For the candidate only:

- expose a fixed off-centering parameter `epsilon` on the semi-implicit /
  Crank-Nicolson treatment of the **linear implicit operator only** (the
  gravity-wave and geopotential terms solved by `implicit_inverse`), so the
  implicit average uses weight `0.5 + epsilon` on the future state and
  `0.5 - epsilon` on the current state;
- start with a small `epsilon = 0.05` (well inside the stable, weakly damping
  regime) and keep it fixed across the rollout;
- leave the explicit advective and forcing terms, the Runge-Kutta tableau, the
  inner step length, hyperdiffusion, and the exponential filter unchanged;
- apply the identical off-centered solve in DFI and positive-time rollout,
  because decentering is a property of the time discretization, not an
  irreversible spinup or output correction;
- fall back to the centered (`epsilon = 0`) solve if the off-centered solve
  produces nonfinite values.

This changes only **how the existing implicit linear modes are time-averaged**.
It is not a new explicit divergence diffusion
(`divergence-selective-gravity-wave-damping`, history), not a change of
Runge-Kutta order (`fourth-order-imex-rk-rollout`, staging), not a change of
inner step length (`six-hundred-second-inner-step`, history), and not an
initialization filter (`balanced-digital-filter-initialization`, history) -- it
suppresses imbalance generated *throughout* the rollout, not only at `t = 0`.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` (off-centering
    weight on the implicit solve)
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` (thread the
    parameter into the equation's implicit treatment if needed)
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input/output/target variables, lead times,
    splits, metrics, and deterministic gates are unchanged.
- Tests to update:
  - Unit-test that `epsilon = 0` exactly reproduces the incumbent centered step
    (bit-for-bit or within float tolerance).
  - Unit-test on a linear gravity-wave eigenproblem that `epsilon > 0` damps a
    fast mode while a slow mode is nearly preserved.
  - Verify the candidate factory preserves every incumbent setting except the
    off-centering weight.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 1-7 if spurious
    gravity-wave noise is a real component of mass-field error.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind`, governed by the accepted
    surface diagnostics rather than fast-mode balance.
- Possible regressions:
  - If DFI already removes most imbalance, the change is neutral.
  - Too-large `epsilon` damps balanced amplitude and degrades medium-lead Z500.

## Risks

- Numerical stability:
  - Improves. Decentering adds damping to the fastest modes and cannot
    destabilize a stable centered scheme for small positive `epsilon`.
- Compute cost:
  - Negligible. It is a coefficient change inside the existing implicit solve;
    no extra transforms, resolution, lead count, or worker changes.
- Data leakage:
  - None. Uses only the model state and a fixed numerical constant.
- Physical plausibility:
  - High. Off-centered semi-implicit integration is a long-standing operational
    technique for controlling gravity-wave noise.
- Rollback complexity:
  - Trivial. Set `epsilon = 0` or remove the candidate factory and registry
    entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` with
    clean diagnostics and no early-lead or variable-by-lead RMSE guardrail
    failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter --workers 4`
    only after iteration promotion; require validation primary delta at least
    `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that gravity-wave
    noise is not a material remaining mass-field error source given the accepted
    DFI, or that the balanced modes are sensitive enough that any decentering
    that helps the fast modes also costs balanced-mode accuracy.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
    implements `crank_nicolson_rk*` / `imex_runge_kutta`; the semi-implicit
    average of the linear implicit operator is centered.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_19-57-46_divergence-selective-gravity-wave-damping`
    added an explicit divergence damping; this proposal instead off-centers the
    implicit solve, a distinct mechanism that also acts during the rollout.
  - Simmons, A. J. and Temperton, C. 1997. Stability of a two-time-level
    semi-implicit integration scheme for gravity-wave motion. Monthly Weather
    Review.
    https://doi.org/10.1175/1520-0493(1997)125%3C0600:SOATTL%3E2.0.CO;2
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics, 2nd ed. Springer
    (semi-implicit off-centering and gravity-wave damping).
    https://doi.org/10.1007/978-1-4419-6412-0
  - ECMWF IFS Documentation, Part III: Dynamics and Numerical Procedures
    (decentering of the semi-implicit scheme).
    https://www.ecmwf.int/en/publications/ifs-documentation

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-19; recorded
here for provenance honesty in the autonomous loop.

This is distinct from the prior gravity-wave and time-stepping ideas: it is not
the explicit divergence damping of `divergence-selective-gravity-wave-damping`
(history), not a Runge-Kutta order change like `fourth-order-imex-rk-rollout`
(staging) or `two-thirds-explicit-tendency-dealiasing` (staging), and not an
inner-step length change like `six-hundred-second-inner-step` (history). Unlike
`balanced-digital-filter-initialization` (history), which removes imbalance only
at initialization, off-centering damps unbalanced fast modes that are
continuously regenerated by forcing and the surface diagnostics during the
forecast. The `epsilon = 0` reproduction test makes the change auditable as a
strict generalization of the incumbent scheme.

## Evaluator Notes

### 2026-06-19T06:48:12Z

Decision: move to `ready`; ranked 1 among ready proposals.

This is the strongest next experiment among the new proposals. The mechanism is
standard, low-cost fast-mode control, and it targets a plausible remaining
mass-field error source without changing initialization data, output
diagnostics, lead times, metrics, or the accepted surface/thermal corrections.
It is distinct from the rejected explicit divergence damping because it acts
through the existing semi-implicit linear solve throughout the rollout rather
than adding a separate modal damping tendency.

Source inspection shows the incumbent rollout uses the SIL3 IMEX path with
`implicit_terms` and `implicit_inverse`, so the implementer must express the
off-centering against that actual implicit pathway and keep the `epsilon = 0`
path exactly incumbent-equivalent. With that constraint, the implementation
surface is small and rollback is clean. The main risk is a near-neutral result
if DFI already removes most fast-mode imbalance, or a Z500/MSLP regression if
the extra damping touches balanced amplitude, but the cost-risk tradeoff is
better than the other untriaged candidates.
