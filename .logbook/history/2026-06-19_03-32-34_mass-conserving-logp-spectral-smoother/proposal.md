---
schema_version: 1
slug: mass-conserving-logp-spectral-smoother
title: Apply a Mass-Conserving Surface-Pressure Spectral Smoother
status: ready
created_at: 2026-06-19T03:26:40Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/filtering.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Apply a Mass-Conserving Surface-Pressure Spectral Smoother

## Hypothesis

The current incumbent has improved thermal balance through theta tendency and
theta mean recentering, but surface-pressure and geopotential errors can still
be amplified by small-scale `log_surface_pressure` noise feeding the
hydrostatic pressure-gradient term. A pure global pressure anchor was stable but
too weak, and a local flux-form continuity correction was cleanly negative. A
stronger but still conservative trajectory-level mechanism is to smooth only
the high-wavenumber component of `log_surface_pressure` while exactly
preserving global dry mass. This should reduce pressure-gradient noise without
targeting MSLP or Z500 outputs directly.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother`.
Preserve the incumbent DFI, weak Held-Suarez forcing, log-pressure and
hydrostatic layer initialization, exact symmetric Coriolis split, horizontal
diffusion, Richardson 10 m wind diagnostic, stability-aware residual decay,
theta tendency, theta mean recentering, emitted variables, WeatherBench2
splits, lead times, metrics, and deterministic gates.

For the candidate only, add a positive-time rollout state filter after the
existing dynamics and thermodynamic filters:

- transform only `log_surface_pressure` through its existing modal
  representation;
- leave the global and planetary-scale modes unchanged, for example total
  wavenumber `n <= 10`;
- apply a fixed smooth high-wavenumber taper to `log_surface_pressure`, with
  the incumbent field unchanged below the cutoff and a bounded damping ramp at
  smaller resolved scales;
- convert filtered and unfiltered `log_surface_pressure` to surface pressure
  and add one scalar log-pressure offset so the area-weighted global mean
  surface pressure after smoothing equals the pre-filter mean;
- cap the local surface-pressure change per inner step, for example to a fixed
  small fraction such as `0.25%`, and fall back to the incumbent next state if
  the mass correction, capped field, or modal transform is nonfinite;
- leave vorticity, divergence, temperature variation, tracers, `sim_time`,
  theta recentering, Coriolis rotation, residual correction, output packing,
  and pressure-level interpolation unchanged;
- keep the filter out of time-reversed DFI because this is a positive-time
  pressure-noise control rather than an initialization balance filter.

This is not an output residual, an MSLP reduction offset, a terrain correction,
or another zero-mode global pressure anchor. It changes the prognostic
surface-pressure trajectory only in nonplanetary modes while preserving total
surface-pressure mass.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, target
    variables, lead times, splits, metrics, and deterministic gates stay
    unchanged.
- Tests to update:
  - Unit-test the modal mask and verify protected low modes are exactly
    unchanged.
  - Unit-test area-weighted surface-pressure mass preservation after the scalar
    log offset.
  - Verify the cap bounds local surface-pressure change and finite fallback
    returns the incumbent state.
  - Verify only `log_surface_pressure` changes and vorticity, divergence,
    temperature variation, tracers, and `sim_time` are unchanged.
  - Verify DFI filters remain incumbent-only while positive-time rollout uses
    the candidate filter.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` from days 3 to 15 if
    high-wavenumber surface-pressure noise is degrading hydrostatic balance and
    pressure-gradient phase.
  - `10m_u_component_of_wind` may improve indirectly if pressure-gradient noise
    contributes to late low-level wind phase errors.
- Expected neutral metrics:
  - `2m_temperature` should stay close to incumbent because the thermal state,
    residual decay, and theta recentering are unchanged.
  - Day-1 behavior should be near incumbent because the filter is bounded and
    leaves low modes unchanged.
- Possible regressions:
  - The existing `log_surface_pressure` high modes may carry useful synoptic
    structure; smoothing them can damp pressure systems and worsen MSLP or wind
    phase.
  - Surface-pressure smoothing can indirectly perturb hydrostatic geopotential
    even if total mass is preserved.

## Risks

- Numerical stability:
  - Low to moderate. The filter is bounded and mass preserving, but it edits a
    prognostic pressure field every positive-time inner step.
- Compute cost:
  - Low. It reuses modal fields and simple reductions without changing
    resolution, lead count, output volume, or worker count.
- Data leakage:
  - None. The filter uses only forecast state, fixed spectral geometry,
    quadrature weights, and predeclared constants.
- Physical plausibility:
  - Moderate. Mass fixers and filters are common in dycores, and this variant
    preserves dry mass while damping pressure-gradient noise. The exact cutoff
    remains a modeling choice and must not be tuned after scores.
- Rollback complexity:
  - Low. Remove one filter option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that
    high-wavenumber surface-pressure noise is not a material remaining error
    source. Any early MSLP, Z500, or 10 m wind guardrail failure would show the
    pressure smoother disrupts balance.

## Citations

- Citation or source:
  - Dynamaxx history:
    `.logbook/history/2026-06-16_17-43-05_global-mean-pressure-anchor/decision.md`
    rejected a pure zero-mode pressure anchor with iteration delta
    `-0.000000944240674982666`, showing that pressure/mass ideas need a
    stronger mechanism than one global mode.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_11-53-08_flux-form-surface-pressure-continuity/decision.md`
    rejected a local continuity correction with iteration delta
    `-0.015126833559440334`, so this proposal does not replace the incumbent
    product-rule balance.
  - Dynamaxx source:
    `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` uses
    `log_surface_pressure` in the sigma-coordinate pressure-gradient and
    implicit terms.
  - ECMWF. Dry mass versus total mass conservation in the IFS.
    https://www.ecmwf.int/en/elibrary/81081-dry-mass-versus-total-mass-conservation-ifs
  - Jablonowski, C. and Williamson, D. L. 2011. The pros and cons of diffusion,
    filters and fixers in atmospheric general circulation models. In Numerical
    Techniques for Global Atmospheric Models.
    https://opensky.ucar.edu/islandora/object/books%3A271
  - Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP
    and climate models. Journal of Computational Physics.
    https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This proposal satisfies the mass/pressure/geopotential diversity requirement
without output-only MSLP or Z500 targeting. It is not a duplicate of
`mass-weighted-theta-recentering`, which changes the conserved theta moment,
and it is not a duplicate of `planetary-wave-preserving-horizontal-diffusion`,
which changes the all-state horizontal diffusion mask. It only smooths the
prognostic pressure field's high modes and then restores total surface-pressure
mass.

## Evaluator Notes

### 2026-06-19T03:31:24Z

Decision: `ready`.

This is the best next experiment among the new proposals. It is forecast-contract
preserving, side-by-side implementable, and clearly distinct from the rejected
global pressure anchor and local flux-form pressure-continuity correction: it
targets only nonplanetary `log_surface_pressure` modes and preserves total
surface-pressure mass with a scalar offset. The mechanism is not output-only
MSLP/Z500 tuning and has a plausible path to improving both MSLP and Z500 while
leaving the accepted theta recentering and Richardson 10 m diagnostic intact.

Risks remain moderate because the incumbent is already strong and pressure
filters can disrupt balanced pressure-gradient evolution. The Orchestrator
should predeclare the protected low-mode cutoff, high-mode taper, local
surface-pressure cap, and mass-preservation calculation before scoring; no
post-score tuning or validation-guided sweeps should be allowed.
