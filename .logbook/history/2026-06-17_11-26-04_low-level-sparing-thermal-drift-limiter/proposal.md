---
schema_version: 1
slug: low-level-sparing-thermal-drift-limiter
title: Limit Free-Tropospheric Thermal Drift While Sparing Low Levels
status: ready
created_at: 2026-06-17T11:20:21Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
expected_code_paths:
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

# Limit Free-Tropospheric Thermal Drift While Sparing Low Levels

## Hypothesis

The rejected `layer-mean-thermal-recentering` candidate is unusually
informative negative evidence: it improved iteration primary score by
`+0.010479318541482652` and validation primary score by
`+0.009368698506964535`, but it failed the fixed early `10m_u_component_of_wind`
mean RMSE guardrail by only `+2.1028446258823053%` against a `2%` limit. That
suggests the remaining free-run thermal drift is a real error source, while
the prior correction was too coupled to lower-tropospheric wind balance.

A low-level-sparing thermal drift limiter should retain the useful
free-tropospheric mass/thickness signal from thermal recentering while avoiding
the boundary-layer thermal edits most likely to project onto the evaluated
10 m zonal wind. The expected benefit is smaller than the rejected full-column
candidate, but the mechanism directly addresses the reason that candidate could
not be accepted.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter`.
Preserve the incumbent initialization, DFI, weak Held-Suarez thermal
relaxation, near-surface residual correction, log-pressure initialization,
layer-mean hydrostatic temperature initialization, vertical advection,
horizontal diffusion, T80 truncation, 900 s inner step, output variables, lead
times, and metrics.

During the positive-time forecast rollout only, add a step filter after the
existing IMEX step and horizontal diffusion. The filter edits only the spectral
zero-wavenumber coefficient of `temperature_variation` in upper and
mid-tropospheric sigma layers, for example sigma centers at or above about
`0.55`, by copying the previous state's value into the next state for those
selected layers. It must leave all lower sigma layers, nonzero temperature
modes, vorticity, divergence, `log_surface_pressure`, passive tracers,
`sim_time`, DFI, and output residuals unchanged.

This is not a coefficient sweep. The first candidate should use one fixed
sigma mask chosen before scoring and should not tune a relaxation strength
against iteration or validation. If the Evaluator wants a different sigma mask,
that choice should be made before implementation and then held fixed.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter`.
- API changes:
  - None. Preserve deterministic `forecast(ForecastInput) -> WeatherState`,
    emitted channel names, target variables, lead times, and metrics.
- Tests to update:
  - Unit-test the sigma mask so selected upper/mid layers are constrained and
    lower sigma layers are unchanged.
  - Unit-test the step filter on a small `primitive_equations.State`: only the
    selected layerwise zero-wavenumber `temperature_variation` coefficients
    should be copied from the previous state.
  - Verify vorticity, divergence, `log_surface_pressure`, tracers, `sim_time`,
    nonzero temperature modes, and all low-level temperature means are
    unchanged.
  - Verify the candidate factory preserves every incumbent flag except the new
    thermal-limiter option.
  - Add registry coverage and a non-JIT finite smoke forecast for the side-by-
    side candidate.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature`, `geopotential_500`, and `mean_sea_level_pressure` at
    medium and long leads if free-tropospheric thermal drift remains a dominant
    column-thickness error source.
  - Primary score should improve less than the rejected full-column thermal
    recentering candidate but with a better chance of passing the early
    `10m_u_component_of_wind` guardrail.
- Expected neutral metrics:
  - Day-1 low-level wind should be closer to the incumbent than in full-column
    thermal recentering because lower sigma-layer means and all wind variables
    are left unchanged by the added filter.
- Possible regressions:
  - Freezing upper layer means can still alter baroclinic pressure gradients and
    project onto low-level wind through the dynamics.
  - A hard sigma cutoff can introduce a vertical thermal-gradient discontinuity
    in the mean state if the selected mask is too shallow.
  - If the full-column gain came mainly from lower-tropospheric temperature
    means, this low-level-sparing version may be guardrail-clean but below the
    fixed promotion threshold.

## Risks

- Numerical stability:
  - Low to moderate. The filter edits bounded modal coefficients and removes no
    prognostic process, but it constrains part of the thermal tendency every
    inner step.
- Compute cost:
  - Low. The operation is a small modal-array update inside the existing step
    filter path and fits the fixed `--workers 4` budget.
- Data leakage:
  - Low. It uses only previous and next forecast states, no future truth,
    validation statistics, target residuals, or golden data.
- Physical plausibility:
  - Moderate. The mechanism represents a constrained free-tropospheric
    mean-state energy/thickness control in a dry dycore without full physics.
    The low-level mask is physically motivated by the failed wind guardrail but
    remains an approximation.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter flag and one side-by-side
    factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, no early day 1-5 mean RMSE guardrail failure, no
    variable+lead RMSE guardrail failure, and especially no early
    `10m_u_component_of_wind` regression above the fixed `2%` limit.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - Any early `10m_u_component_of_wind` guardrail failure would show the
    low-level-sparing mechanism did not solve the known thermal-recentering
    failure mode. A clean but sub-threshold primary delta would show the useful
    signal in full-column recentering was too dependent on the lower layers.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` constructs
  the incumbent step function with `time_integration.step_with_filters`, making
  a guarded forward-rollout state filter implementable without changing the
  forecast API.
- History: `.logbook/history/2026-06-17_04-21-14_layer-mean-thermal-recentering/decision.md`
  rejected full-column thermal recentering despite large primary gains because
  early `10m_u_component_of_wind` mean RMSE regressed by
  `+2.1028446258823053%`.
- History: `.logbook/history/2026-06-16_16-27-03_wind-sparing-held-suarez-relaxation/decision.md`
  accepted thermal-only weak Held-Suarez relaxation, showing wind-sparing
  thermal constraints can improve the fixed WeatherBench2 gates.
- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
  Assimilation Using Incremental Analysis Updates. Monthly Weather Review,
  124, 1256-1271.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is a near-neighbor of a rejected idea only because that history contains a
strong positive signal and a narrow, diagnosable guardrail failure. It is not a
repeat of full-column `layer-mean-thermal-recentering`: the rejected candidate
froze every layer mean, including the boundary-layer layers that feed the
evaluated 10 m wind. This proposal constrains only upper and mid-tropospheric
thermal means and keeps lower sigma layers untouched.

It is also distinct from active staged proposals. It does not change passive
humidity handling, surface-layer output diagnostics, pressure-to-sigma
extrapolation, or vertical transport discretization. It should be ranked only
if the Evaluator accepts that the prior thermal-recentering result justifies
one bounded, wind-protected follow-up.

## Evaluator Notes

2026-06-17T11:23:24Z - Move to `ready`; rank 1 of 6 active ideas.

This is the best next implementation target because it is the only active idea
with direct evidence of a large positive primary-score signal under the fixed
WeatherBench2 gates. The rejected full-column
`layer-mean-thermal-recentering` candidate improved iteration primary by
`+0.010479318541482652` and validation primary by `+0.009368698506964535`, but
missed the early `10m_u_component_of_wind` mean RMSE guardrail by a narrow
margin: `+2.1028446258823053%` against the fixed `2%` limit. That history
supports one bounded follow-up focused on preserving the free-tropospheric
thermal-drift benefit while explicitly protecting low-level wind balance.

The proposal is sufficiently different from the rejected full-column candidate
for one ready trial. It constrains only the spectral zero-wavenumber
`temperature_variation` component in upper and mid sigma layers during the
positive-time forecast rollout, leaves lower sigma layers and all wind fields
untouched, and avoids coefficient tuning. Local source inspection confirms the
adapter already builds the forward step with `time_integration.step_with_filters`,
so a side-by-side state filter can be implemented without changing the forecast
API, output variables, lead times, or fixed evaluation protocol.

Implementation constraints: keep exactly one fixed mask chosen before scoring;
interpret "low-level sparing" as constraining only upper/mid layers with sigma
centers `<= 0.55` and leaving all layers with sigma centers `> 0.55` unchanged;
copy only the selected layerwise zero-wavenumber temperature coefficients from
the previous state into the next state; preserve vorticity, divergence,
`log_surface_pressure`, tracers, `sim_time`, nonzero temperature modes, DFI,
weak-HS settings, near-surface residuals, T80 truncation, 900 s inner step, and
all output diagnostics. Do not tune the mask or relaxation strength after any
score is observed.
