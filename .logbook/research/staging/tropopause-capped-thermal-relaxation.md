---
schema_version: 1
slug: tropopause-capped-thermal-relaxation
title: "Cap Weak Thermal Relaxation Across the Diagnosed Tropopause"
status: staging
created_at: 2026-06-20T07:20:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/held_suarez.py
  - src/dynamaxx/dycore/registry.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - tests/dycore/models/dinosaur/test_dependency.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/models/dinosaur/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

## Hypothesis

The incumbent weak Held-Suarez thermal relaxation improves broad stability, but
its analytic equilibrium profile can still act too uniformly near the upper
troposphere and lower stratosphere. Capping the weak thermal relaxation above a
diagnosed initial tropopause should reduce spurious upper-column temperature
nudging while preserving the accepted lower-column stabilization and surface
residual behavior.

## Mechanism

Add an optional tropopause mask to the existing weak thermal forcing path:

1. During `weather_state_to_dinosaur_state`, diagnose one pressure or sigma
   tropopause level per column from the input temperature profile using a simple
   WMO-style lapse-rate criterion, with a conservative fallback to a fixed
   pressure near 200 hPa when the criterion is ambiguous.
2. Map that level to the model sigma grid and cache it as adapter-local
   auxiliary data for the forecast construction.
3. In the weak Held-Suarez temperature forcing, multiply only the thermal
   relaxation coefficient by a smooth vertical cap that transitions from 1
   below the diagnosed tropopause to a small floor, for example 0.15 to 0.30,
   above it.
4. Keep wind drag disabled as in the incumbent tracer-safe forcing. Do not add
   solar, diurnal, seasonal, residual-memory, or momentum terms.
5. Preserve all incumbent initialization, theta tendency, DFI, Strang Coriolis,
   offcentering, Richardson 10 m wind, theta recentering, and scale-separated
   surface residual settings.

Register a model named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_tropopause_hs_cap`.

This is distinct from staged `weak-hs-positive-time-ramp`,
`column-neutral-weak-hs-heating-split`, and `solar-weighted-thermal-tendency`:
it changes only the vertical mask of an already accepted weak relaxation using
lead-zero column structure.

## Implementation Scope

- Add a boolean adapter option such as
  `use_tropopause_capped_weak_hs_relaxation`.
- Implement a small, documented helper that diagnoses the tropopause level from
  initial pressure-level temperatures and pressures with bounded outputs.
- Thread the resulting sigma-level mask into the thermal-forcing wrapper, or
  construct a forcing object that accepts a static nodal mask.
- Add unit tests for mask bounds, monotone pressure handling, fallback behavior,
  registry exposure, and unchanged behavior when the option is disabled.

No fixed evaluation protocol, target, lead range, score metric, saved forecast
format, or forecast contract should change.

## Expected Metric Movement

- Most likely gains: `geopotential_500` and `mean_sea_level_pressure` at longer
  leads through reduced artificial upper-column thermal adjustment.
- Possible gains: `2m_temperature` if the lower-column weak relaxation remains
  stabilizing while upper-level thermal drift is reduced.
- Expected size: small. The cap is conservative and should not dominate the
  incumbent scale-separated surface residual correction.

## Risks

- Recent `seasonal-stability-surface-residual-decay` was rejected with negative
  aggregate movement and a `2m_temperature` guardrail failure. This proposal
  must avoid residual-memory decay and use only a static vertical thermal mask.
- Diagnosed tropopause levels can be noisy over steep thermal inversions or
  polar columns; the helper needs smoothing, bounds, and a fixed fallback.
- Weak-HS thermal forcing is already accepted, so reducing it too much could
  remove beneficial stabilization.
- Upper-column improvements may not offset any lower-tropospheric temperature
  regression.

## Evaluation Plan

1. Fast protocol: run focused helper tests plus existing dycore import and
   registry tests.
2. Iteration protocol: evaluate against the current incumbent cache at commit
   `ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6` with unchanged protocols.
3. Validation protocol: run only after a clean, promotion-eligible iteration
   result.
4. Inspect upper-air and surface coupling by comparing
   `geopotential_500`, `mean_sea_level_pressure`, and `2m_temperature` by lead.

## Citations

- Source reference:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` constructs the incumbent
  weak Held-Suarez forcing and wraps it with tracer-safe behavior.
- Source reference:
  `src/dynamaxx/dycore/models/dinosaur/held_suarez.py` defines the thermal
  relaxation and equilibrium-temperature structure to be masked.
- History reference:
  accepted `weak-held-suarez-forcing`, accepted
  `stability-aware-surface-residual-correction`, and accepted
  `scale-separated-surface-residual-memory` show that conservative stability
  and near-surface thermal corrections have helped this incumbent family.
- History reference:
  rejected `seasonal-stability-surface-residual-decay` warns against broad
  time-varying surface-residual gates; this proposal avoids that mechanism.
- Held, I. M. and M. J. Suarez, 1994:
  "A Proposal for the Intercomparison of the Dynamical Cores of Atmospheric
  General Circulation Models." Bulletin of the American Meteorological Society.
  DOI: 10.1175/1520-0477(1994)075<1825:APFTIO>2.0.CO;2.
- EUMETSAT User Portal, "Tropopause Height and Temperature," documents use of
  the official WMO lapse-rate tropopause definition for operational satellite
  products.
- ECMWF, 2023:
  IFS Documentation CY48R1, Part III, "Dynamics and numerical procedures," for
  operational context on vertical structure in hydrostatic primitive-equation
  models.

## Researcher Notes

This proposal is meant to be a vertical-localization refinement of an accepted
forcing, not another surface residual decay, passive humidity, or expensive
physics addition. It should be cheap enough for the workers=4 resource policy.

## Evaluator Notes

### 2026-06-20T07:21:19Z

Decision: move to `staging`.

The physical direction is plausible: the accepted weak Held-Suarez thermal
relaxation is useful, and a bounded upper-column mask is a more localized
change than removing the source or changing residual memory. It is also
distinct from staged `weak-hs-positive-time-ramp`,
`column-neutral-weak-hs-heating-split`, and `solar-weighted-thermal-tendency`.

Do not put this in `ready` yet. The current adapter builds `_trajectory_function`
before looping over `initial_times`, while this proposal wants a diagnosed
per-column tropopause mask from each initial pressure-level temperature profile.
Threading that static, per-initial-state mask into the weak-HS forcing would
require a design choice that is broader than the proposal presents: rebuild the
trajectory per initial state, carry a mask through state/tracer auxiliary data,
or restrict the mask to fixed sigma/pressure structure. The recent weak-HS
family evidence is also weak or cautionary: exact source integration and
theta-consistent weak-HS were clean but far below threshold, mass-neutral
weak-HS damaged `2m_temperature`, and the recent seasonal/stability residual
gate failed the `2m_temperature` guardrail. Preserve the idea for later, but
promote it only after the mask threading is specified and the implementation
keeps DFI and lower-column weak-HS behavior incumbent-equivalent.
