---
schema_version: 1
slug: baroclinic-mode-vertical-dse-spinup
title: Baroclinic-Mode Spinup for Pressure-Ramped Vertical DSE
status: ready
created_at: 2026-06-25T16:37:26Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Baroclinic-Mode Spinup for Pressure-Ramped Vertical DSE

## Hypothesis

The current incumbent recovered the large vertical-DSE signal by delaying the
full vertical-DSE increment until after the 24 h MSLP guardrail window. The
unrestricted precursor showed the signal is real, but its day-1 MSLP failure
indicates that the damaging part is likely the equivalent-barotropic column
heating/thickness component, not every vertical-DSE mode. A pressure-thickness
weighted baroclinic projection can expose internal vertical redistribution
earlier while keeping the column-thickness component on the incumbent 24 h to
72 h pressure ramp.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_bmode`, derived from
`dino_hsl2_mass_dse_wtg_vdse_ramp`.

Inside the existing pressure-ramped vertical-DSE increment path:

- compute the raw nodal vertical-DSE temperature increment exactly as the
  incumbent does;
- compute a pressure-thickness-weighted column mean of that increment for each
  horizontal column;
- split the increment into an external component and a zero-column-mean
  baroclinic component;
- apply a conservative smooth early ramp to the baroclinic component, such as
  zero through 12 h and full by 48 h;
- keep the external component on the incumbent zero-through-24 h,
  full-by-72 h ramp and retain the broad low-mode pressure guard;
- combine the two components, then apply the incumbent finite diagnostics,
  per-step Kelvin cap, modal conversion, and fallback behavior;
- leave WTG relaxation, mass-DSE horizontal transport, DFI, surface residuals,
  weak-HS forcing, output variables, target variables, and evaluation protocols
  unchanged.

This is not a WTG refinement. It changes only the vertical-mode decomposition
of the accepted vertical-DSE increment.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused Dinosaur primitive-equation, dependency, and registry tests
- Registry changes:
  - Add one side-by-side model key such as
    `dino_hsl2_mass_dse_wtg_vdse_bmode`.
- API changes:
  - None.
- Tests to update:
  - Verify the baroclinic component has zero pressure-thickness-weighted column
    mean for finite synthetic columns.
  - Verify the external component follows the incumbent 24 h to 72 h ramp.
  - Verify the baroclinic component follows the proposed earlier ramp.
  - Verify the selector is a no-op when disabled and preserves all incumbent
    options except the new vertical-DSE mode split.
  - Verify nonfinite pressure thickness, increments, or modal conversions fall
    back to the incumbent tendency.

## Expected Metric Movement

- Expected improvements:
  - Iteration primary score should improve by roughly `+0.003` to `+0.010` over
    the incumbent if early internal vertical-DSE redistribution carries part of
    the unrestricted `+0.055` iteration signal without the external-mode MSLP
    shock.
  - `geopotential_500` and `mean_sea_level_pressure` at days 2 to 7 should
    improve if earlier baroclinic thickness adjustment reduces phase error.
  - Validation primary score should improve by roughly `+0.0015` to `+0.006`
    if the iteration signal is not split-specific.
- Expected neutral metrics:
  - Day-1 MSLP should remain near incumbent because the column-thickness mode is
    still delayed.
  - `10m_u_component_of_wind` should be mostly neutral unless improved mass
    phase feeds back on near-surface wind.
- Possible regressions:
  - `2m_temperature` and early MSLP can regress if the baroclinic projection is
    not enough to protect hydrostatic adjustment.
  - The incumbent's current gain may depend on the full vertical-DSE increment,
    so splitting the ramp could reduce late-lead skill.

## Risks

- Numerical stability:
  - Moderate. The increment remains bounded and finite-guarded, but it changes
    the timing of a high-signal thermal mechanism.
- Compute cost:
  - Low. The extra work is a vertical reduction and broadcast inside an existing
    tendency path.
- Data leakage:
  - None. The candidate uses only forecast state, fixed sigma geometry, and
    fixed ramp constants.
- Physical plausibility:
  - Moderate to high. Internal baroclinic thermal redistribution is closer to
    available-potential-energy exchange than a column-mean heat pulse, while the
    external column-thickness mode is the part most exposed to MSLP shock.
- Rollback complexity:
  - Low. Remove one selector, one factory/export/registry key, and focused
    tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_bmode`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_bmode --workers 4`.
  - Support requires primary delta at least `+0.002`, clean diagnostics, no
    early day-1-through-day-5 mean RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_bmode --workers 4`
    only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the incumbent
    already uses the useful part of the vertical-DSE increment. Any day-1 MSLP
    guardrail failure would show that the internal-mode split still leaks too
    much external pressure adjustment.

## Citations

- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Kasahara, A. 1974. Various vertical coordinate systems used for numerical
  weather prediction. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1974)102%3C0509:VVCSUF%3E2.0.CO;2
- Lorenz, E. N. 1955. Available potential energy and the maintenance of the
  general circulation. Tellus. https://doi.org/10.3402/tellusa.v7i2.8796
- Jablonowski, C. and Williamson, D. L. 2006. A baroclinic instability test case
  for atmospheric model dynamical cores. Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1256/qj.06.12
- Dynamaxx history:
  `.logbook/history/2026-06-24_05-18-28_vertical-dse-transport-mass-hsl`
  measured a large vertical-DSE iteration gain but failed the day-1 MSLP
  guardrail.
- Dynamaxx history:
  `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg`
  accepted the delayed pressure-ramped version with clean guardrails.

## Researcher Notes

This is distinct from staged `first-baroclinic-tropical-wtg-mass-dse`, which
changes the tropical WTG anomaly subspace, and from staged
`column-neutral-mass-dse-increment`, which acts on the horizontal mass-DSE HSL
increment. It also does not re-propose the accepted ramp unchanged: the new
mechanism is an internal-versus-external vertical-mode split of the accepted
vertical-DSE increment, motivated directly by the rejected day-1 MSLP shock and
the accepted delayed ramp.

## Evaluator Notes

### 2026-06-25T16:41:26Z

Decision: move to `ready`; ranked 1 of 2 new vertical-DSE follow-up proposals.

This is the best next target because it is a bounded side-by-side refinement of
the newly accepted high-signal vertical-DSE mechanism. The accepted incumbent
improved iteration by `+0.03880190339341674` and validation by
`+0.03763133840279842` with clean diagnostics and guardrail movement near
numerical noise, while the unrestricted precursor showed an even larger
iteration signal but failed only the 24 h MSLP single-lead guardrail. Splitting
the increment into a pressure-thickness-weighted column component and a
zero-column-mean internal component directly targets that measured failure
mode without changing WTG, mass-DSE HSL, outputs, or fixed protocols.

The implementation surface is also narrow: the current incumbent already has a
single guarded vertical-DSE increment path with a smooth ramp, broad low-mode
pressure guard, per-step Kelvin cap, modal conversion, and finite fallback.
This proposal can reuse those controls while testing whether internal
baroclinic redistribution can be introduced earlier than the external
thickness mode. The main risk is that zero-column-mean thermal redistribution
can still perturb hydrostatic thickness and MSLP, so the implementation should
keep the incumbent fallback and early pressure guard exact and avoid tuning a
family of ramps.
