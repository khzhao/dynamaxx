---
schema_version: 1
slug: low-mode-geostrophic-wind-init
title: "Initialize Low-Mode Rotational Wind Toward Geostrophic Balance"
status: scrap
created_at: 2026-06-20T07:20:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

The incumbent has strong initialization improvements, but large-scale rotational
wind can still be imbalanced relative to the hydrostatically initialized mass
field after pressure-to-sigma interpolation. A small, low-wavenumber
extratropical geostrophic blend applied only at initialization may reduce
early balanced-mode adjustment and improve pressure and height skill without
changing divergence, moisture, target variables, lead ranges, metrics, or the
forecast contract.

## Mechanism

After the incumbent pressure-to-sigma and hydrostatic-layer initialization, but
before DFI:

1. Compute the initialized sigma-layer geopotential or Montgomery-like pressure
   gradient field from the same state used by the primitive-equation dynamics.
2. Diagnose geostrophic wind in the extratropics with a bounded Coriolis
   denominator, for example tapering from zero equatorward of 20 degrees to one
   poleward of 35 degrees.
3. Convert the geostrophic wind increment to spectral space and retain only
   broad rotational structure, for example total wavenumber <= 8 with a smooth
   taper to zero by wavenumber 14.
4. Blend only the rotational wind or vorticity component toward that diagnostic
   by a small fraction, for example 0.20 to 0.30. Leave divergence, log surface
   pressure, temperature, tracers, humidity, and surface fields unchanged.
5. Preserve global mean angular and mass diagnostics by removing any introduced
   zero-mode or grid-mean wind increment before returning the dinosaur state.

Register a model named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_geostrophic_init`.

This differs from scrapped `thermal-wind-zonal-shear-init` because it is not a
zonal-mean vertical-shear adjustment, differs from rejected broader wind
initialization because it is low-mode, rotational-only, and mass-field-driven,
and differs from staged `geostrophic-surface-wind-residual` because it changes
only initialization rather than output diagnostics.

## Implementation Scope

- Add an adapter option such as `use_low_mode_geostrophic_wind_initialization`.
- Implement a helper that accepts an initialized dinosaur state and returns a
  bounded rotational wind or vorticity increment.
- Use existing spherical harmonic transforms and derivative utilities where
  possible instead of finite-difference grid hacks.
- Keep the helper deterministic, with documented latitude masks, spectral
  cutoff, blend factor, and zero-mean cleanup.
- Add tests for equatorial masking, zero-field no-op behavior, cutoff behavior,
  shape preservation, registry exposure, and unchanged behavior when disabled.

No fixed evaluation protocol, target variable, lead range, metric, saved
forecast schema, multiple-trajectory behavior, or forecast API should change.

## Expected Metric Movement

- Most likely gains: `mean_sea_level_pressure`, `geopotential_500`, and
  synoptic-scale `10m_wind_speed` through reduced initial geostrophic adjustment.
- Possible gains: `2m_temperature` if improved mass-wind balance reduces
  circulation drift that currently interacts with surface residual correction.
- Expected size: small to moderate. The low-mode and blend limits should keep
  the perturbation narrow while targeting a central balance relation.

## Risks

- Geostrophic balance is invalid in the tropics and for strongly curved or
  ageostrophic flows; latitude masking and low blend factors are required.
- The DFI step may already remove much of this imbalance, making the proposal
  subthreshold.
- Prior initialization ideas such as broader Helmholtz or thermal-wind variants
  were weak or scrapped; this proposal must remain narrower and easier to
  diagnose.
- Wind changes can affect surface temperature through advection and may trigger
  guardrails even if pressure fields improve.

## Evaluation Plan

1. Fast protocol: run helper tests plus standard import and registry checks.
2. Iteration protocol: evaluate the registered candidate against the current
   incumbent cache at commit `ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6`.
3. Validation protocol: run only after a clean, promotion-eligible iteration
   result.
4. Inspect lead-1 to lead-5 movement in `mean_sea_level_pressure`,
   `geopotential_500`, `10m_wind_speed`, and `2m_temperature` for evidence of
   reduced spinup rather than late-lead-only noise.

## Citations

- Source reference:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements incumbent
  pressure-to-sigma and hydrostatic-layer initialization before DFI.
- Source reference:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` contains the
  sigma-coordinate primitive-equation operators that define the pressure,
  geopotential, vorticity, and divergence tendencies to keep consistent.
- History reference:
  accepted `balanced-digital-filter-initialization`,
  `log-pressure-interpolation-initialization`, and
  `hydrostatic-layer-initialization` show that initialization balance is a
  productive family for this dycore.
- History reference:
  scrapped `thermal-wind-zonal-shear-init` and rejected broad wind
  initialization variants argue for a localized low-mode rotational-only
  proposal rather than another full-field wind rewrite.
- Okland, H., 1970:
  "On the Adjustment Toward Balance in Primitive Equation Prediction Models."
  Monthly Weather Review. DOI: 10.1175/1520-0493(1970)098<0271:OTATBI>2.3.CO;2.
- Daley, R., 1981:
  "Normal Mode Initialization." Reviews of Geophysics.
  DOI: 10.1029/RG019i003p00450.
- ECMWF, 2023:
  IFS Documentation CY48R1, Part III, "Dynamics and numerical procedures," for
  operational context on balance, semi-implicit integration, and hydrostatic
  primitive-equation initialization.

## Researcher Notes

The proposal avoids the recently scrapped divergence-zero-mode projection and
does not alter mass diagnostics. It is aimed at low-mode rotational balance, so
it is decorrelated from residual-memory, passive-humidity, product-dealiasing,
and weak-HS ramp ideas.

## Evaluator Notes

### 2026-06-20T07:21:19Z

Decision: move to `scrap`.

The geostrophic-balance argument is physically recognizable, but this is still
a pre-DFI prognostic wind initialization edit. That family has poor local
evidence: `helmholtz-wind-initialization` was finite but regressed iteration by
`-0.34423230670441374` with large MSLP and Z500 guardrail failures, and the
narrower `vorticity-preserving-dfi-increment` was clean but negative
(`-0.002335598569885189`). The scrapped `thermal-wind-zonal-shear-init` already
records the same concern for balance-projected wind changes, and staged
`geostrophic-surface-wind-residual` is a safer output-only representative of
the geostrophic signal if that family is revisited.

This proposal is narrower than the failed Helmholtz projection, but it still
requires tunable latitude masks, spectral cutoffs, blend fractions, Coriolis
denominator bounds, rotational projection details, and zero-mode cleanup before
DFI. DFI may remove much of the increment, while any surviving change can
directly affect the fixed early mass-field and 10 m wind guardrails. Do not
spend an iteration on this without prior read-only diagnostics showing a
persistent low-mode extratropical rotational wind imbalance after the incumbent
initialization and DFI.
