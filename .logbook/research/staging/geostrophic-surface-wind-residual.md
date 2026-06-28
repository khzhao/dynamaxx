---
schema_version: 1
slug: geostrophic-surface-wind-residual
title: Add a Bounded Geostrophic Residual to the 10 m Wind Diagnostic
status: staging
created_at: 2026-06-19T10:11:34Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
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

# Add a Bounded Geostrophic Residual to the 10 m Wind Diagnostic

## Hypothesis

The accepted Richardson 10 m wind diagnostic improved the target wind channel by
using lower-column stability and shear, but it remains a local vertical-profile
diagnostic. The new off-centered incumbent substantially improved mass fields,
especially MSLP and Z500. That makes the large-scale horizontal pressure-gradient
signal more trustworthy than it was for older incumbents.

A conservative, midlatitude-only geostrophic residual can use the improved mass
field to correct part of the medium-lead `10m_u_component_of_wind` drift without
touching the prognostic state. The correction should be small, bounded, and
zeroed in the tropics, where geostrophic balance is ill-conditioned.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_geo_10m_wind`.
Preserve the incumbent trajectory, DFI, weak-HS forcing, log-pressure and
hydrostatic initialization, exact symmetric Coriolis split, theta tendency,
theta mean recentering, off-centered SIL3 rollout, stability-aware residual
correction, pressure-level outputs, target variables, and fixed evaluation
protocols.

For the candidate only, add an opt-in diagnostic after the accepted Richardson
10 m wind is computed and before near-surface residual correction:

- compute a synoptic-scale horizontal pressure-gradient proxy from forecast
  `log_surface_pressure` or raw MSLP using the existing spherical-harmonic
  gradient utilities;
- estimate lower-layer density from forecast surface pressure and lowest
  sigma-layer temperature;
- compute a geostrophic `u` component where `|f|` is safely away from zero;
- taper the correction smoothly to zero equatorward of a fixed latitude band
  and cap the geostrophic wind magnitude and residual increment;
- blend only a small fixed fraction of the bounded geostrophic residual into
  the accepted Richardson 10 m `u` diagnostic;
- leave `10m_v_component_of_wind`, pressure-level winds, vorticity, divergence,
  temperature, log surface pressure, tracers, MSLP, Z500, and `2m_temperature`
  unchanged;
- fall back to the accepted Richardson diagnostic wherever pressure, density,
  Coriolis parameter, or the residual is nonfinite.

This is an output diagnostic for a scored channel, not a change to the forecast
dynamics or to the fixed evaluation contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input channels, emitted channels, target
    variables, lead times, splits, and metrics remain unchanged.
- Tests to update:
  - Unit-test the geostrophic residual on synthetic pressure gradients in both
    hemispheres, including tropical tapering and finite fallback.
  - Verify the correction changes only `10m_u_component_of_wind`.
  - Verify zero pressure gradient and zero blend reproduce the accepted
    Richardson diagnostic.
  - Verify the candidate factory preserves all incumbent rollout flags,
    including `semi_implicit_offcentering`.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at days 4 to 15 if large-scale pressure-gradient
    balance supplies missing synoptic wind phase or amplitude after the accepted
    local Richardson diagnostic.
  - Primary score may improve without moving mass fields because the correction
    is output-only.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, and `geopotential_500` should
    remain unchanged except for metric aggregation noise.
- Possible regressions:
  - Near-surface wind is ageostrophic because of friction and turbulence, so a
    geostrophic residual can overcorrect if the cap or latitude taper is too
    permissive.
  - Tropical and high-latitude numerical conditioning must be guarded carefully.

## Risks

- Numerical stability:
  - Very low for the rollout because the correction is output-only.
- Compute cost:
  - Low. It adds one pressure-gradient diagnostic and local algebra per output
    frame.
- Data leakage:
  - None. It uses only forecast state variables and fixed physical constants.
- Physical plausibility:
  - Moderate. Midlatitude synoptic flow is often close to geostrophic balance,
    but 10 m wind is reduced and turned by boundary-layer friction. The bounded
    residual must remain a small correction, not a replacement wind.
- Rollback complexity:
  - Low. Remove one diagnostic option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_geo_10m_wind`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_geo_10m_wind --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no early or variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_geo_10m_wind --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the current
    mass-field improvement does not provide useful additional 10 m wind
    diagnostic signal. Any early wind guardrail failure would show that the
    geostrophic residual is too ageostrophic for screen-level wind.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` computes
    accepted Richardson 10 m winds from lowest-layer wind, lower-column
    stability, and shear without using the horizontal pressure-gradient signal.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/decision.md`
    accepted the local Richardson wind diagnostic with large 10 m wind gains.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md`
    accepted off-centered SIL3 with large MSLP and Z500 improvements, making a
    mass-field-derived wind residual newly plausible.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_01-53-13_monotone-shear-10m-wind-diagnostic/decision.md`
    rejected a vertical-shear-only wind diagnostic; this proposal uses a
    horizontal pressure-gradient balance signal instead.
  - Markowski, P. M. and Bryan, G. H. 2014. Revisiting an Old Concept: The
    Gradient Wind. Monthly Weather Review.
    https://doi.org/10.1175/MWR-D-13-00088.1
  - ECMWF IFS Documentation Part I: Observations, CY48R1, describes the
    Monin-Obukhov based observation operator for surface winds.
    https://www.ecmwf.int/sites/default/files/elibrary/2023/81367-ifs-documentation-cy48r1-part-i-observations.pdf
  - Holton, J. R. and Hakim, G. J. 2012. An Introduction to Dynamic
    Meteorology, 5th ed. Academic Press. ISBN 9780123848666.

## Researcher Notes

This is not a duplicate of the accepted Richardson 10 m wind diagnostic because
it does not rework vertical shear, layer heights, or stability factors. It adds
a separate horizontal pressure-gradient signal that only became attractive after
the off-centered incumbent produced large mass-field improvements.

It is also not a duplicate of rejected `monotone-shear-10m-wind-diagnostic`,
which changed the local shear factor and produced a small negative iteration
delta. This proposal explicitly avoids another local amplitude monotonicity
change and should be rejected if the improved mass fields still cannot support a
bounded geostrophic correction.

## Evaluator Notes

### 2026-06-19T10:15:47Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

The mechanism is plausible after the accepted off-centered SIL3 experiment:
the new incumbent materially improved MSLP and Z500, so a bounded midlatitude
pressure-gradient signal may now carry more useful information for
`10m_u_component_of_wind` than it did under older baselines. The proposal is
also safer than a prognostic wind change because it is output-only, finite
guarded, latitude tapered, and scoped to one diagnostic channel.

Keep it staged rather than ready because it targets a single scored output
channel and the physical link is weaker at 10 m than aloft. Boundary-layer
friction, turning, roughness, and ageostrophic flow mean a geostrophic residual
can easily overcorrect screen-level wind even if the mass field is better.
Recent wind-diagnostic history is mixed: the Richardson 10 m diagnostic was
strongly accepted, but the monotone shear follow-up was slightly negative and
the Coriolis-rotated surface residual failed an early wind guardrail. If this
is promoted later, the latitude taper, blend fraction, and residual cap must be
fixed before scoring and not tuned against iteration or validation.
