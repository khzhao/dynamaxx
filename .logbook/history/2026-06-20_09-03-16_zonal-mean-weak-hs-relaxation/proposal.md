---
schema_version: 1
slug: zonal-mean-weak-hs-relaxation
title: Restrict Weak Held-Suarez Relaxation to Zonal-Mean Thermal Bias
status: ready
created_at: 2026-06-20T08:56:40Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
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

# Restrict Weak Held-Suarez Relaxation to Zonal-Mean Thermal Bias

## Hypothesis

The accepted weak Held-Suarez source improved the incumbent family, but its
current tracer-safe wrapper relaxes the full local temperature field toward a
zonally symmetric equilibrium. That can damp synoptic longitudinal thermal
anomalies that the primitive-equation dynamics should carry, especially after
the incumbent has already added theta-form transport, layer-mean theta
recentering, and scale-separated near-surface residual memory.

A zonal-mean-only weak relaxation should retain the accepted large-scale thermal
bias control while avoiding direct damping of eddy thermal structure. If
remaining error is partly due to over-relaxing local baroclinic anomalies, this
candidate should improve `geopotential_500` and `mean_sea_level_pressure`
without changing the residual mechanism that dominates `2m_temperature`.

## Mechanism

Register a side-by-side model named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs`.

For this candidate only:

- compute the incumbent weak Held-Suarez nodal temperature tendency exactly as
  `_TracerSafeHeldSuarezForcingSigma.explicit_terms` does today;
- replace that local tendency with its longitude mean at each sigma layer and
  latitude, broadcast back over longitude;
- keep the current no-wind-drag behavior and tracer-safe zero tracer tendencies;
- apply the same zonal-mean weak-HS source in DFI and positive-time rollout so
  the DFI equation and forecast equation remain internally consistent;
- leave vorticity, divergence, `log_surface_pressure`, passive tracers, exact
  Coriolis splitting, SIL3 offcentering, theta tendency, theta recentering, and
  scale-separated near-surface residual memory unchanged;
- fall back to the incumbent local weak-HS tendency if the zonal mean or
  broadcast tendency is nonfinite.

This is a forcing-structure experiment, not a sweep over weak-HS amplitudes or
timescales.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one factory and one registry entry for the candidate model name above.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, worker policy,
    and fixed protocols remain unchanged.
- Tests to update:
  - Verify the factory preserves every incumbent option except the new
    zonal-mean weak-HS selector.
  - Unit-test that the forcing modifies only `temperature_variation`.
  - Unit-test that the candidate tendency is constant over longitude and matches
    the longitude mean of the local incumbent weak-HS tendency.
  - Verify tracer tendencies remain zero and finite.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and long leads if
    local weak-HS damping currently weakens useful eddy thermal structure.
  - `2m_temperature` may improve modestly after day 2 if lower-column thermal
    anomalies are less over-relaxed before residual memory decays.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should stay close to incumbent because momentum,
    Coriolis splitting, and 10 m diagnostic/residual paths are unchanged.
- Possible regressions:
  - The accepted local weak-HS tendency may be correcting local thermal bias that
    matters for the fixed score; removing local anomaly relaxation could worsen
    surface temperature or thickness errors.
  - Full-field relaxation may be part of the accepted stabilization, so a
    zonal-mean source can be clean but subthreshold.

## Risks

- Numerical stability:
  - Low. The candidate weakens and smooths an accepted thermal tendency, but it
    changes the DFI and rollout balance source.
- Compute cost:
  - Negligible. It adds a longitude mean and broadcast to an existing forcing.
- Data leakage:
  - None. The mechanism uses only the current model state and fixed forcing
    constants.
- Physical plausibility:
  - Moderate to high. Held-Suarez forcing is defined by Newtonian relaxation
    toward a zonally symmetric equilibrium; this candidate treats the weak
    source as a large-scale bias control rather than local eddy damping.
- Rollback complexity:
  - Low. Remove one forcing selector/subclass, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs`.
  - Require finite metrics and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_zonal_mean_hs --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show that local
    weak-HS anomaly relaxation is not a material remaining error, or that it is
    beneficial. Any early `2m_temperature`, MSLP, or Z500 guardrail failure
    would show the local source is needed for balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` defines
  `_TracerSafeHeldSuarezForcingSigma`, which currently applies the weak thermal
  relaxation locally and leaves momentum/tracers unchanged.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py` defines
  the Held-Suarez equilibrium and relaxation structure used by the incumbent.
- History: `.logbook/history/2026-06-16_16-27-03_wind-sparing-held-suarez-relaxation/decision.md`
  accepted weak thermal-only Held-Suarez relaxation with a large score gain.
- History: `.logbook/history/2026-06-18_22-27-09_theta-consistent-held-suarez-forcing/decision.md`
  rejected a theta-consistent weak-HS source as clean but effectively neutral,
  so this proposal changes the spatial structure instead of the thermodynamic
  variable.
- History: `.logbook/research/staging/column-neutral-weak-hs-heating-split.md`,
  `.logbook/research/staging/weak-hs-positive-time-ramp.md`, and
  `.logbook/research/staging/tropopause-capped-thermal-relaxation.md` are
  active weak-HS variants; this proposal is distinct because it preserves the
  vertical profile and timing while removing only longitudinal anomaly forcing.
- Held, I. M. and Suarez, M. J. 1994. A Proposal for the Intercomparison of the
  Dynamical Cores of Atmospheric General Circulation Models. Bulletin of the
  American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- ECMWF OpenIFS Held-Suarez documentation describes the test as Newtonian
  relaxation toward a zonally symmetric temperature state:
  https://confluence.ecmwf.int/plugins/viewsource/viewpagesrc.action?pageId=56660076
- CESM Held-Suarez documentation describes CAM's idealized Held-Suarez setup as
  relaxation toward a specified zonally symmetric equilibrium:
  https://www.cesm.ucar.edu/models/simple/held-suarez

## Researcher Notes

This is not a duplicate of rejected `calendar-aware-solar-relaxation` or staged
`solar-weighted-thermal-tendency`: it adds no date, longitude, or insolation
forcing and does not move the equilibrium. It is also not
`column-neutral-weak-hs-heating-split`, because no vertical compensation is
introduced. The negative evidence from weak-HS timing and variable-form tests
argues for keeping the implementation very small and fixed.

## Evaluator Notes

### 2026-06-20T09:01:44Z

Decision: move to `ready`; ranked 1 of 3 proposals in this triage batch and
the sole ready idea.

This is the strongest current proposal because it is a small, forecast-contract
preserving forcing-structure experiment with a clear physical mechanism. The
incumbent weak Held-Suarez source was strongly accepted, and the Held-Suarez
equilibrium is zonally symmetric, but the current adapter applies the resulting
thermal tendency locally. Replacing only that tendency with its longitude mean
tests whether the accepted source is acting as useful zonal-mean thermal bias
control while over-damping longitudinal eddy thermal anomalies.

The proposal is distinct from active staged weak-HS ideas: it does not change
timing, vertical compensation, tropopause masking, seasonal structure, or
source strength. It also preserves the accepted DFI, scale-separated residual
memory, Strang Coriolis split, theta tendency, theta recentering, and
offcentered SIL3 mechanisms. The prior `zonal-mean-theta-recentering` failure is
cautionary but not disqualifying because that candidate enforced exact
latitude-by-latitude theta preservation every step and became nonfinite; this
one only smooths an already weak thermal relaxation tendency. The main risk is
that local weak-HS anomaly damping is part of the accepted empirical correction,
so the fixed iteration gate should reject the idea quickly if the eddy damping
is beneficial.
