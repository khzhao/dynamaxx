---
schema_version: 1
slug: log-humidity-passive-tracer
title: Transport Passive Humidity in Log Space
status: staging
created_at: 2026-06-19T05:06:32Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
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

# Transport Passive Humidity in Log Space

## Hypothesis

The incumbent carries pressure-level specific humidity as a passive tracer even
when humidity is not used in the prognostic dynamics. That passive humidity is
then used in virtual-temperature geopotential reconstruction. Spectral transport
of a positive tracer can create small negative or high-amplitude humidity
values, and the prior after-the-fact humidity positivity limiter was essentially
neutral. A stronger but still local representation change is to advect
log-specific-humidity as the passive tracer and exponentiate only for output and
geopotential diagnostics. This keeps humidity positive by construction and may
reduce noisy virtual-temperature contributions to `geopotential_500` without
adding moist feedback to the primitive-equation tendencies.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logq`.
Preserve the incumbent dry dynamics, DFI, weak Held-Suarez forcing, log-pressure
and hydrostatic initialization, symmetric Coriolis split, theta tendency, theta
recenter filter, near-surface residual correction, Richardson 10 m wind
diagnostic, output variables, lead times, and fixed scoring protocols.

For the candidate only:

- during `weather_state_to_dinosaur_state`, clip input pressure-level specific
  humidity to a fixed small positive floor before pressure-to-sigma
  interpolation;
- convert the passive humidity tracer to `log(q)` before storing it in
  `state.tracers`;
- advect `log(q)` with the existing passive tracer machinery, without setting
  `humidity_key` for dynamics and without introducing latent heating or virtual
  temperature in the momentum equations;
- in `dinosaur_state_to_weather_state`, recover diagnostic humidity with
  `exp(logq)` and a fixed finite upper bound before passing it to
  `get_geopotential_on_sigma` and before packing any requested humidity output;
- keep the incumbent fallback if the recovered humidity is nonfinite or outside
  broad physical bounds;
- do not alter temperature, winds, log surface pressure, MSLP, residual
  correction, or pressure-level interpolation except through the recovered
  humidity's virtual-temperature contribution to geopotential.

This is a representation change for a passive tracer. It does not change the
forecast API or add target-dependent post-processing.

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
  - None. The candidate accepts and emits the same `WeatherState` variables as
    the incumbent when humidity channels are present.
- Tests to update:
  - Unit-test humidity floor, log transform, exponentiation, upper-bound guard,
    and finite fallback behavior.
  - Verify dry dynamics stay dry: `humidity_key` remains unset unless a separate
    non-incumbent option explicitly enables moist dynamics.
  - Verify the candidate factory preserves every incumbent option except the
    passive log-humidity selector.
  - Verify pressure-level humidity outputs, when requested, remain positive and
    finite with unchanged names and shapes.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium and long leads if passive humidity overshoots
    currently contaminate virtual-temperature geopotential reconstruction.
  - `mean_sea_level_pressure` may improve slightly through better hydrostatic
    consistency of pressure-level diagnostics, although the prognostic pressure
    path is unchanged.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should be close to neutral
    because temperature, wind, residual correction, and 10 m wind diagnostics are
    unchanged directly.
- Possible regressions:
  - Advecting `log(q)` changes tracer averaging behavior and can introduce a dry
    bias after exponentiation.
  - If the existing passive humidity path is already benign, score movement may
    be near zero, as in the rejected humidity positivity limiter.

## Risks

- Numerical stability:
  - Low. The candidate keeps humidity passive and finite with explicit guards,
    but exponential recovery must be bounded.
- Compute cost:
  - Low. It adds local `log`, `exp`, and clipping operations and does not change
    rollout length, resolution, or output volume.
- Data leakage:
  - None. It uses only same-time forecast state and fixed bounds.
- Physical plausibility:
  - Moderate. Positive-definite moisture transport is physically desirable, but
    log-space advection changes the implied mean humidity and is not mass
    conserving.
- Rollback complexity:
  - Low. Remove one representation selector/helper, one factory/export, one
    registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logq`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logq --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logq --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that log-space
    passive humidity does not improve the current virtual-temperature diagnostic
    path. A Z500 short-lead regression would show the transformed humidity is a
    worse diagnostic input than the incumbent specific-humidity tracer.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` stores humidity in
  `state.tracers` even when `use_humidity_in_dynamics` is false, and
  `dinosaur_state_to_weather_state` uses that passive humidity in
  `primitive_equations.get_geopotential_on_sigma`.
- Dynamaxx history:
  `.logbook/history/2026-06-16_21-13-22_passive-humidity-positivity-limiter/decision.md`
  rejected an after-the-fact positivity limiter with iteration delta
  `-0.0000019440828125105725`; this proposal changes the transported variable
  rather than clipping the transported `q` field after rollout.
- Dynamaxx history:
  `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
  showed that removing passive humidity from geopotential diagnostics regressed
  day-1 Z500, so this proposal preserves humidity's diagnostic role.
- ECMWF IFS Documentation CY48R1, Part III: Dynamics and Numerical Procedures,
  discusses spectral transforms and positive-definite tracer handling in the
  IFS context.
  https://www.ecmwf.int/sites/default/files/elibrary/2023/81369-ifs-documentation-cy48r1-part-iii-dynamics-and-numerical-procedures.pdf
- Diamantakis, M. and Agusti-Panareda, A. 2017. "A positive definite tracer mass
  fixer for high resolution weather and atmospheric composition forecasts."
  ECMWF Technical Memorandum 819.
  https://www.ecmwf.int/sites/default/files/elibrary/2017/17914-positive-definite-tracer-mass-fixer-high-resolution-weather-and-atmospheric-composition.pdf
- Dee, D. P. and da Silva, A. M. 2003. "The Choice of Variable for Atmospheric
  Moisture Analysis." Monthly Weather Review, 131, 155-171.
  https://journals.ametsoc.org/view/journals/mwre/131/1/1520-0493_2003_131_0155_tcovfa_2.0.co_2.xml

## Researcher Notes

This is not a duplicate of rejected `passive-humidity-positivity-limiter`,
which transported specific humidity normally and then clipped negative values.
Here the transported passive scalar is `log(q)`, so positivity is built into
the representation before spectral transport and DFI averaging. It is also not a
repeat of `bounded-moist-virtual-temperature-dynamics` or `moist-virtual-
temperature-dynamics`: humidity remains passive and does not enter momentum,
pressure, or thermodynamic tendencies.

The proposal uses negative evidence directly. Humidity is still needed for the
Z500 diagnostic, but broad moist dynamics have been harmful. The new mechanism
therefore changes only the passive tracer representation that feeds diagnostic
virtual temperature.

## Evaluator Notes

### 2026-06-19T05:10:10Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

The proposal is scientifically plausible and distinct from the rejected
`passive-humidity-positivity-limiter`: positivity is built into the transported
passive variable rather than applied after rollout. It also respects the
important negative result from `dry-consistent-geopotential-diagnostic`, where
removing humidity from virtual-temperature geopotential reconstruction caused a
day-1 Z500 guardrail failure. Keeping humidity passive and diagnostic-only is
the right boundary for this research family.

Keep it staged rather than ready because prior humidity evidence points to a
small expected effect. The clip-after-transport limiter was clean but slightly
negative (`-0.0000019440828125105725`), and there is not yet read-only evidence
that passive humidity undershoots or spectral overshoots materially affect the
current incumbent's fixed target variables. Advecting `log(q)` also changes
humidity means and can introduce a dry diagnostic bias, so it is not a purely
conservative positivity fix.

If promoted later, require narrow tests proving dry dynamics remain dry,
humidity stays finite and positive after exponentiation, and only the passive
humidity tracer plus downstream virtual-temperature geopotential diagnostic are
allowed to differ from the incumbent.
