---
schema_version: 1
slug: high-wavenumber-implicit-offcenter-filter
title: Apply Off-Centering Only to High-Wavenumber Implicit Modes
status: scrap
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

# Apply Off-Centering Only to High-Wavenumber Implicit Modes

## Hypothesis

The accepted incumbent benefits from fixed semi-implicit off-centering, while
the recent full CN-RK3 replacement was strongly negative. That suggests the
current SIL3 path and its gravity-wave damping are important, but uniform
off-centering may damp balanced planetary and synoptic modes that help
`mean_sea_level_pressure` and `geopotential_500`. A modal filter that applies
the accepted off-centering mainly to high total wavenumbers could retain
small-scale gravity-wave damping while leaving large-scale balanced flow closer
to the centered SIL3 phase behavior.

## Mechanism

Keep the existing offcentered SIL3 solver and all incumbent model physics, but
wrap the accepted step in a modal blend with a centered SIL3 step:

1. Build both the incumbent offcentered SIL3 step and the centered SIL3 step for
   the same composed equation and filters.
2. For prognostic modal fields, blend low total wavenumbers from the centered
   step and high total wavenumbers from the offcentered step using a smooth
   total-wavenumber taper, for example fully centered through total wavenumber
   8 and fully offcentered by total wavenumber 20.
3. Apply the blend to `vorticity`, `divergence`, `temperature_variation`, and
   `log_surface_pressure`; apply the incumbent offcentered state to tracers or
   use the same taper if tracer modal shapes match cleanly.
4. Preserve existing post-step filters, symmetric Coriolis split behavior, DFI,
   theta mean recentering, residual correction, Richardson wind diagnostic, and
   analysis-offset HS equilibrium.
5. Guard the blended state with the same nonfinite fallback style already used
   in `time_integration.py`.

Register a side-by-side candidate whose name appends
`_highk_si_offcenter` to the incumbent.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` if the blend is
    cleaner as a reusable guarded step helper
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/`
- Registry changes:
  - Add one model factory and registry key for the high-wavenumber-only
    offcentering candidate.
- API changes:
  - None.
- Tests to update:
  - Unit-test the modal taper shape and low/high wavenumber endpoints.
  - Unit-test that a finite centered/offcentered pair yields a finite blended
    state and that nonfinite candidate fields fall back safely.
  - Add a factory/registry test confirming all incumbent physical options remain
    unchanged.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium and long leads if
    large-scale balanced modes are currently over-damped by uniform
    off-centering.
  - Possible secondary `10m_u_component_of_wind` gains through better synoptic
    pressure-gradient evolution.
- Expected neutral metrics:
  - `2m_temperature` should remain close because the surface residual and
    weak-HS equilibrium are unchanged.
  - Fast diagnostics should remain clean if high-wavenumber gravity damping is
    preserved.
- Possible regressions:
  - Centering low modes may reintroduce slow gravity-mode ringing that the
    incumbent off-centering suppresses.
  - Running two step variants per inner step increases arithmetic and may expose
    differences in filter ordering if implemented too broadly.

## Risks

- Numerical stability:
  - Moderate. It intentionally reduces damping for low wavenumbers, so fast and
    iteration diagnostics must be treated as hard gates.
- Compute cost:
  - Moderate. A naive implementation doubles the SIL3 step work. This remains
    model-selection feasible but should be scoped carefully.
- Data leakage:
  - Low. The change uses no future information and no evaluation metadata.
- Physical plausibility:
  - Moderate. Semi-implicit off-centering is commonly used to control fast-wave
    noise; scale-selective damping is plausible because high wavenumbers carry
    the most numerically problematic gravity-wave energy.
- Rollback complexity:
  - Low to moderate. It can be isolated behind one adapter option and removed
    without changing fixed protocols or source data.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_name>`.
  - Require finite outputs and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_name> --workers 4`.
  - Support requires primary delta at least `+0.002` versus the cached
    incumbent iteration baseline `-0.5150627015910243` and clean RMSE guardrails.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` versus
    `-0.5044433981077879`.
- Outcome that would falsify the hypothesis:
  - Fast instability, any early guardrail failure, or a negative primary delta
    like the full CN-RK3 replacement would show that broad incumbent
    off-centering is still needed for all resolved scales.

## Citations

- Hoskins, B. J., and Simmons, A. J. 1975. "A multi-layer spectral model and
  the semi-implicit method." Quarterly Journal of the Royal Meteorological
  Society, 101, 637-655. https://doi.org/10.1002/qj.49710142918
- Giraldo, F. X. 2005. "Semi-implicit time-integrators for a scalable spectral
  element atmospheric model." Quarterly Journal of the Royal Meteorological
  Society, 131, 2431-2454. https://doi.org/10.1256/qj.03.218
- Durran, D. R. 2010. "Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics." Springer. https://doi.org/10.1007/978-1-4419-6412-0
- ECMWF. 2023. "IFS Documentation CY48R1, Part III: Dynamics and numerical
  procedures." https://www.ecmwf.int/en/elibrary/81369-ifs-documentation-cy48r1-part-iii-dynamics-and-numerical-procedures
- Source context: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements the current offcentered IMEX SIL3 machinery, and
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` selects it through the
  incumbent `semi_implicit_offcentering` flag.

## Researcher Notes

This is not a solver replacement like the rejected `williamson-cn-rk3-rollout`;
it retains the accepted SIL3 route and changes only which horizontal scales get
offcentered damping. It is also not another analysis-HS mask, residual decay, or
surface-wind diagnostic proposal. It is closest to the staged
`divergence-selective-offcentering`, but the selection axis is horizontal scale
rather than variable type, motivated by preserving large-scale balanced modes
while damping high-wavenumber fast waves.

## Evaluator Notes

### 2026-06-21T02:45:40Z

Decision: move to `scrap`.

This is not the right next experiment under the current evidence. Although it
keeps the SIL3 family, the mechanism effectively reintroduces centered
low-wavenumber positive-time evolution by blending two solver outcomes, which
partly removes the accepted off-centering from the large scales that currently
anchor the incumbent. The accepted offcentered SIL3 change produced a large
validated gain, while the recent `williamson-cn-rk3-rollout` solver replacement
was strongly negative despite clean diagnostics. The staged
`divergence-selective-offcentering` audit also found that simple selective
off-centering may be near-noop or require broader implicit-block surgery than
advertised.

The implementation surface is too large for the expected signal: running both a
centered and offcentered step per inner step roughly doubles step work, adds
modal blending/fallback complexity across prognostic leaves, and risks slow
gravity-mode ringing or phase changes in MSLP/Z500. This violates the current
preference for small, reversible candidates compatible with fixed fast,
iteration, and validation gates. Future off-centering work should first produce
a precise low-cost non-noop formulation or diagnostic evidence that uniform
low-wavenumber off-centering is harming the incumbent.
