---
schema_version: 1
slug: vector-wind-pchip-sigma-init
title: Shape-Preserving Vector-Wind Sigma Initialization
status: ready
created_at: 2026-06-21T02:42:06Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Shape-Preserving Vector-Wind Sigma Initialization

## Hypothesis

The incumbent initializes pressure-level winds onto sigma layers with the
accepted log-pressure interpolation, then converts the interpolated vector wind
to vorticity and divergence. This is stable, but pointwise linear interpolation
can create low-level wind overshoots or flatten sharp shear near jets and the
boundary layer. The accepted Richardson 10 m wind diagnostic and the recent
gradient-wind failure both show that the fixed score is sensitive to low-level
wind structure, so a narrower wind-initialization change may improve
`10m_u_component_of_wind` without disturbing the accepted thermal, residual, and
analysis-HS machinery.

## Mechanism

Add an optional wind-only pressure-to-sigma initializer that uses a
monotonicity-preserving cubic Hermite interpolation in log-pressure for
`u_component_of_wind` and `v_component_of_wind`. Apply it after the existing
hydrostatic layer-mean temperature initialization and surface-pressure handling,
but before the spherical-harmonic `uv_nodal_to_vor_div_modal` transform.

The helper should be conservative in scope:

- use the current linear log-pressure remap for temperature, humidity, and all
  pressure/surface fields
- use shape-preserving slopes separately for u and v in each column
- bound the interpolated vector speed by the local min/max speed envelope of the
  bracketing pressure levels, with a small finite tolerance
- fall back to the incumbent wind interpolation for columns with nonfinite data
  or fewer than three usable pressure levels
- preserve DFI, theta tendency, theta mean recentering, offcentered SIL3,
  scale-separated surface residuals, and analysis-offset HS equilibrium

Register a side-by-side candidate whose name appends `_vector_wind_pchip_init`
to the current incumbent.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/`
- Registry changes:
  - Add one candidate factory and one registry entry for the incumbent plus
    wind-only PCHIP initialization.
- API changes:
  - None. Inputs, outputs, target variables, leads, metrics, and protocol names
    remain fixed.
- Tests to update:
  - Unit-test monotone wind-profile interpolation, vector-speed envelope
    limiting, finite fallback behavior, and exact preservation of constant wind.
  - Add registry/factory tests confirming only the new wind initialization flag
    changes relative to the incumbent.
  - Add a non-JIT finite smoke forecast if existing Dinosaur fixtures support it.

## Expected Metric Movement

- Expected improvements:
  - Early to medium-lead `10m_u_component_of_wind`, especially if low-level
    shear aliasing is a remaining source of wind error.
  - Small secondary gains in `mean_sea_level_pressure` and `geopotential_500` if
    cleaner initial divergent wind reduces adjustment before or during DFI.
- Expected neutral metrics:
  - `2m_temperature` should remain near the incumbent because thermal
    initialization, weak-HS equilibrium, residual correction, and output
    diagnostics are unchanged.
- Possible regressions:
  - Wind RMSE can regress if the current linear remap is compensating another
    low-level diagnostic bias.
  - Shape-preserving component interpolation may slightly rotate sheared vector
    winds unless the speed limiter and finite fallback are carefully tested.

## Risks

- Numerical stability:
  - Low to moderate. The change is initialization-only but alters the initial
    vorticity/divergence partition.
- Compute cost:
  - Low. Extra column interpolation work is only at initialization.
- Data leakage:
  - Low. Uses only same-time pressure-level wind inputs already consumed by the
    incumbent.
- Physical plausibility:
  - Moderate. Shape-preserving interpolation is standard for avoiding spurious
    oscillations, but pressure-level winds are point samples rather than layer
    means.
- Rollback complexity:
  - Low. One adapter option, one interpolation helper, one factory, and focused
    tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_name>`.
  - Require finite outputs and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_name> --workers 4`.
  - Support requires primary delta at least `+0.002` versus the cached incumbent
    baseline `-0.5150627015910243`, with clean fixed guardrails.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_name> --workers 4`
    only after iteration promotion.
  - Support requires validation delta at least `+0.001` versus the cached
    validation baseline `-0.5044433981077879`.
- Outcome that would falsify the hypothesis:
  - A clean but subthreshold iteration delta, or any early `10m_u_component_of_wind`
    guardrail regression, would indicate that vertical wind interpolation is not
    a meaningful remaining error source for this incumbent.

## Citations

- Hyman, J. M. 1983. "Accurate Monotonicity Preserving Cubic Interpolation."
  SIAM Journal on Scientific and Statistical Computing, 4(4), 645-654.
  https://doi.org/10.1137/0904045
- Lauritzen, P. H., Nair, R. D., and Ullrich, P. A. 2010. "A conservative
  semi-Lagrangian multi-tracer transport scheme (CSLAM) on the cubed-sphere
  grid." Journal of Computational Physics, 229, 1401-1424.
  https://doi.org/10.1016/j.jcp.2009.10.036
- Held, I. M., and Suarez, M. J. 1994. "A Proposal for the Intercomparison of
  the Dynamical Cores of Atmospheric General Circulation Models." Bulletin of
  the American Meteorological Society, 75, 1825-1830.
  https://doi.org/10.1175/1520-0477(1994)075<1825:APFTIO>2.0.CO;2
- Source context: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  initializes winds through pressure-to-sigma interpolation followed by a
  spherical-harmonic vorticity/divergence transform.

## Researcher Notes

This is not a duplicate of `shape-preserving-logp-sigma-initialization` because
it is wind-only and keeps all scalar initialization unchanged. It is not a
duplicate of `helmholtz-wind-initialization` because it still initializes from
vector winds and targets vertical interpolation overshoot, not pressure-level
vorticity/divergence remapping. It avoids the recent failed 10 m wind diagnostic
family by changing only the model initial wind state, not the output diagnostic.

## Evaluator Notes

### 2026-06-21T02:45:40Z

Decision: move to `ready`; ranked 1 of current model-selection candidates.

This is the best next experiment because it is narrow, reversible, and
mechanistically distinct from the recent failed families. It keeps the accepted
analysis-HS equilibrium, weak-HS rates, residual memory, offcentered SIL3
rollout, target variables, lead range, metrics, and cached incumbent comparison
unchanged. Unlike the recent `gradient-wind-surface-diagnostic` failure, it does
not activate a new day-1 output wind diagnostic; it changes only the initial
vertical wind interpolation before the existing vorticity/divergence transform.

It also supersedes the staged all-field
`shape-preserving-logp-sigma-initialization` for the next run. The broad staged
version changes temperature, wind, and humidity initialization together, while
this proposal isolates the wind interpolation signal that can plausibly affect
the remaining `10m_u_component_of_wind` error with less exposure to early T2m,
MSLP, or Z500 guardrails. The implementation must keep the speed-envelope
limiter and finite fallback tests tight so component-wise PCHIP does not rotate
or amplify low-level shear.
