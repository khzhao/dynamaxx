---
schema_version: 1
slug: mass-diagnostic-analysis-residuals
title: Add Decaying Mass-Diagnostic Analysis Residuals
status: ready
created_at: 2026-06-16T15:24:42Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add Decaying Mass-Diagnostic Analysis Residuals

## Hypothesis

The accepted incumbent already preserves DFI and adds output-only residuals for
`2m_temperature` and `10m_u_component_of_wind`, producing a large fixed-protocol
gain while leaving `geopotential_500` and `mean_sea_level_pressure` effectively
unchanged. The remaining fixed target mass diagnostics still contain adapter
projection error at lead 0: the sigma-coordinate state is initialized from
pressure-level temperature and winds, geopotential is reconstructed
hydrostatically from the projected state with zero orography, and
`mean_sea_level_pressure` is currently emitted as model surface pressure.

Adding a decaying analysis residual for `geopotential_*` pressure-level channels
and `mean_sea_level_pressure` should reduce short-lead diagnostic mismatch for
the two uncorrected mass targets without perturbing the prognostic Dinosaur
trajectory or reintroducing the early mass-field guardrail failures seen in the
terrain/orography candidate.

## Mechanism

Extend the incumbent's output-only residual correction with a separate guarded
option such as `apply_mass_diagnostic_residual_correction`. For each
initialization and requested output channel in the mass-diagnostic set, compute
the lead-0 residual between the input analysis channel and the raw Dinosaur
lead-0 diagnostic:

`analysis_residual = initial_channel - raw_lead_zero_diagnostic`

Apply that residual only at output time with a fixed exponential decay:

`corrected = raw_diagnostic + analysis_residual * exp(-lead_hours / decay_hours)`

Use the same predeclared 48 hour decay as the accepted near-surface residual
unless the Evaluator explicitly requires a shorter fixed value before
implementation. Correct only channels that are both present in the initial state
and emitted by the forecast. The first side-by-side candidate should preserve
the accepted DFI and near-surface correction and add mass residuals for:

- `mean_sea_level_pressure`
- `geopotential_<pressure_level>` channels, including the fixed scored
  `geopotential_500`

Do not change sigma coordinates, orography, pressure interpolation,
semi-implicit reference temperature, target variables, lead times, metrics,
splits, deterministic gates, or the `WeatherState` contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add a side-by-side factory such as
    `dinosaur_dfi_surface_mass_residual`, preserving the existing
    `dinosaur`, `dinosaur_dfi`, and `dinosaur_dfi_surface_residual` entries.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` remains unchanged.
- Tests to update:
  - Add unit tests showing lead-0 `mean_sea_level_pressure` and
    `geopotential_500` match the initial analysis when the mass residual option
    is enabled and lead 0 is requested.
  - Add a decay test showing nonzero mass residuals shrink with lead hours using
    the fixed decay constant.
  - Add a preservation test showing the candidate still applies the accepted
    near-surface residuals for `2m_temperature` and `10m_u_component_of_wind`.
  - Add a negative test showing unsupported or absent initial mass channels are
    skipped rather than synthesized.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at days 1-3 because the current adapter emits
    model surface pressure for the MSLP channel and therefore carries a
    deterministic diagnostic offset from the analyzed MSLP field.
  - `geopotential_500` at days 1-3 if hydrostatic reconstruction and
    sigma-pressure projection produce a persistent initial geopotential offset.
  - Primary score should improve beyond the incumbent if the two mass targets
    have short-lead projection error analogous to the near-surface diagnostics.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should retain the accepted
    incumbent behavior, because this proposal adds mass channels without
    changing the existing near-surface residual formula.
  - Long leads should trend back toward the raw Dinosaur forecast as the
    residual decays.
- Possible regressions:
  - Stale MSLP or Z500 residuals may degrade rapidly evolving cyclones after day
    2 if the fixed decay is too slow.
  - Correcting `geopotential_500` output without correcting wind balance could
    improve RMSE while slightly worsening skill components sensitive to anomaly
    phase.
  - If lead-0 mass diagnostic residuals are small in real evaluation chunks,
    the proposal may be neutral and fail the iteration promotion threshold.

## Risks

- Numerical stability:
  - Very low. The correction is output-only and does not feed back into
    vorticity, divergence, temperature, log surface pressure, DFI, or filters.
- Compute cost:
  - Negligible relative to the spectral rollout; the correction is a few
    channelwise array operations per requested lead.
- Data leakage:
  - Low. The residual uses only forecast-time initial analysis channels already
    available in `ForecastInput.initial_state`, the same information used by
    persistence. It must not inspect truth at positive leads or validation
    artifacts.
- Physical plausibility:
  - Moderate. The correction is a diagnostic analysis-increment surrogate, not a
    full pressure-reduction or geopotential post-processing scheme. It is more
    physically conservative than the rejected terrain candidate because it does
    not alter prognostic surface pressure, orography, or pressure-level
    interpolation.
- Rollback complexity:
  - Low. The mechanism can be isolated behind one adapter flag and one
    side-by-side registry entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_mass_residual`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_mass_residual --workers 4`.
  - Support for the hypothesis is a primary-score improvement of at least the
    fixed promotion threshold against `dinosaur_dfi_surface_residual`, with
    early `geopotential_500` and `mean_sea_level_pressure` RMSE improving or
    staying within guardrails.
  - Reject before validation if the candidate repeats the terrain failure mode:
    early lead 1-5 mean RMSE regression above the fixed limit for
    `geopotential_500` or `mean_sea_level_pressure`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_mass_residual --workers 4`
    only after iteration promotion.
  - Validation should show the same direction of mass-diagnostic movement
    without relying on a single lead or producing near-surface regressions.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with neutral primary movement below the
    promotion threshold, or any fixed RMSE guardrail failure for mass fields,
    would show that lead-0 mass diagnostic residuals are not a useful follow-up
    to the accepted near-surface residual candidate.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  reconstructs pressure-level geopotential from the sigma-coordinate state with
  zero orography and emits both `surface_pressure` and
  `mean_sea_level_pressure` from the same model surface-pressure field.
- Dynamaxx source: `src/dynamaxx/eval/protocols.py` fixes the scored variables
  to `2m_temperature`, `mean_sea_level_pressure`, `geopotential_500`, and
  `10m_u_component_of_wind` at lead days 1 through 15.
- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
  Assimilation Using Incremental Analysis Updates. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
- Polavarapu, S., Ren, S., Clayton, A. M., Sankey, D., and Rochon, Y. 2004. On
  the Relationship between Incremental Analysis Updating and Incremental Digital
  Filtering. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2004)132%3C2495:OTRBIA%3E2.0.CO;2
- ECMWF IFS Documentation Part VI describes pressure-level geopotential and mean
  sea level pressure as post-processed diagnostic quantities, with specialized
  interpolation/reduction procedures rather than a direct lowest-level field
  copy. https://www.ecmwf.int/sites/default/files/elibrary/2003/77032-ifs-documentation-cy23r4-part-vi-technical-and-computational-procedures_1.pdf
- Rasp, S. et al. 2024. WeatherBench 2: A benchmark for the next generation of
  data-driven global weather models. Journal of Advances in Modeling Earth
  Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This is intentionally narrower than the staged Held-Suarez forcing idea and
more directly supported by the accepted incumbent result. It is also not a
duplicate of `near-surface-anomaly-diagnostics`: that accepted candidate changed
only unresolved screen-level temperature and 10 m zonal wind diagnostics, while
this proposal targets the two fixed mass diagnostics that remained nearly
unchanged.

This proposal differs from the rejected `terrain-aware-surface-pressure-orography`
candidate in the mechanism expected to protect guardrails. Terrain/orography
changed prognostic surface-pressure handling and produced large early RMSE
failures for Z500 and MSLP despite aggregate-score gains. Here the raw
prognostic trajectory, zero-orography assumption, and interpolation machinery
remain untouched; the only change is a decaying analysis residual applied at
output time. If that still fails mass-field guardrails, the result should be
treated as evidence against further residual-based mass diagnostic correction.

## Evaluator Notes

2026-06-16T15:27:07Z - Move to `ready` after triage against incumbent
`dinosaur_dfi_surface_residual` at
`845de671268f42c6b44b0a60c287e043087364a1`.

Rank this first among active proposals for Iteration 9. The proposal has a
clear, narrow mechanism: extend the accepted output-only residual correction
from near-surface diagnostics to the two fixed mass diagnostics that were
effectively unchanged by the incumbent. Source inspection confirms the current
adapter already has a guarded residual path, emits `mean_sea_level_pressure`
from the modeled surface-pressure field, and reconstructs pressure-level
geopotential from the sigma-coordinate state with zero orography. A side-by-side
candidate can preserve DFI, preserve the accepted near-surface residuals, and
avoid forecast-contract or evaluation-protocol changes.

The terrain-aware rejection is the main risk signal. That candidate improved
aggregate primary score but failed early Z500 and MSLP RMSE guardrails badly,
so this proposal must stay output-only and must not alter prognostic surface
pressure, orography, sigma coordinates, pressure interpolation, target
variables, lead times, metrics, or fixed protocols. It should be rejected during
scoring if the mass residual repeats the terrain pattern with early mass-field
RMSE regressions. The expected code surface is low, rollback is clean, leakage
risk is low because only forecast-time initial analysis channels are used, and
failure would still provide a useful boundary on residual-based diagnostic
corrections.
