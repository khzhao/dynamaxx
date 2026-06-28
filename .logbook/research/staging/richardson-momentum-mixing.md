---
schema_version: 1
slug: richardson-momentum-mixing
title: Conservative Richardson-Gated Lower-Layer Momentum Mixing
status: staging
created_at: 2026-06-20T17:06:07Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
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

# Conservative Richardson-Gated Lower-Layer Momentum Mixing

## Hypothesis

The incumbent has a Richardson-number 10 m diagnostic, but its prognostic
low-level winds remain governed mostly by the dry primitive-equation dynamics
and numerical filtering. Recent rejected or staged boundary-layer ideas mostly
add drag, heat coupling, geostrophic residuals, or output diagnostics. Those
mechanisms can reduce kinetic energy or alter near-surface thermal budgets, and
prior surface-wind residual history shows that broad wind corrections can harm
short-lead 10 m wind.

A conservative vertical redistribution of horizontal momentum in only the
lowest few sigma layers targets a different error mode: excessive or misplaced
vertical shear near the surface. If the incumbent's late negative 10 m zonal
wind bias partly comes from keeping too much horizontal momentum above the
diagnostic layer, Richardson-gated mixing can move momentum downward in
unstable or weakly stable columns without adding a net column momentum sink.

## Mechanism

Register a side-by-side candidate with a suffix such as `_ri_momentum_mixing`.
Add an opt-in tendency or post-step filter that acts only on horizontal velocity
in the lowest model layers.

The mixing operator should:

- estimate bulk or layerwise Richardson number from the existing temperature,
  geopotential, and vertical wind-shear state;
- compute a nonnegative eddy diffusivity on layer interfaces, smoothly tapered
  to zero above the lower column and strongly reduced in very stable columns;
- apply vertical diffusion to `u` and `v` in flux-divergence form using
  sigma-layer mass weights, so the lower-column mass-weighted horizontal
  momentum is conserved up to explicit numerical tolerances;
- leave temperature, log surface pressure, humidity, DFI, weak-HS forcing, and
  surface residual memory unchanged;
- use a fixed cap on the implicit or explicit mixing Courant number, with a
  finite fallback to no mixing if a column has invalid static stability.

This is not a Rayleigh drag. It should redistribute shear within the lower
column rather than damping wind toward zero or toward a geostrophic target.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add a single opt-in model entry whose name appends
    `_ri_momentum_mixing` to the current incumbent.
- API changes:
  - None. Forecast inputs, outputs, lead times, and target variables stay fixed.
- Tests to update:
  - Unit-test that the operator is finite, damps vertical shear, preserves
    lower-column mass-weighted momentum, and shuts off in very stable columns.
  - Add a registry test for the new candidate.

## Expected Metric Movement

- Expected improvements:
  - Primary target is `10m_u_component_of_wind` at days 3-15 through improved
    low-level momentum placement.
  - Secondary possible gains in `mean_sea_level_pressure` and
    `geopotential_500` if reduced low-level shear noise improves balanced mass
    evolution.
- Expected neutral metrics:
  - `2m_temperature` should be near neutral because no heat or moisture tendency
    is introduced.
- Possible regressions:
  - Excess mixing could degrade day-1 wind or weaken synoptic jets, which would
    harm Z500 and MSLP. The lower-column taper and column-momentum conservation
    are essential safeguards.

## Risks

- Numerical stability:
  - Moderate. Explicit vertical diffusion can impose a tight stability limit, so
    the proposal should either use a tridiagonal implicit solve in the vertical
    column or cap the mixing coefficient so the existing time step remains safe.
- Compute cost:
  - Low to moderate. A column-local vertical operator is inexpensive relative to
    the spectral transforms and should be acceptable with 4 eval workers.
- Data leakage:
  - None. Richardson number and shear are computed only from the forecast state.
- Physical plausibility:
  - Moderate. Boundary-layer eddy diffusivity is standard, but this stripped
    version omits surface fluxes and heat/moisture mixing by design to avoid
    duplicating failed or staged thermal-drag variants.
- Rollback complexity:
  - Low. The change can be isolated behind a model flag and registry suffix.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
  - Require finite outputs and no obvious day-1 wind or pressure failure.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Support the hypothesis if 10 m wind skill improves enough to lift the
    primary score without a compensating 2 m temperature or Z500 regression.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4`.
  - Require validation primary to remain positive relative to the incumbent and
    the 10 m wind sign to match the iteration result.
- Outcome that would falsify the hypothesis:
  - Neutral or negative 10 m wind movement despite verified shear damping, or
    any broad Z500/MSLP degradation, would indicate that lower-column momentum
    redistribution is not the current limiting error.

## Citations

- Louis, J.-F. (1979). "A parametric model of vertical eddy fluxes in the
  atmosphere." Boundary-Layer Meteorology, 17, 187-202.
  https://doi.org/10.1007/BF00117978
- Holtslag, A. A. M., and Boville, B. A. (1993). "Local Versus Nonlocal
  Boundary-Layer Diffusion in a Global Climate Model." Journal of Climate, 6,
  1825-1842. https://doi.org/10.1175/1520-0442(1993)006%3C1825:LVNBLD%3E2.0.CO;2
- Beljaars, A. C. M., and Holtslag, A. A. M. (1991). "Flux Parameterization
  over Land Surfaces for Atmospheric Models." Journal of Applied Meteorology,
  30, 327-341. https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2

## Researcher Notes

This proposal is materially different from staged lower-boundary drag and
surface-heating ideas. It does not add Rayleigh drag, does not relax winds
toward geostrophic flow, and does not alter the 2 m temperature diagnostic.
It also avoids the rejected seasonal/layered surface residual-memory family:
there is no learned residual lifetime, no seasonal phase, and no direct target
variable correction. The negative evidence from broad wind residual corrections
is addressed by conserving lower-column momentum and acting only through
stability-gated vertical shear diffusion.

## Evaluator Notes

### 2026-06-20T17:10:51Z

Decision: move to `staging`.

The physical mechanism is plausible and distinct from staged Rayleigh-drag
ideas: it redistributes lower-column horizontal momentum through
Richardson-gated vertical shear diffusion rather than adding a net momentum
sink or output residual. Boundary-layer eddy diffusivity is standard enough that
the proposal should remain researchable, especially if later diagnostics show
excessive lower-column shear or a misplaced momentum maximum.

Do not make it the next ready idea. It changes prognostic vorticity/divergence
through a new lower-column vertical operator, needs either an implicit solve or
a strict mixing-Courant cap, and can perturb MSLP/Z500 even if column momentum
is conserved. It also sits in the active boundary-layer family with staged
`exponential-boundary-layer-rayleigh-drag`,
`geostrophic-sparing-boundary-layer-drag`, and
`surface-drag-theta-dissipation`; those should not all be promoted before
more isolated output-diagnostic wind ideas are exhausted.
