---
schema_version: 1
slug: low-mode-mass-diagnostic-residual-memory
title: Carry Low-Mode Mass-Field Diagnostic Residuals
status: ready
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

# Carry Low-Mode Mass-Field Diagnostic Residuals

## Hypothesis

The current incumbent validated that horizontally scale-separated residual memory
is a large, stable correction for near-surface diagnostics. The same accepted
run still has growing positive `mean_sea_level_pressure` bias and persistent
negative `geopotential_500` bias through medium and long leads. A previous
mass-diagnostic residual was safe but too weak because it used a full-grid,
single-decay residual before the scale-separated residual result was known.

Only the broad, low-wavenumber part of the initial MSLP and Z500 diagnostic
error is likely to represent the zero-orography and hydrostatic-datum mismatch
that persists under this simplified dycore. Carrying that low-mode component,
while discarding high-mode mass residuals, should improve mass-field RMSE
without perturbing the prognostic trajectory or the accepted near-surface
residual channels.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual`.
Preserve the incumbent rollout, DFI, weak Held-Suarez forcing, log-pressure and
hydrostatic layer initialization, Strang Coriolis split, theta tendency, theta
mean recentering, semi-implicit off-centering, Richardson 10 m wind diagnostic,
and accepted scale-separated residual correction for `2m_temperature` and
`10m_u_component_of_wind`.

Add a separate output-only mass-diagnostic residual pass after the raw Dinosaur
trajectory is converted to `WeatherState`:

- compute lead-zero residuals for `mean_sea_level_pressure` and
  `geopotential_500` only when those exact channels are present in both the
  initial state and requested outputs;
- transform each residual into the existing spherical-harmonic basis and keep
  only a smooth low-mode mask, for example total wavenumber `n <= 8` with a
  taper to zero by `n = 14`;
- apply no high-mode mass residual memory;
- use a fixed, longer low-mode decay such as 120 hours for MSLP and 96 hours for
  Z500, with lead zero still exactly matching the analyzed initial channel;
- cap the absolute correction at each lead to a fixed fraction of the lead-zero
  residual norm, for example no more than `0.75 * exp(-lead_hours / decay)`;
- fall back channel-by-channel to the incumbent output if transforms are
  shape-incompatible or nonfinite;
- leave all prognostic Dinosaur state fields, pressure-level temperature and
  wind channels, `surface_pressure`, `2m_temperature`, and 10 m winds unchanged.

This is deliberately not a new pressure-coordinate rollout, terrain-orography
experiment, global pressure anchor, or flux-form surface-pressure continuity
change.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory with the `_lowmode_mass_residual` suffix.
- API changes:
  - None. Forecast inputs, output variables, lead times, and fixed metrics stay
    unchanged.
- Tests to update:
  - Unit-test low-mode mask construction, taper values, reconstruction, and
    finite fallback.
  - Verify the helper changes only `mean_sea_level_pressure` and
    `geopotential_500`.
  - Verify lead-zero exactness for corrected mass channels.
  - Verify the candidate factory preserves every incumbent option except the
    mass-residual selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 2 to 15 if the positive long-lead pressure
    bias includes a persistent large-scale diagnostic component.
  - `geopotential_500` at days 2 to 15 if the negative height bias includes a
    broad hydrostatic datum or large-scale thickness component.
  - Primary score, because the fixed target set includes both mass channels.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should follow the incumbent
    exactly because their accepted residual path is unchanged.
- Possible regressions:
  - Low-mode residual memory can over-persist evolving synoptic systems and hurt
    medium-lead MSLP or Z500 phase.
  - If the remaining mass error is dynamical rather than diagnostic, the change
    may be clean but subthreshold.

## Risks

- Numerical stability:
  - Very low. The change is output-only and cannot feed back into integration.
- Compute cost:
  - Low. It adds a small number of spherical harmonic transforms per initial
    state, not per inner step.
- Data leakage:
  - Low. It uses only same-time initial analysis channels and the model's own
    lead-zero diagnostic, matching the accepted residual-correction pattern.
- Physical plausibility:
  - Moderate. Low-mode residual separation is physically defensible, but using
    residual memory for mass diagnostics is still a simplified diagnostic
    correction.
- Rollback complexity:
  - Low. Remove one helper/flag, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_lowmode_mass_residual --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean diagnostics
    and guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta, any early MSLP or Z500 guardrail failure,
    or opposite-signed mass-channel movement would show that the remaining mass
    error is not a persistent low-mode diagnostic residual.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_apply_scale_separated_near_surface_residual_correction`, the accepted
  low/high residual split this proposal extends to mass diagnostics.
- Dynamaxx history:
  `.logbook/history/2026-06-19_21-12-19_scale-separated-surface-residual-memory/decision.md`
  accepted scale-separated residual memory with iteration delta
  `+0.03993409285933447` and validation delta `+0.04067763036264238`.
- Dynamaxx history:
  `.logbook/history/2026-06-16_15-28-07_mass-diagnostic-analysis-residuals/decision.md`
  rejected full-grid mass residuals as safe but subthreshold, motivating a
  lower-dimensional low-mode-only mechanism.
- von Storch, H., Langenberg, H., and Feser, F. 2000. "A Spectral Nudging
  Technique for Dynamical Downscaling Purposes." Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2000)128%3C3664:ASNTFD%3E2.0.CO;2
- Rasp, S. et al. 2024. "WeatherBench 2: A Benchmark for the Next Generation of
  Data-Driven Global Weather Models." Journal of Advances in Modeling Earth
  Systems. https://doi.org/10.1029/2023MS004019
- Dinosaur upstream documentation describes the JAX spectral primitive-equation
  dycore used by this adapter: https://github.com/neuralgcm/dinosaur

## Researcher Notes

This is not a duplicate of `persistent-mslp-reduction-offset`, which is an
MSLP-only static reduction-factor diagnostic. It is not a duplicate of the
scrapped `geopotential-datum-output-correction`, which applies a full
columnwise geopotential offset. It also differs from the rejected
`mass-diagnostic-analysis-residuals` by using the newly validated low-mode
spectral split and by excluding high-mode residual memory entirely.

## Evaluator Notes

### 2026-06-19T23:16:12Z

Decision: move to `ready`.

This is the strongest fresh proposal because it is narrow, output-only, and
directly incremental over the newly accepted
`scale-separated-surface-residual-memory` result. That accepted run validated
the exact family of low/high residual separation and produced clean iteration
and validation gains of about `+0.04`, with the scoring notes identifying
2 m temperature as the dominant benefit and leaving mass diagnostics as a
remaining target. The older `mass-diagnostic-analysis-residuals` experiment is
negative evidence, but it was full-grid and decayed both MSLP and Z500 without
the now-validated low-mode separation; this proposal is a lower-dimensional
retest rather than a duplicate.

The active staged `persistent-mslp-reduction-offset` is dominated for the next
slot: it is MSLP-only and persists a multiplicative pressure-reduction factor,
while this proposal tests both target mass channels with spectral isolation and
explicitly leaves high-mode residual noise out. The scrapped
`geopotential-datum-output-correction` remains weaker because it applies a
column datum correction to geopotential only and had unresolved output-adapter
staleness risk.

Scientific support is adequate for a ready item. Spectral nudging literature
supports separating large-scale low-wavenumber structure from smaller-scale
noise in dynamical models, while WeatherBench2's fixed target-variable
benchmark context makes MSLP and Z500 legitimate mass-field targets. See von
Storch et al. 2000, Monthly Weather Review,
https://doi.org/10.1175/1520-0493(2000)128%3C3664:ASNTFD%3E2.0.CO;2 and
Rasp et al. 2024, JAMES, https://doi.org/10.1029/2023MS004019.

Rank: 1 of 3 fresh proposals. Recommended as the single next Orchestrator
selection.
