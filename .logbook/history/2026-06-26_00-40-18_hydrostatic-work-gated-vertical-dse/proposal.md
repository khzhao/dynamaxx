---
schema_version: 1
slug: hydrostatic-work-gated-vertical-dse
title: Hydrostatic-Work-Gated Vertical DSE Increment
status: ready
created_at: 2026-06-26T00:10:51Z
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

# Hydrostatic-Work-Gated Vertical DSE Increment

## Hypothesis

The accepted incumbent recovered most of the previously rejected vertical-DSE
signal with a fixed zero-through-24 h, full-by-72 h pressure ramp, broad low-mode
spinup guard, and `0.05 K` per-step cap. The two immediate follow-ups are
negative evidence against changing that timing or cap: earlier internal-mode
spinup failed through early `2m_temperature`, and late cap widening was clean
but slightly score-negative.

The remaining vertical-DSE question is therefore where the accepted increment
should act, not when or how strongly it should be capped. A local hydrostatic
work gate can preserve vertically redistributive DSE increments while damping
the subset whose column-net thermal work is large relative to their vertical
structure. That should reduce pressure/thickness imbalance risk without
repeating early spinup, late cap release, or boundary-layer sheltering.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_hwg`, derived from the current incumbent.

Inside `pressure_ramped_vertical_dse_increment_temperature_tendency`:

- compute the incumbent raw vertical-DSE increment, forecast-time ramp,
  low-mode pressure guard, finite diagnostics, and per-step cap inputs exactly
  as today;
- before clipping, decompose the pressure-guarded increment into a
  pressure-thickness-weighted column mean and a column-neutral vertical
  residual at each horizontal grid point;
- compute a bounded hydrostatic-work ratio, for example
  `abs(column_mean) / (rms_vertical_increment + epsilon)`, using the existing
  guarded sigma-layer pressure thickness;
- when that ratio is small, leave the accepted increment unchanged; when it is
  large, smoothly blend only the column-mean part toward zero while preserving
  the column-neutral residual;
- apply the incumbent `0.05 K` per-step cap after the blend, with no late cap
  widening and no earlier activation than the incumbent ramp;
- leave WTG relaxation, horizontal mass-DSE HSL transport, weak-HS forcing,
  surface residuals, pressure-level output packing, and target variables
  unchanged;
- fall back exactly to the incumbent vertical-DSE branch if pressure thickness,
  work ratios, blended increments, or capped modal tendencies are nonfinite.

This is a hydrostatic-work selectivity test for the accepted vertical-DSE
increment. It does not add a new heat source and does not change the forecast
contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key such as
    `dino_hsl2_mass_dse_wtg_vdse_hwg`.
- API changes:
  - None. Forecast inputs, outputs, lead steps, target variables, metrics, and
    fixed evaluation protocols remain unchanged.
- Tests to update:
  - Verify disabled-selector behavior is incumbent-equivalent.
  - Verify a column-neutral synthetic vertical-DSE increment is unchanged.
  - Verify a column-uniform synthetic increment is smoothly damped by the work
    gate but still bounded by the incumbent per-step cap.
  - Verify the gate keeps the incumbent ramp values and zero-through-24 h
    behavior unchanged.
  - Verify nonfinite pressure thickness, work ratio, or blended increment falls
    back to the incumbent branch.
  - Add factory, dependency, registry, and finite smoke-forecast coverage.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium leads if part of
    the accepted vertical-DSE increment still applies column-net hydrostatic work
    in places where it is not balanced by pressure evolution.
  - `2m_temperature` should improve or remain neutral if the rejected internal
    spinup's early T2m damage came from net lower-column heat rather than useful
    vertical redistribution.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should move mainly through downstream mass-field
    feedback because momentum and the 10 m diagnostic stay unchanged.
  - Leads before the incumbent vertical-DSE ramp starts should remain exactly or
    numerically equivalent to the incumbent.
- Possible regressions:
  - The accepted vertical-DSE gain may depend on some column-net heating or
    cooling that this gate removes.
  - Over-damping the column-mean component can give back Z500/MSLP benefit while
    leaving the T2m cold bias unresolved.

## Risks

- Numerical stability:
  - Low to moderate. The gate is a bounded convex blend followed by the
    incumbent cap, but it changes an active thermodynamic tendency every step
    after the ramp.
- Compute cost:
  - Low. It adds one pressure-thickness-weighted vertical reduction, local
    ratios, and local blending in an existing tendency path.
- Data leakage:
  - None. It uses only forecast state, fixed sigma geometry, and fixed constants.
- Physical plausibility:
  - Moderate to high. Hydrostatic primitive-equation thermodynamics should not
    inject large column-net heat without compatible mass/thickness response; the
    gate keeps the vertical-DSE redistribution while limiting that work mode.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_hwg`.
  - Require finite outputs and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_hwg --workers 4`.
  - Support requires primary delta at least `+0.002` against cached
    `dino_hsl2_mass_dse_wtg_vdse_ramp`, clean diagnostics, no early day-1-to-5
    mean RMSE guardrail failure, and no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_hwg --workers 4`
    only after iteration promotion.
  - Support requires validation delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the incumbent
    vertical-DSE increment already has the useful hydrostatic-work balance. Any
    early T2m, MSLP, or Z500 guardrail failure would show the gate removed a
    compensating component or was implemented too broadly.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` implements the
  accepted pressure-ramped vertical-DSE increment and already diagnoses guarded
  sigma-layer pressure thickness for the mass-DSE path.
- Dynamaxx history:
  `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg`
  accepted the current incumbent with iteration delta `+0.03880190339341674`
  and validation delta `+0.03763133840279842`.
- Dynamaxx history:
  `.logbook/history/2026-06-25_17-17-23_baroclinic-mode-vertical-dse-spinup`
  rejected earlier internal vertical-DSE spinup after early
  `2m_temperature` mean RMSE regressed by `+2.6769825875213316%`.
- Dynamaxx history:
  `.logbook/history/2026-06-25_21-06-21_late-lead-vertical-dse-cap-release`
  rejected widening the accepted vertical-DSE cap after day 5 with iteration
  delta `-0.00042068732323799485`.
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of `late-lead-vertical-dse-cap-release`: the incumbent
per-step cap and forecast-time ramp remain unchanged. It is not a duplicate of
`baroclinic-mode-vertical-dse-spinup` or early vertical-DSE spinup variants:
no vertical-DSE component is exposed before the accepted ramp. It is not a
duplicate of staged `boundary-layer-sheltered-vertical-dse`, because it uses a
local column hydrostatic-work ratio rather than a fixed sigma/boundary-layer
mask. It is also distinct from staged `column-neutral-mass-dse-increment`,
which projects the horizontal mass-DSE HSL increment; this proposal acts only
on the already accepted vertical-DSE increment.

## Evaluator Notes

### 2026-06-26T00:15:42Z

Decision: move to `ready`; ranked 1 of 2 reviewed proposals.

This is implementable now as a side-by-side incumbent variant with no forecast
contract or fixed-protocol change. It targets the accepted vertical-DSE
increment along a materially different axis from the two rejected follow-ups:
it does not expose the increment earlier, does not widen the late cap, and
keeps the incumbent zero-through-24h/full-by-72h ramp and `0.05 K` per-step
cap.

The physical rationale is stronger than the staged boundary-layer shelter for
the next experiment because it gates a local column-net hydrostatic-work mode
while preserving column-neutral vertical redistribution. That keeps the
proposal close to the large accepted vertical-DSE signal but tests a concrete
remaining imbalance mechanism. Main risk is that the incumbent's gain depends
on some column-mean thermal work; the bounded blend and exact incumbent
fallback keep the implementation blast radius acceptable for a ready candidate.
