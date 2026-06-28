---
schema_version: 1
slug: low-mode-mass-divergence-iau
title: Insert Low-Mode Mass Residuals Through a Bounded Divergence IAU
status: scrap
created_at: 2026-06-20T00:57:57Z
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

# Insert Low-Mode Mass Residuals Through a Bounded Divergence IAU

## Hypothesis

The most recent low-mode mass residual candidate was clean but subthreshold
because it corrected only saved `mean_sea_level_pressure` and `geopotential_500`
outputs after the trajectory had already evolved. That negative result says
stationary output-only mass residual memory is too weak, not that broad
mass-field imbalance is irrelevant. The incumbent still has negative mean
iteration skill for MSLP and near-neutral mean Z500 skill, with growing
long-lead MSLP bias.

A bounded low-mode divergence incremental analysis update (IAU) can insert the
same broad mass information into the early trajectory through the continuity
equation. If the residual represents a real balanced mass phase error, changing
early divergent adjustment should affect later pressure and thickness fields
more strongly than output carryover while preserving fixed protocols.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_mass_div_iau`.
Preserve the incumbent DFI, weak-HS forcing, log-pressure and hydrostatic layer
initialization, Strang Coriolis split, theta tendency, theta mean recentering,
SIL3 off-centering, Richardson 10 m wind diagnostic, and scale-separated
surface residual correction.

For the candidate only:

- after building the initial Dinosaur state, reconstruct the model's lead-zero
  mass diagnostics for `mean_sea_level_pressure` and `geopotential_500`;
- compute analyzed-minus-model lead-zero residuals only for those channels when
  both are available, then keep only a smooth low-mode mask such as total
  wavenumber `n <= 6` tapering to zero by `n = 12`;
- convert the MSLP residual into a bounded log-surface-pressure increment proxy
  and the Z500 residual into a compatible broad thickness increment proxy;
- solve a small spectral Poisson problem for a divergent wind potential whose
  sigma-integrated divergence would reduce the low-mode log-pressure increment
  over a 12-hour IAU window;
- add a positive-time-only tendency to `divergence` during the IAU window, with
  zero global-mean mass increment, a fixed amplitude cap, and no direct
  vorticity, temperature, tracer, or output edits;
- optionally taper the vertical structure toward lower and middle sigma layers
  using fixed sigma weights so the update is not barotropic-only;
- keep DFI on the incumbent equation and apply the IAU only after DFI, avoiding
  the rejected DFI-routing family;
- fall back to the incumbent if the residual projection, Poisson solve, or
  IAU-integrated tendency is nonfinite.

This is deliberately not another output-only low-mode mass residual. It uses
lead-zero mass diagnostics to produce an early, bounded divergence tendency that
can alter subsequent dynamics.

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
  - Add one side-by-side factory with the `_mass_div_iau` suffix.
- API changes:
  - None. Forecast inputs, requested outputs, target variables, lead times, and
    protocols remain unchanged.
- Tests to update:
  - Unit-test low-mode residual masking and zero-global-mean projection.
  - Unit-test the spectral Poisson solve on synthetic log-pressure increments.
  - Verify the IAU tendency integrates to the bounded target over the fixed
    window and is exactly zero after the window.
  - Verify vorticity, temperature, tracers, output residual helpers, and DFI
    equation construction remain incumbent-equivalent.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 2 to 15 if broad mass adjustment is a
    remaining trajectory error rather than only an output diagnostic offset.
  - `geopotential_500` at medium leads if early divergent mass adjustment
    improves balanced thickness evolution.
- Expected neutral metrics:
  - `2m_temperature` should retain the accepted scale-separated residual gains.
  - `10m_u_component_of_wind` should remain close to incumbent if the divergence
    increment is low-mode, time-limited, and vorticity-free.
- Possible regressions:
  - A divergent IAU can excite gravity waves or disturb the accepted
    off-centered balance, especially in early MSLP/Z500.
  - If the low-mode residual is mostly a diagnostic terrain/MSLP mismatch, a
    prognostic divergence update can move the trajectory the wrong way.

## Risks

- Numerical stability:
  - Moderate. This changes a prognostic mass-coupled tendency during the first
    12 hours, so fast and early guardrails are critical.
- Compute cost:
  - Low to moderate. Adds one initialization residual diagnostic and a local
    tendency wrapper during the IAU window.
- Data leakage:
  - Low. Uses only same-time initial analysis channels and model lead-zero
    diagnostics, not future targets or validation statistics.
- Physical plausibility:
  - Moderate. IAU is a standard gradual-increment method, and divergent
    adjustment is the dynamical route to surface-pressure change, but deriving
    it from MSLP/Z500 residuals is approximate.
- Rollback complexity:
  - Moderate. Remove one residual projection helper, one equation wrapper, one
    factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_mass_div_iau`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_mass_div_iau --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_mass_div_iau --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean diagnostics
    and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold delta would show that low-mode mass residuals remain
    too weak even when inserted dynamically. Any early mass or wind guardrail
    failure would show the divergence IAU disrupts the accepted balance.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-19_23-29-46_low-mode-mass-diagnostic-residual-memory/decision.md`
  rejected stationary output-only low-mode mass residual memory as clean but
  subthreshold with iteration delta `+0.0007877795793892473`.
- Dynamaxx history:
  `.logbook/history/2026-06-17_22-19-32_continuity-balanced-divergence-init/decision.md`
  is negative evidence against one-time initial divergence correction; this
  proposal differs by using a time-limited positive-time IAU and low-mode mass
  residuals from the current incumbent diagnostics.
- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. "Data
  Assimilation Using Incremental Analysis Updates." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
- Polavarapu, S., Ren, S., Clayton, A. M., Sankey, D., and Rochon, Y. 2004.
  "On the Relationship between Incremental Analysis Updating and Incremental
  Digital Filtering." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2004)132%3C2495:OTRBIA%3E2.0.CO;2
- Lynch, P. and Huang, X.-Y. 1992. "Initialization of the HIRLAM Model Using a
  Digital Filter." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Rasp, S. et al. 2024. "WeatherBench 2: A Benchmark for the Next Generation of
  Data-Driven Global Weather Models." Journal of Advances in Modeling Earth
  Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This is materially different from the rejected
`low-mode-mass-diagnostic-residual-memory`: it does not carry MSLP/Z500 outputs
forward after the forecast. It creates a bounded early divergence tendency, so
any benefit must come from improved trajectory evolution. It is also distinct
from staged `balanced-low-mode-thermal-iau`, which inserts pressure-level
thermal residuals into `temperature_variation`; this proposal directly tests
mass-continuity adjustment through `divergence` and keeps temperature tendency
unchanged.

## Evaluator Notes

### 2026-06-20T01:00:53Z

Decision: move to `scrap`; dominated by prior mass/divergence evidence and too
invasive relative to expected gain.

IAU itself is a reputable mechanism. Bloom et al. 1996 describe incremental
analysis updating as gradually incorporating analysis increments into model
integration: https://journals.ametsoc.org/view/journals/mwre/124/6/1520-0493_1996_124_1256_dauiau_2_0_co_2.xml.
The problem is the loop-specific evidence. The most recent low-mode mass
diagnostic residual was clean but only `+0.0007877795793892473`, below the
fixed `+0.002` promotion threshold. The older continuity-balanced divergence
initialization was also clean but negative on primary score
(`-0.001312899911693144`). This proposal combines both weak axes and makes them
more invasive by changing a prognostic divergence tendency during the first 12
hours.

The scientific distinction from output-only mass residuals is real, so this is
not a duplicate scrap. It is still a poor next search point: it risks gravity
wave adjustment, early mass/wind guardrail failures, and cache-invalidating
shared primitive-equation edits while targeting a mass residual signal that has
twice failed to clear the fixed model-selection threshold. The staged
`balanced-low-mode-thermal-iau` is a better IAU representative because it
targets thermal thickness/Z500 errors directly and already remains available
for a later spinup test. Do not move unrelated staging files.
