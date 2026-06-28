---
schema_version: 1
slug: pressure-coordinate-weak-hs-rate-mask
title: Place Weak Held-Suarez Thermal Damping in Pressure Coordinates
status: scrap
created_at: 2026-06-21T10:18:55Z
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

# Place Weak Held-Suarez Thermal Damping in Pressure Coordinates

## Hypothesis

The incumbent's weak Held-Suarez thermal forcing was valuable, and the accepted
analysis-offset equilibrium improved it further. Recent negative evidence shows
that weakening the local rate where the offset is large is harmful, and that
removing local surface-pressure coupling from the equilibrium is harmful. A
different, narrower question remains: the thermal damping mask itself is still a
pure sigma-coordinate function, so the lower-tropospheric damping transition
moves with terrain-following sigma rather than with pressure thickness.

Using the same accepted equilibrium temperature and the same column-integrated
thermal damping strength, but placing the lower-tropospheric rate transition in
local pressure coordinates, may reduce thermal drift in columns with unusual
surface pressure while avoiding the rejected rate-weakening and fixed-pressure
equilibrium mechanisms.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_pressure_hs_rate`.
Preserve the accepted analysis-offset equilibrium, DFI, log-pressure and
hydrostatic initialization, exact Coriolis Strang split, theta tendency, theta
recentring, off-centered SIL3, scale-separated surface residuals, and all fixed
evaluation protocols.

For this candidate only, add an opt-in variant of
`_TracerSafeHeldSuarezForcingSigma.kt()`:

- compute nodal pressure ratio `p / p0 = sigma * surface_pressure / p0` from the
  current state, using the same local surface pressure already used by the
  accepted equilibrium temperature;
- define the lower-tropospheric transition using pressure ratio, for example a
  smooth ramp between `p/p0 = 0.7` and `1.0`, instead of the current fixed sigma
  ramp;
- preserve the incumbent `ka` and `ks` endpoint rates and normalize the new mask
  by layer so the global area-weighted column-mean damping rate remains close to
  the incumbent for a 1000 hPa column;
- keep `kf = 0`, so no Rayleigh momentum drag is introduced;
- keep the accepted analysis-offset equilibrium temperature exactly local in
  surface pressure; do not use the rejected fixed-pressure equilibrium;
- use the same forcing in DFI and positive-time rollout, with finite fallback to
  the incumbent sigma-rate mask if pressure diagnostics are invalid.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, outputs, lead times, target variables, and metrics
    remain unchanged.
- Tests to update:
  - Unit-test that 1000 hPa columns reproduce the incumbent sigma-rate mask
    within tolerance after normalization.
  - Unit-test high and low surface-pressure columns produce finite pressure-rate
    masks with the expected vertical shift.
  - Verify zero analysis-HS offset and valid pressure recover the same
    equilibrium temperature as the incumbent except for rate placement.
  - Verify candidate factory preserves every incumbent option except the
    pressure-coordinate weak-HS rate selector.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and late leads if lower-tropospheric thermal drift
    is partly caused by a sigma-placed damping transition in columns with
    anomalous surface pressure.
  - `mean_sea_level_pressure` and `geopotential_500` if improved lower-column
    thermal thickness reduces hydrostatic mass-field drift.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be near neutral because no momentum drag,
    wind diagnostic, Coriolis split, diffusion, or surface residual path changes.
- Possible regressions:
  - The Held-Suarez benchmark is intentionally sigma based; pressure-coordinate
    rate placement may overfit terrain or surface-pressure variability in this
    flat-orography adapter.
  - Moving damping vertically can perturb early mass fields even with unchanged
    column-mean rate.

## Risks

- Numerical stability:
  - Moderate. This changes a thermal tendency every step, but preserves endpoint
    rates, uses no momentum drag, and has an incumbent fallback.
- Compute cost:
  - Low. It adds local pressure algebra inside weak-HS forcing, with no extra
    trajectory steps.
- Data leakage:
  - None. It uses only the current forecast state and fixed physical constants.
- Physical plausibility:
  - Moderate. Pressure-coordinate thermal damping is physically interpretable
    for lower-tropospheric relaxation, but it is a departure from the canonical
    Held-Suarez sigma mask.
- Rollback complexity:
  - Low. Remove one forcing option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_pressure_hs_rate`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_pressure_hs_rate --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_pressure_hs_rate --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show sigma-coordinate
    rate placement is not a material remaining error source. Any early
    `2m_temperature`, MSLP, or Z500 guardrail failure would show the pressure
    mask disrupts the accepted thermal balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
  defines the canonical sigma-coordinate `kt()` thermal relaxation mask.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` composes the
  accepted weak-HS forcing and analysis-offset equilibrium path.
- History: `.logbook/history/2026-06-20_19-13-38_analysis-offset-relaxation-rate-mask/decision.md`
  rejected reducing thermal damping where the accepted analysis offset is large;
  this proposal preserves endpoint and column-mean damping strength instead.
- History: `.logbook/history/2026-06-21_04-36-53_fixed-pressure-analysis-hs-equilibrium/decision.md`
  rejected removing local surface-pressure coupling from the equilibrium; this
  proposal keeps that local equilibrium and changes only rate-mask placement.
- History: `.logbook/history/2026-06-21_08-11-13_startup-subcycled-first-day-rollout/decision.md`
  rejected smaller startup steps, so this proposal does not change timestep,
  subcycling, or rollout length.
- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not active staged `weak-hs-positive-time-ramp`,
`column-neutral-weak-hs-heating-split`, `tropopause-capped-thermal-relaxation`,
`solar-weighted-thermal-tendency`, or `static-stability-limited-analysis-hs-offset`.
Those ideas change timing, vertical heat compensation, tropopause masking,
solar weighting, or offset limiting. This proposal keeps timing, endpoint rates,
momentum drag, and the accepted analysis-HS equilibrium unchanged while moving
only the thermal-rate transition from sigma to local pressure.

It explicitly accounts for the recent negative evidence: it does not propose
smaller startup steps or any subcycling variant, it does not alter theta
recentring or mass-weighted moments, and it does not repeat the rejected
fixed-pressure analysis-HS equilibrium.

## Evaluator Notes

### 2026-06-21T10:25:51Z

Decision: move to `scrap`.

This is not an exact duplicate of the rejected
`analysis-offset-relaxation-rate-mask` or
`fixed-pressure-analysis-hs-equilibrium`, but the evidence against this family
is now strong. The rate-mask experiment regressed iteration by
`-0.016312861142089408`, failed early `2m_temperature` by
`57.31598628733586%`, failed early MSLP by `3.232225060994042%`, and produced
many variable-lead guardrail violations. The fixed-pressure equilibrium also
regressed the primary score, while lead decay, barotropic projection, and
spectral smoothing of the accepted analysis-HS target were clean but
subthreshold or negative.

The canonical Held-Suarez sigma forcing in the source defines the lower
thermal-rate transition from `sigma_b`; changing that transition to local
pressure would alter a thermal tendency at every step. Preserving endpoint
rates and the accepted local equilibrium reduces but does not remove the core
risk: this is another weak-HS rate-placement variant in a crowded, recently
negative queue. The mechanism is also closer to coordinate-dependent rate
tuning than to a well-diagnosed physical error in the incumbent.

Reject rather than stage to keep the active queue from accumulating more
near-duplicate weak-HS rate/equilibrium followups. If pressure-coordinate
forcing is revisited, it should first be motivated by a read-only diagnostic
showing terrain/surface-pressure-dependent lower-tropospheric thermal drift,
and it should be treated as a new proposal rather than revived from this file.
