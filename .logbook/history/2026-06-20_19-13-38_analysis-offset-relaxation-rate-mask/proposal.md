---
schema_version: 1
slug: analysis-offset-relaxation-rate-mask
title: Mask Weak-HS Relaxation Rates with the Analysis-Offset Equilibrium
status: ready
created_at: 2026-06-20T19:03:48Z
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

# Mask Weak-HS Relaxation Rates with the Analysis-Offset Equilibrium

## Hypothesis

The accepted incumbent improved by adding a bounded low-wavenumber analysis
offset to the weak Held-Suarez equilibrium. That result says the idealized
equilibrium temperature was missing persistent large-scale structure, but the
weak relaxation rate is still spatially uniform for a given layer and latitude.
Where the accepted offset is large, a uniform Newtonian relaxation can still
overdamp stationary thermal anomalies that the accepted equilibrium is trying
to preserve. A bounded rate mask derived from the same low-mode offset should
retain stabilizing weak-HS behavior in ordinary columns while relaxing more
slowly in columns where the analysis says the idealized equilibrium is least
representative.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask`.
Preserve every incumbent option and add one opt-in multiplier inside the
tracer-safe Held-Suarez thermal forcing.

For each initial state, reuse the accepted low-mode analysis-offset computation
already needed by `use_analysis_offset_weak_held_suarez_equilibrium`. Convert
the absolute offset magnitude into a smooth relaxation-rate multiplier, for
example
`rate_multiplier = clip(1 / (1 + abs(offset) / 12 K), 0.55, 1.0)`.
Apply the multiplier only to the thermal Newtonian relaxation tendency,
not to the equilibrium temperature itself, wind drag, pressure, temperature
initialization, DFI, Coriolis splitting, theta tendency, theta recentering,
off-centering, scale-separated near-surface residuals, or the Richardson 10 m
wind diagnostic. The multiplier must be low-mode, finite-guarded, and bounded;
nonfinite offset diagnostics fall back to multiplier `1.0`, which is exactly
the incumbent rate.

This is not a new surface-residual memory variant and not a DFI ordering
variant. It changes the weak-HS relaxation operator, whereas the recent
DFI-balanced HS rejection only changed when the same accepted offset was
computed.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one candidate factory and registry entry with the suffix `_hs_rate_mask`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, metrics, and
    fixed protocols remain unchanged.
- Tests to update:
  - Unit-test that zero analysis offset gives multiplier `1.0`.
  - Unit-test finite bounds and fallback for large, negative, and nonfinite
    offsets.
  - Verify only the weak-HS thermal tendency changes; vorticity, divergence,
    log surface pressure, tracers, DFI setup, residual correction, and output
    packing stay on the incumbent path.
  - Verify the candidate factory preserves every incumbent flag except the new
    rate-mask selector.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and longer leads if the accepted offset still
    decays too aggressively where idealized HS climatology is a poor anchor.
  - `geopotential_500` if slower relaxation of large-scale baroclinic thermal
    anomalies improves thickness evolution.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be less exposed than in recent wind-output
    diagnostics because no wind diagnostic or momentum tendency is changed.
  - Early lead-zero behavior should remain unchanged apart from DFI effects
    already present in the incumbent.
- Possible regressions:
  - Weak-HS relaxation is stabilizing; reducing it in offset-rich columns can
    allow thermal drift and pressure-gradient errors.
  - The accepted candidate showed a small day-4 MSLP regression, so this idea
    should be watched for MSLP drift around days 3 to 5.

## Risks

- Numerical stability:
  - Low to moderate. The multiplier weakens a stabilizing source but remains
    bounded and finite-guarded.
- Compute cost:
  - Low. It reuses the accepted offset and adds local arithmetic inside an
    existing forcing path.
- Data leakage:
  - Low. The multiplier uses only same-time initial analysis state already used
    by the accepted analysis-offset equilibrium, with no future truth,
    validation statistics, or golden data.
- Physical plausibility:
  - Moderate to high. Newtonian relaxation toward an idealized equilibrium is a
    modeling closure; spatially reducing its strength where the analyzed
    equilibrium offset is largest is a conservative way to acknowledge missing
    stationary structure.
- Rollback complexity:
  - Low. Remove one flag/helper, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_hs_rate_mask --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the accepted
    equilibrium offset exhausted the useful weak-HS improvement. Any early MSLP
    or Z500 guardrail failure would show the rate mask removed needed thermal
    stabilization.

## Citations

- Held, I. M. and Suarez, M. J. 1994. A Proposal for the Intercomparison of the
  Dynamical Cores of Atmospheric General Circulation Models. Bulletin of the
  American Meteorological Society, 75, 1825-1830.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Jablonowski, C. and Williamson, D. L. 2006. A baroclinic instability test
  case for atmospheric model dynamical cores. Quarterly Journal of the Royal
  Meteorological Society, 132, 2943-2975. https://doi.org/10.1256/qj.06.12
- Polichtchouk, I., Shepherd, T. G., and Byrne, N. J. 2018. Impact of the
  vertical resolution of climate models on the Brewer-Dobson circulation.
  Quarterly Journal of the Royal Meteorological Society, 144, 2341-2354.
  https://doi.org/10.1002/qj.3353

## Researcher Notes

The accepted `.logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium`
showed that a bounded low-order analysis offset to the weak-HS equilibrium
materially improved both iteration and validation, with only small MSLP
regression. This proposal keeps that accepted offset and asks a different
operator question: whether the relaxation rate should also know where the
idealized equilibrium is least representative.

It is not a duplicate of
`.logbook/history/2026-06-20_15-00-13_dfi-balanced-analysis-hs-equilibrium`,
which recomputed the same equilibrium offset from a DFI-balanced state and was
near-neutral. It is also not `zonal-mean-weak-hs-relaxation`, `mass-neutral
weak-HS`, `weak-hs-positive-time-ramp`, or `tropopause-capped-thermal-relaxation`:
those change zonal/global mean heating, source timing, or vertical masks. This
proposal uses the accepted three-dimensional low-mode offset only to make the
thermal relaxation locally less aggressive.

## Evaluator Notes

### 2026-06-20T19:12:40Z

Decision: move to `ready`; ranked 1 of 3 triaged proposals.

This is the strongest next experiment because it extends the one recent
mechanism with clear positive evidence. The accepted
`analysis-offset-held-suarez-equilibrium` improved iteration by
`+0.016990568302663656` and validation by `+0.01745893975367474` with clean
diagnostics and no RMSE guardrail failure. This proposal asks a different,
localized follow-up question: whether the accepted low-mode analysis offset
should weaken only the Newtonian thermal relaxation rate where the idealized HS
anchor is least representative.

The negative evidence is real but not disqualifying. `dfi-balanced-analysis-hs-
equilibrium` was clean and slightly negative (`-0.00001282596467677699`), which
warns against merely recomputing the same offset around DFI. `zonal-mean-weak-
hs-relaxation` and related weak-HS variants warn that reducing useful local
thermal damping can regress mass fields. This proposal remains worth one ready
slot because it is bounded, finite-guarded, reuses incumbent same-time analysis
information, preserves DFI and output diagnostics, and has a small rollback
surface. The Scorer should watch early MSLP/Z500 and day-3-through-day-5 MSLP
because the accepted analysis-offset incumbent already showed its largest RMSE
regression there.
