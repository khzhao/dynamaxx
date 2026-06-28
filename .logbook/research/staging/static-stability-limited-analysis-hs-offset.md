---
schema_version: 1
slug: static-stability-limited-analysis-hs-offset
title: Limit the Analysis-HS Offset by Static Stability
status: staging
created_at: 2026-06-21T00:48:04Z
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

# Limit the Analysis-HS Offset by Static Stability

## Hypothesis

The accepted analysis-HS equilibrium offset improves the large-scale thermal
anchor, but it is clipped independently at each sigma layer. Independent layer
clipping can leave the relaxed equilibrium with vertical temperature increments
that locally weaken dry static stability, especially where the analyzed offset
changes sign with height. A stability-limited offset should retain most of the
accepted large-scale anomaly while preventing the weak-HS forcing from nudging
the model toward vertically noisy thermal structures that degrade Z500 and
MSLP.

This is a constraint on the equilibrium target, not a post-step state repair.
The rejected `baroclinic-theta-variance-guard` showed that broad variance
preservation after each step was too weak; the proposed mechanism acts only on
the persistent weak-HS target before it influences the rollout.

## Mechanism

Add an opt-in candidate that computes the accepted analysis-HS offset, then
applies a conservative vertical stability limiter before returning it:

- build the incumbent dry equilibrium temperature plus the bounded low-mode
  offset in nodal sigma coordinates;
- compute layerwise dry potential temperature of that candidate equilibrium
  using sigma pressure from the initial surface pressure;
- where adjacent-layer potential temperature differences fall below a small
  positive floor, reduce only the offset component with a bounded multiplicative
  factor until the equilibrium is no less statically stable than a conservative
  floor or the original Held-Suarez equilibrium;
- preserve horizontal low-mode filtering, the Kelvin cap, finite fallbacks, and
  all incumbent rollout settings;
- do not alter prognostic state variables, theta mean recentering, DFI,
  pressure-level output interpolation, target variables, or metric semantics.

Suggested registered name:
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_stable_offset`.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate factory and registry entry.
- API changes:
  - None.
- Tests to update:
  - Verify absent or nonfinite pressure/temperature diagnostics fall back to the
    incumbent offset.
  - Verify the limiter never increases the absolute offset beyond the incumbent
    capped offset.
  - Verify the candidate equilibrium potential-temperature differences satisfy
    the configured finite floor in simple columns.
  - Verify all non-offset incumbent flags are unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 3 to 15 if part of
    the remaining error comes from vertically inconsistent thermal relaxation
    targets.
  - Neutral to small positive `2m_temperature` movement because the accepted
    lower-column residual memory and weak-HS source remain active.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because no direct
    momentum tendency, Coriolis split, or 10 m diagnostic changes.
- Possible regressions:
  - The limiter may remove useful baroclinic structure from the accepted offset,
    weakening the gain that made the current incumbent successful.

## Risks

- Numerical stability:
  - Low to moderate. The candidate changes a persistent thermal target, so the
    limiter must be monotone, bounded, and finite-guarded.
- Compute cost:
  - Negligible to low. It adds per-initial-condition vertical diagnostics while
    building the analysis-HS offset.
- Data leakage:
  - None. It uses only same-time initial pressure and temperature fields already
    consumed by the incumbent.
- Physical plausibility:
  - Good. Dry static stability is a core constraint for hydrostatic primitive
    equation balance.
- Rollback complexity:
  - Low. Remove one option/helper path plus candidate factory, export, registry,
    and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_stable_offset`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run fixed `iteration` against the incumbent cache.
  - Support requires primary-score delta at least `+0.002` and no fixed
    guardrail failures.
- Validation gate:
  - Run fixed `validation` only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` and clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A subthreshold or negative iteration delta, especially with worse
    `geopotential_500` or MSLP, would indicate the accepted offset's vertical
    structure is beneficial rather than harmful.

## Citations

- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AECAAM%3E2.0.CO;2
- Jablonowski, C. and Williamson, D. L. 2006. A baroclinic instability test
  case for atmospheric model dynamical cores. Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1256/qj.06.12
- Dynamaxx history:
  `.logbook/history/2026-06-20_12-57-53_baroclinic-theta-variance-guard/decision.md`
  rejected a post-step theta variance guard; this proposal instead constrains
  only the persistent analysis-HS equilibrium offset.

## Researcher Notes

This is not a duplicate of active staged `tropopause-capped-thermal-relaxation`,
which masks the weak-HS relaxation coefficient above a diagnosed tropopause and
has unresolved per-initial mask threading. This proposal keeps the weak-HS
coefficient unchanged and limits only the already computed per-initial
analysis-HS equilibrium offset. It is also not another lead-decay, rate-mask,
DFI-source, or barotropic projection variant.

## Evaluator Notes

### 2026-06-21T00:50:17Z

Decision: move to `staging`; not selected for the next model-selection run.

The mechanism is more physically interpretable than a post-step theta variance
guard because it constrains only the persistent equilibrium target, but it is
still close to recently weak theta/analysis-HS territory. The post-step
baroclinic theta variance guard was clean but score-neutral/slightly negative,
and the barotropic analysis-HS projection suggests the accepted vertical
structure may be important. A stability limiter could therefore remove useful
baroclinic signal while adding more implementation complexity than the smooth
horizontal taper.

Keep staged for later only if diagnostics show the accepted analysis-HS target
creates dry-static-stability defects. Until then it should not be the single
ready candidate because the evidence for harmful vertical instability is
speculative and the proposal could over-constrain the incumbent's accepted
thermal anomaly.
