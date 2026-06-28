---
schema_version: 1
slug: dfi-mass-neutral-log-pressure-restore
title: Restore Global Surface Mass After Digital Filter Initialization
status: staging
created_at: 2026-06-21T14:14:13Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Restore Global Surface Mass After Digital Filter Initialization

## Hypothesis

Digital filter initialization damps fast adjustment modes, but the filtered
state can slightly change the global mean of `log_surface_pressure` or the
area-mean surface pressure implied by it. Positive-time pressure anchoring and
continuity rewrites have negative or weak history, but those results do not
isolate a narrower question: whether the DFI merge itself introduces a small
zero-mode dry-mass shift before the accepted rollout begins.

Restoring only the post-DFI global dry surface mass to the pre-DFI initialized
mass should preserve the useful gravity-wave filtering while preventing a
nonphysical mass offset from seeding MSLP and thickness drift.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_dfi_mass_restore`.
Preserve every incumbent option except for wrapping the output of digital filter
initialization.

Inside the DFI trajectory wrapper:

- compute the area-weighted global mean surface pressure from the initialized
  pre-DFI state;
- run the accepted DFI initializer exactly as the incumbent does;
- compute the area-weighted global mean surface pressure from the filtered
  state;
- add a spatially uniform log-pressure offset to the filtered
  `log_surface_pressure` so the global mean surface pressure matches the
  pre-DFI value;
- leave vorticity, divergence, temperature variation, tracers, weak-HS
  equilibrium offset, positive-time continuity, residual memory, and outputs
  unchanged;
- fall back to the unmodified filtered state if any diagnostic is nonfinite or
  the required pressure means are not positive.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate factory; do not alter the incumbent factory.
- API changes:
  - None. The forecast input, output contract, metrics, target variables, and
    split definitions remain unchanged.
- Tests to update:
  - Unit-test exact global surface-pressure restoration on finite synthetic
    states.
  - Verify nonfinite and nonpositive fallback to the incumbent DFI output.
  - Verify vorticity, divergence, temperature, and tracers are bitwise unchanged
    by the restore helper except for `log_surface_pressure`.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 1 to 15 if DFI introduces a small global
    dry-mass offset that the accepted rollout then preserves or amplifies.
  - `geopotential_500` may improve through reduced column-mass and thickness
    drift.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should remain close because
    thermal and wind fields are unchanged at the DFI restore point.
- Possible regressions:
  - If the DFI pressure zero-mode shift is part of the filter's balanced
    adjustment, restoring it can reintroduce a small mass imbalance.
  - Matching mean surface pressure rather than mean log pressure can slightly
    alter the log-pressure anomaly baseline.

## Risks

- Numerical stability:
  - Low to moderate. The correction is a single global scalar and finite-guarded,
    but it changes the mass field after DFI.
- Compute cost:
  - Low. It adds two global reductions during initialization.
- Data leakage:
  - Low. The target mass is the same forecast's pre-DFI initialized state, not a
    future verifying state.
- Physical plausibility:
  - Moderate. A closed dry primitive-equation atmosphere should not gain or lose
    global dry mass through an initialization filter, but the model's `log(ps)`
    representation makes the exact invariant subtle.
- Rollback complexity:
  - Low. Remove one DFI wrapper option, one factory/registry entry, and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_dfi_mass_restore`.
  - Require clean diagnostics and finite outputs.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_dfi_mass_restore --workers 4`.
  - Support requires at least `+0.002` primary-score delta with no fixed
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_dfi_mass_restore --workers 4` only after iteration promotion.
  - Require at least `+0.001` validation delta with clean diagnostics.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show that any DFI
    global-mass shift is immaterial or beneficial in the accepted incumbent.
    An early MSLP/Z500 guardrail failure would show the restore disrupts DFI
    balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` wraps
  `time_integration.digital_filter_initialization` before positive-time
  rollout when `apply_digital_filter_initialization=True`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  carries `log_surface_pressure` as a prognostic state coupled to divergence in
  the semi-implicit primitive-equation system.
- History: `.logbook/history/2026-06-16_09-54-58_balanced-digital-filter-initialization/decision.md`
  accepted DFI as useful, so this proposal preserves the DFI filter and adjusts
  only its global mass zero mode.
- History: `.logbook/history/2026-06-16_17-43-05_global-mean-pressure-anchor/decision.md`
  and `.logbook/history/2026-06-18_11-53-08_flux-form-surface-pressure-continuity/decision.md`
  provide negative evidence for positive-time pressure anchoring or continuity
  rewrites; this proposal is DFI-only.
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
  digital filter. Monthly Weather Review.
- Lynch, P. 1997. The Dolph-Chebyshev window: a simple optimal filter. Monthly
  Weather Review.

## Researcher Notes

This is not a duplicate of staged `surface-pressure-tendency-zero-mode-projection`
or scrapped `divergence-zero-mode-projection`, which act during positive-time
rollout. It is also distinct from the rejected global pressure anchor, because
it does not repeatedly pull the forecast pressure field toward an external
reference. The only reference is the same initialized state immediately before
DFI.

## Evaluator Notes

### 2026-06-21T14:18:59Z

Decision: move to `staging`; ranked 2 of 3 current proposals.

This is plausible and narrower than positive-time pressure anchoring, but it is
not the best immediate ready target. The incumbent DFI wrapper is localized in
the adapter, so a side-by-side post-DFI mass restore is technically feasible:
compute the pre-DFI and post-DFI area-mean surface pressure, apply one guarded
uniform `log_surface_pressure` offset, and leave all other state leaves and
forecast outputs unchanged.

Keep it staged because the physical and numerical payoff is uncertain. The DFI
algorithm is an initialization filter, and dry-mass conservation is a reasonable
diagnostic concern, but the model prognoses `log_surface_pressure`; matching
mean pressure by a uniform log-pressure offset is only an approximate invariant
repair. The pressure/mass family has repeated negative or weak evidence:
global pressure anchoring was rejected, positive-time pressure-tendency
projection is already staged rather than ready, mass-weighted theta recentering
was clean but negative, and recent startup/divergence cleanup ideas did not
show a useful remaining fast-mode signal.

This proposal should be reconsidered after either a read-only check shows that
incumbent DFI materially shifts global surface mass, or the narrower
screen-temperature initialization candidate is exhausted. If promoted later,
the implementation must use fixed constants, preserve non-pressure leaves
exactly, guard nonfinite or nonpositive means, and compare only through the
fixed fast, iteration, and validation gates.
