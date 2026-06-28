---
schema_version: 1
slug: hypsometric-dynamic-mslp-reduction
title: Diagnose MSLP with a Dynamic Hypsometric Reduction
status: staging
created_at: 2026-06-20T22:43:21Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Diagnose MSLP with a Dynamic Hypsometric Reduction

## Hypothesis

The adapter still treats mean sea level pressure as essentially the modeled
surface pressure, while real MSLP is a diagnostic reduction through a
near-surface thermal column. A staged persistent MSLP factor would only carry a
static initial ratio. A dynamic hypsometric reduction can use the forecast
surface pressure and lower-column temperature at each lead, plus an inferred
same-time terrain height, to improve MSLP without changing the prognostic
surface pressure, geopotential, winds, thermal tendencies, or evaluation
contract.

## Mechanism

Add a side-by-side output-only candidate, for example suffixing the incumbent
with `_hypsometric_mslp`. Preserve the full incumbent trajectory and all
non-MSLP output paths.

For the candidate only:

- infer a bounded effective terrain height at initialization from the ratio of
  analyzed MSLP to analyzed surface pressure using the dry hypsometric relation
  and the lowest available temperature;
- clip the inferred height to a broad physical range and fall back to zero if
  required initial channels are missing or nonfinite;
- at every output lead, compute a dynamic sea-level pressure reduction from the
  forecast surface pressure and forecast lowest-layer temperature, optionally
  using a two-layer mean temperature where available;
- cap the multiplicative MSLP correction and require finite fallback to the
  incumbent raw MSLP;
- change only the emitted `mean_sea_level_pressure` channel.

This is not a terrain lower-boundary or pressure-gradient experiment. It never
feeds terrain, MSLP, or corrected pressure back into the dycore.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused adapter tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model factory and registry entry.
- API changes:
  - None.
- Tests to update:
  - Unit-test inferred height, clipping, and finite fallback.
  - Verify only `mean_sea_level_pressure` changes.
  - Verify zero inferred height is exactly incumbent behavior.
  - Verify lead-zero MSLP is closer to analyzed MSLP when both analyzed pressure
    channels are available.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` across leads if a terrain-reduction diagnostic
    error remains in the zero-orography adapter.
  - Primary score can improve without mass-field trajectory side effects.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and `geopotential_500` should
    be unchanged except for metric aggregation noise.
- Possible regressions:
  - The inferred height can entangle synoptic analysis increments with static
    reduction structure.
  - A simple dry reduction can overcorrect warm or cold columns.

## Risks

- Numerical stability:
  - Very low; output-only.
- Compute cost:
  - Negligible.
- Data leakage:
  - Low. The candidate uses only same-time initial channels and forecast-state
    lead fields, not future targets or validation statistics.
- Physical plausibility:
  - Moderate. Hypsometric sea-level pressure reduction is standard, but this is
    a bounded simplified diagnostic without a full terrain or boundary-layer
    state.
- Rollback complexity:
  - Low.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary delta at least `+0.002`, clean diagnostics, no
    early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero delta would show MSLP reduction is not a material
    remaining bottleneck. Any MSLP guardrail failure would show the dynamic
    hypsometric formula is too crude.

## Citations

- Pauley, P. M. 1998. An example of uncertainty in sea level pressure
  reduction. Weather and Forecasting.
  https://doi.org/10.1175/1520-0434(1998)013%3C0833:AEOUIS%3E2.0.CO;2
- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
  Survey, second edition. Academic Press.
- ECMWF IFS Documentation, Part III: Dynamics and Numerical Procedures,
  describes hydrostatic pressure and geopotential relationships used in
  pressure diagnostics.
- Dynamaxx history:
  `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography/decision.md`
  rejected prognostic terrain/orography coupling after severe mass-field
  guardrail failures; this proposal is output-only.
- Dynamaxx research:
  `.logbook/research/ready/persistent-mslp-reduction-offset.md` proposes a
  persistent initial factor; this proposal differs by recomputing the reduction
  from forecast lower-column temperature at each lead.

## Researcher Notes

This avoids the known bad terrain mechanism by leaving surface pressure and
pressure gradients untouched. It is also not a duplicate of the staged
persistent MSLP offset: the correction is dynamic in lead time through the
forecast thermal column, so it tests a different diagnostic error source.

## Evaluator Notes

### 2026-06-20T22:47:09Z

Decision: move to `staging`; ranked second of the three triaged proposals.

The proposal is implementable and clearly output-only: it changes only emitted
`mean_sea_level_pressure`, does not alter prognostic surface pressure,
geopotential, winds, thermal tendencies, pressure gradients, DFI, or the
forecast contract, and uses only same-time initial fields plus forecast lower
column temperature. That distinction matters because the terrain-aware
surface-pressure/orography experiment showed large aggregate gains can still be
invalid when mass-field guardrails fail. This proposal avoids that prognostic
terrain path.

Do not promote it now. Active staging already contains
`persistent-mslp-reduction-offset`, a simpler MSLP-only diagnostic test of the
same core surface-pressure-versus-MSLP mismatch. The dynamic hypsometric version
is more physically motivated, but it is also more formula-dependent and more
exposed to overcorrecting synoptic thermal columns. Because it improves only
one scored channel through an output diagnostic, the evidence bar should be
higher to avoid metric-facing post-processing without a broader dycore benefit.
Keep staged behind the simpler persistent MSLP diagnostic and behind the
trajectory-level analysis-HS projection.

### 2026-06-27T19:07:18Z

Decision: keep in `staging`.

The new incumbent still has negative MSLP skill, so MSLP reduction diagnostics
remain relevant. Keep this idea staged because it is the more complex follow-up
to the now-ready `persistent-mslp-reduction-offset`: it recomputes a
hypsometric reduction from forecast lower-column temperature, which is more
physical but also more exposed to dry-formula and synoptic overcorrection.

If the persistent offset fails cleanly or proves too static, this dynamic
version is the next MSLP-output diagnostic to revisit. It should not be ready
at the same time as the simpler persistent offset because both target the same
single channel and would overfill the ready queue with closely related
metric-facing adapters.

### 2026-06-28T07:01:40Z

Decision: keep in `staging`; rank 2 of 4.

This remains implementable and output-only, so it is not scrap. It is still
inferior to `persistent-mslp-reduction-offset` for the next experiment because
it tests the same MSLP reduction family with more formula surface: inferred
effective terrain height, lower-column temperature dependence, correction
caps, and dry-reduction failure modes. The recent rejection history argues for
small, isolated changes, and this proposal is a reasonable follow-up only if
the persistent factor fails cleanly, is too static by score diagnostics, or a
read-only diagnostic shows the lower-column thermal evolution explains MSLP
error better than the initial MSLP/surface-pressure offset.
