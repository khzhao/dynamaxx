---
schema_version: 1
slug: dry-static-energy-hsl-transport
title: Transport Dry Static Energy with the Accepted HSL2 Departure
status: ready
created_at: 2026-06-23T11:17:35Z
author_role: Researcher
target_model: dino_hsl2_theta
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

# Transport Dry Static Energy with the Accepted HSL2 Departure

## Hypothesis

The accepted incumbent gains come from using midpoint horizontal
semi-Lagrangian transport for dry potential-temperature anomaly. Recent HSL
trajectory variants were neutral or unstable, which argues against changing the
departure geometry again. The remaining error may instead be the transported
thermal invariant: horizontal advection of `theta` alone can create hydrostatic
thickness inconsistency when the same step also diagnoses geopotential from the
temperature column.

Dry static energy, `s = c_p T + Phi`, is the hydrostatic thermodynamic quantity
that better couples temperature transport to layer thickness. Transporting a
bounded dry-static-energy anomaly with the already accepted HSL2 departure may
reduce thermal-thickness drift without adding pressure work, changing HSL
trajectories, or touching mass/pressure tendencies.

## Mechanism

Register a side-by-side candidate such as `dino_hsl2_theta_dse_hsl`. Preserve
all incumbent options, including the midpoint HSL2 departure, weak-HS forcing,
ocean bulk sensible heat flux, theta mean recentering, SIL3 off-centering,
surface residuals, and Richardson 10 m wind diagnostic.

For the candidate only:

- compute nodal dry static energy from absolute temperature plus the incumbent
  hydrostatic sigma geopotential diagnostic;
- subtract a horizontally uniform layer reference so only the anomaly is
  horizontally HSL-transported;
- use the accepted HSL2 midpoint departure and bilinear remap to estimate the
  horizontal dry-static-energy tendency;
- convert the transported dry-static-energy tendency back to a temperature
  tendency through `c_p`, while leaving the incumbent vertical theta tendency
  and adiabatic pressure-work helper unchanged;
- finite-fallback to the accepted theta-HSL tendency if geopotential,
  dry-static-energy, or converted tendencies are nonfinite.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
- Registry changes:
  - Add one side-by-side model factory for `dino_hsl2_theta_dse_hsl`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, and metrics
    stay fixed.
- Tests to update:
  - Verify default `dino_hsl2_theta` tendencies are unchanged.
  - Verify the candidate uses the accepted HSL2 displacement path, not a new
    trajectory solver.
  - Verify finite fallback reproduces the incumbent theta-HSL tendency.
  - Verify non-thermal tendencies and output variables are unchanged by the
    option.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` if horizontal thermal
    transport is currently creating hydrostatic thickness phase error.
  - `2m_temperature` at medium leads if lower-column thermal drift partly comes
    from HSL interpolation of theta rather than energy-like temperature.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because momentum, Coriolis, and the surface wind
    diagnostic remain on the incumbent path.
- Possible regressions:
  - The accepted theta variable may already be empirically optimal, and dry
    static energy transport can over-couple temperature and geopotential.

## Risks

- Numerical stability:
  - Moderate. The trajectory is unchanged, but the thermal tendency variable
    changes every inner step.
- Compute cost:
  - Low to moderate. It adds a geopotential/dry-static-energy diagnostic before
    the existing HSL remap.
- Data leakage:
  - None. The mechanism uses only forecast state and fixed physical constants.
- Physical plausibility:
  - High as a thermodynamic-invariant test, but it must remain consistent with
    the existing pressure-work and semi-implicit split.
- Rollback complexity:
  - Low. Remove one option, helper, factory/export, registry entry, and tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_theta_dse_hsl`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_theta_dse_hsl --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_theta_dse_hsl --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta, or early Z500/MSLP guardrail
    failure, would show theta remains the better transported HSL scalar.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements the accepted HSL2 theta transport in
  `horizontal_semilagrangian_theta_transport`.
- Dynamaxx history:
  `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
  accepted `dino_hsl2_theta` with iteration delta `+0.0071755259598786925`.
- Dynamaxx history:
  `.logbook/history/2026-06-22_21-59-29_picard-hsl-theta-departure/decision.md`
  and `.logbook/history/2026-06-23_06-13-46_coriolis-centered-hsl-theta-departure/decision.md`
  rejected further trajectory refinements as effectively neutral.
- Holton, J. R. and Hakim, G. J. 2012. *An Introduction to Dynamic
  Meteorology*, fifth edition, discusses dry static energy and hydrostatic
  thermodynamics.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Durran, D. R. 2010. *Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics*, second edition. Springer.

## Researcher Notes

This is not an HSL trajectory variant: it reuses the accepted midpoint
departure exactly and changes only the thermodynamic scalar being transported.
It is also not staged `mass-flux-theta-transport`, which changes flux form and
layer mass continuity, nor staged `column-dry-static-energy-recentering`, which
is a post-step column constraint. This proposal is a narrow transported-variable
experiment on top of the accepted HSL2 path.

## Evaluator Notes

### 2026-06-23T11:21:12Z

Decision: move to `ready`; ranked 1 of 3 new proposals and recommended first.

This is the strongest immediate candidate because it tests a different
thermodynamic invariant while preserving the accepted HSL2 midpoint departure.
Recent evidence rejects changing the HSL neighborhood itself: CFL blending
failed fast, qmono remap was strongly negative, Picard and Coriolis-centered
departure changes were effectively neutral, mean-neutral HSL was far below the
promotion threshold, and the Charney-Phillips vertical theta variant failed
fast. This proposal avoids that rejected trajectory/remap pattern by keeping
the accepted departure geometry and changing only the transported thermal
scalar.

The mechanism is physically coherent: dry static energy couples temperature and
hydrostatic thickness more directly than theta alone, so it can plausibly move
`geopotential_500`, `mean_sea_level_pressure`, and `2m_temperature` without a
forecast-contract change or metric-only output remapping. It is distinct from
staged `column-dry-static-energy-recentering`, which is a post-step zero-mode
constraint, and from staged `mass-flux-theta-transport`, which changes flux
form/mass coupling rather than the HSL transported invariant. Implementation
risk is moderate but bounded by a side-by-side model, finite fallback to the
accepted theta-HSL tendency, and no changes to fixed metrics, splits, target
variables, lead times, or incumbent cache policy.
