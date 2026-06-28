---
schema_version: 1
slug: smooth-analysis-hs-spectral-taper
title: Smooth the Analysis-HS Equilibrium Spectral Taper
status: ready
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

# Smooth the Analysis-HS Equilibrium Spectral Taper

## Hypothesis

The accepted incumbent gained skill by adding a bounded low-wavenumber analysis
offset to the weak Held-Suarez equilibrium. Its current mask is deliberately
hard: zonal wavenumbers larger than 3 and total wavenumbers larger than 12 are
zeroed. A hard spectral cutoff can introduce weak gridpoint ringing in the
equilibrium field that is then relaxed toward for the full rollout. Replacing
the cutoff with a compact raised-cosine taper should preserve the accepted
planetary-scale anchor while reducing spectral edge artifacts in the thermal
forcing.

This targets the structure of the accepted equilibrium offset, not its source
state, decay rate, DFI ordering, or vertical projection. That distinction
matters because recent post-incumbent variants of those other axes did not
promote.

## Mechanism

Add an opt-in candidate that changes only
`_analysis_offset_weak_hs_low_mode_mask` for the analysis-HS equilibrium:

- keep all incumbent initialization, DFI, Strang Coriolis split, theta tendency,
  theta mean recentering, semi-implicit offcentering, scale-separated surface
  residuals, weak-HS rates, and output diagnostics unchanged;
- replace the binary total-wavenumber cutoff with a raised-cosine taper that is
  one through a conservative inner range such as total wavenumber 9, decays
  smoothly through total wavenumbers 10 to 14, and is zero above the outer
  range;
- replace the binary zonal-wavenumber edge with a similarly smooth transition
  that retains the accepted planetary scales but avoids a rectangular spectral
  corner;
- keep the existing finite checks and the same Kelvin cap after transforming
  the tapered offset back to nodal space;
- fall back to the incumbent mask if the taper shape is incompatible with the
  grid.

Suggested registered name:
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_smooth_taper`.

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
  - None. The forecast contract, variables, metrics, lead range, and protocols
    remain unchanged.
- Tests to update:
  - Verify the tapered mask is bounded in `[0, 1]`, finite, and shape-compatible
    with the horizontal modal grid.
  - Verify the candidate preserves all incumbent flags except the new taper
    option.
  - Verify the existing Kelvin cap still bounds the final nodal offset.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium to long leads if
    the current hard-edged low-mode equilibrium offset injects weak ringing into
    hydrostatic thickness and pressure evolution.
  - Small `2m_temperature` gains after the surface residual memory decays, if
    smoother large-scale thermal anchoring avoids local overshoot.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to the incumbent because
    momentum equations and the Richardson diagnostic are unchanged.
- Possible regressions:
  - The hard mask may be part of the accepted empirical gain; smoothing could
    weaken useful planetary-wave thermal anchoring and produce a near-zero or
    negative aggregate delta.

## Risks

- Numerical stability:
  - Low. The offset remains bounded, low order, and finite-guarded.
- Compute cost:
  - Negligible. It changes a static mask used while building the per-initial
    equilibrium offset.
- Data leakage:
  - None. It uses only same-time initial fields already used by the incumbent.
- Physical plausibility:
  - Good. Smooth spectral filtering is standard practice to reduce truncation
    artifacts in spectral models.
- Rollback complexity:
  - Low. Remove one adapter option/helper branch, one factory/export, one
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_smooth_taper`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run the fixed `iteration` protocol against the cached incumbent baseline.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-lead
    guardrail failure.
- Validation gate:
  - Run fixed `validation` only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with the same
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that hard-mask
    ringing is not a material remaining error source.

## Citations

- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Gottlieb, D. and Shu, C.-W. 1997. On the Gibbs phenomenon and its resolution.
  SIAM Review. https://doi.org/10.1137/S0036144596301390
- ECMWF IFS Documentation CY49R1, Part III: Dynamics and Numerical Procedures,
  documents spectral-transform hydrostatic dynamics and filtering context.
  https://www.ecmwf.int/sites/default/files/elibrary/112024/81625-ifs-documentation-cy49r1-part-iii-dynamics-and-numerical-procedures.pdf
- Dynamaxx history:
  `.logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium/decision.md`
  accepted the low-mode analysis-HS equilibrium, while later DFI-ordering,
  rate-mask, lead-decay, and barotropic-projection variants did not promote.

## Researcher Notes

This is not a duplicate of `analysis-offset-relaxation-rate-mask`,
`lead-decayed-analysis-hs-equilibrium`,
`barotropic-analysis-hs-equilibrium-offset`, or
`dfi-balanced-analysis-hs-equilibrium`. Those changed rate, time dependence,
vertical projection, or source state. This proposal changes only the horizontal
spectral taper of the already accepted equilibrium offset.

## Evaluator Notes

### 2026-06-21T00:50:17Z

Decision: move to `ready`; ranked 1 of 1 model-selection proposals approved
for the next Orchestrator candidate.

This is the strongest next experiment because it is small, reversible, and
targets a distinct remaining axis of the accepted analysis-HS equilibrium:
the hard horizontal spectral mask. Recent post-incumbent failures penalize
analysis-HS follow-ups generally, but they tested different mechanisms:
DFI-balanced source state, relaxation-rate masking, lead decay, and barotropic
vertical projection. This proposal preserves the accepted raw source, forcing
rate, persistence over lead time, vertical structure, forecast contract,
target variables, splits, lead range, metrics, leaderboard policy, and golden
usage.

The implementation surface is narrow: the incumbent already has
`_analysis_offset_weak_hs_low_mode_mask`, and this candidate can be a
side-by-side smooth-mask variant with bounded `[0, 1]` weights and the same
Kelvin cap and finite fallback. The physical rationale is plausible because
smooth spectral tapers are a standard way to reduce hard-cutoff ringing, but
the expected gain is uncertain after several analysis-HS follow-ups failed.
That uncertainty is acceptable for exactly one next model-selection run
because the candidate is cheap to implement, easy to roll back, and tests a
cleanly separable numerical mechanism.
