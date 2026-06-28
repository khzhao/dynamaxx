---
schema_version: 1
slug: boundary-layer-sheltered-vertical-dse
title: Boundary-Layer-Sheltered Pressure-Ramped Vertical DSE
status: ready
created_at: 2026-06-25T20:29:05Z
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

# Boundary-Layer-Sheltered Pressure-Ramped Vertical DSE

## Hypothesis

The accepted pressure-ramped vertical-DSE incumbent recovered a large score
signal, but the immediately rejected baroclinic-mode follow-up showed that
earlier internal thermal redistribution worsened early `2m_temperature` by
`+2.6769825875213316%` over days 1-5. That failure suggests the lower-column
part of the vertical-DSE increment is more dangerous to screen-temperature
skill than the free-tropospheric part. A smooth boundary-layer shelter on only
the accepted vertical-DSE increment should preserve most medium-lead mass and
height benefit while reducing near-surface thermal drift and lowering the risk
of future vertical-DSE refinements failing through early T2m.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_pblcap`, derived from the current incumbent.

Inside `pressure_ramped_vertical_dse_increment_temperature_tendency`:

- compute the raw accepted vertical-DSE increment, forecast-time pressure ramp,
  low-mode pressure guard, and per-step Kelvin cap exactly as the incumbent
  does;
- multiply only the vertical-DSE increment by a fixed smooth sigma envelope
  that is full strength through the free troposphere, tapers across the lower
  troposphere, and has a small floor in the lowest sigma layers;
- apply the shelter before modal conversion and after all incumbent finite
  diagnostics needed for pressure thickness, DSE, and sigma-dot;
- leave WTG relaxation, horizontal mass-DSE HSL transport, weak Held-Suarez
  forcing, DFI, surface residual diagnostics, output variables, target
  variables, and fixed evaluation protocols unchanged;
- fall back exactly to the incumbent tendency if the shelter weights or the
  sheltered increment are nonfinite.

This is not an early vertical-DSE spinup. It keeps the accepted zero-through-24h
and full-by-72h ramp, and it reduces the lower-boundary part of the increment
rather than introducing any component earlier.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused primitive-equation, dependency, and registry tests
- Registry changes:
  - Add one side-by-side model key such as
    `dino_hsl2_mass_dse_wtg_vdse_pblcap`.
- API changes:
  - None.
- Tests to update:
  - Verify the lower-sigma shelter is bounded, smooth, finite, shape-compatible,
    and has the documented floor.
  - Verify the selector is an exact no-op when disabled.
  - Verify free-tropospheric synthetic increments are nearly unchanged while
    lowest-layer increments are reduced.
  - Verify nonfinite shelter weights or sheltered increments fall back to the
    incumbent vertical-DSE branch.
  - Verify factory/dependency and registry coverage for the new model key.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2-15 if the accepted vertical-DSE increment is
    contributing to the current late cold T2m bias visible in cached iteration
    and validation artifacts.
  - `mean_sea_level_pressure` and `geopotential_500` should remain close to
    incumbent if most of the accepted signal comes from the free troposphere.
  - Iteration primary score should improve by roughly `+0.002` to `+0.006` if
    near-surface shelter removes harmful lower-column thermal drift without
    giving back the vertical-DSE gain.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should move little because momentum, Richardson
    10 m diagnostics, and WTG are unchanged.
  - Day-1 MSLP should remain close because the incumbent time ramp and low-mode
    pressure guard are preserved.
- Possible regressions:
  - Z500 or MSLP can regress if the lower-tropospheric part of vertical-DSE was
    essential to the accepted mass/thickness signal.
  - T2m can regress if the current late cold bias is dominated by residual
    diagnostics or surface energy terms instead of lower-column vertical-DSE.

## Risks

- Numerical stability:
  - Low. The candidate only damps an accepted finite-guarded increment and
    retains the incumbent tendency cap and fallback.
- Compute cost:
  - Low. It adds a static sigma envelope and elementwise multiplication inside
    an existing tendency path.
- Data leakage:
  - None. It uses fixed sigma geometry and forecast state only.
- Physical plausibility:
  - Moderate to high. Boundary-layer temperature is strongly controlled by
    turbulent and surface exchange processes, so a dry free-tropospheric DSE
    vertical transport increment should not be allowed to dominate the lowest
    layers.
- Rollback complexity:
  - Low. Remove one selector, one helper, one factory/export/registry key, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_pblcap`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_pblcap --workers 4`.
  - Support requires primary delta at least `+0.002`, clean diagnostics, no
    early day-1-through-day-5 mean RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_pblcap --workers 4`
    only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show that
    lower-column vertical-DSE is not the remaining T2m bottleneck. Any early
    Z500 or MSLP guardrail failure would show that the shelter disrupts the
    accepted thickness balance.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg`
  accepted the current pressure-ramped vertical-DSE increment with iteration
  delta `+0.03880190339341674` and validation delta
  `+0.03763133840279842`.
- Dynamaxx history:
  `.logbook/history/2026-06-25_17-17-23_baroclinic-mode-vertical-dse-spinup`
  rejected earlier internal vertical-DSE redistribution after a negative
  iteration delta and early `2m_temperature` guardrail failure.
- Dynamaxx cached metrics:
  `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv` and
  `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv` show strongly
  negative `2m_temperature` skill versus persistence and a late cold bias near
  `-1.5 K`.
- Stull, R. B. 1988. An Introduction to Boundary Layer Meteorology. Springer.
  https://link.springer.com/book/10.1007/978-94-009-3027-8
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://journals.ametsoc.org/view/journals/mwre/109/4/1520-0493_1981_109_0758_aeaamc_2_0_co_2.xml

## Researcher Notes

This is distinct from staged `tropopause-capped-vertical-dse-increment`, which
limits upper-column behavior near the tropopause. It is also distinct from the
rejected `baroclinic-mode-vertical-dse-spinup`, because it does not expose any
vertical-DSE component earlier than the incumbent ramp; it reduces the
near-surface portion of the already accepted increment. It is not a duplicate
of active `lower-troposphere-shielded-vertical-dse-spinup`: that proposal
reintroduces an earlier free-tropospheric internal-mode spinup while shielding
the lower troposphere, whereas this proposal keeps every vertical-DSE component
on the incumbent time ramp and only tests whether the accepted increment is too
strong in boundary-layer sigma levels. It is not a WTG microvariant because the
WTG filter, mask, relaxation time scale, and mass-DSE anomaly are unchanged. It
is also not a duplicate of staged surface-diagnostic or PBL-mixing proposals,
because it acts only inside the vertical-DSE thermal tendency rather than
adding a boundary-layer source, drag, or output formula.

## Evaluator Notes

### 2026-06-25T20:33:00Z

Decision: move to `staging`; ranked 2 of 4 current proposals.

This is implementable now as a side-by-side incumbent variant with no forecast
contract or fixed-protocol change. It directly responds to the rejected
baroclinic-mode run's early `2m_temperature` failure by reducing the
near-surface part of the already accepted vertical-DSE increment, and it keeps
the incumbent zero-through-24h/full-by-72h ramp rather than exposing any
vertical-DSE component earlier.

Stage rather than ready because it damps a mechanism that just produced a large
clean accepted gain. The physical argument is coherent, but the upside depends
on lower-column vertical-DSE being the remaining T2m bottleneck; if that lower
column contribution is part of the accepted MSLP/Z500 signal, the candidate can
give back primary score. It is a strong fallback after the lower-blast-radius
late-cap release is tested.

### 2026-06-27T11:49:00Z

Decision: move to `ready`.

The late-cap, WTG filter-order, WTG timing, WTG moisture-gating, WTG envelope,
and vertical-DSE midpoint timing follow-ups have now been tested and rejected
or shown subthreshold. This proposal remains directly targeted to the current
`dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent, does not alter the forecast
contract, and has a low implementation surface: one fixed sigma envelope
multiplies only the accepted pressure-ramped vertical-DSE increment. Implement
as exactly one side-by-side candidate and preserve the incumbent path when the
selector is disabled.
