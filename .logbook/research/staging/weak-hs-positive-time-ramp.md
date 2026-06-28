---
schema_version: 1
slug: weak-hs-positive-time-ramp
title: Ramp Weak Held-Suarez Forcing During Positive-Time Spinup
status: staging
created_at: 2026-06-20T04:46:29Z
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

# Ramp Weak Held-Suarez Forcing During Positive-Time Spinup

## Hypothesis

The accepted weak Held-Suarez relaxation remains useful, but it is applied at
full strength immediately after DFI and after the hydrostatic/theta
initialization chain. Several forcing-family experiments show that removing or
restructuring the source can damage `2m_temperature`, while exact time
integration of the same source was clean but too weak. A short positive-time
ramp should preserve the accepted long-lead thermal relaxation while reducing
early adjustment shocks in pressure, thickness, and screen temperature.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_hs_ramp`.
Preserve the incumbent DFI, residual corrections, log-pressure and hydrostatic
initialization, Strang Coriolis split, theta tendency, theta recentering,
SIL3 off-centering, and scale-separated near-surface residual memory.

For this candidate only:

- add an opt-in Held-Suarez forcing wrapper that multiplies the existing weak
  thermal tendency by a smooth ramp from `0` to `1` over a fixed positive-time
  window, for example 24 hours;
- initialize `State.sim_time` only for this candidate so the ramp is tied to
  forecast model time and not to output lead post-processing;
- keep DFI on the incumbent full-strength weak-HS equation so this is not
  another DFI routing experiment;
- keep the asymptotic weak-HS tendency exactly equal to the incumbent after the
  ramp window;
- leave vorticity, divergence, `log_surface_pressure`, tracers, pressure-level
  interpolation, target variables, lead times, and metrics unchanged;
- fall back to the incumbent weak-HS tendency if model time or the ramp factor
  is nonfinite.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. Forecast inputs, outputs, leads, target variables, metrics, and fixed
    protocols remain unchanged.
- Tests to update:
  - Unit-test ramp values at `t=0`, mid-window, and after the window.
  - Verify DFI still uses the incumbent full-strength weak-HS path.
  - Verify the candidate equals incumbent weak-HS forcing after the ramp.
  - Verify non-HS models and missing `sim_time` states retain incumbent behavior.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 1 to 5 if abrupt
    weak-HS activation creates an early thermal/thickness adjustment.
  - `2m_temperature` after day 1 if the accepted residual correction benefits
    from a less shocked lower-column thermal state.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should stay close to incumbent because wind state,
    Coriolis splitting, and 10 m diagnostics are unchanged.
  - Long leads should approach incumbent behavior once the ramp reaches unity.
- Possible regressions:
  - If full-strength weak-HS immediately corrects an important cold bias, the
    ramp can worsen early or medium-lead `2m_temperature`.
  - Any thermal source timing change can perturb pressure-gradient balance.

## Risks

- Numerical stability:
  - Low to moderate. The forcing is weaker than incumbent early and identical
    later, but it changes the thermal trajectory during spinup.
- Compute cost:
  - Negligible. It adds scalar time algebra to the existing forcing.
- Data leakage:
  - None. It uses only model time and fixed constants.
- Physical plausibility:
  - Moderate. Gradual insertion is consistent with spinup/IAU practice, but the
    ramp is a pragmatic dycore bias-control envelope rather than a physical
    radiation scheme.
- Rollback complexity:
  - Low. Remove one forcing selector/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_hs_ramp`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_hs_ramp --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_hs_ramp --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show abrupt weak-HS
    activation is not a material remaining spinup error. Any early
    `2m_temperature`, MSLP, or Z500 guardrail failure would show the accepted
    full-strength source is needed immediately.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` composes the
  current weak Held-Suarez thermal forcing through `_compose_weak_held_suarez_equation`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  already carries optional `State.sim_time` tendencies, making a time-ramped
  forcing mechanically local.
- Dynamaxx history:
  `.logbook/history/2026-06-16_16-27-03_wind-sparing-held-suarez-relaxation/decision.md`
  accepted weak thermal relaxation, so this proposal preserves the long-lead
  source rather than removing it.
- Dynamaxx history:
  `.logbook/history/2026-06-18_22-27-09_theta-consistent-held-suarez-forcing/decision.md`
  and `.logbook/history/2026-06-18_01-58-44_exact-weak-hs-thermal-split/decision.md`
  show weak-HS implementation details were clean but subthreshold, motivating a
  different source-timing mechanism.
- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
  Assimilation Using Incremental Analysis Updates. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2

## Researcher Notes

This is not a residual-memory proposal and does not change low-mode or
stability-aware residual lifetimes. It is also not `mass-neutral-weak-hs-forcing`
or `column-neutral-weak-hs-heating-split`: no vertical redistribution or
column-integral compensation is introduced. Unlike exact weak-HS source
integration or DFI weak-HS splitting, the only scientific question is whether a
full-strength external relaxation should be delayed during the first positive
forecast day.

## Evaluator Notes

### 2026-06-20T04:52:50Z

Decision: move to `staging`, not `ready`.

The mechanism is distinct from prior weak-HS source experiments and is
scientifically plausible: IAU and physics-dynamics coupling literature support
gradual insertion of increments or forcings as a way to reduce spinup shocks.
Source inspection also confirms the implementation can be localized because
weak-HS forcing is composed in `adapter.py`, and `State.sim_time` is already
advanced by the time integrator when initialized.

Do not spend the next implementation here. Local evidence for weak-HS timing
changes is weak: DFI weak-HS splitting was effectively neutral at
`+0.0000017470501787464343`, exact weak-HS source integration was clean but
only `+0.000047270501076557`, and theta-consistent weak-HS forcing was clean
but only `+0.000008267650489002243`. The mass-neutral weak-HS variant also
showed that removing the accepted thermal mean can badly damage
`2m_temperature`. A positive-time ramp is more intrusive than the neutral
time-discretization variants because it weakens accepted thermal relaxation for
the first forecast day.

If promoted later, the Implementer must keep DFI on the incumbent full-strength
weak-HS path, set `sim_time=0` only after DFI for the positive-time rollout,
make the forcing exactly incumbent after the ramp window, and add finite and
missing-time fallback tests.
