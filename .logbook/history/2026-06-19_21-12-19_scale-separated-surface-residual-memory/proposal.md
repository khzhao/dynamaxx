---
schema_version: 1
slug: scale-separated-surface-residual-memory
title: Split Near-Surface Residual Memory by Horizontal Scale
status: ready
created_at: 2026-06-19T21:03:11Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
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

# Split Near-Surface Residual Memory by Horizontal Scale

## Hypothesis

The incumbent's accepted near-surface residual correction treats the initial
`2m_temperature` and `10m_u_component_of_wind` residuals as gridpoint-local
signals with one stability-aware decay family. That helped substantially, but
the current iteration metrics still show large negative skill for
`2m_temperature` and declining late `10m_u_component_of_wind` skill. A single
gridpoint residual mixes two physically different errors: broad synoptic or
surface-regime bias that can persist for several days, and high-wavenumber
analysis/model mismatch that should decay quickly.

Separating the residual into low-wavenumber and high-wavenumber pieces should
retain useful synoptic surface bias memory longer while allowing small-scale
noise to decay at least as fast as the incumbent correction. This is a
diagnostic residual change, not a forecast-trajectory anchor.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual`.
Preserve the incumbent rollout, DFI, weak Held-Suarez forcing, log-pressure and
hydrostatic layer initialization, symmetric exact Coriolis split, theta
tendency, theta layer-mean recentering, fixed SIL3 off-centering, Richardson
10 m wind diagnostic, output variables, lead schedule, and fixed evaluation
protocols.

For this candidate only:

- compute the initial residual for the same output channels already corrected
  by `_apply_near_surface_residual_correction`;
- transform each residual field through the existing Dinosaur spherical
  harmonic grid in the model latitude order;
- keep a smooth low-mode residual mask, for example total wavenumber `n <= 12`
  with a taper to zero by `n = 20`, and define the high-mode residual as the
  remaining gridpoint residual;
- apply a longer but fixed low-mode decay, for example 96 hours before the
  existing stability-aware local modifier, while applying the incumbent
  stability-aware decay to the high-mode residual with an upper cap no larger
  than the current 72 hour maximum;
- preserve lead-zero exactness by replacing lead-zero outputs with the initial
  analysis values, as the incumbent already does;
- fall back to the incumbent residual correction if the spectral residual split
  is nonfinite, shape-incompatible, or unavailable for a grid.

The candidate should not alter pressure-level fields, MSLP, Z500, prognostic
state variables, DFI filters, or the supported forecast API.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, target
    variables, lead times, and metric definitions remain unchanged.
- Tests to update:
  - Unit-test the residual modal mask for finite values, protected low modes,
    smooth taper modes, and zero high-mode leakage for a synthetic low-mode
    residual.
  - Verify low plus high residual reconstructs the original gridpoint residual
    within transform tolerance.
  - Verify lead-zero exactness and finite fallback to the incumbent correction.
  - Verify non-corrected channels are unchanged by the candidate helper.
  - Verify the candidate factory preserves every incumbent option except the
    scale-separated residual selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3 to 15 if broad lower-boundary or screen-level
    bias persists after the current residual decays.
  - `10m_u_component_of_wind` at medium and late leads if synoptic-scale
    low-level wind bias is being over-decayed by the current local residual.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500` should be unchanged except
    through aggregate bookkeeping because the correction is output-only and
    limited to near-surface channels.
- Possible regressions:
  - Low-mode residual memory can act too much like persistence and degrade real
    synoptic evolution.
  - If the remaining T2m and 10 m wind errors are local physics errors rather
    than broad bias, the split may be clean but sub-threshold.

## Risks

- Numerical stability:
  - Very low. The change is output-only and cannot feed back into the Dinosaur
    trajectory.
- Compute cost:
  - Low. It adds two spherical harmonic transforms per corrected residual
    channel and initialization, not per inner rollout step.
- Data leakage:
  - Low. It uses only the same forecast's initial analysis and raw lead-zero
    model diagnostic. It must not use target truth, validation statistics, or
    learned climatology.
- Physical plausibility:
  - Moderate. Scale separation is well established for retaining large-scale
    flow constraints, but here it is applied to diagnostic residual memory
    rather than full analysis nudging.
- Rollback complexity:
  - Low. Remove one selector, one helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that residual
    horizontal-scale memory is not a material remaining error source. Any
    early 2 m temperature or 10 m wind guardrail failure would show that
    low-mode residual persistence is too strong.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_apply_near_surface_residual_correction` and currently applies one
  stability-aware decay family to full gridpoint residuals.
- Dynamaxx history:
  `.logbook/history/2026-06-18_15-57-11_stability-aware-surface-residual-decay/decision.md`
  accepted stability-aware residual decay, so this proposal preserves that
  mechanism as the high-mode fallback.
- Dynamaxx history:
  `.logbook/history/2026-06-19_18-05-11_ekman-inflow-10m-wind-diagnostic/decision.md`
  rejected a 10 m wind diagnostic with a clean but sub-threshold
  `+0.0013746829600840282` iteration delta, motivating a mechanism that can
  also affect `2m_temperature`.
- von Storch, H., Langenberg, H., and Feser, F. 2000. A Spectral Nudging
  Technique for Dynamical Downscaling Purposes. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2000)128%3C3664:ASNTFD%3E2.0.CO;2
- Waldron, K. M., Paegle, J., and Horel, J. D. 1996. Sensitivity of a
  Spectrally Filtered and Nudged Limited-Area Model to Outer Model Options.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C0529:SOASFA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of staged `diurnal-surface-residual-memory`, which
changes temporal phase for `2m_temperature`; this proposal changes horizontal
scale separation and applies to both accepted residual channels. It is also not
the scrapped `decaying-planetary-wave-initial-anchor`, because it never blends
prognostic vorticity, divergence, temperature, or log pressure toward the
initial state. It changes only output residual memory after the incumbent
trajectory is complete.

The recent DFI-routing and DFI-theta rejections are negative evidence against
more initialization bookkeeping. This proposal deliberately stays outside DFI.
The theta implicit rejection is negative evidence against broad gravity/pressure
operator changes; this proposal leaves those operators unchanged.

## Evaluator Notes

### 2026-06-19T21:10:25Z

Decision: move to `ready`; ranked 1 of 3 fresh proposals.

This is the strongest next candidate because it builds on the locally accepted
near-surface residual family while staying output-only. Source inspection
confirms the incumbent applies `_apply_near_surface_residual_correction` after
the Dinosaur trajectory has already been converted into a `WeatherState`, so a
scale-separated residual helper can leave the dycore trajectory, DFI,
off-centering, pressure-level diagnostics, MSLP, and Z500 pathways unchanged.
The accepted stability-aware residual experiment improved iteration by
`+0.021993842696981458` and validation by `+0.02232254120121757`, while the
recent Ekman 10 m wind diagnostic was clean but sub-threshold; this proposal
has a better score surface because it can affect both remaining near-surface
channels instead of wind alone.

This is distinct from staged `diurnal-surface-residual-memory`, which changes
the temporal phase of only the `2m_temperature` residual, and from scrapped
initial-state anchors because it does not feed residuals into prognostic
vorticity, divergence, temperature, or pressure. A literature check supports
the general scale-separation premise: von Storch et al. 2000 use spectral
nudging to retain reliable large-scale information while separating smaller
scales, but that citation should be treated as analog support only because this
proposal applies the split to diagnostic residual memory rather than full model
nudging.

Implementation should keep the modal cutoff and decay constants fixed before
scoring, prove low-plus-high reconstruction within transform tolerance, preserve
lead-zero exactness, and leave non-corrected channels bitwise unchanged except
for unavoidable transform tolerance in the corrected residual helper. Ready is
appropriate because the expected upside is broad enough for the fixed primary
score and the rollback surface is small.
