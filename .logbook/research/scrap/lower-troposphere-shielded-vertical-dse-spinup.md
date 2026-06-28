---
schema_version: 1
slug: lower-troposphere-shielded-vertical-dse-spinup
title: Lower-Troposphere-Shielded Vertical DSE Spinup
status: scrap
created_at: 2026-06-25T20:26:17Z
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

# Lower-Troposphere-Shielded Vertical DSE Spinup

## Hypothesis

The accepted `dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent proved that the
vertical-DSE increment is a high-signal mechanism: iteration improved by
`+0.03880190339341674` and validation by `+0.03763133840279842` with clean
diagnostics and guardrail movement near numerical noise. The latest follow-up,
`baroclinic-mode-vertical-dse-spinup`, tested whether internal vertical-DSE
redistribution could be exposed earlier, but it regressed iteration by
`-0.006174866536629547` and failed the early day-1-to-5 `2m_temperature`
guardrail at `+2.6769825875213316%`.

That failure does not prove that all earlier internal vertical-DSE structure is
harmful. It more specifically shows that earlier thermal redistribution is too
exposed to lower-tropospheric and near-surface temperature error. A candidate
that permits only free-tropospheric internal vertical-DSE spinup while holding
the lower troposphere and column-thickness mode on the accepted incumbent ramp
should test the remaining aloft signal without repeating the measured early
`2m_temperature` failure.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_ftspin`, derived from
`dino_hsl2_mass_dse_wtg_vdse_ramp`.

Inside the existing `pressure_ramped_vertical_dse_increment_temperature_tendency`
path:

- compute the raw vertical-DSE temperature increment exactly as the incumbent
  does;
- split the increment into a pressure-thickness-weighted column component and a
  zero-column-mean internal component, as in the rejected baroclinic-mode
  experiment;
- build a fixed smooth free-tropospheric mask from sigma coordinate alone,
  equal to `1.0` above about `sigma = 0.65`, tapering smoothly to `0.0` by
  about `sigma = 0.80`, and exactly `0.0` in the lower-tropospheric buffer;
- apply the earlier internal-mode ramp only to the masked free-tropospheric
  internal component, for example zero through 12 h and full by 48 h;
- keep the column component and the lower-tropospheric internal component on
  the accepted incumbent zero-through-24 h, full-by-72 h ramp;
- retain the incumbent low-mode pressure guard, per-step Kelvin cap, modal
  conversion, WTG relaxation, mass-DSE HSL transport, finite diagnostics, and
  fallback behavior;
- fall back exactly to the incumbent vertical-DSE tendency if the mask,
  projection, pressure thickness, increment, ramp, or converted modal tendency
  is nonfinite.

This is not a WTG refinement and not a new near-surface output diagnostic. It
changes only the vertical placement of the rejected earlier internal
vertical-DSE spinup, with the lower-tropospheric buffer chosen before scoring
to address the observed early `2m_temperature` failure.

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
    `dino_hsl2_mass_dse_wtg_vdse_ftspin`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, metrics, and
    fixed protocols remain unchanged.
- Tests to update:
  - Verify the free-tropospheric mask is bounded, smooth, and exactly zero in
    the lower-tropospheric shield.
  - Verify the column component and lower-tropospheric internal component follow
    the incumbent ramp exactly.
  - Verify the free-tropospheric internal component follows the earlier ramp.
  - Verify zero-column-mean projection is pressure-thickness weighted for finite
    synthetic columns.
  - Verify disabled selector and nonfinite diagnostics fall back to exact
    incumbent behavior.
  - Add factory, registry, and finite smoke-forecast coverage.

## Expected Metric Movement

- Expected improvements:
  - Iteration primary score should improve by roughly `+0.002` to `+0.006` if
    free-tropospheric internal vertical-DSE redistribution carries part of the
    rejected baroclinic-mode signal without the lower-column temperature cost.
  - `geopotential_500` and `mean_sea_level_pressure` at days 2 to 7 should be
    the most likely beneficiaries if aloft thickness and phase adjust earlier.
  - Validation primary score should improve by roughly `+0.001` to `+0.004` if
    the aloft signal is robust across splits.
- Expected neutral metrics:
  - Early day-1-to-5 `2m_temperature` should remain close to incumbent and well
    below the fixed `2%` mean-RMSE guardrail because the lower troposphere stays
    on the accepted ramp.
  - `10m_u_component_of_wind` should be mostly neutral because the momentum
    state, surface wind diagnostic, and WTG filter are unchanged.
- Possible regressions:
  - Free-tropospheric thermal changes can still project hydrostatically onto
    MSLP or lower-column temperature.
  - The rejected baroclinic-mode result may indicate that the incumbent already
    uses all useful internal vertical-DSE timing, not merely the lower-column
    part.

## Risks

- Numerical stability:
  - Moderate. The candidate changes timing of a high-signal thermal increment,
    but it remains capped, finite-guarded, and reuses the incumbent fallback.
- Compute cost:
  - Low. The extra work is a vertical projection, a fixed sigma mask, and local
    algebra inside an existing tendency path.
- Data leakage:
  - None. The mask and ramps use forecast state, sigma geometry, and fixed
    constants only; no validation, golden, or future truth enters the model.
- Physical plausibility:
  - Moderate. Shielding the lower troposphere is consistent with the fact that
    screen-level temperature is strongly tied to boundary-layer and surface
    diagnostics not resolved by the dry dycore, while the free troposphere is
    the more defensible place to test internal baroclinic DSE redistribution.
- Rollback complexity:
  - Low to moderate. Remove one selector/helper, one factory/export, one
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ftspin`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ftspin --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    `dino_hsl2_mass_dse_wtg_vdse_ramp`, clean diagnostics, no early day-1-to-5
    mean RMSE guardrail failure, and no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ftspin --workers 4`
    only after iteration promotion.
  - Support requires validation primary-score delta at least `+0.001` with
    clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that earlier
    free-tropospheric internal spinup lacks useful signal. Any early
    `2m_temperature` guardrail failure would show the lower-tropospheric shield
    is insufficient or the aloft increment still couples too strongly to the
    near-surface diagnostic.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg`
  accepted the current incumbent with iteration delta
  `+0.03880190339341674`, validation delta `+0.03763133840279842`, and clean
  fixed guardrails.
- Dynamaxx history:
  `.logbook/history/2026-06-25_17-17-23_baroclinic-mode-vertical-dse-spinup`
  rejected earlier internal vertical-DSE spinup after iteration delta
  `-0.006174866536629547` and early `2m_temperature` mean RMSE regression
  `+2.6769825875213316%`.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Jablonowski, C. and Williamson, D. L. 2006. A baroclinic instability test
  case for atmospheric model dynamical cores. Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1256/qj.06.12
- Stull, R. B. 1988. An Introduction to Boundary Layer Meteorology. Springer.
  https://doi.org/10.1007/978-94-009-3027-8
- ECMWF Newsletter 178, "Improved two-metre temperature forecasts in the 2024
  upgrade," describes two-metre temperature as a diagnostic surface-layer
  product derived from lowest-model-level and surface information with
  stability safeguards.
  https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade

## Researcher Notes

This is intentionally not a near-repeat of the rejected
`baroclinic-mode-vertical-dse-spinup`: the new mechanism is the
lower-tropospheric shield, which directly targets the measured early
`2m_temperature` regression. It also differs from staged
`tropopause-capped-vertical-dse-increment`, which limits the upper-column
accepted increment, and from staged `bulk-richardson-2m-temperature-diagnostic`
or `lower-column-thermal-iau-spinup`, which act on output diagnostics or initial
lower-column thermal insertion rather than the vertical-DSE tendency path.

## Evaluator Notes

### 2026-06-25T20:33:00Z

Decision: move to `scrap`; ranked 4 of 4 current proposals.

Reject for this cycle because it is still an earlier internal vertical-DSE
spinup experiment immediately after a measured early-spinup failure. The
lower-tropospheric shield is a real attempt to address the rejected
`2m_temperature` guardrail, but the free-tropospheric early thermal increment
can still project hydrostatically onto MSLP, Z500, and lower-column diagnostics
during days 1-5.

The idea is dominated by safer vertical-DSE follow-ups now available:
`late-lead-vertical-dse-cap-release` is an exact early no-op, and
`boundary-layer-sheltered-vertical-dse` targets the lower-column T2m concern
without introducing earlier spinup. Spending the next implementation on another
early internal-mode timing change is not a good cost-risk tradeoff against the
current incumbent.
