---
schema_version: 1
slug: equatorial-gravity-wave-divergence-sponge
title: Add a Weak Equatorial Gravity-Wave Divergence Sponge
status: staging
created_at: 2026-06-20T19:03:48Z
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

# Add a Weak Equatorial Gravity-Wave Divergence Sponge

## Hypothesis

The accepted off-centered semi-implicit solver and exact Coriolis split control
global fast modes, but tropical equatorial waves can still project onto
divergence and log-surface-pressure errors that affect MSLP, Z500, and
near-surface temperature after several days. Prior broad divergence damping and
vertical normal-mode filtering were unattractive because they acted too widely
or had high implementation cost. A weak, equatorially confined, high-zonal-mode
divergence/log-pressure sponge may target unresolved equatorial gravity-wave
noise while preserving extratropical Rossby dynamics, vorticity, theta
transport, weak-HS forcing, surface residuals, and wind output diagnostics.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_eq_wave_sponge`.
Preserve all incumbent initialization, forcing, time stepping, diagnostics, and
evaluation protocols. Add a positive-time-only filter after the normal dynamics
step and existing horizontal diffusion:

- build a smooth equatorial latitude taper that is one inside about 8 degrees
  latitude and zero outside about 20 degrees, with no discontinuity at the
  taper edges;
- transform divergence and log-surface-pressure increments to nodal space,
  multiply by the taper, transform back to modal space, and keep only
  high-zonal or high-total wavenumbers associated with short equatorial
  gravity-wave structure;
- damp only the selected divergence and log-surface-pressure modes with a weak
  fixed timescale, for example 3 to 5 days, and cap the per-step modal change;
- leave vorticity, temperature variation, tracers, Coriolis rotation,
  weak-HS forcing, theta recentering, near-surface residual corrections, and
  10 m wind diagnostics unchanged;
- do not apply the filter during DFI, because DFI already handles initial fast
  modes and prior DFI re-routing evidence is weak;
- fall back to the incumbent state when transforms, masks, or filtered fields
  are nonfinite.

This is not the rejected broad divergence-selective gravity-wave damping. It is
geographically and spectrally targeted at equatorial fast-wave noise and avoids
vertical eigenmode construction.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py` only if a
    shared zonal/total-mode mask helper is useful
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate with suffix `_eq_wave_sponge`.
- API changes:
  - None. Forecast inputs, outputs, metrics, splits, and lead times stay fixed.
- Tests to update:
  - Unit-test latitude taper bounds and smooth zero behavior outside the
    equatorial band.
  - Unit-test modal mask selection and per-step cap.
  - Verify vorticity, temperature, tracers, and output diagnostic options are
    unchanged by the filter.
  - Verify DFI filter lists remain incumbent-equivalent.
  - Verify finite fallback and candidate registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium leads if tropical
    divergence/log-pressure fast-wave noise aliases into global mass fields.
  - `2m_temperature` after day 5 if lower-tropospheric pressure/thickness drift
    is reduced without changing surface residual memory.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be less exposed than in wind-output
    candidates because the accepted Richardson diagnostic and low-level wind
    output path are unchanged.
  - Extratropical balanced flow should remain close to incumbent because the
    latitude taper is zero outside the equatorial waveguide.
- Possible regressions:
  - Equatorial Kelvin and inertia-gravity waves are real forecast signals; too
    much damping can degrade tropical mass and height phase.
  - Damping log-surface-pressure modes can perturb MSLP guardrails even with a
    weak cap.

## Risks

- Numerical stability:
  - Low to moderate. The filter is damping and capped, but it changes prognostic
    divergence and mass fields in a dynamically sensitive region.
- Compute cost:
  - Low. It adds a few spectral transforms and modal masks per inner step, much
    cheaper than a vertical normal-mode eigensystem.
- Data leakage:
  - None. The filter uses only forecast state, latitude geometry, spectral
    indices, and fixed constants.
- Physical plausibility:
  - Moderate. Sponge layers and scale-selective damping are standard numerical
    tools, and equatorial wave theory motivates the geographic target, but real
    tropical waves must not be overdamped.
- Rollback complexity:
  - Low. Remove one filter/flag, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_eq_wave_sponge`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_eq_wave_sponge --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_eq_wave_sponge --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show equatorial
    divergence/log-pressure noise is not a material remaining error source.
    Any MSLP or Z500 guardrail failure would show the sponge damages physical
    tropical wave structure or mass balance.

## Citations

- Matsuno, T. 1966. Quasi-geostrophic motions in the equatorial area. Journal of
  the Meteorological Society of Japan, 44, 25-43.
  https://doi.org/10.2151/jmsj1965.44.1_25
- Wheeler, M. and Kiladis, G. N. 1999. Convectively Coupled Equatorial Waves:
  Analysis of Clouds and Temperature in the Wavenumber-Frequency Domain.
  Journal of the Atmospheric Sciences, 56, 374-399.
  https://doi.org/10.1175/1520-0469(1999)056%3C0374:CCEWAO%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Jablonowski, C. and Williamson, D. L. 2011. The pros and cons of diffusion,
  filters and fixers in atmospheric general circulation models. In Numerical
  Techniques for Global Atmospheric Models. Springer.
  https://doi.org/10.1007/978-3-642-11640-7_13

## Researcher Notes

This proposal accounts for rejected `williamson-cn-rk3-rollout` by keeping the
accepted off-centered SIL3 rollout and adding only a weak positive-time filter.
It accounts for rejected `absolute-vorticity-flux-dealiasing` by leaving
vorticity and absolute-vorticity fluxes unchanged. It accounts for rejected
seasonal/layered surface residual memory variants by leaving near-surface
residual variables and decay times untouched.

It is distinct from scrapped `vertical-normal-mode-gravity-wave-filter`, which
needed a coupled vertical eigenbasis for divergence, temperature, and log
surface pressure. It is also distinct from older broad
`divergence-selective-gravity-wave-damping`: this filter is equatorially
confined, high-mode selected, positive-time only, and paired with a small
log-surface-pressure damping so it tests equatorial waveguide noise rather than
global divergence damping.

## Evaluator Notes

### 2026-06-20T19:12:40Z

Decision: move to `staging`; ranked 2 of 3 triaged proposals.

The proposal is physically plausible and implementable, but it should not take
the single ready slot ahead of the analysis-offset rate mask. The accepted
off-centered SIL3 result already supplied the dominant fast-mode/mass-field
gain (`+0.25891536186185515` iteration, `+0.2522585257774621` validation), and
the direct `divergence-selective-gravity-wave-damping` experiment was clean but
slightly negative (`-0.00020461043258523937`). The scrapped
`vertical-normal-mode-gravity-wave-filter` also records that extra gravity-wave
filtering has a weak cost-risk tradeoff unless diagnostics show a remaining
coherent fast-mode source.

This idea is narrower than those rejected/scrapped variants because it is
equatorially confined, high-mode selected, and avoids a vertical eigenbasis.
That distinction keeps it out of scrap. The remaining risk is that equatorial
Kelvin and inertia-gravity waves are real forecast signals, and damping
log-surface-pressure in the tropics can spend MSLP/Z500 guardrail margin. Keep
it staged until the stronger HS-rate follow-up is tried or read-only diagnostics
show persistent equatorial divergence/log-pressure noise in incumbent
trajectories.
