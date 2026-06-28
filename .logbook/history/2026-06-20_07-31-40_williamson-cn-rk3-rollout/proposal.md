---
schema_version: 1
slug: williamson-cn-rk3-rollout
title: "Use Williamson CN-RK3 for Positive-Time Rollout"
status: ready
created_at: 2026-06-20T07:20:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
  - src/dynamaxx/dycore/registry.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - tests/dycore/models/dinosaur/test_registry.py
  - tests/dycore/models/dinosaur/test_dependency.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

## Hypothesis

The incumbent uses the accepted offcentered SIL3 semi-implicit solver for both
digital-filter initialization and positive-time rollout. A lower-storage
Crank-Nicolson RK3 positive-time rollout may reduce phase and amplitude error
in balanced synoptic modes without changing the forecast contract, target
variables, lead ranges, metrics, or learned parameters.

This is intentionally distinct from the staged `fourth-order-imex-rk-rollout`
idea: it uses the already-present `crank_nicolson_rk3` implementation rather
than a fourth-order scheme, keeps the 900 s inner step, and should remain within
the current worker and runtime policy.

## Mechanism

Add an adapter option such as `rollout_time_integrator: str = "sil3"` while
leaving the DFI solver unchanged. For the proposed model variant:

1. Keep incumbent initialization, hydrostatic layer initialization, exact/Strang
   Coriolis handling, theta tendency, theta recentering, scale-separated surface
   residual, and Richardson 10 m diagnostic unchanged.
2. Continue to run DFI with the incumbent offcentered SIL3 path so the accepted
   initialization behavior is preserved.
3. Use `time_integration.crank_nicolson_rk3` only for positive-time rollout.
4. Reuse the incumbent filter chain and pass the same physics, implicit terms,
   and explicit terms through the existing `trajectory_from_step` path.
5. Register a model named
   `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_cn_rk3_rollout`.

The implementation should avoid new numerical kernels unless a thin selector in
`adapter.py` is needed to choose between `imex_rk_sil3` and the existing
`crank_nicolson_rk3` routine.

## Implementation Scope

- Add a rollout solver selector to `DinosaurPrimitiveEquationsDycoreModel`.
- In `_trajectory_function`, choose the positive-time `ode_solver` from the
  selector while keeping the DFI integration path on incumbent SIL3.
- Add a factory based on `scale_separated_surface_residual_dinosaur_dycore_model`
  that sets the selector to `crank_nicolson_rk3` and updates `name`.
- Export and register the factory.
- Add focused tests that the registry resolves the new model and that the DFI
  path still constructs separately from the rollout solver.

No source-data preparation, fixed evaluation protocol, forecast API, target
variable, lead range, metric, or ensemble contract should change.

## Expected Metric Movement

- Most likely gains: `geopotential_500`, `mean_sea_level_pressure`, and
  large-scale `10m_wind_speed` through smaller low-mode phase drift.
- Possible secondary gains: `2m_temperature` if improved balanced wave timing
  keeps the accepted surface residual correction better aligned with the
  evolving circulation.
- Expected size: small to moderate. This is a numerical-time-discretization
  refinement, not a new physical correction.

## Risks

- The staged `fourth-order-imex-rk-rollout` covers a nearby solver-family
  direction, so the implementation must remain clearly cheaper and lower order.
- Solver swaps can shift all variables, including the fragile `2m_temperature`
  guardrail.
- Prior `six-hundred-second-inner-step` evidence suggests that pure time-step
  changes can be weak or negative; this proposal changes the integration
  stencil at fixed step rather than changing cadence.
- If CN-RK3 weakens the incumbent offcentered gravity-wave damping, fast
  diagnostics may look clean while iteration score remains subthreshold.

## Evaluation Plan

1. Fast protocol: run the standard import, registry, and focused dycore tests
   only; do not change any evaluation protocol files.
2. Iteration protocol: evaluate the registered candidate against the current
   incumbent cache at commit `ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6`.
3. Validation protocol: run only if the iteration score clears the incumbent
   promotion threshold and no variable guardrail fails.
4. Inspect per-variable movement, with special attention to
   `2m_temperature`, `mean_sea_level_pressure`, and `geopotential_500`.

## Citations

- Source reference:
  `src/dynamaxx/dycore/models/dinosaur/time_integration.py` already contains
  `crank_nicolson_rk3`, `imex_rk_sil3`, and DFI utilities.
- Source reference:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently wires the
  accepted offcentered SIL3 solver through `_trajectory_function`.
- History reference:
  accepted `offcentered-semi-implicit-gravity-wave` and accepted
  `scale-separated-surface-residual-memory` show that numerics and rollout
  alignment can move validation metrics materially.
- History reference:
  staged `fourth-order-imex-rk-rollout` is related but higher cost and higher
  order; this proposal is a distinct RK3 selector using existing code.
- Whitaker, J. S. and S. K. Kar, 2013:
  "Implicit-Explicit Runge-Kutta Methods for Fast-Slow Wave Problems."
  Monthly Weather Review. DOI: 10.1175/MWR-D-13-00132.1.
- Williamson, J. H., 1980:
  "Low-storage Runge-Kutta schemes." Journal of Computational Physics.
  DOI: 10.1016/0021-9991(80)90033-9.
- ECMWF, 2023:
  IFS Documentation CY48R1, Part III, "Dynamics and numerical procedures,"
  for operational context on semi-implicit primitive-equation integration.

## Researcher Notes

This proposal deliberately avoids product dealiasing, residual memory, pressure
remapping, and time-ramp ideas with recent negative or staged evidence. It is a
single numerical selector with a narrow implementation surface and no training
cost.

## Evaluator Notes

### 2026-06-20T07:21:19Z

Decision: move to `ready`; ranked 1 of 1 ready ideas from this batch.

Source inspection confirms `time_integration.crank_nicolson_rk3` already exists
and the adapter currently routes one `_ode_solver()` through both positive-time
rollout and DFI. The proposal is therefore implementable as a small side-by-side
adapter selector: keep DFI on the incumbent off-centered SIL3 path, use CN-RK3
only for the scored positive-time rollout, preserve the accepted Strang
Coriolis, theta recentering, weak-HS, and scale-separated residual settings,
and avoid new numerical kernels.

This is related to staged `fourth-order-imex-rk-rollout`, but it is narrower
and cheaper: it uses an existing three-stage CN/RK routine and leaves DFI
unchanged. The main risk is that the accepted off-centered SIL3 improvement was
large and likely came from positive-time fast-mode damping; CN-RK3 has no
equivalent off-centering knob in the current source. That makes the expected
gain uncertain, but the implementation surface is small, the candidate is
cleanly reversible, and it tests whether residual positive-time phase/amplitude
error remains after the accepted off-centered incumbent. Ready is capped at one
idea, so this is the recommended next implementation if the Orchestrator wants
to continue immediately.
