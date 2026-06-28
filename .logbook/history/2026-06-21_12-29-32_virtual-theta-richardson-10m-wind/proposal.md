---
schema_version: 1
slug: virtual-theta-richardson-10m-wind
title: Use Virtual Potential Temperature in the Richardson 10 m Wind Diagnostic
status: ready
created_at: 2026-06-21T12:19:53Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Virtual Potential Temperature in the Richardson 10 m Wind Diagnostic

## Hypothesis

The incumbent 10 m wind diagnostic already improves on the lowest-model-layer
wind by using a bounded lower-column Richardson number. That Richardson number
is currently dry: it computes static stability from dry potential temperature
even when passive humidity is available in the forecast trajectory. Boundary-
layer buoyancy and bulk Richardson diagnostics are usually based on virtual
potential temperature because water vapor changes density without requiring the
model to activate moist pressure-gradient dynamics.

Using bounded virtual potential temperature only inside the accepted 10 m wind
diagnostic may improve `10m_u_component_of_wind` in humid lower-tropospheric
columns while preserving the dry rollout, virtual-temperature geopotential
diagnostic, weak-HS forcing, residual memory, and all pressure/mass fields.

## Mechanism

Register one side-by-side candidate with a suffix such as `_virtual_ri_wind`.
Preserve all incumbent forecast settings and change only the optional
Richardson wind helper.

For this candidate only:

- pass sigma-level specific humidity from `dinosaur_state_to_weather_state` into
  `_surface_layer_richardson_10m_wind` when the humidity tracer is present;
- clip diagnostic humidity to a broad fixed range such as `[0.0, 0.04]` kg/kg
  before it is used, with exact dry fallback when humidity is absent or
  nonfinite;
- compute lower and upper virtual potential temperature as
  `theta_v = theta * (1 + (R_v/R_d - 1) * q)` using the same dry pressure
  estimates as the incumbent Richardson diagnostic;
- keep the incumbent layer-height, shear floor, Richardson clipping, neutral
  factor, wind-factor bounds, and finite fallback unchanged;
- leave `vorticity`, `divergence`, `temperature_variation`,
  `log_surface_pressure`, humidity tracer evolution, DFI, weak-HS forcing,
  pressure-level output interpolation, and surface residual correction
  unchanged.

This is not another active moist-dynamics proposal. Humidity remains passive in
the primitive-equation rollout and is used only to interpret lower-column
buoyancy in an output diagnostic that already exists in the incumbent.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate model name ending in `_virtual_ri_wind`.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, lead
    handling, and fixed protocols stay unchanged.
- Tests to update:
  - Verify absent humidity reproduces the incumbent Richardson diagnostic.
  - Verify finite humidity changes only the 10 m wind factor and respects the
    existing wind-factor bounds.
  - Verify humidity clipping and nonfinite fallback.
  - Verify non-wind output channels and the Dinosaur trajectory are unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast for the candidate.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at days 1 to 7 where dry static stability
    misclassifies humid low-level stratification.
  - Small secondary `2m_temperature` metric benefit is possible only through
    shared residual aggregation, not through trajectory changes.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500` should be neutral because
    mass, thickness, and pressure-level geopotential outputs stay on the
    incumbent path.
- Possible regressions:
  - The accepted dry Richardson diagnostic may already encode the best empirical
    wind scaling for this benchmark, and virtual stability could over-damp humid
    tropical low-level winds.

## Risks

- Numerical stability:
  - Low. The rollout state is unchanged and the diagnostic has bounded finite
    fallbacks.
- Compute cost:
  - Negligible. It adds local humidity algebra to an existing output helper.
- Data leakage:
  - None. It uses only same-lead forecast humidity already carried as a passive
    tracer from the initial state.
- Physical plausibility:
  - Good for a surface-layer diagnostic; virtual potential temperature is the
    standard buoyancy variable in moist boundary-layer stability.
- Rollback complexity:
  - Low. Remove one selector, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers <worker_count>`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 mean RMSE guardrail failure, and no
    variable-lead RMSE guardrail failure.
- Validation gate:
  - Run fixed `validation` only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A negative or subthreshold iteration delta, or any early
    `10m_u_component_of_wind` guardrail regression, would show that humidity is
    not a useful remaining ingredient for the accepted 10 m diagnostic.

## Citations

- Stull, R. B. 1988. An Introduction to Boundary Layer Meteorology. Kluwer
  Academic Publishers. Boundary-layer Richardson diagnostics are formulated
  using buoyancy variables closely related to virtual potential temperature.
- Garratt, J. R. 1992. The Atmospheric Boundary Layer. Cambridge University
  Press. Discusses bulk Richardson number and virtual-potential-temperature
  stability in the surface layer.
- Code reference: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_surface_layer_richardson_10m_wind` and already diagnoses sigma-layer
  humidity for geopotential output without enabling moist dynamics.

## Researcher Notes

This is distinct from rejected active moist virtual-temperature dynamics and
bounded saturation adjustment because it does not feed humidity back into
pressure gradients, temperature tendencies, or latent heating. It is also
distinct from staged `virtual-temperature-analysis-hs-offset`, which changes
the accepted weak-HS equilibrium anchor, and from wind-output residual ideas,
because this changes only the buoyancy variable inside the already accepted
Richardson diagnostic.

## Evaluator Notes

### 2026-06-21T12:28:02Z

Decision: move to `ready`; ranked first among the current proposals.

This is the best next model-selection candidate because it is output-only,
uses a standard boundary-layer stability variable, and changes only the
already accepted Richardson 10 m wind diagnostic. The original Richardson wind
diagnostic was a large accepted improvement, while later wind-diagnostic
variants show that broad or poorly gated corrections can fail early
`10m_u_component_of_wind` guardrails. This proposal is narrower than those
failures: it keeps the rollout, pressure, mass, thermal, residual, and
humidity-tracer dynamics unchanged, and uses clipped humidity only to compute
diagnostic virtual potential temperature.

The local evidence is not uniformly positive. `monotone-shear-10m-wind` was
clean but slightly negative, `gradient-wind-surface-diagnostic` failed the
early wind guardrail, and `ekman-inflow-10m-wind` was subthreshold. Humidity
evidence is also mixed: virtual-temperature geopotential diagnostics were
important, but passive-humidity DFI preservation was neutral and active moist
dynamics failed. Still, the implementation surface is small, rollback is easy,
and non-wind fields should remain incumbent-equivalent, so this is a
reasonable single ready item. The Implementer should fix humidity clipping,
fallbacks, and all wind-factor bounds before scoring; the Scorer should reuse
the valid cached incumbent metrics unless the cache is concretely invalid.
