---
schema_version: 1
slug: diurnal-surface-residual-memory
title: Use Diurnal Surface-Layer Memory for 2 m Temperature Residuals
status: scrap
created_at: 2026-06-19T14:51:51Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/radiation.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Diurnal Surface-Layer Memory for 2 m Temperature Residuals

## Hypothesis

The incumbent still emits raw `2m_temperature` from the lowest sigma-layer
temperature and then applies the accepted near-surface residual correction. The
residual currently decays monotonically with lead time. Because fixed scoring
uses daily lead intervals, the same local solar phase recurs at each scored
lead, so part of the initial screen-temperature residual can be a repeatable
surface-layer representativeness error rather than a transient imbalance that
should vanish exponentially.

A bounded diurnal-memory component for the `2m_temperature` residual should
improve days 2 to 15 without changing the positive-time dycore trajectory,
pressure fields, geopotential, or the accepted Richardson 10 m wind diagnostic.
This proposal is not a DFI or theta-recentering variant; it changes only how the
already accepted same-time screen-temperature residual is carried through the
output diagnostic.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_diurnal_t2m_residual`.
Preserve the incumbent DFI, weak Held-Suarez forcing, hydrostatic/log-pressure
initialization, Strang Coriolis split, theta tendency, theta mean recentering,
0.05 semi-implicit off-centering, horizontal diffusion, pressure-level outputs,
and Richardson 10 m wind diagnostic.

For `2m_temperature` only:

- compute the raw lead-zero residual exactly as the accepted residual correction
  does: analyzed `2m_temperature` minus raw model `2m_temperature`;
- compute local solar phase and normalized top-of-atmosphere insolation at the
  initial time and at each valid time using the existing `radiation.py`
  orbital utilities, longitude, and latitude;
- split the residual coefficient into the incumbent monotone component plus a
  bounded diurnal-memory component whose sign and amplitude depend on solar
  phase similarity between initialization and valid time;
- make the diurnal coefficient decay more slowly than the monotone component,
  but clip the total `2m_temperature` residual multiplier to a fixed range such
  as `[0, 1]`, with lead zero still exactly matching the analyzed field;
- leave the `10m_u_component_of_wind` residual correction on the accepted
  stability-aware path and leave all other variables unchanged;
- fall back to the incumbent residual coefficient if any time, insolation, or
  phase diagnostic is nonfinite.

This is distinct from a surface-layer lapse-rate or bulk-Richardson 2 m
temperature diagnostic: it does not infer a new raw screen temperature from the
lowest two model layers. It also differs from lower-column thermal IAU because
it does not insert screen residuals into the prognostic thermal state.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/radiation.py` only if a small vectorized
    local-solar-phase helper is needed
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate model name above.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, target
    variables, lead times, and evaluation protocols remain unchanged.
- Tests to update:
  - Unit-test solar phase similarity and finite fallback behavior for a small
    synthetic grid and fixed UTC times.
  - Verify lead-zero `2m_temperature` exactly matches the analyzed initial field
    when the residual correction is active.
  - Verify the candidate changes only corrected `2m_temperature` values; 10 m
    winds, MSLP, Z500, pressure-level fields, and raw trajectory outputs remain
    unchanged relative to the incumbent before the final T2m residual write.
  - Verify the candidate factory preserves every incumbent flag except the new
    diurnal T2m residual option.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2 to 15, especially where the current daily-lead
    cold bias indicates that the accepted residual decays too quickly at the
    repeated local time.
  - Aggregate primary score, because current incumbent iteration metrics show
    strongly negative `2m_temperature` skill versus persistence after day 1.
- Expected neutral metrics:
  - `mean_sea_level_pressure`, `geopotential_500`, and pressure-level variables
    should be unchanged except for metric noise because the trajectory and
    pressure output path are unchanged.
  - `10m_u_component_of_wind` should remain on the accepted Richardson and
    stability-aware residual path.
- Possible regressions:
  - A recurring residual can preserve an initial representativeness error that
    should actually decay.
  - The fixed daily scoring cadence makes local solar phase similar at every
    lead; if the raw residual is not diurnally coherent, the added memory can
    degrade T2m without helping other variables.

## Risks

- Numerical stability:
  - Low. This is output-only and cannot feed back into the primitive-equation
    rollout.
- Compute cost:
  - Low. Solar phase algebra is local grid arithmetic and uses already vendored
    helpers.
- Data leakage:
  - Low if the mechanism uses only forecast initialization time, valid time,
    longitude, latitude, and the same lead-zero residual already accepted in the
    incumbent. It must not inspect future verification fields or validation
    metrics.
- Physical plausibility:
  - Moderate. Screen-level temperature is a diagnostic surface-layer quantity,
    and local solar phase is a physically relevant driver, but the candidate is
    still a simplified residual-memory model rather than a full land surface.
- Rollback complexity:
  - Low. Remove one residual option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_diurnal_t2m_residual`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_diurnal_t2m_residual --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_diurnal_t2m_residual --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that daily
    solar-phase residual memory is not a material remaining error source. Any
    early `2m_temperature` guardrail failure would show the residual multiplier
    is too persistent or insufficiently local.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  packs `2m_temperature` from the lowest sigma-layer temperature and then
  applies `_apply_near_surface_residual_correction`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/radiation.py` provides
  deterministic local solar phase and top-of-atmosphere radiation utilities.
- Local history:
  `.logbook/history/2026-06-18_15-57-11_stability-aware-surface-residual-decay/decision.md`
  accepted stability-aware near-surface residual decay, showing that same-time
  near-surface residuals can carry useful forecast signal.
- Local history:
  `.logbook/history/2026-06-17_13-35-18_surface-layer-diagnostic-extrapolation/decision.md`
  rejected a simple two-layer surface extrapolation with near-surface guardrail
  failures; this proposal avoids a new lapse-rate diagnostic and changes only
  T2m residual memory.
- ECMWF Newsletter 178, "Improved two-metre temperature forecasts in the 2024
  upgrade", describes 2 m temperature as a diagnostic variable derived from
  surface and lowest-model-level information using Monin-Obukhov similarity
  theory: https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade
- American Meteorological Society Glossary, "Monin-Obukhov similarity theory",
  summarizes surface-layer similarity as relationships for nondimensional mean
  flow and turbulence properties in the atmospheric surface layer:
  https://glossary.ametsoc.org/wiki/monin-obukhov-similarity-theory/
- Beljaars, A. C. M. and Holtslag, A. A. M. 1991. "Flux Parameterization over
  Land Surfaces for Atmospheric Models." Journal of Applied Meteorology.
  https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2

## Researcher Notes

The active staging queue already contains `bulk-richardson-2m-temperature-
diagnostic`, `lower-column-thermal-iau-spinup`, and `solar-weighted-thermal-
tendency`. This proposal is deliberately outside those mechanisms: it does not
alter the raw 2 m diagnostic, does not heat the prognostic lower column, and
does not add a solar thermal tendency. It only modifies the time structure of
the accepted T2m residual correction using local solar phase.

Recent negative DFI/theta evidence is not directly implicated because this
candidate does not change DFI, recentering, or the positive-time primitive
equation. The main negative evidence is the rejected surface-layer diagnostic
extrapolation, which motivates keeping the scope output-only, T2m-only, and
bounded.

## Evaluator Notes

### 2026-06-19T14:56:55Z

Decision: move to `staging`; ranked 2 of 3 fresh proposals.

This is implementable and distinct from the active staged
`bulk-richardson-2m-temperature-diagnostic` and `lower-column-thermal-iau-spinup`
ideas. Source inspection confirms that raw `2m_temperature` is still packed
from the lowest sigma layer and then adjusted by `_apply_near_surface_residual_correction`,
so the proposal can remain output-only and keep the positive-time dycore,
forecast contract, pressure fields, geopotential, and Richardson 10 m wind path
unchanged. The cited ECMWF T2m material supports the general point that screen
temperature is a diagnostic surface-layer quantity rather than a prognostic
model variable.

Keep staged rather than ready because this is still a single-channel,
output-only residual-memory change. Under the fixed daily lead cadence, local
solar phase will often recur almost exactly at each scored lead, so the
diurnal-memory term risks collapsing into a longer-lived T2m residual
multiplier with extra machinery. That may help the remaining late T2m cost from
the off-centered incumbent, but it is also close to metric-targeted
post-processing and is unlikely to move MSLP, Z500, or wind except through
score averaging. If promoted later, constants must be fixed before evaluation,
lead-zero matching must remain exact, and tests must prove that only corrected
`2m_temperature` differs from the incumbent output path.

### 2026-06-27T19:07:18Z

Decision: demote to `scrap`.

Under daily lead scoring, the proposed solar-phase memory mostly behaves like a
longer-lived T2m residual multiplier. The new incumbent already accepted a
late-ramped land/ocean low-mode T2m residual memory with clean validation
gains, so this staged variant is now both overlapping and more metric-facing
than the ready bounded Richardson diagnostic.

The residual-memory path has become a fragile, high-value part of the
incumbent. Further extending it with calendar/diurnal coefficients would invite
constant tuning without a clearly separate physical signal. Scrap this unless a
future read-only analysis demonstrates a robust diurnally coherent residual
that the current land/ocean memory cannot represent.
