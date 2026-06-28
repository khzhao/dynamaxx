---
schema_version: 1
slug: horizontal-semilagrangian-passive-humidity
title: Apply Horizontal Semi-Lagrangian Transport to Passive Humidity
status: staging
created_at: 2026-06-22T14:33:04Z
author_role: Researcher
target_model: dino_hsl_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Apply Horizontal Semi-Lagrangian Transport to Passive Humidity

## Hypothesis

The incumbent keeps `specific_humidity` dynamically passive, but the adapter
still uses the humidity tracer when reconstructing virtual-temperature
geopotential for pressure-level outputs. Prior humidity-only experiments show
that clipping, DFI bypassing, or activating moist dynamics is not useful, yet
the rejected dry-geopotential path showed that removing passive humidity from
Z500 diagnostics is harmful. The accepted `dino_hsl_theta` result is strong
local evidence that horizontal semi-Lagrangian scalar transport can remove a
large remaining transport error in this dycore.

Applying the same bounded horizontal semi-Lagrangian transport idea only to the
passive humidity tracer may reduce moisture phase and overshoot error in the
diagnostic virtual-temperature column, improving `geopotential_500` and
possibly `mean_sea_level_pressure` while preserving the accepted dry dynamics,
theta transport, lower-boundary behavior, and forecast contract.

## Mechanism

Add one side-by-side candidate with short alias `dino_hsl_q`.

For the candidate only:

- keep `use_humidity_in_dynamics=False`, so humidity still does not enter
  pressure-gradient, vorticity, divergence, or thermodynamic tendencies;
- keep the accepted horizontal semi-Lagrangian theta anomaly path exactly as in
  `dino_hsl_theta`;
- route only the `specific_humidity` tracer's horizontal scalar tendency through
  a bounded backward-departure remap using the existing horizontal wind and
  departure cap;
- leave passive humidity vertical transport, all non-humidity tracers, theta
  tendency, log-surface-pressure continuity, momentum tendencies, DFI, weak-HS
  forcing, ocean bulk sensible heat flux, residual diagnostics, and output
  variable names unchanged;
- clip recovered humidity only to broad finite physical bounds already suitable
  for diagnostics, not as a tuned mass fixer;
- fall back to the incumbent passive-humidity horizontal advection whenever the
  humidity tracer is absent, the remap is nonfinite, or a diagnostic bound fails.

This is a passive-tracer transport experiment. It is not moist dynamics,
log-humidity representation, vertical upwind humidity transport, humidity
diffusion bypass, or a new geopotential output correction.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model registered as `dino_hsl_q`.
- API changes:
  - None. The candidate accepts and emits the same `WeatherState` variables as
    the incumbent.
- Tests to update:
  - Verify absent humidity reproduces `dino_hsl_theta`.
  - Verify the selector changes only the `specific_humidity` tracer horizontal
    tendency; vorticity, divergence, temperature, log surface pressure, and
    non-humidity tracer tendencies remain incumbent-equivalent.
  - Verify `use_humidity_in_dynamics=False` is preserved.
  - Verify remap nonfinite diagnostics fall back to incumbent passive humidity
    transport.
  - Verify recovered humidity used in pressure-level output diagnostics is
    positive, finite, and shape-compatible.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium and late leads if passive moisture phase error
    is contaminating virtual-temperature thickness in the output diagnostic.
  - `mean_sea_level_pressure` may improve slightly through a more coherent
    pressure-level hydrostatic column, although prognostic surface pressure is
    unchanged.
- Expected neutral metrics:
  - `2m_temperature` should remain near `dino_hsl_theta` because thermal
    dynamics, residual memory, and lower-boundary fluxes are unchanged.
  - `10m_u_component_of_wind` should remain near incumbent because momentum and
    the Richardson 10 m wind diagnostic are unchanged.
- Possible regressions:
  - The passive humidity target is indirect; the fixed metric has no humidity
    variable, so score movement may be near zero.
  - Semi-Lagrangian remapping can diffuse or shift sharp humidity gradients,
    worsening Z500 where the incumbent spectral passive tracer is compensating
    other diagnostic errors.

## Risks

- Numerical stability:
  - Low to moderate. Humidity remains passive and fallback guarded, but the
    tracer feeds diagnostic geopotential.
- Compute cost:
  - Low to moderate. It adds one bounded horizontal remap for the humidity tracer
    per inner step when humidity is present.
- Data leakage:
  - None. It uses only current forecast state, initialized humidity, and fixed
    grid geometry.
- Physical plausibility:
  - Moderate to high. Semi-Lagrangian transport of water vapor in spectral
    atmospheric models is an established approach, and keeping humidity passive
    respects prior negative moist-dynamics evidence.
- Rollback complexity:
  - Low. Remove one tracer-specific selector/helper path, one factory/export,
    one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_q`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_q --workers 4`.
  - Support requires clean diagnostics, fixed RMSE guardrails passing, and
    iteration primary delta at least `+0.002` against cached `dino_hsl_theta`
    incumbent metrics.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_q --workers 4` only
    after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with clean
    diagnostics and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show passive-humidity
    horizontal transport is not a material remaining score source. A short-lead
    Z500 guardrail regression would show the incumbent passive humidity
    transport is safer for diagnostic geopotential.

## Citations

- Local evidence:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` stores optional
    `specific_humidity` in `state.tracers` and uses recovered humidity in
    `dinosaur_state_to_weather_state` for virtual-temperature geopotential.
  - `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
    rejected removing passive humidity from geopotential diagnostics after a
    damaging Z500 result.
  - `.logbook/history/2026-06-16_21-13-22_passive-humidity-positivity-limiter/decision.md`
    and `.logbook/history/2026-06-17_12-29-40_passive-humidity-dfi-bypass/decision.md`
    show humidity bookkeeping changes were clean but score-irrelevant or
    slightly negative, motivating a transport-specific mechanism rather than
    another clip or DFI route.
  - `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
    accepted horizontal semi-Lagrangian scalar transport for theta with large
    iteration and validation gains.
- Literature:
  - Williamson, D. L. and Rasch, P. J. 1994. Water vapor transport in the NCAR
    CCM2. Tellus A. https://doi.org/10.3402/tellusa.v46i1.15426
  - Rasch, P. J. and Williamson, D. L. 1990. On shape-preserving interpolation
    and semi-Lagrangian transport. SIAM Journal on Scientific and Statistical
    Computing. https://doi.org/10.1137/0911039
  - Lin, S.-J. and Rood, R. B. 1996. Multidimensional flux-form
    semi-Lagrangian transport schemes. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of active staged `log-humidity-passive-tracer`, which
changes the transported humidity variable, nor `passive-humidity-upwind-
vertical-transport`, which changes only vertical tracer transport. It is also
not scrapped `passive-humidity-diffusion-bypass`, `passive-humidity-global-
mass-fixer`, `bounded-virtual-humidity-geopotential`, or any moist-dynamics
proposal: humidity remains passive and only its horizontal transport stencil
changes.

The proposal deliberately avoids the recent rejected lower-boundary family
(`sst-sea-ice-ocean-flux-anchor` and `snow-soil-land-thermal-reservoir`) and
does not change the fixed evaluation protocol, target variables, lead schedule,
or golden usage. It can be implemented and scored independently of the midpoint
theta-departure proposal.

## Evaluator Notes

### 2026-06-22T14:36:17Z

Decision: move to `staging`; rank 2 of 2 new proposals; do not recommend for
the next implementation while the midpoint theta-departure proposal is ready.

The mechanism is plausible and distinct from the staged humidity ideas:
`log-humidity-passive-tracer` changes representation, and
`passive-humidity-upwind-vertical-transport` changes only the vertical stencil,
while this proposal changes horizontal passive-tracer transport. The literature
check supports semi-Lagrangian moisture/tracer transport and shape-preserving
interpolation as established numerical tools, and local history confirms that
passive humidity should remain in virtual-temperature geopotential diagnostics.

Keep it staged because the expected fixed-score leverage is indirect. Humidity
is not a target variable, humidity remains dynamically passive, and prior
humidity-only experiments were either near-neutral or harmful:
`passive-humidity-positivity-limiter` and `passive-humidity-dfi-bypass` were
clean but slightly negative, while removing passive humidity from geopotential
caused a day-1 Z500 guardrail failure. This proposal may still be worth testing
later because horizontal transport is a stronger mechanism than clipping or DFI
bookkeeping, but it is less likely than midpoint theta departure to beat the
current `dino_hsl_theta` incumbent in the next fixed iteration gate.

### 2026-06-22T21:57:42Z

Decision: remain in `staging`; not promoted for the next cycle.

The new incumbent is now `dino_hsl2_theta`, so this proposal would need to be
rebased conceptually on the midpoint theta path before implementation. It
remains distinct from log-humidity and vertical-humidity proposals and still
has a plausible diagnostic-geopotential mechanism, but the fixed score has no
humidity target and recent humidity-only histories were weak or negative. Given
the small `+0.0072` margin of the accepted midpoint follow-up, the next cycle
should favor a direct theta-trajectory experiment over an indirect passive
humidity diagnostic effect.
