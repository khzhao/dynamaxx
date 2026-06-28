---
schema_version: 1
slug: baroclinic-shear-selective-hyperdiffusion
title: Baroclinic Shear Selective Hyperdiffusion
status: scrap
created_at: 2026-06-23T14:35:50Z
author_role: Researcher
target_model: dino_hsl2_theta_dse_hsl
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/filtering.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Baroclinic Shear Selective Hyperdiffusion

## Hypothesis

The accepted DSE-HSL thermodynamic transport improves broad scalar structure,
but small-scale vertically sheared wind noise can still project onto MSLP,
geopotential, and the 10 m wind diagnostic. A filter that damps only high
wavenumber baroclinic shear, while preserving the vertical barotropic wind and
low planetary modes, should reduce noisy shear-driven tendencies with less
large-scale phase damage than uniform momentum diffusion.

## Mechanism

Create an opt-in step filter that converts vorticity/divergence to nodal winds,
computes a pressure- or sigma-weighted vertical mean wind, subtracts that mean
to obtain baroclinic shear winds, applies high-order horizontal diffusion only
to the shear component above a selected total-wavenumber cutoff, then recombines
the untouched barotropic component with the filtered shear. Convert the
recombined winds back to vorticity/divergence and leave temperature,
log-surface pressure, and tracers unchanged. If the wind transform or filtered
state is nonfinite, return the unfiltered step result.

## Implementation Scope

- Expected files: `adapter.py` for a
  `_baroclinic_shear_hyperdiffusion_step_filter`; `filtering.py` only if an
  existing modal filter helper cannot express the cutoff cleanly; `__init__.py`
  and `registry.py` for a side-by-side alias such as `dino_hsl2_bcshear`.
- Registry changes: add one factory derived from
  `dry_static_energy_hsl_transport_dinosaur_dycore_model()` with an
  `apply_baroclinic_shear_hyperdiffusion` boolean.
- API changes: none.
- Tests to update: add tests proving a vertically uniform wind is preserved,
  high-wavenumber vertically sheared wind is damped, non-wind state leaves are
  unchanged, and nonfinite filtered diagnostics fall back to the incumbent
  state.

## Expected Metric Movement

- Expected improvements: `mean_sea_level_pressure` and
  `10m_u_component_of_wind` at medium leads from reduced noisy low-level
  convergence and less grid-scale shear.
- Expected neutral metrics: large-scale `geopotential_500` should be preserved
  by leaving the barotropic wind and low modes untouched.
- Possible regressions: too much baroclinic damping could weaken baroclinic
  wave growth and degrade Z500 or MSLP amplitude after day 5.

## Risks

- Numerical stability: repeated wind transform/filter/inverse operations must
  preserve finite modal shapes and not inject polar artifacts.
- Compute cost: extra wind transform and filtering per inner step; higher than
  scalar-only proposals but still bounded and suitable for `--workers 4` if the
  filter is implemented with existing spectral utilities.
- Data leakage: none; all calculations use the model state.
- Physical plausibility: selective shear damping is a numerical closure, not a
  physical turbulence parameterization; coefficients and cutoffs should be weak
  and scale-selective.
- Rollback complexity: low if implemented as an optional step filter.

## Evaluation Plan

- Fast gate: run `uv run pytest` and
  `uv run dynamaxx-eval fast --model dino_hsl2_bcshear`; reject on nonfinite
  fast forecasts or slowdowns that exceed normal HSL runtime by a large margin.
- Iteration gate: run
  `uv run dynamaxx-eval iteration --model dino_hsl2_bcshear --workers 4` and
  inspect both primary score and Z500/MSLP guardrails.
- Validation gate: run
  `uv run dynamaxx-eval validation --model dino_hsl2_bcshear --workers 4` only
  after fixed iteration promotion.
- Outcome that would falsify the hypothesis: no primary-score gain, or Z500
  amplitude regression indicating the filter damps resolved baroclinic waves
  rather than only noisy shear.

## Citations

- Smagorinsky, J. (1963), "General Circulation Experiments with the Primitive
  Equations. I. The Basic Experiment," Monthly Weather Review, 91, 99-164,
  https://doi.org/10.1175/1520-0493(1963)091<0099:GCEWTP>2.3.CO;2.
- Jablonowski, C. and Williamson, D. L. (2006), "A Baroclinic Instability Test
  Case for Atmospheric Model Dynamical Cores," Quarterly Journal of the Royal
  Meteorological Society, 132, 2943-2975, https://doi.org/10.1256/qj.06.12.
- Boer, G. J. and Shepherd, T. G. (1983), "Large-Scale Two-Dimensional
  Turbulence in the Atmosphere," Journal of the Atmospheric Sciences, 40,
  164-184, https://doi.org/10.1175/1520-0469(1983)040<0164:LSTDTI>2.0.CO;2.
- Local code reference:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py`, existing
  `_horizontal_diffusion_step_filter` and step-filter composition.

## Researcher Notes

This is not another HSL trajectory variant and does not modify thermal
pressure-work. Earlier broad diffusion and divergence-damping attempts give
negative evidence against indiscriminate damping; this proposal is narrower
because it preserves vertically coherent barotropic flow and low modes while
targeting only high-wavenumber vertical shear. It is decorrelated from the
moist-static-energy proposal and from lower-boundary surface stress because it
is a numerical spectral/vertical-structure filter rather than a thermodynamic
transport or physical surface-flux closure.

## Evaluator Notes

### 2026-06-23T14:38:43Z

Decision: move to `scrap`.

The proposal is not vague, but its cost-risk balance is unfavorable under the
current incumbent and history. It sits in the same broad family as momentum
diffusion, selective damping, and vertical-mode filtering ideas, where local
evidence has been mostly neutral or negative: Helmholtz-projected momentum
diffusion was clean but effectively neutral, broad diffusion changes have
shown wind or guardrail risk, and multiple active staged ideas already cover
more grounded state-dependent or vertically targeted damping mechanisms.

The implementation surface is also larger than its expected signal. It would
need reliable wind reconstruction, vertical barotropic/baroclinic splitting,
mode-selective filtering, recombination, and inverse wind-to-vorticity/
divergence transforms every step, with finite fallback that may make the
candidate hard to interpret if the filter only activates in a subset of states.
The main expected gains are `mean_sea_level_pressure` and
`10m_u_component_of_wind`, but the same damping could weaken resolved
baroclinic wave growth and degrade `geopotential_500`.

Scrapping this proposal keeps the ready/staging set focused. If future scoring
establishes a specific high-wavenumber vertical-shear pathology that survives
the staged Leith, deformation-rate, and boundary-layer momentum proposals, a
new proposal should be written around that diagnostic rather than reviving this
general filter.
