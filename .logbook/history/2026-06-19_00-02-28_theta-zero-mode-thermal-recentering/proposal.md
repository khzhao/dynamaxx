---
schema_version: 1
slug: theta-zero-mode-thermal-recentering
title: Recenter Layer-Mean Theta Drift Under the Current Wind Diagnostic
status: ready
created_at: 2026-06-18T23:56:34Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Recenter Layer-Mean Theta Drift Under the Current Wind Diagnostic

## Hypothesis

The current theta-form incumbent improved the thermodynamic rollout, but the
fixed iteration metrics still show strong long-lead `2m_temperature` cold bias
and growing `mean_sea_level_pressure` error. Prior full-column layer-mean
thermal recentering produced large positive primary-score movement, but it was
rejected because the old low-level 10 m wind output failed the early guardrail
by a narrow margin. The current incumbent now has a bounded Richardson 10 m wind
diagnostic and a theta-form thermal tendency, so a theta-space version of the
layer-mean control may recover the useful thermal-thickness signal while the
accepted wind diagnostic protects the formerly failing output channel.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter`.
Preserve incumbent initialization, DFI span, weak Held-Suarez forcing,
log-pressure and hydrostatic layer initialization, symmetric exact-Coriolis
split, stability-aware residual correction, Richardson 10 m wind diagnostic,
horizontal diffusion, vertical coordinate, output variables, and fixed
evaluation protocols.

Add one positive-time step wrapper after the incumbent dynamics and diffusion
step. The wrapper should:

- diagnose full temperature and layer pressure from the previous and next
  states;
- convert each to dry potential temperature on sigma layers;
- compute area-weighted horizontal layer means of theta;
- adjust only the horizontally uniform component of the next state's
  `temperature_variation` so each layer's theta mean matches the previous
  state's theta mean;
- leave all nonzero thermal modes, vorticity, divergence,
  `log_surface_pressure`, tracers, `sim_time`, Coriolis rotation, output
  interpolation, residual correction, and the Richardson 10 m wind diagnostic
  unchanged;
- run only during positive-time rollout, not during the time-reversed DFI
  initialization;
- fall back to the incumbent next state if pressure, theta, or the converted
  zero-mode increment is nonfinite.

This is not another scalar split-form or weak-HS algebra rewrite. It tests
whether the current dry dycore still benefits from suppressing global
layer-mean thermal drift, but expresses the constraint in the same dry
potential-temperature variable that improved the incumbent.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, lead times,
    target variables, splits, and metrics remain unchanged.
- Tests to update:
  - Unit-test the theta mean diagnostic and finite fallback on synthetic sigma
    states.
  - Verify the wrapper changes only layerwise zero-mode
    `temperature_variation` coefficients and leaves nonzero modes and all
    non-temperature fields unchanged.
  - Verify the candidate factory preserves every incumbent flag except the new
    theta mean recentering selector.
  - Verify DFI receives the incumbent filter set while positive-time rollout
    receives the new wrapper.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and long leads if global lower-column thermal
    drift is still driving the post-residual cold bias.
  - `geopotential_500` and `mean_sea_level_pressure` if layer-mean theta control
    improves dry thickness and balanced mass evolution.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be more protected than in the older
    rejected thermal recentering run because the accepted Richardson 10 m wind
    diagnostic and residual decay remain in force.
- Possible regressions:
  - Freezing layer-mean theta can still alter pressure-gradient adjustment and
    degrade wind dynamics, even if the output diagnostic is better protected.
  - If the accepted theta tendency already removed the useful drift, this may
    be clean but subthreshold.

## Risks

- Numerical stability:
  - Moderate. The operation is bounded to a zero-mode thermal correction, but
    it runs every positive-time inner step.
- Compute cost:
  - Low to moderate. It adds local pressure/theta conversions and layerwise
    reductions but no extra forecast steps, resolution, or evaluation workers.
- Data leakage:
  - None. It uses only previous and next forecast states plus fixed physical
    constants.
- Physical plausibility:
  - Moderate. Potential temperature is the dry materially conserved variable,
    but constraining its layer mean is an idealized energy/thickness control
    rather than full physics.
- Rollback complexity:
  - Low. Remove one option, one wrapper/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that theta
    zero-mode drift is not a material remaining error source. Any early MSLP,
    Z500, or 10 m wind guardrail failure would show the constraint disrupts
    balanced evolution more than it helps.

## Citations

- Citation or source:
  - Dynamaxx history:
    `.logbook/history/2026-06-17_04-21-14_layer-mean-thermal-recentering/decision.md`
    rejected full-column thermal recentering only after a narrow early wind
    guardrail failure despite large primary-score gains.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/decision.md`
    accepted the current bounded Richardson 10 m wind diagnostic with large wind
    gains and effectively unchanged non-wind metrics.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md`
    accepted the current theta-form thermal tendency and noted small pressure
    and geopotential side effects.
  - Polichtchouk, I., Malardel, S., and Diamantakis, M. 2020. Potential
    temperature as a prognostic variable in hydrostatic semi-implicit
    semi-Lagrangian IFS. ECMWF Technical Memorandum 869.
    https://www.ecmwf.int/en/elibrary/81180-potential-temperature-prognostic-variable-hydrostatic-semi-implicit-semi
  - Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
    Assimilation Using Incremental Analysis Updates. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With
    Applications to Geophysics, second edition. Springer.
    https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is intentionally close to a rejected thermal-recentering family only
because that family produced one of the strongest positive primary-score
signals in history and failed on a channel that the current incumbent has since
materially changed. It is not a repeat of raw temperature zero-mode freezing:
the constraint is formulated in dry potential temperature, targets the current
theta incumbent, preserves the accepted Richardson 10 m wind diagnostic, and
does not alter weak-HS forcing or scalar-advection symmetry.

This is also not a duplicate of the rejected `theta-skew-symmetric-scalar-
advection`, which changed scalar transport form and was nearly neutral, nor of
`theta-consistent-held-suarez-forcing`, which was almost algebraically neutral.
The proposed mechanism can move scores because it constrains a layer-mean
thermal drift mode that previous evaluation showed can materially affect the
fixed primary score.

## Evaluator Notes

### 2026-06-19T00:01:16Z

Decision: `ready`.

This is the strongest next candidate among the new proposals. It is close to
the rejected `layer-mean-thermal-recentering` experiment, but the prior run is
not decisive against this variant: that candidate cleared the primary-score
threshold by a large margin and failed only the early 10 m wind mean-RMSE
guardrail by a narrow `+2.1028446258823053%` regression. Since then, the
incumbent has accepted both the bounded Richardson 10 m wind diagnostic and the
theta-form thermodynamic tendency, so the previous wind failure mode is partly
addressed and the new theta-space formulation is a materially different test.

The proposal preserves the forecast contract, fixed target variables,
protocols, splits, and deterministic gates. It does not use future truth,
validation statistics, or golden data. Implementation risk is moderate because
the wrapper changes the positive-time thermal trajectory each step, but the
change is confined to the horizontally uniform theta component and has clear
rollback boundaries. Score upside is supported by prior history, and expected
guardrail risk is explicit and measurable.

Rank: 1 of 3. Promote as the only ready item so the Orchestrator can select one
implementation target without mixing ideas.
