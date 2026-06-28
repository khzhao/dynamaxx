---
schema_version: 1
slug: low-mode-virtual-temperature-pressure-gradient
title: Use Bounded Low-Mode Virtual Temperature in Pressure-Gradient Coupling
status: scrap
created_at: 2026-06-21T18:00:06Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Bounded Low-Mode Virtual Temperature in Pressure-Gradient Coupling

## Hypothesis

The incumbent keeps humidity passive in the dry dynamics, while pressure-level geopotential output already uses passive humidity through virtual temperature. Earlier full moist virtual-temperature dynamics were harmful, but that does not prove that all moisture-density information is useless: the broad failure likely mixed active high-wavenumber humidity, tracer transport noise, and full momentum feedback into every resolved scale.

A narrower candidate that uses only the bounded, low-horizontal-mode virtual-temperature correction in the sigma pressure-gradient and hydrostatic geopotential coupling may improve `geopotential_500` and MSLP through large-scale density structure while avoiding high-wavenumber moist noise, latent heating, saturation adjustment, or a new surface diagnostic.

## Mechanism

Register a side-by-side candidate extending the incumbent name with `_lowmode_virtual_pg`. Preserve the incumbent passive humidity tracer transport, DFI, weak-HS analysis equilibrium, theta tendency, theta recentering, off-centered SIL3, scale-separated residuals, Richardson wind diagnostic, target variables, and fixed protocols.

For this candidate only:

- require pressure-level specific humidity input and the existing passive humidity tracer; otherwise fall back to the incumbent dry dynamics;
- in the primitive-equation sigma diagnostic path, compute a virtual-temperature multiplier from specific humidity using the existing dry-air and water-vapor gas constants;
- transform only the humidity-derived virtual-temperature anomaly to modal space, retain a conservative low-mode mask such as total wavenumber `n <= 8` tapering to zero by `n = 14`, and clip the resulting temperature-equivalent correction to a small fixed bound;
- apply this low-mode virtual-temperature correction only in pressure-gradient and hydrostatic geopotential-difference terms that couple density to divergence and mass fields;
- do not add humidity to the thermal tendency, do not add latent heating, do not modify the passive humidity tracer tendency, and do not change output diagnostics except through the changed forecast state;
- use the same low-mode selector in DFI and positive-time rollout for consistency;
- fall back to the incumbent dry pressure-gradient path if humidity, the modal mask, corrected tendencies, or resulting state leaves are nonfinite.

This is not a revival of full moist dynamics: high-wavenumber humidity is discarded, moisture remains passive, and only large-scale density effects enter mass-coupled pressure-gradient terms.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate with a `_lowmode_virtual_pg` suffix.
- API changes:
  - None. Forecast input/output schema, lead schedule, metrics, and splits remain unchanged.
- Tests to update:
  - Unit-test the low-mode humidity mask and clipping on synthetic humidity fields.
  - Verify zero humidity anomaly exactly reproduces the incumbent dry pressure-gradient terms.
  - Verify high-wavenumber humidity anomalies are suppressed before entering pressure-gradient coupling.
  - Verify humidity tracer tendencies and output variable selection remain unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium leads if large-scale water-vapor density structure currently appears only in diagnostics but not in mass-field evolution.
  - `mean_sea_level_pressure` if virtual-temperature thickness corrections improve hydrostatic mass adjustment.
- Expected neutral metrics:
  - `2m_temperature` should stay close to incumbent because thermal forcing and screen diagnostics are unchanged.
  - `10m_u_component_of_wind` should be less exposed than in full moist dynamics because high-wavenumber humidity and direct momentum noise are suppressed.
- Possible regressions:
  - Prior moist dynamics evidence is negative; even low-mode virtual-temperature pressure gradients can perturb accepted dry balance.
  - If passive humidity transport is phase-shifted, using it dynamically may degrade Z500 or MSLP despite masking.

## Risks

- Numerical stability:
  - Moderate. The candidate changes core pressure-gradient coupling, so strict finite fallback and conservative clipping are required.
- Compute cost:
  - Low to moderate. It adds one masked humidity transform and extra density algebra in existing tendency evaluations.
- Data leakage:
  - None. It uses only same-forecast humidity already present in the initialized state.
- Physical plausibility:
  - Moderate. Virtual temperature is physically relevant to hydrostatic thickness and pressure gradients, but the low-mode restriction is a pragmatic guard against known moist-dynamics failures.
- Rollback complexity:
  - Moderate. Remove one primitive-equation option, one adapter flag, one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_lowmode_virtual_pg`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_lowmode_virtual_pg --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_lowmode_virtual_pg --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A fast diagnostic failure, clean negative iteration delta, or early MSLP/Z500 guardrail regression would show that even bounded low-mode virtual-temperature coupling disrupts the accepted dry balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` carries passive humidity tracers and uses humidity in `get_geopotential_on_sigma` for output reconstruction while keeping `use_humidity_in_dynamics` false for the incumbent.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` already contains humidity-aware virtual-temperature pressure-gradient helpers behind the `humidity_key` path, which can be narrowed rather than reinvented.
- Dynamaxx history: `.logbook/history/2026-06-16_07-36-31_moist-virtual-temperature-dynamics/decision.md` and `.logbook/history/2026-06-17_18-02-45_bounded-moist-virtual-temperature-dynamics/decision.md` are strong negative evidence against full moist dynamics.
- Dynamaxx history: `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md` showed that removing passive humidity from virtual-temperature geopotential diagnostics regressed Z500, so large-scale humidity density information remains physically relevant.
- Emanuel, K. A. 1994. Atmospheric Convection. Oxford University Press, for virtual temperature and moist hydrostatic thickness context.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum conserving vertical finite-difference scheme and hybrid vertical coordinates. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AECAAM%3E2.0.CO;2

## Researcher Notes

This proposal deliberately avoids surface diagnostics, screen-temperature nudging, startup-only fixes, off-centering changes, and diffusion/projection variants. It is distinct from failed full moist dynamics because humidity remains passive, high modes are removed, and the only new dynamic role is a bounded large-scale density correction in pressure-gradient coupling.

## Evaluator Notes

### 2026-06-21T18:04:23Z

Decision: move to `scrap`; ranked 3 of 3 in this triage pass.

Reject this as too close to a failed moist-dynamics family and too risky for the
current incumbent. The proposal is more restrained than enabling full
humidity-aware dynamics, but it still feeds passive humidity into the core
pressure-gradient and hydrostatic coupling in both DFI and positive-time
rollout. That is exactly the pathway where prior evidence is strongest against
promotion: the original moist virtual-temperature dynamics failed fast with
nonfinite forecasts, and the bounded moist version later ran cleanly but
regressed iteration by `-0.055193744700895`. The largest bounded-moist guardrail
movement was early `10m_u_component_of_wind`, consistent with
humidity-altered pressure gradients perturbing balanced flow.

The positive humidity evidence is diagnostic, not dynamic. Removing passive
humidity from geopotential output caused a large 24 h `geopotential_500`
guardrail failure, so the incumbent should keep humidity in virtual-temperature
geopotential reconstruction. That result does not support reintroducing
humidity into pressure-gradient tendencies, even with an ad hoc low-mode mask
and clipping. The current staging queue already contains narrower humidity
uses, such as `virtual-temperature-analysis-hs-offset`, that avoid active moist
pressure-gradient feedback.

The low-mode mask and fixed clip would also add new tuning degrees of freedom
without a read-only diagnostic showing that broadscale humidity density
feedback is the remaining error source. Under the fixed protocols and current
incumbent, the expected cost-risk tradeoff is worse than the staged pressure
and analysis-offset alternatives, so this should not remain staged.
