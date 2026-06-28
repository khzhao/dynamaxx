---
schema_version: 1
slug: dse-aware-held-suarez-relaxation
title: Relax Dry Static Energy Toward the Analysis-Offset Held-Suarez State
status: staging
created_at: 2026-06-23T18:04:37Z
author_role: Researcher
target_model: dino_hsl2_theta_dse_hsl
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Relax Dry Static Energy Toward the Analysis-Offset Held-Suarez State

## Hypothesis

The incumbent still applies weak Held-Suarez relaxation as a temperature
tendency, while the latest accepted transport result shows that dry static
energy is a better thermal variable for horizontal evolution. The weak-HS
analysis-offset equilibrium is useful, but its temperature-form relaxation can
act against the DSE-HSL tendency by nudging temperature without considering the
hydrostatic geopotential part of the column.

A side-by-side candidate should test a DSE-aware relaxation variable: compute
the standard analysis-offset Held-Suarez equilibrium temperature, convert both
the current and equilibrium states to dry static energy using the same
hydrostatic sigma geopotential diagnostic, relax the DSE anomaly at the same
weak-HS rates, and convert the heating back to temperature through `c_p`. This
keeps the accepted rates, masks, and analysis offset but aligns the relaxation
variable with the accepted DSE-HSL invariant.

## Mechanism

Register a candidate such as `dino_hsl2_theta_dse_hs_dse_relax`.

For the candidate only:

- preserve the incumbent analysis-offset Held-Suarez equilibrium construction
  and its low-order spectral cap;
- inside the weak-HS forcing, diagnose current dry static energy
  `s = c_p T + Phi(T)`;
- diagnose equilibrium dry static energy
  `s_eq = c_p T_eq + Phi(T_eq)` using the same sigma-coordinate hydrostatic
  operator and zero orography used by the incumbent;
- compute `-(s - s_eq) * k_t / c_p` as the thermal tendency instead of
  `-(T - T_eq) * k_t`;
- leave friction, momentum, log-surface-pressure, tracers, HSL2 departure,
  DSE-HSL transport, surface residuals, and output diagnostics unchanged;
- finite-fallback to the incumbent temperature-form weak-HS tendency if any DSE
  diagnostic is invalid.

This is not a pressure-work replacement, not a lead ramp, and not a change to
fixed evaluation metrics or output variables.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model factory for the DSE-aware weak-HS relaxation
    candidate.
- API changes:
  - None.
- Tests to update:
  - Verify the incumbent weak-HS forcing remains unchanged by default.
  - Verify DSE-aware relaxation produces zero tendency when current and
    equilibrium DSE match.
  - Verify invalid DSE diagnostics fall back to the incumbent weak-HS tendency.
  - Verify model registration and unchanged forecast contract.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` if temperature-form weak-HS
    relaxation is now the main source of thermal-thickness inconsistency after
    DSE-HSL transport.
  - Medium-lead `2m_temperature` if lower-column relaxation better respects
    hydrostatic column energy.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because friction is unchanged and no momentum
    tendencies are modified directly.
- Possible regressions:
  - Weak-HS temperature relaxation may already be empirically tuned to the fixed
    benchmark; DSE relaxation could weaken beneficial near-surface damping.
  - Short-lead Z500 could regress if equilibrium geopotential amplifies vertical
    structure errors in the first day.

## Risks

- Numerical stability:
  - Low to moderate. The forcing is weak and bounded, but it touches every
    thermal tendency step.
- Compute cost:
  - Low. It adds two hydrostatic geopotential diagnostics inside an already
    weak thermal forcing.
- Data leakage:
  - None. The analysis offset is already part of the incumbent and uses only the
    initial forecast state.
- Physical plausibility:
  - Good as a consistency test after accepted DSE-HSL, though Held-Suarez is an
    idealized forcing rather than a full physical parameterization.
- Rollback complexity:
  - Low. Remove one forcing option, factory/export, registry key, and tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_theta_dse_hs_dse_relax`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_theta_dse_hs_dse_relax --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_theta_dse_hs_dse_relax --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show that the
    accepted DSE-HSL benefit does not transfer to the weak-HS relaxation
    variable. A short-lead Z500/MSLP guardrail failure would indicate that the
    DSE equilibrium is less balanced than the incumbent temperature equilibrium.

## Citations

- Dynamaxx source: `_TracerSafeHeldSuarezForcingSigma` and
  `_analysis_offset_weak_held_suarez_equilibrium` in
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` define the incumbent weak-HS
  relaxation path.
- Dynamaxx history:
  `.logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium/decision.md`
  accepted the analysis-offset Held-Suarez equilibrium, making it the correct
  baseline forcing path to preserve.
- Dynamaxx history:
  `.logbook/history/2026-06-23_11-22-34_dry-static-energy-hsl-transport/decision.md`
  accepted DSE-HSL, motivating a DSE-variable relaxation test.
- Held, I. M. and Suarez, M. J. 1994. A Proposal for the Intercomparison of
  the Dynamical Cores of Atmospheric General Circulation Models. Bulletin of
  the American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Jablonowski, C. and Williamson, D. L. 2006. A Baroclinic Instability Test
  Case for Atmospheric Model Dynamical Cores. Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1256/qj.06.12

## Researcher Notes

This proposal is decorrelated from the latest HSL transport candidates because
it changes only the weak thermal relaxation variable. It is not a pressure-work
replacement or ramp, does not use passive humidity, does not touch terrain, and
does not change the forecast contract. It is also distinct from staged lapse,
solar, and column-neutral weak-HS ideas: the rates and equilibrium source are
kept fixed, while the relaxed thermodynamic variable is changed to match the
accepted DSE-HSL invariant.

## Evaluator Notes

### 2026-06-23T18:45:00Z

Decision: move to `staging`; ranked 2 of 3 current proposals.

The mechanism is scientifically coherent: after the accepted DSE-HSL transport
win, it is reasonable to ask whether the weak Held-Suarez thermal relaxation
should act on the same dry-static-energy variable rather than raw temperature.
It keeps the accepted analysis-offset equilibrium source, rates, forecast
contract, and output variables unchanged, and it should be clean to roll back as
one forcing option plus model registration and tests.

Do not make it the immediate ready candidate. The weak-HS family is already
crowded in staging, including column-neutral, lapse-rate, static-stability, and
tropopause-capped variants. Prior evidence is mixed: the analysis-offset
Held-Suarez equilibrium was a strong accepted improvement, but several
follow-ups to weak-HS structure or thermal repair have been neutral or
negative. This proposal also adds extra hydrostatic-geopotential diagnostics
inside a forcing path every step, so the implementation surface is broader than
the mass-weighted DSE-HSL transport test.

This should stay staged as a credible second-line experiment. It becomes more
attractive if the mass-weighted DSE-HSL idea is neutral or if diagnostics point
to weak-HS thermal-thickness drift after the accepted DSE transport. If
promoted, require exact incumbent fallback, tests that the default weak-HS path
is unchanged, and close inspection of short-lead Z500/MSLP guardrails.
