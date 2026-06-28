---
schema_version: 1
slug: balanced-wind-increment-limiter
title: Limit Extreme One-Step Wind Increments While Preserving Large-Scale Flow
status: scrap
created_at: 2026-06-21T00:30:15Z
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

# Limit Extreme One-Step Wind Increments While Preserving Large-Scale Flow

## Hypothesis

Several broad wind-control families have weak or negative evidence: simple
diffusion, rollout filters, pressure-gradient/dealiasing, and surface wind
diagnostics have either failed guardrails or produced subthreshold gains. Those
results argue against adding another always-on damping tendency or output-only
wind correction. A narrower alternative is an a posteriori limiter that acts
only on extreme gridpoint wind increments after one accepted step, while
preserving the area-mean vector increment and low-wavenumber flow.

If rare local momentum increments from nonlinear advection or pressure-gradient
imbalance seed later `10m_u_component_of_wind` and Z500 errors, a bounded
increment limiter can improve robustness without changing the accepted
off-centered fast-mode treatment, analysis-HS forcing, near-surface residuals,
or fixed evaluation contract.

## Mechanism

Add a side-by-side candidate with a suffix such as `_wind_increment_limiter`.
Preserve every incumbent option and add one positive-time post-step limiter.

For the candidate only:

- after each accepted positive-time inner step, convert previous and candidate
  next-state vorticity/divergence to nodal horizontal wind;
- compute the one-step wind increment vector at each sigma level and gridpoint;
- split the increment into a low-wavenumber component and a residual component;
- preserve the low-wavenumber component exactly and limit only the residual
  vector magnitude using a broad fixed cap, for example the smaller of
  `3 * rms(residual_increment)` per level and `12 m/s` per `900 s` step after
  nondimensional conversion;
- preserve each level's area-mean wind increment before converting the corrected
  wind increment back to vorticity/divergence modal fields;
- leave temperature, log-surface-pressure, tracers, weak-HS forcing, theta mean
  recentering, Coriolis splitting, residual correction, and output diagnostics
  unchanged;
- no-op on nonfinite transforms, unexpected shapes, or failed inverse
  Helmholtz conversion.

This is not broad horizontal diffusion: coherent planetary and synoptic wind
increments are explicitly preserved, and only local residual one-step outliers
are limited.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory extending the incumbent name with
    `_wind_increment_limiter`.
- API changes:
  - None. Forecast inputs, outputs, lead times, variables, metrics, and splits
    stay fixed.
- Tests to update:
  - Verify sub-cap wind increments pass through exactly.
  - Verify extreme residual increments are bounded while low modes and area
    means are preserved.
  - Verify temperature, log-surface-pressure, tracers, and `sim_time` are
    unchanged by the limiter.
  - Verify finite fallback leaves incumbent vorticity/divergence unchanged when
    transforms fail or inputs are nonfinite.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at early and medium leads if local momentum
    spikes contaminate low-level wind evolution after the accepted Richardson
    diagnostic.
  - `geopotential_500` if cleaner rotational/divergent wind increments reduce
    downstream balanced mass-field error.
- Expected neutral metrics:
  - `2m_temperature` and `mean_sea_level_pressure` should remain close to
    incumbent because thermal and mass variables are not directly limited.
- Possible regressions:
  - Real rapidly deepening systems can require large local wind increments; a
    cap can suppress physically meaningful ageostrophic adjustment.
  - Correcting vorticity/divergence from limited nodal winds can introduce
    small imbalance with unchanged mass and thermal fields.

## Risks

- Numerical stability:
  - Moderate. The limiter is bounded and finite-guarded but modifies prognostic
    momentum after each step.
- Compute cost:
  - Moderate. It adds wind transforms and a low-mode split for each positive
    inner step, but no extra forecast leads or evaluations.
- Data leakage:
  - None. It uses only previous and next forecast states and fixed caps.
- Physical plausibility:
  - Moderate. Flux-corrected and monotonic limiting are standard for controlling
    local numerical extrema, but applying a limiter to vector wind increments is
    a pragmatic dycore safeguard rather than a first-principles parameterization.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show local wind
    increments are not a material remaining error source. Any early wind, Z500,
    or MSLP guardrail failure would show the limiter disrupts balanced dynamics.

## Citations

- Boris, J. P. and Book, D. L. 1973. Flux-corrected transport. I. SHASTA, a
  fluid transport algorithm that works. Journal of Computational Physics.
  https://doi.org/10.1016/0021-9991(73)90147-2
- Zalesak, S. T. 1979. Fully multidimensional flux-corrected transport
  algorithms for fluids. Journal of Computational Physics.
  https://doi.org/10.1016/0021-9991(79)90051-2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Dynamaxx history:
  `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected broad diffusion after early 10 m wind degradation, so this proposal
  preserves low modes and acts only on one-step residual increments.
- Dynamaxx history:
  `.logbook/history/2026-06-20_17-12-34_gradient-wind-surface-diagnostic/decision.md`
  rejected an output-only surface wind diagnostic after an early wind guardrail
  failure, so this proposal targets prognostic momentum outliers rather than
  changing the 10 m diagnostic.

## Researcher Notes

This is deliberately not a pressure-gradient/dealiasing proposal and not a
surface-wind diagnostic. It is an a posteriori local increment limiter with
large-scale preservation. The Evaluator should treat the broad damping history
as negative evidence and only stage this if the one-step residual mechanism is
considered materially different enough to justify a bounded implementation.

## Evaluator Notes

### 2026-06-21T00:35:34Z

Decision: move to `scrap`.

The proposal is narrower than broad diffusion because it preserves low modes
and area-mean wind increments, but it remains an a posteriori momentum limiter
applied after every positive-time step. The cap values are empirical, the
Helmholtz round trip adds substantial transform and balance risk, and limiting
only momentum while leaving pressure, temperature, and mass fields unchanged
can create the same kind of balanced-flow disruption that the proposal is
trying to avoid.

The negative and duplicate evidence is strong. Scale-selective hyperdiffusion
regressed primary score by `-0.05124210065383061` and failed the early 10 m
wind guardrail; gradient-wind surface diagnostics also failed the early wind
guardrail; absolute-vorticity flux dealiasing and nonlinear tendency filtering
were clean but far below promotion. Active staging already contains cleaner
wind or momentum representatives: `richardson-momentum-mixing` tests a
physically interpretable conservative lower-column momentum redistribution,
`geostrophic-surface-wind-residual` is output-only and lower-risk, and
`vorticity-sparing-horizontal-diffusion` tests component-selective rotational
damping with a smaller implementation surface. This limiter is therefore not a
good use of a ready or staging slot.
