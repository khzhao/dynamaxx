---
schema_version: 1
slug: land-sea-wind-residual-memory
title: Land-Sea-Aware 10 m Wind Residual Memory
status: ready
created_at: 2026-06-22T00:00:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Land-Sea-Aware 10 m Wind Residual Memory

## Hypothesis

The incumbent now uses static land-sea information to improve `2m_temperature`
residual memory, but `10m_u_component_of_wind` still uses the same
scale-separated residual decay everywhere. Near-surface wind representativeness
depends strongly on surface type through roughness, thermal coupling, and marine
boundary-layer persistence. A fixed land-sea split for only the existing 10 m
wind residual should recover some remaining `10m_u_component_of_wind` skill
without touching the dry prognostic trajectory, pressure fields, or the accepted
land-sea temperature correction.

## Mechanism

Add an opt-in branch inside the scale-separated near-surface residual correction
for `10m_u_component_of_wind`:

- reuse the existing WeatherBench2 `land_sea_mask` loading, validation, and grid
  alignment path already accepted for `2m_temperature`;
- leave pure-land wind residual decay exactly incumbent;
- over ocean, keep low-mode 10 m wind residual memory modestly longer than the
  incumbent high-mode wind residual, while keeping high-mode wind residual decay
  at or near the incumbent value to avoid carrying small-scale analysis noise;
- blend continuously across coastlines by land fraction;
- preserve lead-zero exact analysis matching and fall back to the incumbent wind
  residual correction if the mask is unavailable, nonfinite, or shape-mismatched.

This is output-only. It does not change vorticity, divergence, temperature,
surface pressure, weak-HS forcing, Coriolis splitting, DFI, or the Richardson
10 m diagnostic before the residual correction.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for a boolean selector,
    a small `_land_sea_surface_wind_residual_decays` helper, and a side-by-side
    candidate factory based on the current incumbent.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` for the new factory export.
  - `src/dynamaxx/dycore/registry.py` for a registered candidate name such as
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_landsea_wind`.
  - `tests/dycore/models/dinosaur/test_primitive_equations.py` or adjacent
    adapter tests for decay helper behavior.
  - `tests/dycore/test_registry.py` for registration coverage.
- Registry changes:
  - Add exactly one side-by-side model entry; keep the incumbent entry unchanged.
- API changes:
  - None. The public `DycoreModel.forecast` contract, variables, lead handling,
    and evaluation protocols remain unchanged.
- Tests to update:
  - Verify missing-mask fallback is incumbent-equivalent.
  - Verify pure-land points reproduce incumbent wind decays.
  - Verify pure-ocean points have the intended longer low-mode wind residual
    memory but bounded high-mode behavior.
  - Verify `2m_temperature` land-sea behavior is unchanged relative to the
    accepted incumbent.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind`, especially days 2-15 over ocean and coastal
    regions if the current residual decays too quickly over smoother marine
    surfaces.
  - Small primary-score gain if wind improvements add to the accepted T2m gain
    without moving mass fields.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500` should be numerically
    unchanged because this is output-only and changes only the wind residual
    correction after the trajectory is packed.
  - `2m_temperature` should remain the accepted land-sea correction.
- Possible regressions:
  - Early `10m_u_component_of_wind` can regress if marine wind analysis residuals
    are less persistent than assumed.
  - Carrying low-mode ocean wind residuals too long may hurt cyclone translation
    or trade-wind phase at longer leads even though pressure fields are unchanged.

## Risks

- Numerical stability:
  - Low. The mechanism is bounded algebra on emitted arrays and uses finite
    fallbacks.
- Compute cost:
  - Negligible. The land-sea mask is already loaded for the incumbent; this adds
    a few array operations during output correction.
- Data leakage:
  - None beyond the accepted use of a static same-grid land-sea mask and the
    lead-zero analysis residual already used by the incumbent.
- Physical plausibility:
  - Moderate. Surface type strongly controls near-surface wind, but this is a
    residual-memory surrogate rather than a roughness-length or flux scheme.
- Rollback complexity:
  - Low. Remove one selector, one helper, one factory/export, one registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_landsea_wind`.
  - Require finite forecasts, zero diagnostic issues, and no obvious early wind
    blow-up.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_landsea_wind --workers 4`.
  - Support requires at least the fixed `+0.002` primary-score improvement over
    the cached incumbent with clean RMSE guardrails, ideally with most movement
    in `10m_u_component_of_wind`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_landsea_wind --workers 4` only if iteration promotes.
  - Validation should preserve the wind improvement without mass-field or T2m
    regressions.
- Outcome that would falsify the hypothesis:
  - A clean but subthreshold or negative iteration delta, an early wind RMSE
    guardrail failure, or movement only in non-target diagnostics would show that
    surface-type wind residual memory is not a material remaining error source.

## Citations

- Citation or source:
  - Local code: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements the
    accepted scale-separated residual correction and the current
    `land_sea_mask` loading path.
  - Local history: `.logbook/history/2026-06-21_23-32-41_land-sea-contrast-surface-temperature/decision.md`
    accepted land-sea-aware `2m_temperature` residual memory with clean
    validation gain.
  - Local history: `.logbook/history/2026-06-21_21-39-17_coherent-u-residual-gate/decision.md`
    rejected a u-only coherence gate as safe but too small, motivating a
    stronger physical surface-type split rather than another generic gate.
  - Stull, R. B. 1988. `An Introduction to Boundary Layer Meteorology`. Kluwer.
    Describes surface-layer control of near-surface wind by roughness and
    stability.
  - ECMWF IFS Documentation, Part IV: Physical Processes. The surface-layer and
    turbulent-exchange documentation treats 10 m wind as a diagnostic tied to
    surface type, roughness, and boundary-layer exchange.

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is not the accepted land-sea T2m proposal: that candidate changes only the
`2m_temperature` residual decay, while this proposal leaves that accepted branch
unchanged and targets `10m_u_component_of_wind`. It is not the rejected
`coherent-u-residual-gate`, which damped a wind residual by temporal/spatial
coherence rather than surface type. It also does not duplicate staged
geostrophic or boundary-layer drag ideas because it never changes prognostic
wind, vorticity, divergence, or pressure; it only tests whether a static
surface-type residual memory is enough to move the fixed wind score.

## Evaluator Notes

### 2026-06-22T01:42:36Z

Decision: move to `ready`; ranked 1 of 1 ready proposals.

This is the strongest current triage target because it extends an accepted,
low-risk mechanism with a clear new physical axis. The accepted
`land-sea-contrast-surface-temperature` candidate produced a clean validation
gain of `+0.01672614488585067` by making only `2m_temperature` residual memory
land-sea aware. This proposal preserves that branch and tests the analogous
surface-type persistence signal for the remaining near-surface target channel,
`10m_u_component_of_wind`.

The idea is distinct from the rejected `coherent-u-residual-gate`, which was
safe but only improved iteration primary score by
`+0.00007187425176757856`. The proposed mask split is more physically grounded
than another generic wind residual gate: surface roughness and marine boundary
layer persistence plausibly affect 10 m wind residual decay, while the change
remains output-only and leaves mass fields, dry dynamics, DFI, weak-HS forcing,
theta tendency, and the accepted T2m land-sea correction unchanged.

Source inspection supports feasibility. The incumbent already loads and
validates `land_sea_mask` for the accepted T2m residual path, and
`_apply_scale_separated_near_surface_residual_correction` already has channel
specific decay hooks. The implementation should be limited to a side-by-side
candidate, a small wind decay helper, focused fallback tests, and registry
coverage. Use the fixed protocols only: `pytest`, `fast`, `iteration --workers
4`, and `validation --workers 4` only if iteration promotes; do not run
`golden`.
