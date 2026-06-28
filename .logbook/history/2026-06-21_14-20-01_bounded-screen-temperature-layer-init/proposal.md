---
schema_version: 1
slug: bounded-screen-temperature-layer-init
title: Initialize the Lowest Sigma Temperature With a Bounded Screen-Level Blend
status: ready
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

# Initialize the Lowest Sigma Temperature With a Bounded Screen-Level Blend

## Hypothesis

The incumbent still diagnoses `2m_temperature` from the lowest sigma-layer
temperature and then applies the accepted scale-separated residual correction.
That output correction is valuable, but it does not change the lower-layer
prognostic thermal state that feeds pressure thickness, weak-HS relaxation, and
later screen-temperature diagnostics.

A bounded, initialization-only blend of the lowest sigma-layer temperature
toward the analyzed `2m_temperature` can reduce the initial surface-layer
representativeness error before it becomes a rollout thermal error. Because the
blend is small, lowest-layer-only, and capped, it is distinct from another
residual-memory schedule or a prognostic heat-mixing scheme.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init`.
Preserve the accepted DFI, log-pressure sigma initialization, hydrostatic
layer initialization, Strang Coriolis split, theta tendency, theta mean
recentering, semi-implicit off-centering, scale-separated residuals, and
analysis-offset weak-HS equilibrium.

After the accepted pressure-level to sigma interpolation and hydrostatic
temperature initialization, but before modal conversion:

- if `2m_temperature` is present, compute the local difference between the
  analyzed screen temperature and the initialized lowest sigma-layer absolute
  temperature;
- keep only a bounded increment, for example clipped to +/- 2 K and multiplied
  by a small fixed blend factor such as 0.25;
- optionally taper the increment by static stability using the existing
  lower-column potential-temperature proxy, so very stable columns receive less
  prognostic perturbation;
- apply the increment only to the lowest sigma temperature layer, with finite
  fallback to the incumbent initialized temperature;
- leave all pressure-level target outputs and residual-correction logic
  unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate factory; do not change the incumbent factory.
- API changes:
  - None. Forecast inputs, returned variables, lead times, target variables,
    metrics, and evaluation protocols remain fixed.
- Tests to update:
  - Unit-test cap, blend factor, finite fallback, and absent-`2m_temperature`
    incumbent-equivalence.
  - Verify that only the lowest sigma temperature changes before modal packing.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 1 to 7 if unresolved screen-layer thermal mismatch
    is still leaking into the lower prognostic layer after residual decay.
  - Small secondary gains in `mean_sea_level_pressure` and `geopotential_500` if
    lower-column thickness is initialized closer to the analyzed near-surface
    thermal state.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain near neutral because winds and the
    accepted Richardson 10 m diagnostic are unchanged.
- Possible regressions:
  - `mean_sea_level_pressure` and `geopotential_500` can regress if the screen
    increment is not representative of the lowest resolved sigma layer.
  - Early `2m_temperature` can worsen if the accepted residual correction already
    handles the useful part of the screen-layer mismatch.

## Risks

- Numerical stability:
  - Low to moderate. The increment is initialization-only and capped, but it
    perturbs hydrostatic lower-column balance.
- Compute cost:
  - Low. The change is one local array operation during initialization.
- Data leakage:
  - Low. It uses only same-time initial `2m_temperature`, already present in the
    forecast input, and no future truth or validation statistics.
- Physical plausibility:
  - Moderate. Operational systems diagnose screen temperature with surface-layer
    relationships, so using a small screen-level increment as an initialization
    boundary cue is plausible, but it is not a full land-surface model.
- Rollback complexity:
  - Low. Remove one option, one factory/registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init`.
  - Require clean diagnostics and finite outputs.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init --workers 4`.
  - Support requires at least `+0.002` primary-score delta with no fixed
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_screen_t_init --workers 4` only after iteration promotion.
  - Require at least `+0.001` validation delta with clean diagnostics.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would indicate that the
    accepted output residual path already captures the useful screen-temperature
    signal, or that changing the prognostic lowest layer is not beneficial.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  maps `2m_temperature` to `temperature[:, -1]` during output packing and then
  applies near-surface residual corrections after the raw trajectory is packed.
- History: `.logbook/history/2026-06-19_21-12-19_scale-separated-surface-residual-memory/decision.md`
  accepted scale-separated near-surface residual memory with large iteration
  and validation gains, showing that surface-layer representativeness remains
  high leverage.
- History: `.logbook/history/2026-06-21_12-29-32_virtual-theta-richardson-10m-wind/decision.md`
  rejected a diagnostic-only virtual-temperature extension for 10 m wind, so
  this proposal changes the prognostic lower thermal initialization instead of
  adding another wind diagnostic.
- ECMWF. 2023. IFS Documentation CY48R1, Part IV: Physical Processes,
  section on surface-layer diagnostics.
- Stull, R. B. 1988. An Introduction to Boundary Layer Meteorology. Kluwer
  Academic Publishers.

## Researcher Notes

This is not a duplicate of staged `bulk-richardson-2m-temperature-diagnostic`
or `diurnal-surface-residual-memory`, which only change output diagnostics or
residual memory. It is also not the scrapped near-surface heat-mixing family,
because no positive-time vertical diffusion is added. The mechanism is a
single, capped initialization correction to the lowest prognostic thermal layer.

## Evaluator Notes

### 2026-06-21T14:18:59Z

Decision: move to `ready`; ranked 1 of 3 current proposals.

This is implementable now and has the best cost-risk profile in the current
batch. Source inspection confirms that the incumbent initializes sigma-layer
temperature from the pressure-level stack, then later emits raw
`2m_temperature` from the lowest sigma layer before applying the accepted
near-surface residual correction. A candidate can therefore add a side-by-side,
bounded initialization-only lowest-layer temperature increment without changing
the forecast contract, fixed protocols, target variables, residual-output path,
or positive-time solver.

The proposal is close to staged `lower-column-thermal-iau-spinup` and active
surface-temperature diagnostic ideas, but it is narrower than both: it applies
one capped same-time cue to the lowest resolved thermal layer before rollout
instead of adding a positive-time IAU tendency or another output-only residual
memory rule. That gives a concrete test of whether the remaining
screen-temperature error belongs partly in the prognostic lower layer while
keeping rollback simple.

Recent history is a warning rather than a rejection. Surface-output diagnostics
and residual-memory changes have been high leverage but fragile, and
`virtual-theta-richardson-10m-wind` plus `gradient-wind-surface-diagnostic`
argue against another wind diagnostic. This proposal avoids that family and
targets the thermal initialization state directly. The cap and lowest-layer-only
scope are essential; an implementation should preserve absent-`2m_temperature`
incumbent equivalence, finite fallback, and tests proving no non-lowest-layer
state changes at initialization.
