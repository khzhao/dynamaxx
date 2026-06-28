---
schema_version: 1
slug: lowmode-mslp-analysis-residual-diagnostic
title: Low-Mode MSLP Analysis Residual Diagnostic
status: scrap
created_at: 2026-06-28T06:55:05Z
author_role: Researcher
target_model: dinosaur
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

# Low-Mode MSLP Analysis Residual Diagnostic

## Hypothesis

The latest accepted incumbent improved T2m but still leaves MSLP as a plausible remaining error channel. The Dinosaur adapter emits `mean_sea_level_pressure` from the modeled surface-pressure field, while WeatherBench2 MSLP is a sea-level reduction diagnostic. Existing staged ideas test a persistent multiplicative pressure-reduction factor or a dynamic hypsometric reduction. A simpler, more conservative alternative is to persist only the large-scale additive MSLP analysis residual diagnosed at initialization, with tight amplitude clipping and a spectral low-pass filter.

This should capture stationary broad terrain-reduction or datum mismatch components without feeding anything back into the trajectory and without persisting grid-scale synoptic residuals.

## Mechanism

Register one side-by-side candidate derived from the current incumbent, for example `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_lmmslp`.

For the candidate only:

- compute the raw incumbent MSLP diagnostic at initialization from the initialized Dinosaur state;
- compare it with the initial `mean_sea_level_pressure` input channel when present;
- form an additive residual `initial_target_mslp - initial_raw_mslp`;
- transform the residual to the Dinosaur spectral grid and retain only a fixed low-wavenumber band, for example total wavenumber <= 8 or the closest existing coarse modal mask;
- clip the low-mode residual to a fixed pressure-amplitude bound, for example +/- 1200 Pa, and fall back to zero wherever inputs are missing or nonfinite;
- add the same clipped low-mode residual to emitted `mean_sea_level_pressure` at all leads;
- leave `surface_pressure`, pressure-level fields, geopotential, winds, T2m, the prognostic state, and fixed evaluation protocols unchanged.

This differs from a persistent multiplicative MSLP ratio because it is additive, spectrally filtered, and intentionally unable to alter local cyclone intensity through grid-scale residuals. It differs from dynamic hypsometric MSLP reduction because it does not infer terrain height or recompute pressure reduction from forecast temperature.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one candidate factory and registry key for `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_lmmslp`.
- API changes:
  - None. Forecast input/output contract and fixed metrics remain unchanged.
- Tests to update:
  - Verify missing initial MSLP produces exact incumbent output.
  - Verify the helper clips residual amplitude and drops nonfinite residuals.
  - Verify only `mean_sea_level_pressure` changes and non-MSLP channels are unchanged.
  - Verify the low-mode filter removes a synthetic grid-scale residual while preserving a large-scale residual.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` at most leads if broad MSLP reduction or datum errors are quasi-stationary relative to the zero-orography Dinosaur surface pressure.
  - Primary score if MSLP remains a negative aggregate channel.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and `geopotential_500`, because the change is output-only and one-channel.
- Possible regressions:
  - Persisting an initial synoptic MSLP residual can overcorrect evolving pressure systems, especially if the residual is not purely terrain or datum related.
  - A fixed low-mode additive residual may improve early leads but degrade later leads if broad pressure biases evolve.

## Risks

- Numerical stability:
  - Very low. The change is output-only and finite-fallback guarded.
- Compute cost:
  - Low. One initialization residual, one low-mode projection, and one addition per output lead.
- Data leakage:
  - Low if implemented exactly as specified. It uses only same-time initial analysis channels and never validation statistics, future targets, or golden data.
- Physical plausibility:
  - Moderate. Sea-level pressure reduction has a static terrain/datum component, but an additive residual is less physically complete than a hypsometric operator.
- Rollback complexity:
  - Low. Remove one helper/flag, one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_lmmslp`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_lmmslp --workers 4`.
  - Promote only if the candidate beats cached incumbent iteration by the protocol threshold with clean diagnostics and no guardrail failure.
- Validation gate:
  - Run fixed validation only after iteration promotion and require the protocol validation threshold.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that broad initial MSLP residual persistence is not a material remaining bottleneck. Any MSLP guardrail failure would show the residual is too synoptic or too static.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` emits both `surface_pressure` and `mean_sea_level_pressure` from the same surface-pressure diagnostic path.
- Dynamaxx history: `.logbook/history/2026-06-16_15-28-07_mass-diagnostic-analysis-residuals/decision.md` found a broader decaying MSLP/Z500 residual safe but below promotion, motivating a narrower MSLP-only low-mode test.
- Dynamaxx staging: `.logbook/research/staging/persistent-mslp-reduction-offset.md` and `.logbook/research/staging/hypsometric-dynamic-mslp-reduction.md` cover multiplicative and hypsometric variants; this proposal tests a clipped additive low-mode residual instead.
- Pauley, P. M. 1998. An Example of Uncertainty in Sea Level Pressure Reduction. Weather and Forecasting. https://doi.org/10.1175/1520-0434(1998)013%3C0833:AEOUIS%3E2.0.CO;2
- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory Survey. Academic Press.
- ECMWF IFS Documentation, Part III: Dynamics and Numerical Procedures, describes hydrostatic pressure/geopotential relationships relevant to pressure diagnostics.

## Researcher Notes

This is intentionally narrower than prior mass-diagnostic residuals: it is MSLP-only, additive, low-mode, and output-only. It is not a duplicate of `persistent-mslp-reduction-offset`, which persists a multiplicative MSLP/surface-pressure ratio, or `hypsometric-dynamic-mslp-reduction`, which recomputes a physical reduction from forecast temperature.

## Evaluator Notes

### 2026-06-28T06:58:29Z

Decision: move to `scrap`.

The proposal is low-blast-radius and output-only, but it is another
metric-facing MSLP post-processing adapter in a queue that already contains
better-ranked MSLP diagnostics. Existing staging has
`persistent-mslp-reduction-offset` as the simpler direct test of the
surface-pressure-versus-MSLP mismatch, `hypsometric-dynamic-mslp-reduction` and
`pressure-level-hypsometric-mslp-diagnostic` as more physically grounded
hypsometric follow-ups, and `coupled-lowmode-hydrostatic-mass-residual` as the
more constrained low-mode residual variant.

Measured history argues against spending a full iteration on this narrower
residual carryover. `low-mode-mass-diagnostic-residual-memory` was clean but
only improved iteration by `+0.0007877795793892473`, below the `+0.002`
promotion gate, and its decision record concluded that future mass-diagnostic
proposals need a stronger mechanism than output-only low-mode lead-zero
residual carryover. The earlier `mass-diagnostic-analysis-residuals` run was
also clean but subthreshold. This proposal removes Z500 coupling rather than
adding stronger physical evidence, so its likely incremental signal is weaker
than the existing staged alternatives.

Literature checks support caution rather than promotion: sea-level pressure
reduction is a real diagnostic problem, but reduction methods are uncertain and
terrain-sensitive. A fixed additive low-mode residual is less physically
grounded than a bounded reduction-factor or hypsometric diagnostic and can
still persist weather-dependent analysis increments.

Recommendation: do not implement this new residual variant. If the loop moves
back to MSLP, promote an existing staged MSLP idea first, with
`persistent-mslp-reduction-offset` ranked ahead of the hypsometric variants and
this proposal below them.
