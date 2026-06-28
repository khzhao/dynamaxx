---
schema_version: 1
slug: pressure-level-loglaw-10m-wind
title: Diagnose 10 m Wind from Pressure-Level Log-Law Shear
status: scrap
created_at: 2026-06-21T00:38:35Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
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

# Diagnose 10 m Wind from Pressure-Level Log-Law Shear

## Hypothesis

The incumbent's accepted Richardson 10 m wind diagnostic scales the lowest
sigma-layer wind. That helped, but it still ties the scored 10 m zonal wind to
the sigma grid's lowest model level. A bounded diagnostic that derives the
surface-layer wind from forecast pressure-level winds, using hypsometric
heights and a neutral log-law profile, may reduce grid-level dependence without
changing prognostic winds, vorticity, DFI, Coriolis splitting, weak-HS forcing,
or residual timing.

## Mechanism

Register a side-by-side candidate with a suffix such as `_pl_loglaw_10m_wind`.
Preserve the incumbent trajectory and all non-10 m output paths.

For the candidate only:

- compute the normal forecast pressure-level wind fields already used for
  output packing;
- select the lowest two available pressure levels above the surface in each
  column, preferring 1000/925 hPa when finite and falling back to the nearest
  valid pair;
- estimate their heights above the model surface with the dry hypsometric
  relation using local forecast temperature;
- diagnose a neutral log-law 10 m wind from the lower pressure-level wind and
  bounded shear between the pressure levels;
- cap the diagnosed 10 m wind speed ratio relative to the incumbent Richardson
  diagnostic, for example `[0.65, 1.15]`, and preserve the incumbent value
  wherever height, wind, or temperature inputs are nonfinite;
- change only `10m_u_component_of_wind` and, if emitted, the paired
  `10m_v_component_of_wind`.

This is not a gradient-wind diagnostic, wind increment limiter, vorticity
projection, or rollout wind damping. It is a forecast-output surface-layer
diagnostic built from standard pressure-level winds.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry entry.
- API changes:
  - None. Forecast inputs, output names, target variables, lead times, and
    fixed metrics remain unchanged.
- Tests to update:
  - Unit-test height estimation, speed-ratio caps, finite fallback, and
    component-preserving wind direction.
  - Verify non-wind channels are unchanged.
  - Verify the factory preserves all incumbent flags except the new output
    diagnostic selector.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind`, especially after the accepted residual memory has
    decayed and the lowest-sigma proxy dominates.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, and `geopotential_500` should
    be unchanged apart from metric bookkeeping noise.
- Possible regressions:
  - Pressure-level winds may be less representative of screen-level flow than
    the accepted Richardson-scaled sigma wind in stable boundary layers.

## Risks

- Numerical stability:
  - Low. The change is output-only and finite-guarded.
- Compute cost:
  - Low. It reuses pressure-level output fields already computed by the adapter.
- Data leakage:
  - None. It uses only forecast-state fields and fixed physical constants.
- Physical plausibility:
  - Moderate. Log-law surface diagnostics are standard, but this dycore lacks
    roughness length, stability functions, and surface fluxes.
- Rollback complexity:
  - Low. Remove one helper/flag, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show the accepted
    Richardson sigma-level diagnostic remains preferable. Any day-1 wind
    guardrail failure would show the pressure-level log-law proxy is too crude.

## Citations

- ECMWF IFS Documentation Part IV: Physical Processes describes 10 m wind as a
  surface-layer diagnostic product based on near-surface similarity theory.
  https://www.ecmwf.int/sites/default/files/elibrary/2016/17117-part-iv-physical-processes.pdf
- Stull, R. 1988. An Introduction to Boundary Layer Meteorology. Kluwer
  Academic Publishers. https://doi.org/10.1007/978-94-009-3027-8
- Monin, A. S. and Obukhov, A. M. 1954. Basic laws of turbulent mixing in the
  surface layer of the atmosphere.
- Dynamaxx history:
  `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/decision.md`
  accepted a bounded surface-layer 10 m wind diagnostic, motivating a different
  output-only wind diagnostic rather than a rollout change.
- Dynamaxx history:
  `.logbook/history/2026-06-20_17-12-34_gradient-wind-surface-diagnostic/decision.md`
  rejected a gradient-wind diagnostic; this proposal avoids pressure-gradient
  curvature and uses only local vertical shear.

## Researcher Notes

This is materially different from the accepted Richardson 10 m wind diagnostic
because it does not scale the lowest sigma wind directly. It is also not a
wind limiter or vorticity idea: it never changes the trajectory, vorticity,
divergence, or initialized winds.

## Evaluator Notes

### 2026-06-21T00:41:38Z

Decision: move to `scrap`.

Reject this as a low-priority near-duplicate of already consumed 10 m wind
diagnostic work. The accepted Richardson 10 m diagnostic is already in the
incumbent and produced a large, clean improvement concentrated in
`10m_u_component_of_wind`. The most recent alternate output-only wind idea,
`gradient-wind-surface-diagnostic`, failed the iteration promotion gate with a
negative primary delta and an early day-1-through-day-5 10 m wind guardrail
regression. That is direct negative evidence against another broad day-1
replacement for the accepted Richardson path.

The proposed pressure-level log-law mechanism is physically recognizable, but
the available forecast state lacks roughness length, stability functions,
surface fluxes, and a reliable terrain-aware surface-layer geometry. It also
derives a scored near-surface channel from pressure-level output fields after
the incumbent already solved the main 10 m wind proxy problem. The cap against
the incumbent diagnostic reduces numerical risk, but it also makes the
candidate mostly a metric-facing post-processor with limited new physical
signal. Do not spend a model-selection evaluation on this unless future
read-only diagnostics show a clear pressure-level shear error that the accepted
Richardson diagnostic cannot represent.
