---
schema_version: 1
slug: delayed-lowmode-virtual-geopotential-coupling
title: Delayed Low-Mode Virtual-Geopotential Coupling
status: staging
created_at: 2026-06-26T07:37:35Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
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

# Delayed Low-Mode Virtual-Geopotential Coupling

## Hypothesis

The incumbent still keeps humidity out of the prognostic pressure-gradient path,
even though humidity-aware geopotential is already used when outputting
pressure-level geopotential. Fully moist or virtual-temperature dynamics have
unfavorable local evidence, but a delayed, low-horizontal-mode humidity
thickness increment may improve medium-lead MSLP and Z500 without reintroducing
the early pressure shock that rejected several recent vertical-DSE variants.

The physical reason is narrow: water vapor changes density and hydrostatic
thickness through virtual temperature. If that signal is only allowed into the
large-scale free-tropospheric divergence tendency after the accepted vertical-DSE
ramp has spun up, it may correct slowly growing mass-height errors while leaving
short-lead balance and near-surface temperature mostly incumbent-like.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_ramp_lm_vgeo`.

For this candidate only:

- keep the incumbent HSL mass-DSE, WTG, pressure-ramped vertical-DSE, surface
  residual, ocean heat flux, DFI, diffusion, Coriolis split, and output contract
  unchanged;
- compute the existing humidity-induced pressure/geopotential divergence
  tendency as an increment relative to the dry incumbent tendency;
- discard the humidity-induced vorticity correction and any direct humidity
  thermodynamic transport, so this is not full moist dynamics;
- project the divergence increment to broad horizontal modes only, for example
  full through total wavenumber 6 and zero by wavenumber 12;
- apply a smooth free-tropospheric sigma envelope, for example zero below
  sigma 0.82, full from 0.35 to 0.65, and zero above sigma 0.18;
- use a fixed forecast-time ramp that is zero through 72 h and full by 144 h;
- cap the resulting divergence increment per inner step and fall back exactly to
  the incumbent when humidity, pressure, geopotential, ramp weights, masks, or
  candidate tendencies are nonfinite.

This tests whether the missing humidity-density signal is useful only after the
accepted dry balance machinery has settled. It deliberately does not change the
transported DSE scalar, pressure-level output interpolation, passive humidity
advection, or target variables.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one model key such as `dino_hsl2_mass_dse_wtg_vdse_ramp_lm_vgeo`.
- API changes:
  - None. Forecast inputs, forecast outputs, lead steps, target variables, and
    fixed evaluation protocols remain unchanged.
- Tests to update:
  - Verify the new factory differs from the incumbent only by the opt-in virtual
    geopotential coupling selector and candidate name.
  - Unit-test ramp weights at 72 h and 144 h.
  - Unit-test that the low-mode and sigma masks are finite, bounded, and
    broadcast only to three-dimensional divergence tendencies.
  - Verify no-op behavior when humidity is absent or nonfinite.
  - Verify the candidate suppresses the humidity vorticity correction.
  - Add registry and non-JIT finite smoke forecast coverage.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` from days 5-15 if broad
    humid-column thickness errors are accumulating in the dry incumbent.
  - Small downstream improvement in `2m_temperature` where large-scale pressure
    and height fields improve advection indirectly.
- Expected neutral metrics:
  - Day 1-3 fields should remain nearly incumbent-equivalent because the ramp is
    zero through 72 h.
  - `10m_u_component_of_wind` should be mostly neutral because the proposal does
    not change surface drag, wind diagnostics, or vorticity tendency.
- Possible regressions:
  - MSLP and Z500 may worsen after day 6 if passive humidity drift is noisier
    than the missing density signal.
  - Any broad divergence increment can perturb balanced mass fields once the
    ramp activates.

## Risks

- Numerical stability:
  - Moderate. The candidate touches the prognostic divergence tendency, but only
    through a delayed, low-mode, capped increment with finite fallback.
- Compute cost:
  - Low to moderate. The extra humidity-geopotential tendency and modal mask are
    cheap relative to the existing transforms and fixed `--workers 4` resource
    envelope.
- Data leakage:
  - None. The candidate uses only forecast state, initial humidity already in
    the input, fixed masks, and fixed lead-time ramp constants.
- Physical plausibility:
  - Moderate. Virtual temperature is physically relevant for hydrostatic
    thickness, but this candidate is a pragmatic filtered approximation rather
    than a complete moist primitive-equation model.
- Rollback complexity:
  - Low. Remove one selector, one helper, one factory/export, one registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_lm_vgeo`.
  - Require finite outputs and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_lm_vgeo --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the cached `dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent with no day 1-5
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_lm_vgeo --workers 4` only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that delayed
    humidity-density coupling is not a useful remaining signal. Any early MSLP,
    Z500, or T2m guardrail failure would show the ramp and low-mode filter are
    insufficiently protective.

## Citations

- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  *Monthly Weather Review*. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. *Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics*, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Holton, J. R. and Hakim, G. J. 2013. *An Introduction to Dynamic Meteorology*,
  fifth edition. Academic Press. See the virtual-temperature treatment of moist
  hydrostatic balance and thickness.
- Dynamaxx source reference:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` already contains
  humidity pressure/geopotential tendency helpers and humidity-aware
  geopotential diagnostics.

## Researcher Notes

This is not a retry of the rejected hydrostatic-work or baroclinic vertical-DSE
experiments: it leaves the accepted vertical-DSE increment, cap, timing, and
WTG path unchanged. It is also distinct from the rejected roughness-aware
surface-wind diagnostic because it changes a large-scale dynamical tendency, not
only output wind reduction.

The active/scrap humidity neighborhood is risky. This proposal differs from
`virtual-geopotential-mass-dse-hsl` by not changing the transported DSE scalar,
from passive-humidity transport ideas by not changing humidity advection, and
from broad virtual-temperature pressure-gradient ideas by using only a delayed,
low-mode, free-tropospheric divergence increment with vorticity suppressed. The
negative history means this should be evaluated as a targeted medium-lead
thickness test, not as evidence for broad moist dynamics.

## Evaluator Notes

### 2026-06-26T07:40:57Z

Decision: move to `staging`; ranked 2 of 2 in this proposal triage.

This is more disciplined than the scrapped
`low-mode-virtual-temperature-pressure-gradient` idea because it suppresses the
humidity vorticity term, delays activation until after 72 h, filters to broad
free-tropospheric divergence increments, and keeps the accepted vertical-DSE
ramp and output contract unchanged. The physical claim is standard enough for
triage: virtual temperature affects density and hydrostatic thickness, and the
source already has humidity-aware geopotential and humidity tendency helpers.

Keep it staged rather than ready because it still feeds passive humidity into
an active mass/divergence tendency. Local evidence around this pathway is poor:
full or bounded moist virtual-temperature dynamics were previously rejected,
the low-mode virtual pressure-gradient neighbor was scrapped, and recent
vertical-DSE perturbations either degraded early `2m_temperature` or failed to
recover useful late-lead signal. The accepted incumbent score is strong
(`-0.2197104515448394` iteration, `-0.21940899263836755` validation), so the
next implementation should avoid core pressure-gradient risk unless the lower
risk surface-residual candidate fails or read-only diagnostics show a clear
medium-lead humidity-thickness error. Caveat: if promoted later, the ramp,
spectral taper, sigma envelope, and cap must be fixed before scoring and not
tuned against iteration or validation.
