---
schema_version: 1
slug: bounded-1000hpa-2m-temperature
title: Diagnose 2 m Temperature from Bounded 1000 hPa Thermal Blending
status: scrap
created_at: 2026-06-21T00:38:35Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Diagnose 2 m Temperature from Bounded 1000 hPa Thermal Blending

## Hypothesis

The incumbent emits raw `2m_temperature` from the lowest sigma-layer
temperature before applying accepted residual memory. The staged
bulk-Richardson 2 m diagnostic uses stability and shear; the rejected
two-layer extrapolation was too aggressive. A lower-risk alternative is to
blend the incumbent lowest-sigma diagnostic with the already reconstructed
1000 hPa forecast temperature, using only a small bounded increment. This
tests whether the remaining screen-temperature error is partly a pressure-level
placement mismatch rather than a missing boundary-layer stability model.

## Mechanism

Register a side-by-side candidate with a suffix such as `_t1000_2m_temp`.
Preserve the incumbent rollout, weak-HS equilibrium, DFI, off-centering,
Coriolis splitting, residual decay, Richardson 10 m wind diagnostic, and all
pressure/mass outputs.

For the candidate only:

- compute the incumbent pressure-level temperature output fields;
- when `temperature_1000` is available and finite, form a bounded raw 2 m
  diagnostic as a convex blend of the lowest-sigma temperature and the 1000 hPa
  temperature;
- make the blend local and conservative, for example no more than `0.35` weight
  on `temperature_1000` and no more than `1.25 K` absolute departure from the
  incumbent raw 2 m value;
- fall back exactly to the incumbent raw 2 m temperature where `temperature_1000`
  is absent, below ground in the sigma pressure geometry, or nonfinite;
- apply the existing accepted near-surface residual correction after this raw
  diagnostic so lead zero remains anchored to analyzed `2m_temperature`;
- leave `10m_u_component_of_wind`, `mean_sea_level_pressure`,
  `geopotential_500`, surface pressure, pressure-level winds, and the trajectory
  unchanged.

This is not the staged bulk-Richardson 2 m diagnostic and not the rejected
linear two-layer extrapolation. It is a one-channel pressure-placement blend
with a fixed small cap.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry entry.
- API changes:
  - None.
- Tests to update:
  - Unit-test blend caps, missing-channel fallback, and lead-zero residual
    anchoring.
  - Verify only raw `2m_temperature` changes before residual correction.
  - Verify the factory preserves all incumbent options except the new diagnostic
    selector.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` after days 2-15 if the lowest sigma-layer proxy has a small
    systematic warm/cold offset relative to the near-surface pressure level.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, `mean_sea_level_pressure`, and
    `geopotential_500` should be unchanged.
- Possible regressions:
  - Over elevated terrain or stable boundary layers, 1000 hPa temperature may be
    less physically representative of 2 m conditions than the incumbent sigma
    diagnostic.

## Risks

- Numerical stability:
  - Low. Output-only with exact fallback.
- Compute cost:
  - Negligible.
- Data leakage:
  - None. Uses only same-lead forecast fields and fixed caps.
- Physical plausibility:
  - Moderate. 1000 hPa temperature is a standard near-surface pressure level,
    but it is not a substitute for a full screen-level diagnostic over terrain.
- Rollback complexity:
  - Low.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no early or per-lead `2m_temperature` guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A negative or near-zero clean iteration delta would show the accepted raw
    lowest-sigma 2 m proxy plus residual memory remains better than this
    pressure-level blend. Any early 2 m guardrail failure would show the cap is
    still too intrusive.

## Citations

- ECMWF IFS Documentation Part IV: Physical Processes describes screen-level
  2 m temperature as a diagnostic variable derived from model-level and
  surface-layer information.
  https://www.ecmwf.int/sites/default/files/elibrary/2016/17117-part-iv-physical-processes.pdf
- Beljaars, A. C. M. and Holtslag, A. A. M. 1991. Flux Parameterization over
  Land Surfaces for Atmospheric Models. Journal of Applied Meteorology.
  https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2
- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
  Survey, second edition. https://doi.org/10.1016/C2009-0-00034-8
- Dynamaxx history:
  `.logbook/history/2026-06-17_13-35-18_surface-layer-diagnostic-extrapolation/decision.md`
  rejected a broad two-layer extrapolation for both 2 m temperature and 10 m
  wind; this proposal is temperature-only and tightly capped.
- Dynamaxx research:
  `.logbook/research/staging/bulk-richardson-2m-temperature-diagnostic.md`
  uses lower-column stability and shear; this proposal instead tests a simpler
  pressure-placement blend.

## Researcher Notes

The mechanism deliberately avoids residual-rate changes, HS timing changes,
and surface wind changes. It should be evaluated only as a side-by-side output
diagnostic; if it moves non-temperature targets, that is an implementation bug.

## Evaluator Notes

### 2026-06-21T00:41:38Z

Decision: move to `scrap`.

Reject this in favor of the already staged
`bulk-richardson-2m-temperature-diagnostic`. Both ideas target the same
remaining raw `2m_temperature` weakness before the accepted residual correction,
but the staged bulk-Richardson proposal uses lower-column stability and shear,
which is the more physically standard surface-layer signal. This proposal uses
a bounded blend with `temperature_1000`; over elevated terrain and stable
boundary layers, 1000 hPa temperature is often not a screen-level proxy, and
the proposal itself requires below-ground and nonfinite fallbacks.

Recent history is unfavorable for another simple near-surface extrapolation:
the broad two-layer surface diagnostic regressed primary score by
`-0.10115079559414197` and failed both `10m_u_component_of_wind` and
`2m_temperature` guardrails. Narrowing to temperature-only and adding a small
cap reduces blast radius, but it does not add enough physical structure to beat
the staged bulk-Richardson diagnostic. Keeping both would split evaluation
budget across very similar output-only temperature post-processing ideas, so
this weaker pressure-placement blend should be scrapped.
