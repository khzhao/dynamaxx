---
schema_version: 1
slug: balanced-low-mode-thermal-iau
title: Apply a Balanced Low-Mode Thermal IAU Spinup
status: staging
created_at: 2026-06-19T23:12:17Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Apply a Balanced Low-Mode Thermal IAU Spinup

## Hypothesis

The accepted hydrostatic layer initialization improves the initial thermal
column by using geopotential thickness, while the accepted theta tendency and
theta mean recentering improve positive-time thermal evolution. The current
incumbent nevertheless develops large negative `2m_temperature` skill and a
negative `geopotential_500` bias with lead. A small part of this may come from
an initialization compromise: the state is hydrostatically balanced but no
longer exactly matches the broad analyzed pressure-level thermal structure.

A time-limited incremental analysis update (IAU) of only the low-mode
free-tropospheric thermal residual should insert that broad thermal information
gradually, reducing insertion shock compared with a direct initialization
override and avoiding another DFI merge or theta recentering variant.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_thermal_iau`.
Preserve the incumbent forecast contract, output variables, DFI equation, weak
Held-Suarez forcing, exact Coriolis Strang split, theta tendency, theta mean
recenter filter, semi-implicit off-centering, Richardson 10 m wind diagnostic,
and scale-separated near-surface residual correction.

For the candidate only:

- after `weather_state_to_dinosaur_state` builds the initial Dinosaur state,
  reconstruct the model's lead-zero pressure-level temperature diagnostic using
  the same sigma-to-pressure path as output packing;
- compare it with the analyzed pressure-level temperature channels in the
  initial `WeatherState`;
- keep only a smooth low-mode residual mask, for example total wavenumber
  `n <= 10` tapering to zero by `n = 16`;
- vertically project the residual back to sigma layers with the existing
  pressure-to-sigma log-pressure interpolation, then convert to a dry theta
  increment using the incumbent pressure field;
- remove each layer's area mean from the increment before applying the existing
  theta layer-mean recenter filter, so this proposal does not fight the
  accepted zero-mode theta constraint;
- add a bounded positive-time thermal tendency whose integral over the first
  12 hours equals at most a fixed fraction of the increment, for example
  `0.35`, with local clipping such as `[-1.5 K, 1.5 K]` in temperature
  equivalent;
- apply the IAU tendency only during positive-time rollout, not during DFI;
- leave vorticity, divergence, `log_surface_pressure`, tracers, output
  residuals, and evaluation protocols unchanged;
- fall back to the incumbent equation if required channels are absent or any
  increment diagnostic is nonfinite.

This tests a broad thermal spinup mechanism, not a surface-screen residual
insertion and not another implicit-gravity or DFI-routing change.

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
  - Add one side-by-side factory with the `_lowmode_thermal_iau` suffix.
- API changes:
  - None. The model still implements `DycoreModel.forecast` and emits the same
    requested channels.
- Tests to update:
  - Unit-test the low-mode thermal residual split and sigma projection on a
    synthetic pressure-level temperature stack.
  - Verify the IAU tendency integrates to the bounded fraction over the fixed
    12-hour window.
  - Verify zero tendency and incumbent fallback when temperature pressure-level
    channels are absent or nonfinite.
  - Verify DFI uses the incumbent equation while positive-time rollout uses the
    IAU-wrapped equation.
  - Add factory, registry, and finite non-JIT smoke coverage.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at days 2 to 10 if broad free-tropospheric temperature
    residuals currently project onto thickness errors.
  - `2m_temperature` at days 2 to 15 if lower-tropospheric thermal drift is
    partly column-thermal rather than only screen-level representativeness.
  - Possibly `mean_sea_level_pressure` through a more balanced column thickness.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because momentum
    and the accepted Richardson diagnostic are unchanged.
- Possible regressions:
  - Thermal IAU can perturb hydrostatic and pressure-gradient balance despite
    low-mode filtering and clipping.
  - If the hydrostatic layer initialization deliberately improved the analyzed
    thermal structure, restoring residual pressure-level temperature could
    regress Z500 or MSLP.

## Risks

- Numerical stability:
  - Moderate. The update is bounded and low-mode, but it changes the
    positive-time thermodynamic trajectory.
- Compute cost:
  - Low to moderate. It adds one initialization diagnostic and a simple
    time-window tendency during rollout.
- Data leakage:
  - Low. It uses only same-time initial pressure-level temperature channels and
    the model's own lead-zero diagnostic.
- Physical plausibility:
  - Moderate to high. IAU is designed to insert analysis increments gradually,
    and low-mode filtering avoids high-frequency thermal shocks.
- Rollback complexity:
  - Moderate. Remove one equation wrapper, one adapter flag/helper, one factory,
    one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_thermal_iau`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_thermal_iau --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail violation.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_thermal_iau --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean diagnostics.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold iteration delta, any early Z500 or MSLP guardrail
    failure, or a T2m regression would imply the residual thermal increment is
    either unhelpful or too disruptive under the fixed protocol.

## Citations

- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. "Data
  Assimilation Using Incremental Analysis Updates." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
- ECMWF IFS Documentation CY48R1, Part III, documents semi-implicit,
  semi-Lagrangian hydrostatic primitive-equation dynamics and the importance of
  balanced numerical insertion in operational models:
  https://www.ecmwf.int/sites/default/files/elibrary/2023/81369-ifs-documentation-cy48r1-part-iii-dynamics-and-numerical-procedures.pdf
- Dynamaxx history:
  `.logbook/history/2026-06-19_14-58-18_theta-consistent-implicit-gravity-operator/decision.md`
  rejected a broad theta-consistent implicit rewrite as subthreshold, motivating
  a narrower positive-time thermal increment.
- Dynamaxx history:
  `.logbook/history/2026-06-19_11-55-13_dfi-theta-mean-recenter/decision.md`
  and `.logbook/history/2026-06-19_10-17-34_centered-dfi-offcenter-rollout/decision.md`
  are negative evidence against more DFI routing for the current incumbent.
- Rasp, S. et al. 2024. "WeatherBench 2: A Benchmark for the Next Generation of
  Data-Driven Global Weather Models." Journal of Advances in Modeling Earth
  Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This is not a duplicate of staged `lower-column-thermal-iau-spinup`, which uses
the initial screen-temperature residual and projects it into the lower column.
This proposal uses pressure-level temperature residuals, removes the theta
zero-mode, keeps only broad horizontal modes, and targets free-tropospheric
thickness/Z500 behavior. It also differs from scrapped initial anchors because
it is time-limited IAU forcing, not a decaying relaxation toward the full
initial state.

## Evaluator Notes

### 2026-06-19T23:16:12Z

Decision: move to `staging`.

The proposal is plausible and distinct from active staged
`lower-column-thermal-iau-spinup`: it uses pressure-level thermal residuals and
a low-mode free-tropospheric projection instead of a screen-temperature residual
inserted into the lower column. Incremental analysis update is a reputable
mechanism for gradual insertion of analysis increments; Bloom et al. describe
IAU as incorporating increments into model integration gradually, and later IAU
work treats insertion stability as a real concern rather than a guaranteed
benefit. See Bloom et al. 1996, Monthly Weather Review,
https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2 and
Takacs et al. 2018, Monthly Weather Review,
https://doi.org/10.1175/MWR-D-18-0117.1.

Do not put it in `ready` yet. Unlike the mass proposal, this changes the
positive-time thermodynamic trajectory and can perturb hydrostatic thickness,
pressure gradients, and the already accepted theta mean-recenter behavior.
Recent history is cautionary: `theta-consistent-implicit-gravity-operator`
regressed iteration primary by `-0.10312119608544257` with MSLP and wind
guardrail failures, while DFI/theta routing variants were clean but
subthreshold or slightly negative. The mechanism is narrower than those failed
changes, so it should not be scrapped, but it needs to sit behind safer
output-only mass-field diagnostics.

Rank: 2 of 3 fresh proposals. Keep staged as a later thermal-spinup test if
the ready mass diagnostic is rejected or if additional diagnostics show broad
pressure-level thermal residuals dominate Z500 error.
