---
schema_version: 1
slug: tropopause-capped-vertical-dse-increment
title: Tropopause-Capped Pressure-Ramped Vertical DSE Increment
status: staging
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

# Tropopause-Capped Pressure-Ramped Vertical DSE Increment

## Hypothesis

The accepted vertical-DSE ramp treats upper-tropospheric, tropopause, and lower
stratospheric sigma layers with the same pressure-time ramp once the finite
guards pass. That recovered a large aggregate signal, but vertical DSE transport
near strong static-stability transitions can over-project upper-column thermal
structure into Z500 and MSLP. A tropopause-aware cap on only the added
vertical-DSE increment should preserve the accepted tropospheric DSE gain while
reducing noisy upper-column thermal adjustment.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_tropcap`, derived from the current incumbent.

Within `pressure_ramped_vertical_dse_increment_temperature_tendency`:

- compute the incumbent raw vertical-DSE increment and pressure ramp exactly as
  today;
- diagnose a smooth upper-atmosphere cap from the current column's thermal
  structure, using a guarded lapse-rate or static-stability proxy and a fixed
  fallback to a conservative sigma cap when the diagnostic is ambiguous;
- multiply only the vertical-DSE increment by that cap before the incumbent
  low-mode pressure guard and Kelvin tendency cap;
- set the cap near `1.0` through the mid and lower troposphere, smoothly taper
  through the diagnosed tropopause transition, and retain a small nonzero floor
  in upper layers rather than hard-zeroing the mechanism;
- leave WTG relaxation, horizontal mass-DSE transport, weak-HS relaxation,
  ocean heat flux, residual diagnostics, DFI, output variables, target
  variables, and fixed protocols unchanged;
- fall back to the incumbent vertical-DSE increment if the cap, stability
  diagnostic, or capped increment is nonfinite.

This is not a new WTG support mask and not a new Held-Suarez thermal relaxation
mask. It limits only the incremental vertical-DSE thermal tendency that was
accepted in the current incumbent.

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
    `dino_hsl2_mass_dse_wtg_vdse_tropcap`.
- API changes:
  - None.
- Tests to update:
  - Verify synthetic tropospheric columns receive cap values near one.
  - Verify synthetic strong-stability/tropopause columns taper the upper
    vertical-DSE increment but do not alter the incumbent tendency when the
    selector is disabled.
  - Verify nonfinite stability, pressure, or capped increments fall back to the
    incumbent vertical-DSE branch.
  - Verify the cap is smooth, bounded in `[floor, 1]`, and shape-compatible with
    modal conversion.
  - Add factory/dependency and registry coverage.

## Expected Metric Movement

- Expected improvements:
  - Iteration primary score should improve by roughly `+0.002` to `+0.006` if
    current late-lead error includes upper-column vertical-DSE overcorrection.
  - `geopotential_500` at days 3 to 15 should improve most directly, with MSLP
    following if hydrostatic thickness errors are reduced.
  - Validation primary score should improve by roughly `+0.001` to `+0.004` if
    the cap removes robust upper-column noise rather than split-specific noise.
- Expected neutral metrics:
  - Day-1 MSLP should remain close because the incumbent pressure ramp and early
    guard are preserved.
  - `2m_temperature` and `10m_u_component_of_wind` should be close to incumbent
    because lower-tropospheric thermal increments, residual diagnostics, and the
    Richardson wind path are unchanged.
- Possible regressions:
  - Z500 and MSLP can regress if upper-tropospheric vertical-DSE increments are
    part of the accepted positive signal.
  - A noisy tropopause proxy can introduce spatially noisy caps unless it is
    smoothed and finite-guarded.

## Risks

- Numerical stability:
  - Low to moderate. The candidate reduces an accepted increment and keeps the
    incumbent caps, but a bad diagnostic could create sharp vertical masks.
- Compute cost:
  - Low. It adds local vertical thermal diagnostics and elementwise scaling in
    an existing tendency path.
- Data leakage:
  - None. It uses current forecast state and fixed constants only.
- Physical plausibility:
  - Moderate. The tropopause is a real stability transition and upper-layer
    thermal adjustment should be treated differently from tropospheric
    baroclinic thermal transport, but this is still a dry dycore safeguard.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export/registry key, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_tropcap`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_tropcap --workers 4`.
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_tropcap --workers 4`
    only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` and clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that upper-column
    vertical-DSE increments are not a material remaining error source. Any Z500
    or MSLP guardrail regression would show the cap damages useful vertical-DSE
    structure or diagnoses the tropopause too noisily.

## Citations

- World Meteorological Organization lapse-rate tropopause definition, as
  summarized by EUMETSAT user documentation for tropopause height products:
  https://user.eumetsat.int/catalogue/EO%3AEUM%3ADAT%3A0115
- Highwood, E. J. and Hoskins, B. J. 1998. The tropical tropopause. Quarterly
  Journal of the Royal Meteorological Society.
  https://doi.org/10.1002/qj.49712454911
- Reichler, T., Dameris, M., and Sausen, R. 2003. Determining the tropopause
  height from gridded data. Geophysical Research Letters.
  https://doi.org/10.1029/2003GL018240
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Dynamaxx research:
  `.logbook/research/staging/tropopause-capped-thermal-relaxation.md` applies a
  tropopause mask to weak-HS thermal relaxation, not to vertical-DSE transport.
- Dynamaxx history:
  `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg`
  accepted the current pressure-ramped vertical-DSE increment with clean
  guardrails.

## Researcher Notes

This is distinct from staged `tropopause-capped-thermal-relaxation` because it
does not modify the Held-Suarez equilibrium or relaxation rate. It is also not
another small WTG variant: the accepted WTG filter is unchanged, and the cap is
applied only to the incremental vertical-DSE thermal tendency in the current
incumbent. The expected signal is smaller than the accepted ramp, but the
implementation is bounded and directly tests whether the newly accepted
vertical-DSE mechanism is too strong near the upper stability transition.

## Evaluator Notes

### 2026-06-25T16:41:26Z

Decision: move to `staging`; ranked 2 of 2 new vertical-DSE follow-up
proposals.

This is a plausible bounded fallback, but it should not take the next ready
slot. It is distinct from staged `tropopause-capped-thermal-relaxation` because
it caps only the accepted vertical-DSE increment rather than weak-HS thermal
relaxation, and it leaves WTG, mass-DSE HSL, outputs, and fixed protocols
unchanged. The mechanism is physically interpretable because the tropopause is
a strong static-stability transition and upper-column thermal adjustment can
project onto Z500 and MSLP.

Stage it because the evidence for a remaining upper-column overcorrection is
weaker than the evidence behind the baroclinic-mode split. The current
pressure-ramped vertical-DSE incumbent already recovered a large primary-score
gain with clean diagnostics and RMSE guardrails near numerical noise, so a cap
that mostly reduces part of that accepted increment could simply give back
skill. The proposal also depends on a noisy column tropopause or static
stability diagnostic, duplicating the implementation concern already noted for
the staged tropopause-capped weak-HS idea. Promote only if future score notes
or diagnostics identify upper-layer vertical-DSE noise as the remaining error
source, or if the baroclinic split fails cleanly while preserving evidence that
vertical-DSE still has unused headroom.
