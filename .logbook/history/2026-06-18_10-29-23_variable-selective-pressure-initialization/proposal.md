---
schema_version: 1
slug: variable-selective-pressure-initialization
title: Use Variable-Selective Pressure Interpolation at Initialization
status: ready
created_at: 2026-06-18T10:17:15Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use Variable-Selective Pressure Interpolation at Initialization

## Hypothesis

The accepted log-pressure initialization remaps all pressure-level variables
through the same log-pressure interpolation path. That was a strong improvement
over the original all-linear remap, but recent follow-ups show that additional
thermodynamic initialization refinements are now fragile: potential-temperature
log-p initialization, bounded log-p extrapolation, and sigma-native hydrostatic
initialization all regressed or failed the promotion gate.

Operational interpolation systems often use variable-dependent vertical
coordinates and algorithms. In ECMWF IFS observation and post-processing
documentation, wind and geopotential interpolation are treated differently from
temperature, humidity, and pressure vertical velocity. A narrower candidate can
preserve the accepted hydrostatic layer-mean temperature construction while
testing whether the single all-field log-p interpolation is leaving wind,
humidity, or thermal projection errors in the sigma initial state.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init`.
Preserve the incumbent DFI, weak-HS forcing, near-surface residuals,
hydrostatic layer-mean temperature construction, horizontal diffusion, inner
step, outputs, and symmetric exact-Coriolis split.

Add an initialization mode that applies pressure-to-sigma interpolation by
variable family:

- compute the accepted hydrostatic layer-mean pressure-level temperature first,
  exactly as the incumbent does;
- interpolate horizontal winds with the accepted log-pressure coordinate, so
  the candidate keeps the main wind-coordinate improvement from the accepted
  log-p initialization;
- interpolate temperature and specific humidity with pressure-linear
  interpolation and nearest finite extrapolation;
- leave surface pressure, latitude ordering, modal transforms, humidity tracer
  storage, DFI, weak-HS forcing, and forecast outputs unchanged;
- fall back to the incumbent all-log-p interpolation when required variable
  stacks are missing or a grouped interpolation produces nonfinite values;
- do not change pressure-level output interpolation, geopotential diagnostics,
  sigma grid placement, or target variables.

The first candidate should be intentionally simple: one variable grouping, one
side-by-side registry entry, and no learned or validation-tuned coefficients.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py` only if a
    reusable grouped interpolation helper is cleaner than adapter-local calls
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, emitted variables, shapes, lead times, and fixed
    protocols remain unchanged.
- Tests to update:
  - Unit-test grouped interpolation on synthetic columns where log-p and
    pressure-linear paths differ, verifying winds use log-p while temperature
    and humidity use pressure-linear interpolation.
  - Verify the hydrostatic layer-mean temperature helper runs before grouped
    interpolation and is not replaced by sigma-native hydrostatic logic.
  - Verify the candidate factory preserves all Strang incumbent flags except
    the interpolation selector.
  - Verify fallback behavior for absent humidity or nonfinite grouped outputs.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at early and medium leads if retaining log-p wind
    interpolation while reducing scalar projection error improves the balanced
    initial sigma state.
  - `geopotential_500` and `mean_sea_level_pressure` if pressure-linear scalar
    interpolation better preserves the accepted hydrostatic temperature and
    humidity structure after remapping.
- Expected neutral metrics:
  - Lead-zero supported outputs should remain finite and close to incumbent
    because this changes only interpolation coordinates, not channel meanings.
  - `2m_temperature` should retain the accepted near-surface residual behavior.
- Possible regressions:
  - The accepted all-log-p remap may already be empirically optimal for this
    coarse vertical grid and flat-sigma adapter.
  - Reverting scalar interpolation from log-p to pressure-linear may undo part
    of the accepted log-pressure initialization gain.
  - Humidity interpolation changes can perturb geopotential diagnostics even
    though humidity remains passive in dynamics.

## Risks

- Numerical stability:
  - Low to moderate. The change is initialization-only, but it changes the sigma
    thermal and humidity columns entering DFI and rollout.
- Compute cost:
  - Low. It adds a few separate interpolation calls at initialization and does
    not alter resolution, inner step, lead count, or `--workers 4` scoring.
- Data leakage:
  - None. It uses only same-time pressure-level analysis fields already present
    in `ForecastInput.initial_state`.
- Physical plausibility:
  - Moderate. Variable-specific vertical interpolation is standard in
    operational systems, but the best grouping for this simplified Dinosaur
    sigma adapter must be measured rather than assumed.
- Rollback complexity:
  - Low. Remove one interpolation selector, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    diagnostics clean, no early day 1-5 RMSE guardrail failure, and no
    variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that all-field
    log-pressure initialization remains preferable. Early `10m_u_component_of_wind`
    or Z500 guardrail failure would show the variable grouping disrupts the
    accepted initialized balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  selects one pressure-to-sigma interpolation function for temperature, winds,
  humidity, and all initialized pressure-level fields when
  `use_log_pressure_initialization` is enabled.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py`
  already implements both pressure-linear and log-pressure pressure-to-sigma
  interpolation functions.
- History: `.logbook/history/2026-06-17_00-55-17_log-pressure-sigma-initialization/decision.md`
  accepted all-field log-pressure initialization, so this proposal keeps the
  successful mechanism as the baseline being refined.
- History: `.logbook/history/2026-06-17_10-15-26_potential-temperature-logp-initialization/decision.md`
  and `.logbook/history/2026-06-18_07-30-18_sigma-native-hydrostatic-initialization/decision.md`
  are negative evidence against another broad thermodynamic initialization
  remap; this proposal changes only the interpolation coordinate grouping.
- ECMWF IFS Documentation CY49R1, Part I: Observations, describes variable
  dependent vertical interpolation, including pressure-linear interpolation for
  temperature and specific humidity and log-pressure interpolation for wind.
  https://www.ecmwf.int/sites/default/files/elibrary/112024/81623-ifs-documentation-cy49r1-part-i-observations.pdf
- ECMWF IFS Documentation CY23R4, Part VI: Technical and Computational
  Procedures, documents variable-specific FULL-POS interpolation choices for
  wind, temperature, geopotential, humidity, and pressure-coordinate vertical
  velocity.
  https://www.ecmwf.int/sites/default/files/elibrary/2003/77032-ifs-documentation-cy23r4-part-vi-technical-and-computational-procedures_1.pdf
- Rasp, S. et al. 2024. WeatherBench 2: A benchmark for the next generation of
  data-driven global weather models. Journal of Advances in Modeling Earth
  Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This is not a duplicate of accepted `log-pressure-sigma-initialization`; it is a
side-by-side refinement of that accepted mechanism for the newer Strang
incumbent. It is also not a duplicate of rejected
`log-pressure-output-interpolation`, because it changes only the initial
pressure-to-sigma remap and does not alter pressure-level forecast outputs.

The recent `sigma-native-hydrostatic-initialization` rejection is direct
negative evidence against further hydrostatic temperature remapping. This
proposal therefore preserves the accepted hydrostatic layer-mean temperature
construction and tests only whether all variables should share one vertical
interpolation coordinate during initialization.

## Evaluator Notes

### 2026-06-18T10:25:42Z

Decision: move to `ready`, rank 1.

This is the best next implementation target from the current queue. It has a
small implementation surface because the adapter already has pressure-linear
and log-pressure interpolation helpers, and the proposal preserves the accepted
Strang Coriolis split, DFI, weak-HS forcing, near-surface residuals,
hydrostatic layer-mean temperature construction, output contract, target
variables, and fixed protocols. ECMWF IFS documentation supports the premise
that vertical interpolation can be variable dependent: temperature and specific
humidity are handled linearly in pressure while wind uses log-pressure
interpolation.

The risk is real but bounded. The accepted all-field log-pressure initialization
was a large gain, and recent thermodynamic initialization refinements are
negative evidence: potential-temperature log-p initialization regressed
slightly and sigma-native hydrostatic initialization regressed by
`-0.008345744027537627`. This proposal is still worth a ready slot because it
keeps the accepted wind and hydrostatic mechanisms, tests one operationally
motivated grouping, has no leakage risk, and would give a clear lesson if the
incumbent all-log-p remap remains empirically better.
