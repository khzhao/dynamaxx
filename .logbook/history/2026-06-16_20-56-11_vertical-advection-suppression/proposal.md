---
schema_version: 1
slug: vertical-advection-suppression
title: Suppress Explicit Vertical Advection in the Incumbent Dynamics
status: ready
created_at: 2026-06-16T19:54:27Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Suppress Explicit Vertical Advection in the Incumbent Dynamics

## Hypothesis

The incumbent starts from WeatherBench2 pressure-level analyses, interpolates
them onto sigma levels, and runs a dry primitive-equation model with zero
orography, DFI, weak thermal relaxation, and near-surface diagnostic residuals.
The accepted weak-Held-Suarez candidate shows that correcting large thermal
drift helps, while recent pressure-anchor and 600 s inner-step experiments show
that one-mode mass constraints and simple time-step convergence are not the next
limiting factors.

The remaining error may come partly from explicit vertical transport terms that
move wind, temperature variation, and passive tracers through a sigma-coordinate
column initialized from pressure-level data without matching physical
parameterizations. Suppressing explicit vertical advection is a bounded
dynamical ablation already supported by the local `include_vertical_advection`
switch. It preserves horizontal advection, pressure-gradient coupling,
adiabatic temperature tendency, semi-implicit gravity-wave treatment, DFI, weak
thermal relaxation, and the output contract, while testing whether the current
vertical transport coupling is helping or hurting 1-15 day forecasts.

## Mechanism

Register a side-by-side factory that preserves the accepted incumbent flags but
sets `include_vertical_advection=False`:

- candidate model name: `dinosaur_dfi_surface_residual_weak_hs_no_vadv`
- keep `apply_digital_filter_initialization=True`
- keep `apply_near_surface_residual_correction=True`
- keep `apply_weak_held_suarez_relaxation=True` with incumbent coefficients
- keep default `900.0` s inner step and default horizontal diffusion
- disable only the explicit sigma-dot vertical advection terms controlled by
  `include_vertical_advection`

This should not require new data, metrics, adapters, forecast outputs, or
evaluation protocols. It is a single fixed ablation, not a sweep over vertical
transport strength.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - registry tests under `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dinosaur_dfi_surface_residual_weak_hs_no_vadv`.
- API changes:
  - None. `ForecastInput`, `WeatherState`, requested variables, leads, and
    deterministic output shape are unchanged.
- Tests to update:
  - Verify the candidate factory preserves incumbent DFI, weak-Held-Suarez, and
    near-surface residual flags while setting `include_vertical_advection=False`.
  - Verify the incumbent factory still has `include_vertical_advection=True`.
  - Add registry coverage and a finite non-JIT smoke forecast for the candidate.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and long leads if
    explicit sigma-coordinate vertical transport is amplifying column-structure
    error from pressure-level initialization.
  - `10m_u_component_of_wind` could improve or remain neutral if suppressing
    vertical wind transport avoids part of the incumbent's long-lead low-level
    wind drift.
- Expected neutral metrics:
  - Early day-1 outputs should remain close to the incumbent because DFI,
    horizontal dynamics, thermal relaxation, and diagnostic residuals are
    unchanged.
- Possible regressions:
  - Baroclinic development and vertical temperature structure may degrade if
    explicit vertical advection is physically important for the evaluated flow.
  - `2m_temperature` can regress if the vertical transport terms help maintain
    lower-tropospheric thermal structure after weak thermal relaxation.

## Risks

- Numerical stability:
  - Low. The code path already exists and removes tendencies rather than adding
    a new source term, but a fast gate is still required.
- Compute cost:
  - Low. It may be slightly cheaper than the incumbent because several vertical
    tendency calculations become zero.
- Data leakage:
  - Low. The candidate uses a fixed local model switch and no future truth,
    validation statistics, climatology, or target-specific fitting.
- Physical plausibility:
  - Moderate to high risk. Vertical advection is a real primitive-equation
    process; the hypothesis is only that this particular dry sigma-coordinate
    setup may represent it poorly for WeatherBench2 pressure-level forecasts.
- Rollback complexity:
  - Low. A side-by-side factory and registry entry can be reverted without
    touching accepted incumbent code.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_no_vadv`.
  - Require clean diagnostics and finite outputs.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_no_vadv --workers 4`.
  - Compare only against `dinosaur_dfi_surface_residual_weak_hs` records by
    exact model name.
  - Require primary delta at least `+0.002`, clean diagnostics, no early
    day 1-5 mean RMSE regression above 2 percent, and no variable-lead RMSE
    regression above 10 percent.
- Validation gate:
  - Run validation only if iteration promotes:
    `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_no_vadv --workers 4`.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with worse or sub-threshold primary score
    would show that explicit vertical advection is not a harmful remaining
    coupling for the current incumbent. Any early 2 m temperature or Z500
    guardrail failure would indicate that the ablation removed essential
    baroclinic structure.

## Citations

- Staniforth, A. and Cote, J. 1991. "Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review." Monthly Weather Review, 119, 2206-2223.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lin, S.-J. and Rood, R. B. 1996. "Multidimensional Flux-Form Semi-Lagrangian
  Transport Schemes." Monthly Weather Review, 124, 2046-2070.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, 2nd edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  uses `include_vertical_advection` to control sigma-dot vertical tendencies in
  horizontal wind, temperature, and tracer tendency calculations.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` already
  exposes `include_vertical_advection` on `DinosaurPrimitiveEquationsDycoreModel`,
  so a side-by-side factory can test this without changing the forecast API.

## Researcher Notes

This is not a duplicate of `pressure-aware-sigma-layer-grid` or `standard-
atmosphere-reference-profile`: it does not change the sigma grid, reference
temperature, or pressure interpolation. It is also not a duplicate of
`six-hundred-second-inner-step`: it does not alter time-step size or perform a
time-discretization sweep. The proposal tests one physical-numerical coupling
that remains active in the accepted incumbent.

This candidate is intentionally riskier than the divergence-selective damping
proposal because it removes a real primitive-equation process. Its value is as a
single bounded ablation with a cheap implementation surface and clear
falsification under the fixed iteration gate. It must not be combined with any
other idea in the same iteration.

## Evaluator Notes

2026-06-16T19:57:10Z - Move to `staging`.

This proposal is implementable and distinct from recent rejected pressure,
time-step, reference-profile, or residual candidates. Source inspection
confirms `include_vertical_advection` is already a
`DinosaurPrimitiveEquationsDycoreModel` flag and controls vertical tendencies
in wind, temperature, and tracer paths, so a side-by-side
`dinosaur_dfi_surface_residual_weak_hs_no_vadv` factory would be low surface
area and easy to roll back.

Do not promote it ahead of the divergence-selective candidate. Suppressing
vertical advection removes a real primitive-equation process across multiple
state components, so the physical risk is broader than a selective divergence
filter. The cited literature supports the importance and numerical treatment
of transport, but it does not by itself establish that disabling explicit
vertical advection should improve this WeatherBench2 incumbent. It may still
be useful as a bounded ablation after a lower-risk, more targeted experiment.

Ranked recommendation: 1. keep staged behind
`divergence-selective-gravity-wave-damping`; 2. promote only if the ready
candidate is rejected cleanly or if a future Researcher pass adds stronger
evidence that vertical sigma-coordinate transport is the active error source
for `dinosaur_dfi_surface_residual_weak_hs`.

2026-06-16T20:55:33Z - Move to `ready`.

The clean rejection of `divergence-selective-gravity-wave-damping` satisfies the
prior promotion condition for this staged proposal. That candidate was stable,
diagnostic-clean, and guardrail-clean, but its iteration primary delta was
negative (`-0.00020461043258523937`), so another damping-style change is not the
best next direction.

`vertical-advection-suppression` remains physically riskier because it disables
a real primitive-equation process across wind, temperature, and tracer
tendencies. It is still suitable as the next single candidate because it tests
a different vertical-transport coupling, preserves the forecast contract and
fixed WeatherBench2 protocols, requires only a side-by-side factory using the
existing `include_vertical_advection` switch, and is cleanly falsifiable by the
normal fast and iteration gates. Recent clean rejections of the pressure anchor,
fixed `600.0` s inner step, and divergence-only damping reduce the priority of
mass-mode, time-step, and damping follow-ups, making this bounded ablation the
strongest remaining active proposal.

Ranked recommendation: implement
`dinosaur_dfi_surface_residual_weak_hs_no_vadv` next as the sole ready
iteration 14 candidate. Do not combine it with any other idea, do not change the
evaluation protocol, and do not run golden for selection.
