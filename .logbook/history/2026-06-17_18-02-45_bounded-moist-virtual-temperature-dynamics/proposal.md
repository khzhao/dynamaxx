---
schema_version: 1
slug: bounded-moist-virtual-temperature-dynamics
title: Enable Bounded Moist Virtual-Temperature Dynamics
status: ready
created_at: 2026-06-17T17:58:54Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Enable Bounded Moist Virtual-Temperature Dynamics

## Hypothesis

The incumbent now initializes a hydrostatically balanced dry temperature from
same-time geopotential thickness, but the rollout dynamics still keep
`use_humidity_in_dynamics=False`. Specific humidity is carried as a passive
tracer and is already used in hydrostatic geopotential diagnostics, and the
`dry-consistent-geopotential-diagnostic` rejection showed that removing humidity
from the virtual-temperature diagnostic damages short-lead Z500. That is direct
evidence that the fixed benchmark is sensitive to moisture's density effect.

The original `moist-virtual-temperature-dynamics` candidate was rejected before
the finite pressure-output repair and failed the same nonfinite output pattern
later found in the dry baseline. A renewed, bounded moist-dynamics candidate is
therefore researchable if it targets the current finite incumbent, preserves all
accepted initialization and forcing mechanisms, and prevents unphysical passive
humidity undershoots or overshoots from entering virtual-temperature and moist
thermodynamic factors during the rollout.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist`.
Preserve the incumbent DFI, near-surface residual correction, weak wind-sparing
Held-Suarez thermal relaxation, log-pressure initialization, layer-mean
hydrostatic temperature initialization, T80 truncation, 900 s inner step,
finite output extrapolation, zero orography, output variables, lead times, and
fixed evaluation protocols.

Enable the existing moist primitive-equation path with `use_humidity_in_dynamics=True`,
but add a physical humidity bound for the moisture values used by dynamics:

- clip `specific_humidity` to `[0, 1]` in the initial Dinosaur state before it
  is passed to the moist equation;
- apply the same bound to the `specific_humidity` tracer after each forward
  inner step, before the next step can use it in virtual-temperature,
  pressure-gradient, and moist thermodynamic factors;
- use the bounded humidity in `PrimitiveEquationsSigma` virtual-temperature
  adjustment and moist temperature-tendency denominators, avoiding negative
  density factors if spectral tracer transport creates undershoots;
- leave the forecast API, target variables, WeatherBench2 splits, metrics,
  deterministic gates, and forecast lead contract unchanged.

This is not a tunable moisture-physics parameterization. It is a physically
bounded activation of an existing moist hydrostatic primitive-equation pathway.

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
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState`, emitted variables,
    forecast lead handling, and fixed evaluation target variables remain
    unchanged.
- Tests to update:
  - Unit-test a humidity-bounding helper on negative, physical, and above-one
    values.
  - Unit-test that bounded moist dynamics select `PrimitiveEquationsSigma` with
    `humidity_key="specific_humidity"` while the incumbent remains dry.
  - Unit-test that the candidate factory preserves every incumbent flag and
    additionally enables bounded moist dynamics.
  - Unit-test the post-step tracer bound leaves vorticity, divergence,
    temperature variation, log surface pressure, non-humidity tracers, and
    `sim_time` unchanged.
  - Add registry coverage and a non-JIT finite smoke forecast with complete
    humidity channels if the existing fixtures support it cheaply.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 1-7 if moisture's
    virtual-temperature effect improves thickness and pressure-gradient balance
    after the accepted hydrostatic initialization.
  - `2m_temperature` may improve modestly where lower-tropospheric moist density
    corrections reduce dry thermal drift.
  - Primary score should improve only if the mass-field gains exceed the added
    moist-tracer transport noise.
- Expected neutral metrics:
  - Near-surface residual correction still controls `2m_temperature` and
    `10m_u_component_of_wind` at short leads, so early surface channels should
    not move sharply.
- Possible regressions:
  - `10m_u_component_of_wind` could regress if changed moist pressure gradients
    perturb geostrophic balance.
  - Long-lead fields could regress because humidity remains passive: there is no
    condensation, precipitation, radiation, or boundary-layer moisture source or
    sink.
  - The physical bound is not conservative for humidity mass. That is acceptable
    for this fixed dry-score target set only if the scored fields improve and
    all guardrails remain clean.

## Risks

- Numerical stability:
  - Moderate. Moist pressure-gradient and thermodynamic terms change the
    prognostic trajectory. The humidity bound is intended to avoid the most
    obvious unphysical tracer excursions, but the fixed fast gate must be
    authoritative.
- Compute cost:
  - Low to moderate. One active tracer enters dynamics and is bounded after each
    step; resolution, lead count, output size, and worker policy are unchanged.
- Data leakage:
  - Low. The candidate uses only same-time initialized humidity and physical
    bounds, with no future truth, target residuals, validation statistics, or
    learned correction.
- Physical plausibility:
  - Moderate. Virtual-temperature effects are part of moist hydrostatic
    primitive-equation dynamics, while the absence of phase changes limits
    realism. The `[0, 1]` bound enforces the physical range of specific
    humidity rather than fitting a metric.
- Rollback complexity:
  - Low. The model can be isolated behind one adapter option, one side-by-side
    factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, no fixed early day-1-through-day-5 RMSE guardrail
    failure, and no fixed variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - Any fast diagnostic failure, any early `10m_u_component_of_wind`,
    `geopotential_500`, or `mean_sea_level_pressure` guardrail failure, or a
    clean iteration primary delta below `+0.002` would show that bounded moist
    virtual-temperature dynamics are not a useful next mechanism for this
    incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  carries complete `specific_humidity` pressure-level stacks as tracers while
  the incumbent keeps `use_humidity_in_dynamics=False`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements `PrimitiveEquationsSigma` with humidity-dependent virtual
  temperature and moist pressure-gradient terms.
- History: `.logbook/history/2026-06-16_07-36-31_moist-virtual-temperature-dynamics/decision.md`
  rejected the original moist candidate at the fast gate before the finite
  pressure-output repair.
- History: `.logbook/history/2026-06-16_07-55-11_finite-pressure-level-extrapolation/decision.md`
  accepted the finite output repair and noted that the dry baseline shared the
  lower-pressure diagnostic failure pattern.
- History: `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
  showed that removing humidity from geopotential reconstruction caused a
  `+19.566144167188776%` 24 h Z500 guardrail regression.
- Dinosaur README: Dinosaur supports dry and moist primitive equations on sigma
  coordinates. https://github.com/neuralgcm/dinosaur
- Kochkov et al. 2024, "Neural general circulation models for weather and
  climate", Nature, describes the Dinosaur-backed NeuralGCM dycore as solving
  hydrostatic primitive equations with moisture using a horizontal
  pseudo-spectral discretization and vertical sigma coordinates.
  https://www.nature.com/articles/s41586-024-07744-y
- ECMWF IFS Documentation Part III defines virtual temperature as
  `T [1 + ((Rvap/Rdry) - 1) q]` in the hydrostatic primitive-equation dynamics.
  https://www.ecmwf.int/sites/default/files/elibrary/2020/81188-ifs-documentation-cy47r1-part-iii-dynamics-and-numerical-procedures_1.pdf
- Lin, S.-J. and Rood, R. B. 1996. "Multidimensional Flux-Form Semi-Lagrangian
  Transport Schemes." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Skamarock, W. C. 2006. "Positive-Definite and Monotonic Limiters for
  Unrestricted-Time-Step Transport Schemes." Monthly Weather Review.
  https://doi.org/10.1175/MWR3170.1

## Researcher Notes

This is a revival of a physical mechanism, but it is not a duplicate variant of
the rejected early `moist-virtual-temperature-dynamics` candidate. The previous
candidate targeted canonical `dinosaur` before the finite pressure-output
repair and failed a nonfinite pattern later shown to affect the dry baseline.
This proposal targets the current accepted finite incumbent, preserves all
accepted initialization and weak-forcing improvements, and adds a physical
humidity bound before moisture is allowed to affect virtual temperature and
pressure-gradient dynamics.

This is also materially different from rejected humidity-only proposals.
`passive-humidity-positivity-limiter` was diagnostic-time only and had no
prognostic moisture feedback. `passive-humidity-dfi-bypass` preserved a passive
diagnostic tracer through DFI and was effectively neutral. This proposal uses
humidity dynamically, which creates a larger but scientifically distinct test of
whether moisture's density effect is a remaining mass-field error source after
the accepted hydrostatic initialization.

Negative evidence still matters. Broad wind projection, damping, vertical
transport, pressure-grid, terrain/orography, and output-remap changes have
repeatedly failed or produced guardrail issues, so this candidate should be
rejected quickly if fast diagnostics fail or if iteration shows wind or
mass-field guardrail damage. I found no second non-duplicate model proposal with
a better cost-risk tradeoff in this renewed audit.

## Evaluator Notes

2026-06-17T18:01:22Z - Move to `ready`; sole ready proposal after full proposal
triage.

Approve this as a legitimate renewed candidate, not a duplicate fast-failed
revival. The original `moist-virtual-temperature-dynamics` run targeted the
early canonical `dinosaur` baseline and failed the fast gate with nonfinite
full-forecast output before the accepted finite pressure-level extrapolation
repair. That failure is no longer decisive against the mechanism because the
dry incumbent shared the same diagnostic class and the current incumbent is now
finite under the fixed gates. This proposal also adds a material stability
constraint that the original candidate lacked: bound `specific_humidity` before
moist dynamics can use it in virtual-temperature, pressure-gradient, and moist
temperature-tendency factors.

Source inspection supports feasibility. The adapter already carries complete
pressure-level `specific_humidity` stacks as tracers when available, gates the
primitive equation with `use_humidity_in_dynamics`, and can register a
side-by-side model without changing the forecast API. `PrimitiveEquationsSigma`
uses `humidity_key` in virtual-temperature adjustment, humidity pressure-gradient
corrections, and moist adiabatic temperature tendencies, so the candidate tests
a real active-dynamics pathway rather than another passive diagnostic tweak.

The prior humidity history is mixed but not disqualifying. The passive humidity
positivity limiter and passive humidity DFI bypass were clean and essentially
neutral, which argues against further passive humidity bookkeeping. Conversely,
`dry-consistent-geopotential-diagnostic` showed that removing humidity from
virtual-temperature geopotential reconstruction caused a `+19.566144167188776%`
24 h `geopotential_500` RMSE guardrail regression, so the benchmark is sensitive
to moisture's density effect. This proposal is the remaining bounded way to test
whether that density effect belongs in the rollout after the accepted
hydrostatic initialization sequence.

Risk remains moderate because this changes prognostic mass, wind, and
temperature evolution with passive moisture and no phase changes. The ready
status is therefore conditional on strict implementation scope: preserve the
incumbent configuration, add one side-by-side registered model, keep fixed
evaluation protocols and forecast outputs unchanged, and apply humidity bounds
only as physical state constraints. Any fast diagnostic issue, wind/mass-field
guardrail damage, or clean iteration delta below the fixed promotion threshold
should be treated as falsification rather than a prompt for protocol changes or
additional tuning.
