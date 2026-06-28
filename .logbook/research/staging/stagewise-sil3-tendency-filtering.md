---
schema_version: 1
slug: stagewise-sil3-tendency-filtering
title: Stagewise SIL3 Tendency Filtering
status: staging
created_at: 2026-06-26T00:00:00Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
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

# Stagewise SIL3 Tendency Filtering

## Hypothesis

The incumbent applies horizontal diffusion after each complete SIL3 step, but nonlinear explicit tendencies are evaluated on intermediate Runge-Kutta stage states before that post-step filter is applied. High-wavenumber stage noise can therefore feed pressure, kinetic-energy, and scalar-advection tendencies inside the step even if the final state is subsequently diffused. Applying a small, fractional version of the existing horizontal diffusion to SIL3 stage states before tendency evaluation may reduce aliasing-like stage noise and medium-lead phase drift while preserving the accepted total post-step diffusion and all physical parameterizations.

## Mechanism

Add one side-by-side candidate, for example `dino_hsl2_mass_dse_wtg_vdse_ramp_stagefilter`.

For this candidate only:

- keep the incumbent model stack, step size, SIL3 tableau, off-centering, DFI, weak-HS forcing, surface residuals, Richardson wind diagnostic, ocean heat flux, mass-DSE HSL, WTG relaxation, and vertical-DSE ramp unchanged;
- add an opt-in SIL3 stepper wrapper that applies the incumbent horizontal diffusion operator with fractional stage weights to intermediate stage states `Y` before evaluating `F(Y)` and `G(Y)`;
- keep the existing full post-step diffusion filter in place, so this is not a diffusion-strength reduction or replacement;
- use fixed stage fractions derived from the SIL3 stage times, not tuned against scores;
- fall back to the incumbent unfiltered-stage SIL3 step when a filtered stage is nonfinite.

This tests filter placement inside the existing time discretization, not a new physical damping process or a new Runge-Kutta scheme.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one model key such as `dino_hsl2_mass_dse_wtg_vdse_ramp_stagefilter`.
- API changes:
  - None. Forecast inputs, outputs, target variables, and fixed protocols remain unchanged.
- Tests to update:
  - Verify the candidate factory differs from the incumbent only by the stage-filter selector and model name.
  - Unit-test that zero stage-filter strength reproduces incumbent SIL3.
  - Unit-test finite fallback when a stage filter emits nonfinite values.
  - Verify the normal post-step filter list is preserved.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500`, `mean_sea_level_pressure`, and `10m_u_component_of_wind` at medium and late leads if stage-level high-wavenumber tendency noise contributes to phase or amplitude drift.
  - Small `2m_temperature` improvement if cleaner scalar tendencies reduce lower-column thermal noise.
- Expected neutral metrics:
  - Day-1 fields should remain close to incumbent because the final post-step diffusion and all accepted physics remain unchanged.
- Possible regressions:
  - Filtering stage states can overdamp useful near-truncation dynamics and reduce synoptic amplitude.
  - The existing post-step diffusion may already control the relevant noise, making the result neutral or negative.

## Risks

- Numerical stability:
  - Low to moderate. The operation is dissipative and finite-guarded, but it changes states seen by explicit and implicit tendency evaluations.
- Compute cost:
  - Moderate. Additional modal scaling is cheap, but it occurs inside every SIL3 step. The fixed `--workers 4` resource envelope is adequate for one run.
- Data leakage:
  - None. The filter uses only grid geometry, the incumbent diffusion operator, and current model stage states.
- Physical plausibility:
  - Moderate. This is numerical regularization of a spectral-transform RK discretization, not a new physical law.
- Rollback complexity:
  - Low. Remove one stepper wrapper/selector, one factory/export, one registry entry, and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_stagefilter`.
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_stagefilter --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached `dino_hsl2_mass_dse_wtg_vdse_ramp`, clean diagnostics, and no early day-1-through-day-5 or variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_stagefilter --workers 4` only after iteration promotion.
  - Support requires validation primary-score delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that within-step high-wavenumber stage noise is not a material remaining error source. Early wind, MSLP, or Z500 guardrail failure would show the stage filtering is too intrusive.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py` implements the SIL3 IMEX Runge-Kutta stages, while `adapter.py` applies horizontal diffusion as a post-step filter through `time_integration.step_with_filters`.
- Dynamaxx history: `.logbook/history/2026-06-18_13-26-11_symmetric-horizontal-diffusion-split/decision.md` rejected splitting the final post-step diffusion into half steps; this proposal instead filters intermediate SIL3 stage states before tendency evaluation.
- Dynamaxx history: `.logbook/history/2026-06-20_07-31-40_williamson-cn-rk3-rollout/decision.md` rejected replacing the accepted SIL3 rollout, so this proposal preserves the SIL3 tableau and only adds a guarded stage regularization.
- Whitaker, J. S. and Kar, S. K. 2013. Implicit-Explicit Runge-Kutta Methods for Fast-Slow Wave Problems. *Monthly Weather Review*. https://doi.org/10.1175/MWR-D-13-00132.1
- Patterson, G. S. and Orszag, S. A. 1971. Spectral Calculations of Isotropic Turbulence: Efficient Removal of Aliasing Interactions. *Physics of Fluids*. https://doi.org/10.1063/1.1693365
- Canuto, C., Hussaini, M. Y., Quarteroni, A., and Zang, T. A. 2007. *Spectral Methods: Evolution to Complex Geometries and Applications to Fluid Dynamics*. Springer. https://doi.org/10.1007/978-3-540-30728-0

## Researcher Notes

This is not a duplicate of the rejected symmetric horizontal-diffusion split: that changed placement around complete positive-time steps, while this proposal leaves the full post-step filter in place and targets intermediate SIL3 stage states before nonlinear tendencies are sampled. It is also not the staged RK4 proposal because the SIL3 tableau, step count, DFI contract, and forecast lead contract remain fixed.

The proposal is decorrelated from the recent vertical/thermal failures: it does not change vertical-DSE ramp timing, cap release, hydrostatic-work gates, WTG strength, mass-DSE scalar centering, roughness-aware wind output, or coupled surface residual decay. It is riskier than pure transform precision because stage states feed both explicit and implicit tendency paths, so the Evaluator should rank it behind lower-surface-risk ideas if numerical-filter evidence remains weak.

## Evaluator Notes

### 2026-06-26T15:05:45Z

Decision: move to `staging`; ranked 2 of 2 in this triage.

This proposal is plausible but not the next implementation target. The mechanism
is grounded in a real numerical concern for pseudo-spectral nonlinear tendency
evaluation, and it preserves the accepted SIL3 family rather than replacing it.
However, source inspection shows this would require a new SIL3 wrapper or
equation/filter interface that applies diffusion to intermediate stage states
before both explicit and implicit tendency evaluations. That is a materially
broader behavior change than changing the existing spherical-transform
precision selector.

Recent history also argues for caution. Symmetric post-step diffusion splitting
was clean but slightly negative, and broad time-integration replacement via
Williamson CN-RK3 was strongly negative. The latest
`mass-centered-dse-anomaly-hsl` rejection shows that clean, physically safe
numerical refinements can still be far below the fixed promotion threshold.
Stage filtering is more intrusive than those arithmetic cleanup paths because it
changes the states sampled inside the step and can damp useful near-truncation
dynamics even if diagnostics stay clean.

Keep staged as a fallback if lower-risk numerical-fidelity ideas fail cleanly or
if diagnostics identify within-step high-wavenumber stage noise as a dominant
remaining error source. Before promotion, the stage fractions and exact
application points should be fixed in the proposal, and the Implementer should
prove zero-strength equivalence to the incumbent plus preservation of the normal
post-step filter chain.
