---
schema_version: 1
slug: lower-column-thermal-iau-spinup
title: Apply a Bounded Lower-Column Thermal IAU From the Initial Screen Residual
status: staging
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

# Apply a Bounded Lower-Column Thermal IAU From the Initial Screen Residual

## Hypothesis

The current incumbent still has strongly negative `2m_temperature` skill versus
persistence after the accepted residual begins to decay. The accepted residual
correction fixes the emitted near-surface diagnostic at lead zero, but it does
not change the lower-tropospheric thermal trajectory. A bounded incremental
analysis update (IAU) that inserts only the initial screen-temperature residual
into the lowest sigma layers during the first forecast day may reduce
post-residual near-surface cold drift while preserving the accepted theta
tendency, weak-HS forcing, and Richardson 10 m wind diagnostic.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_t2m_iau`.
Preserve incumbent initialization, DFI, weak Held-Suarez forcing, theta-form
thermodynamic tendency, log-pressure and hydrostatic layer initialization,
symmetric exact-Coriolis split, stability-aware residual correction,
Richardson 10 m wind diagnostic, horizontal diffusion, output variables, and
fixed evaluation protocols.

For the candidate only:

- after building the initial Dinosaur state, diagnose the raw lowest-sigma
  screen-temperature proxy that would feed `2m_temperature`;
- compare it with the same-time analyzed `2m_temperature` from the initial
  `WeatherState`;
- clip the local residual to one fixed bound, for example `[-3 K, 3 K]`;
- project the bounded increment onto a smooth lower-column sigma taper, such as
  zero above `sigma = 0.75` and largest at the lowest layer;
- during positive-time rollout only, add a decaying thermal tendency whose time
  integral over the first 24 hours equals the tapered increment under a fixed
  IAU window;
- add the tendency to `temperature_variation` or the theta-tendency equivalent
  in a formulation consistent with the incumbent theta path;
- leave vorticity, divergence, `log_surface_pressure`, tracers, Coriolis,
  horizontal diffusion, weak-HS forcing, output packing, and near-surface
  residual correction unchanged;
- keep DFI on the incumbent equation so the update is a positive-time spinup
  tendency rather than another DFI merge change;
- fall back to the incumbent rollout if the increment or tendency is nonfinite.

This is not a post-processing 2 m temperature diagnostic and not a persistence
blend. It tests whether the accepted lead-zero screen residual should be
inserted gradually into the lower-column thermodynamic state instead of being
used only as an output residual.

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
  - Unit-test residual clipping, vertical taper construction, finite fallback,
    and zero tendency when `2m_temperature` is absent.
  - Verify the integrated IAU tendency over the fixed window equals the bounded
    tapered increment for a simple synthetic state.
  - Verify direct tendency leaves vorticity, divergence, `log_surface_pressure`,
    tracers, Coriolis options, and output diagnostics unchanged.
  - Verify DFI stays on the incumbent equation while positive-time rollout uses
    the IAU wrapper.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` from days 2 to 15 if the raw lower-column thermal state is
    too cold after the accepted output residual decays.
  - `mean_sea_level_pressure` and `geopotential_500` may improve if lower-column
    temperature thickness becomes more consistent with the analyzed screen
    temperature.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because the
    accepted Richardson wind diagnostic, wind state, Coriolis split, and
    residual correction remain unchanged.
- Possible regressions:
  - Even a bounded lower-column thermal increment can perturb hydrostatic
    balance and pressure gradients, causing MSLP, Z500, or wind regressions.
  - If the lead-zero 2 m residual mostly reflects unresolved land/surface
    physics rather than lower-air temperature, inserting it into the dycore
    state can hurt dynamics.

## Risks

- Numerical stability:
  - Moderate. The update is bounded and time-limited but changes the positive-
    time thermodynamic trajectory.
- Compute cost:
  - Low. It adds one initial residual computation and a local tendency during
    the first forecast day; no resolution, lead, or worker count changes.
- Data leakage:
  - Low. The update uses only same-time initial analysis fields already present
    in `ForecastInput.initial_state`, not future targets, validation scores, or
    golden data.
- Physical plausibility:
  - Moderate. IAU is a standard way to insert analysis increments gradually, but
    using screen temperature as a lower-column thermal increment is an
    approximate boundary-layer spinup device.
- Rollback complexity:
  - Low to moderate. Remove one per-initial-state increment path, one equation
    wrapper or step wrapper, one factory/export, one registry entry, and focused
    tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_t2m_iau`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_t2m_iau --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_t2m_iau --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the current
    2 m temperature error is better handled as an output diagnostic than as a
    lower-column state increment. Any early MSLP, Z500, or wind guardrail
    failure would show the thermal insertion disrupts balance.

## Citations

- Citation or source:
  - Dynamaxx history:
    `.logbook/history/2026-06-18_15-57-11_stability-aware-surface-residual-decay/decision.md`
    accepted stability-aware near-surface residual decay, showing that initial
    screen-level residuals carry useful forecast information.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md`
    accepted theta-form thermodynamic tendency but retained small pressure and
    near-surface thermal sensitivity.
  - Dynamaxx history:
    `.logbook/history/2026-06-17_19-31-12_bounded-saturation-adjustment/decision.md`
    rejected irreversible moist heating after it improved 2 m temperature but
    degraded mass and wind fields; this proposal is dry, bounded, and
    time-limited.
  - Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
    Assimilation Using Incremental Analysis Updates. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
  - Polavarapu, S., Ren, S., Clayton, A. M., Sankey, D., and Rochon, Y. 2004.
    On the Relationship between Incremental Analysis Updating and Incremental
    Digital Filtering. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(2004)132%3C2495:OTRBIA%3E2.0.CO;2
  - ECMWF Newsletter 178 describes 2 m temperature as a diagnostic surface-layer
    product derived from lowest model level and surface information with
    stability safeguards.
    https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade

## Researcher Notes

Record prior-history comparisons and why this is not a duplicate.

This is not a duplicate of active staged `bulk-richardson-2m-temperature-
diagnostic`, which changes only raw output packing for 2 m temperature. This
proposal feeds a clipped initial screen-temperature residual into the
positive-time thermodynamic state, so it can affect later temperature,
pressure, and geopotential evolution after the accepted output residual decays.

It is also not a repeat of `bounded-saturation-adjustment` or
`bounded-moist-virtual-temperature-dynamics`: no moisture feedback, latent heat,
or humidity-dependent density is introduced. The new mechanism is a dry,
time-limited IAU-style lower-column increment, and it should be rejected if the
mass-field guardrails show that even this bounded insertion is too intrusive.

## Evaluator Notes

### 2026-06-19T00:01:16Z

Decision: `staging`.

The mechanism is scientifically plausible in the broad IAU sense and preserves
the external forecast contract, but it is not the best immediate target. It
uses a same-time initial `2m_temperature` residual, which is allowed by the
loop rules only with strong justification, and then inserts that screen-level
residual into the prognostic lower-column thermal state. That is substantially
more intrusive than the accepted near-surface residual output correction.

The main risk is physical attribution: the lead-zero screen residual may
reflect land, surface-layer, representativeness, or diagnostic-height error
rather than a true lower-tropospheric thermal increment. Prior
`bounded-saturation-adjustment` showed that a bounded thermal improvement can
still degrade MSLP, Z500, and 10 m wind guardrails. This proposal is dry and
time-limited, so it is not a duplicate, but it needs either a safer staged
diagnostic result or more evidence that the residual belongs in the dycore
state before consuming the next implementation slot.

Rank: 3 of 3. Keep staged, behind the theta zero-mode recentering candidate and
behind less intrusive diagnostic candidates.
