---
schema_version: 1
slug: bounded-saturation-adjustment
title: Add Bounded Saturation-Adjustment Latent Heating
status: ready
created_at: 2026-06-17T19:27:53Z
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

# Add Bounded Saturation-Adjustment Latent Heating

## Hypothesis

The renewed bounded moist virtual-temperature candidate is important negative
evidence. It showed that simply allowing passive humidity to enter density,
pressure-gradient, and moist thermodynamic factors is now numerically stable,
but it regresses iteration primary score by `-0.055193744700895`. The failure
was not a diagnostic or humidity-bound problem; it was a model-skill problem,
with the largest guardrail movement in early `10m_u_component_of_wind`.

That rejection does not test the materially different moist-physics mechanism
that the decision record identifies as missing: phase-change removal of
supersaturation and latent-heat release. A bounded saturation-adjustment filter
can let humidity affect temperature through a standard diabatic pathway while
deliberately keeping the rejected direct virtual-temperature dynamics path off.
If part of the incumbent's persistent cold `2m_temperature` bias and mass-field
drift comes from a dry rollout that advects water vapor without condensation
heating, a local supersaturation adjustment may improve temperature, thickness,
and pressure fields without applying a global humidity density feedback.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust`.
Preserve the incumbent DFI, weak wind-sparing Held-Suarez thermal relaxation,
near-surface residual correction, log-pressure initialization,
layer-mean hydrostatic temperature initialization, zero orography, vertical
advection, T80 truncation, 900 s inner step, output variables, lead handling,
metrics, and forecast API.

Keep `use_humidity_in_dynamics=False`. Specific humidity remains an advected
tracer in the dry primitive-equation rollout and in geopotential diagnostics,
but it does not enter the rejected moist virtual-temperature pressure-gradient
path. Add one forward-rollout-only step filter after the existing positive-time
IMEX and horizontal-diffusion step. Do not include this irreversible moist
adjustment in the time-reversed DFI initializer.

For each positive inner step, the filter should:

- transform temperature variation and `specific_humidity` to nodal sigma-level
  fields;
- clip specific humidity to a fixed physical range before use, for example
  `[0, 0.08] kg kg^-1`;
- diagnose sigma-layer pressure from the current log surface pressure and sigma
  centers;
- compute saturation specific humidity with a documented Bolton-style saturation
  vapor pressure formula over liquid water, with finite guards where vapor
  pressure approaches layer pressure;
- where `q > q_sat`, remove only the supersaturated vapor amount from the tracer
  and add `L_v / c_p * (q - q_sat)` to dry temperature;
- transform the adjusted temperature variation and humidity tracer back to
  modal space;
- leave vorticity, divergence, log surface pressure, non-humidity tracers, and
  `sim_time` unchanged by the filter.

This is not a parameter sweep, not a precipitation-output feature, and not a
revival of active moist density dynamics. It is a single bounded moist
thermodynamic source/sink applied to the existing side-by-side incumbent.

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
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState`, emitted channel names,
    lead selection, target variables, metrics, and fixed gates remain
    unchanged.
- Tests to update:
  - Unit-test saturation specific humidity on finite warm, cold, low-pressure,
    and near-singular pressure cases.
  - Unit-test the adjustment filter on unsaturated, exactly saturated, and
    supersaturated columns: unsaturated columns are unchanged; supersaturated
    columns lose humidity and gain the corresponding latent heat.
  - Verify the filter clips humidity to the configured physical range before
    adjustment and never produces negative humidity.
  - Verify vorticity, divergence, log surface pressure, non-humidity tracers,
    and `sim_time` are unchanged by the filter.
  - Verify the candidate factory preserves every incumbent flag and keeps
    `use_humidity_in_dynamics=False`.
  - Add registry coverage and a non-JIT finite smoke forecast with humidity
    channels present.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 1-7 if latent heating offsets part of the
    incumbent's cold lower-tropospheric drift without changing the existing
    near-surface residual contract.
  - `geopotential_500` and `mean_sea_level_pressure` if local diabatic warming
    improves column thickness and slows the long-lead mass-field degradation.
  - Primary score should improve only if those thermal and mass-field gains are
    larger than any added moist-adjustment noise.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should move less than in the rejected bounded
    moist virtual-temperature candidate because humidity is not directly
    altering pressure gradients through virtual-temperature density feedback.
  - Lead-zero output and fixed lead selection remain identical in contract.
- Possible regressions:
  - Latent heating can still alter baroclinic evolution and indirectly regress
    winds or mass fields.
  - Removing water vapor without cloud water, precipitation fallout, radiation,
    or re-evaporation is only a minimal moist-physics closure.
  - Warm-rain saturation adjustment may under-represent ice-phase processes in
    cold upper layers.

## Risks

- Numerical stability:
  - Moderate. The adjustment is locally bounded by humidity clipping and
    saturation, but it introduces an irreversible thermodynamic source after
    every forward inner step. The fixed fast gate must be authoritative.
- Compute cost:
  - Low to moderate. The filter adds nodal transforms, pointwise thermodynamic
    formulas, and modal transforms per inner step. Resolution, output volume,
    lead count, and worker policy are unchanged.
- Data leakage:
  - Low. The filter uses only the forecast state, fixed physical constants, and
    a published saturation formula. It uses no future truth, validation
    statistics, target residuals, learned corrections, or golden artifacts.
- Physical plausibility:
  - Moderate. Saturation adjustment and latent heating are standard moist NWP
    closures, but this proposal intentionally omits cloud condensate storage,
    precipitation diagnostics, and ice microphysics to keep the dycore-side
    experiment bounded.
- Rollback complexity:
  - Low. The mechanism can be isolated behind one adapter flag, one forward-only
    filter, one side-by-side factory/export, one registry entry, and focused
    tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and
    no fixed variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - Any fast diagnostic failure, any early `10m_u_component_of_wind` guardrail
    failure, or a clean iteration primary delta below `+0.002` would show that
    minimal saturation adjustment is not a useful missing-moist-physics
    mechanism for this incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  carries pressure-level `specific_humidity` as a tracer while the incumbent
  keeps `use_humidity_in_dynamics=False`, and it builds forward steps through
  `time_integration.step_with_filters`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/scales.py` already
  provides `ISOBARIC_HEAT_CAPACITY`, `LATENT_HEAT_OF_VAPORIZATION`,
  `IDEAL_GAS_CONSTANT`, and `IDEAL_GAS_CONSTANT_H20` for a local thermodynamic
  adjustment.
- History:
  `.logbook/history/2026-06-17_18-02-45_bounded-moist-virtual-temperature-dynamics/decision.md`
  rejected clean active moist virtual-temperature dynamics with iteration delta
  `-0.055193744700895`, motivating a moist-physics mechanism that avoids direct
  humidity pressure-gradient feedback.
- History:
  `.logbook/history/2026-06-17_12-29-40_passive-humidity-dfi-bypass/decision.md`
  found passive humidity DFI bookkeeping effectively neutral, so the proposal
  must change thermodynamics rather than only preserve the tracer.
- Bolton, D. 1980. "The Computation of Equivalent Potential Temperature."
  Monthly Weather Review. The paper gives widely used empirical saturation
  vapor pressure formulas. https://doi.org/10.1175/1520-0493(1980)108%3C1046:TCOEPT%3E2.0.CO;2
- ECMWF IFS Documentation, Part IV: Physical Processes, documents saturation
  adjustment and latent-heat terms in operational moist physics.
  https://www.ecmwf.int/sites/default/files/2023-06/Part-IV-Physical-Processes.pdf
- Kochkov et al. 2024. "Neural general circulation models for weather and
  climate." Nature. The cited Dinosaur-backed NeuralGCM system is based on
  hydrostatic primitive-equation dynamics with moisture in a spectral sigma
  dycore. https://www.nature.com/articles/s41586-024-07744-y

## Researcher Notes

This is intentionally the only proposal from the post-moist-rejection search.
It is not another passive humidity preservation variant and not another active
virtual-temperature dynamics variant. The rejected candidate allowed humidity
to feed back through density and pressure-gradient dynamics without phase
changes; this proposal leaves that path off and tests only bounded
saturation-adjustment latent heating plus water-vapor removal.

It is also distinct from prior thermal and diagnostic proposals. It does not
freeze layer means, alter Held-Suarez coefficients, add output residuals, change
pressure interpolation, change vertical transport, add damping, alter wind
initialization, introduce terrain, or tune evaluation protocols. The mechanism
is researchable only because the new rejection specifically says humidity
feedback is not useful without additional moist physics; this is the narrowest
bounded additional moist-physics test I found.

## Evaluator Notes

### 2026-06-17T19:30:09Z

Decision: ready.

This is the only active proposal, and ready/staging were empty at review time,
so promoting it leaves at most one ready idea. The proposal is source-supported:
the incumbent adapter already carries `specific_humidity` as a passive tracer,
`use_humidity_in_dynamics` can remain false to avoid the rejected active moist
virtual-temperature pressure-gradient path, forward step filters are already
composed separately from digital filter initialization, and `scales.py` exposes
the thermodynamic constants needed for a bounded local latent-heating update.

The recent humidity history argues against passive or direct-dynamics humidity
replays, but does not falsify this narrower mechanism. Passive humidity DFI
bookkeeping was neutral, the passive humidity positivity limiter was neutral,
the original moist dynamics path fast-failed with nonfinite output, and the
bounded moist virtual-temperature dynamics candidate ran cleanly but regressed
iteration primary by `-0.055193744700895`, with the largest guardrail movement
in early `10m_u_component_of_wind`. This proposal deliberately keeps that
direct density/pressure-gradient coupling off and tests only local
supersaturation removal plus latent heat release.

The idea is not low risk. Applying saturation adjustment every positive inner
step is a physical parameterization, removes water vapor without cloud water,
precipitation fallout, re-evaporation, or ice-phase treatment, and can still
modify baroclinic evolution enough to damage winds or mass fields. I am not
scrapping it because the implementation can be isolated behind a side-by-side
model flag, preserves the fixed forecast contract and evaluation metrics, uses
published saturation-vapor-pressure and saturation-adjustment concepts, and has
a clearly attributable falsification path under fast and iteration gates.
