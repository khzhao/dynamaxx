---
schema_version: 1
slug: leith-nonlinear-eddy-viscosity
title: Flow-Dependent Leith Nonlinear Eddy Viscosity
status: staging
created_at: 2026-06-19T06:22:41Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/filtering.py
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

# Flow-Dependent Leith Nonlinear Eddy Viscosity

## Hypothesis

The incumbent dissipates exclusively with **flow-independent linear operators**:
scale-selective hyperdiffusion (order raised 2 -> 4 in
`scale-selective-hyperdiffusion`) plus the `exponential_filter` in
`filtering.py`. Both damp a fixed function of total wavenumber every step
regardless of the local flow state. That uniform damping is mistuned to the
actual synoptic enstrophy cascade: it over-damps coherent eddies in quiescent
regions while under-controlling grid-scale enstrophy production near sharp
gradients (fronts, jet exits). A **nonlinear Leith eddy viscosity**, in which
the diffusion coefficient scales with the local magnitude of the vorticity
gradient `|grad(zeta)|` (the resolved enstrophy-cascade rate), concentrates
dissipation only where the resolved enstrophy flux is large and relaxes it
elsewhere. This matches the `k^-3` enstrophy-cascade phenomenology of the
quasi-two-dimensional synoptic scale and should sharpen `geopotential_500` and
`mean_sea_level_pressure` structure at medium leads while still suppressing
near-truncation noise.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_leith_viscosity`.
Preserve incumbent initialization, DFI, weak-HS forcing, exact symmetric
Coriolis split, potential-temperature tendency, theta mean recentering,
stability-aware residual decay, Richardson 10 m wind diagnostic, output
variables, WeatherBench2 splits, lead times, metrics, and deterministic gates.

For the candidate only:

- each Runge-Kutta substep, transform relative vorticity `zeta` to the Gaussian
  grid and compute the grid-space gradient magnitude `|grad(zeta)|` using the
  existing spherical-harmonic spatial-derivative operators;
- form a bounded Leith viscosity field `nu_L = (C_L * dx)^3 * |grad(zeta)|`,
  where `dx` is the nominal grid spacing implied by the spectral truncation and
  `C_L` is a fixed dimensionless constant (start near `C_L = 1.0`), with an
  upper clip so `nu_L` never exceeds a fixed multiple of the incumbent linear
  hyperdiffusion coefficient at the truncation wavenumber;
- apply `nu_L` as a state-dependent Laplacian diffusion to vorticity,
  divergence, and temperature tendencies (transform the diffusive tendency back
  to spectral space and add it), so the operator damps where resolved enstrophy
  production is strong;
- **retain the incumbent linear hyperdiffusion and exponential filter as an
  unconditional floor** and add Leith viscosity as a bounded supplement, so
  near-truncation control never weakens and the candidate is a strict bounded
  perturbation of the incumbent dissipation;
- use the identical operator in DFI and positive-time rollout, because a
  state-dependent viscosity is a reversible numerical discretization choice, not
  an irreversible spinup or output correction;
- fall back to incumbent dissipation if `nu_L` produces nonfinite values or
  shape mismatches.

This is not a linear hyperdiffusion order change (`scale-selective-hyperdiffusion`),
not a linear mode-selective filter (`planetary-wave-preserving-horizontal-diffusion`,
staged), not the exponential dealiasing filter
(`nonlinear-tendency-exponential-dealiasing`), and not a divergence-only damping
(`divergence-selective-gravity-wave-damping`). It is a fundamentally different,
**state-dependent** dissipation paradigm.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py` (Leith viscosity helper)
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` (apply in
    tendency assembly)
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
  - Unit-test the Leith operator on synthetic vorticity fields: zero viscosity
    for a solid-body-rotation (constant-gradient) field of low amplitude,
    positive viscosity concentrated at a synthetic front, and the upper clip
    enforced.
  - Verify the linear hyperdiffusion/exponential-filter floor is still applied.
  - Verify the candidate factory preserves every incumbent setting except the
    added viscosity.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 3-10 if reduced
    spurious damping of coherent synoptic eddies sharpens the balanced flow.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind`, which are dominated by the
    accepted surface diagnostics and forcing rather than free-atmosphere
    enstrophy dissipation.
  - Day-1 fields, which are initial-condition dominated.
- Possible regressions:
  - If the incumbent linear hyperdiffusion is already near-optimal, the added
    viscosity is neutral or slightly over-dissipative.
  - State-dependent viscosity can add grid-scale noise if `C_L` is too large or
    the clip too high, degrading early Z500/MSLP guardrails.

## Risks

- Numerical stability:
  - Moderate. State-dependent viscosity can stiffen the explicit step; the fixed
    upper clip and the retained linear floor bound the worst case, and the
    finite-fallback guards nonfinite output.
- Compute cost:
  - Low-to-moderate. Adds one vorticity-gradient evaluation and one extra
    grid<->spectral transform pair per substep; no change to resolution, lead
    count, output volume, or worker count.
- Data leakage:
  - None. Uses only forecast vorticity, spectral grid geometry, and fixed
    constants.
- Physical plausibility:
  - High. Leith viscosity is an established large-eddy closure for
    quasi-two-dimensional and atmospheric flows.
- Rollback complexity:
  - Low. Remove one filter helper, one tendency hook, one factory/export, one
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_leith_viscosity`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_leith_viscosity --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` with
    clean diagnostics and no early-lead or variable-by-lead RMSE guardrail
    failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_leith_viscosity --workers 4`
    only after iteration promotion; require validation primary delta at least
    `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the incumbent
    linear dissipation is not over-damping synoptic eddies and that flow-aware
    viscosity adds no skill. An early Z500/MSLP guardrail failure would show the
    added viscosity injects grid-scale noise.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/filtering.py`
    implements `exponential_filter`; the IMEX SIL3 stepper applies linear
    hyperdiffusion after each Runge-Kutta step.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion`
    raised the linear diffusion order 2 -> 4 but kept flow-independent damping;
    this proposal makes the coefficient flow-dependent instead.
  - Leith, C. E. 1996. Stochastic models of chaotic systems. Physica D.
    https://doi.org/10.1016/0167-2789(96)00107-8
  - Leith, C. E. 1971. Atmospheric predictability and two-dimensional
    turbulence. Journal of the Atmospheric Sciences.
    https://doi.org/10.1175/1520-0469(1971)028%3C0145:APATDT%3E2.0.CO;2
  - Smagorinsky, J. 1963. General circulation experiments with the primitive
    equations. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1963)091%3C0099:GCEWTP%3E2.3.CO;2

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-19; recorded
here for provenance honesty in the autonomous loop.

This is distinct from every prior dissipation idea because the coefficient is
**state-dependent**: `scale-selective-hyperdiffusion` (history) only changed the
linear order, `planetary-wave-preserving-horizontal-diffusion` (staging) is a
linear mode-selective kernel, `nonlinear-tendency-exponential-dealiasing`
(history) is a fixed spectral dealiasing filter, and
`divergence-selective-gravity-wave-damping` (history) damps only divergence with
a fixed coefficient. None make the viscosity scale with the resolved vorticity
gradient. The incumbent linear dissipation is retained as a floor so the change
is a bounded, reversible supplement rather than a replacement.

## Evaluator Notes

### 2026-06-19T06:48:12Z

Decision: move to `staging`.

The proposal is scientifically credible and distinct from the earlier fixed
linear diffusion changes: a Leith closure is a real state-dependent
enstrophy-cascade mechanism, and retaining the incumbent hyperdiffusion/filter
floor makes the candidate bounded rather than a replacement of the stabilizing
path. It is also implementable in principle using the existing spectral/nodal
operators and side-by-side registry pattern.

Do not promote it to `ready` now. The scored dissipation family has negative
local evidence: scale-selective hyperdiffusion regressed strongly, symmetric
horizontal diffusion split was clean but slightly negative, and explicit
divergence gravity-wave damping was clean but negative. This candidate is more
mechanistic than those, but it also adds extra vorticity-gradient work and an
explicit state-dependent viscosity each substep, which could over-damp the
already accepted theta-recentered incumbent or spend the remaining late-wind
guardrail margin. Keep it staged as a later closure experiment if cheaper
mass-balance and time-discretization ideas fail.
