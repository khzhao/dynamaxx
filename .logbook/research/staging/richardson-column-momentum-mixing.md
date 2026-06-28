---
schema_version: 1
slug: richardson-column-momentum-mixing
title: Richardson-Gated Column-Conservative Momentum Mixing
status: staging
created_at: 2026-06-22T05:21:08Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Richardson-Gated Column-Conservative Momentum Mixing

## Hypothesis

The incumbent has no active boundary-layer momentum redistribution: the
weak-Held-Suarez path keeps the Rayleigh wind-drag coefficient at zero, and the
accepted Richardson 10 m wind improvement is diagnostic only. Recent output-wind
and residual-memory variants were clean but too weak or negative, suggesting
that remaining low-level wind error may require changing the rollout state.

A narrow vertical momentum-mixing filter can reduce excessive lower-column shear
without introducing a net surface momentum sink. By conserving the layer-mass
weighted column mean wind over the mixed lower layers, it should be less likely
than Rayleigh drag or geostrophic-sparing drag to disrupt large-scale pressure
and geopotential balance, while still changing the 10 m wind source state.

## Mechanism

Register a side-by-side candidate extending the incumbent with a
`_ri_column_momentum_mix` suffix. Preserve DFI, weak-HS analysis equilibrium,
Strang Coriolis split, theta tendency, theta mean recentering, semi-implicit
off-centering, horizontal diffusion, Richardson 10 m wind diagnostic,
scale-separated and land-sea near-surface residual corrections, output
variables, and fixed evaluation protocols.

Add an opt-in positive-time step filter after the incumbent dynamics and scalar
filters, before or inside the existing symmetric Coriolis wrapper:

- convert modal vorticity/divergence to nodal winds;
- diagnose lower-column potential-temperature stability and vertical wind shear
  from the lowest three sigma layers using the same dry-theta and pressure
  helpers already used by the theta and Richardson diagnostic paths;
- form a bounded bulk Richardson number for each adjacent lower-layer pair;
- when the column is near-neutral or weakly unstable, mix only the adjacent
  lower-layer winds with a small exact pairwise exchange coefficient;
- choose the pairwise update so the layer-thickness-weighted mean `u` and `v`
  over the affected layers is conserved exactly;
- apply no direct temperature tendency, no `log_surface_pressure` tendency, no
  surface drag, and no dissipative-heating return in the first candidate;
- convert the mixed winds back to vorticity/divergence and finite-fallback to
  the incumbent next state if any diagnostic is nonfinite.

The first implementation should mix at most the lowest two adjacent layer pairs,
use a fixed small per-step exchange cap, and be exactly no-op in stable columns.
That makes this smaller than the staged `richardson-momentum-mixing` idea and
decorrelated from staged net-drag and dissipative-heating proposals.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for the dataclass flag,
    filter helper, side-by-side factory, and export.
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` only if shared
    pressure/theta helper extraction is needed for clean tests.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` and
    `src/dynamaxx/dycore/registry.py` for registration.
  - Focused tests under `tests/dycore/models/dinosaur/` plus
    `tests/dycore/test_registry.py`.
- Registry changes:
  - Add one side-by-side model named
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ri_column_momentum_mix`.
- API changes:
  - None. Forecast inputs, outputs, lead times, target variables, and evaluation
    commands remain unchanged.
- Tests to update:
  - Verify stable-column no-op behavior.
  - Verify pairwise mixing conserves layer-thickness-weighted lower-column mean
    `u` and `v`.
  - Verify only vorticity/divergence change; temperature, log pressure, tracers,
    output variables, and residual helpers are unchanged.
  - Verify finite fallback on nonfinite wind, pressure, theta, or Richardson
    diagnostics.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and late leads if lower-column shear or
    under-mixed boundary-layer momentum is a remaining source of wind error.
  - `mean_sea_level_pressure` may improve modestly if reduced low-level shear
    noise reduces spurious convergence while preserving column momentum.
- Expected neutral metrics:
  - `2m_temperature` should remain close because thermal forcing, surface
    residuals, and output diagnostics are not changed.
  - `geopotential_500` should be near neutral under the lower-column confinement
    and momentum-conservative update.
- Possible regressions:
  - Mixing may weaken real low-level jets or frontal shear, degrading 10 m wind.
  - Even column-conservative wind redistribution can alter convergence and
    pressure evolution enough to hurt MSLP.

## Risks

- Numerical stability:
  - Moderate. The filter changes prognostic winds, but the pairwise exchange is
    bounded, column-conservative, and finite-guarded. The per-step coefficient
    must not overshoot or reverse shear in one step.
- Compute cost:
  - Low to moderate. It adds one wind transform pair and local lower-column
    algebra per inner step, acceptable under the reported 48 CPU and 172 GiB RAM
    budget with fixed `--workers 4`.
- Data leakage:
  - None. The filter uses only the forecast state, sigma geometry, and fixed
    constants.
- Physical plausibility:
  - Moderate to high. Richardson-number-gated turbulent momentum diffusion is a
    standard boundary-layer closure pattern, but this candidate is deliberately
    a reduced dry momentum-only test.
- Rollback complexity:
  - Low. Remove one flag, one filter helper, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ri_column_momentum_mix`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ri_column_momentum_mix --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no fixed RMSE guardrail failure, and no early `10m_u_component_of_wind`
    degradation that offsets later wind gains.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ri_column_momentum_mix --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` and clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show lower-column
    momentum redistribution is not a high-leverage remaining error source. Any
    MSLP/Z500 guardrail failure would show that even column-conservative mixing
    perturbs balanced flow too much.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` sets
    `DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY = 0.0`, so the accepted weak-HS path
    has no lower-layer Rayleigh wind damping.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` already
    contains the Richardson 10 m wind diagnostic and wind/vorticity-divergence
    transform path needed for a bounded lower-column momentum filter.
  - Dynamaxx history:
    `.logbook/history/2026-06-22_01-43-33_land-sea-wind-residual-memory/decision.md`
    rejected a clean output-only wind residual-memory change, motivating a
    rollout-level wind-state mechanism instead of another residual variant.
  - Dynamaxx history:
    `.logbook/history/2026-06-21_16-05-39_helmholtz-projected-momentum-diffusion/decision.md`
    found a vector-projected momentum diffusion change effectively neutral; this
    proposal changes the physical trigger to lower-column stability and shear.
  - Louis, J. F. 1979. "A parametric model of vertical eddy fluxes in the
    atmosphere." Boundary-Layer Meteorology, 17, 187-202.
    https://doi.org/10.1007/BF00117978
  - Holtslag, A. A. M. and Boville, B. A. 1993. "Local versus nonlocal
    boundary-layer diffusion in a global climate model." Journal of Climate, 6,
    1825-1842.
    https://doi.org/10.1175/1520-0442(1993)006%3C1825:LVNBLD%3E2.0.CO;2
  - Held, I. M. and Suarez, M. J. 1994. "A proposal for the intercomparison of
    the dynamical cores of atmospheric general circulation models." Bulletin of
    the American Meteorological Society, 75, 1825-1830.
    https://www.gfdl.noaa.gov/bibliography/related_files/ih9401.pdf

## Researcher Notes

This is a specific smaller refinement of staged `richardson-momentum-mixing`.
It limits the first test to pairwise lower-layer momentum exchange, exact
lower-column mean-wind conservation, stable-column no-op behavior, and no heat,
mass, or surface-drag tendency. It is not a duplicate of staged
`exponential-boundary-layer-rayleigh-drag` or
`geostrophic-sparing-boundary-layer-drag` because it adds no net momentum sink.
It is also not another generic residual-memory variant, and it leaves the fixed
forecast contract, target variables, worker counts, and validation promotion
rules unchanged.

## Evaluator Notes

### 2026-06-22T05:25:51Z

Decision: move to `staging`; ranked 2 of 2 fresh proposals.

The scientific basis is plausible but not enough for immediate `ready`.
Boundary-layer literature supports turbulent mixing of momentum, heat, moisture,
and scalars, and Holtslag and Boville 1993 describe local eddy diffusivity in
global models based on vertical gradients of wind and virtual potential
temperature. Louis 1979 likewise supports static-stability-dependent vertical
eddy fluxes in forecast models. Those sources support Richardson/stability-gated
mixing as a general closure family, but they do not specifically validate this
reduced, dry, pairwise, momentum-only post-step filter.

Stage rather than promote because local evidence for new prognostic wind filters
is weak. The accepted Richardson 10 m wind diagnostic was a major output-side
win, but follow-up Richardson and wind-residual variants were clean and negative,
and the recent Helmholtz-projected momentum diffusion experiment was effectively
neutral. This proposal is narrower and better specified than staged
`richardson-momentum-mixing`, but it still changes prognostic vorticity and
divergence through wind transforms and lower-column redistribution. Conserving
the lower-column mean wind does not guarantee neutral convergence, MSLP, or Z500
behavior under the fixed gates.

Keep this as the preferred refined version of the Richardson momentum-mixing
family if later diagnostics show a clear lower-column shear error or if safer
thermal ideas are exhausted. Orchestrator concern: the existing broader staged
`richardson-momentum-mixing` overlaps heavily; consolidate or retire one before
selecting this family for implementation.
