---
schema_version: 1
slug: exact-ocean-bulk-heat-flux-split
title: Exact Split for Ocean Bulk Heat-Flux Relaxation
status: staging
created_at: 2026-06-22T10:02:44Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf
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

# Exact Split for Ocean Bulk Heat-Flux Relaxation

## Hypothesis

The accepted incumbent gained substantial iteration and validation skill from a
weak ocean-only bulk sensible heat flux. That forcing is currently composed into
the explicit primitive-equation tendency, where the lowest-layer temperature is
advanced through the general IMEX Runge-Kutta stages and then limited by a
per-step increment cap. Because the ocean flux is locally a relaxation toward a
fixed lead-zero thermal anchor with a bounded wind-dependent exchange rate, it
has an analytic exponential update. Applying that update as a positive-time
split source may preserve the accepted physical signal while reducing
time-discretization and cap-ordering error in the lower-layer thermal tendency.

This does not change the lower-boundary anchor, the ocean mask, or the transfer
coefficient family. The recent rejected SST/sea-ice anchor is negative evidence
against changing the boundary data source; this proposal instead keeps the
accepted air-temperature anchor and asks whether the accepted source should be
integrated more faithfully.

## Mechanism

Register a short side-by-side candidate such as `dino_obulk_exact`. The
candidate should reproduce the full accepted incumbent except for how the ocean
bulk heat-flux tendency is applied during positive-time rollout.

For the candidate only:

- remove the ocean bulk sensible heat-flux forcing from the composed
  primitive-equation explicit tendency;
- after the existing dynamics, horizontal diffusion, theta recentering, and
  Coriolis split for each positive inner step, apply a step filter to the
  lowest sigma-layer temperature;
- diagnose the same ocean weight, thermal anchor, lowest-layer wind speed, and
  capped exchange rate used by the accepted incumbent;
- update lowest-layer temperature with
  `T_next = T_anchor + (T_next - T_anchor) * exp(-ocean_weight * rate * dt)`,
  then cap the net single-step increment using the accepted cap;
- leave vorticity, divergence, `log_surface_pressure`, tracers, residual
  corrections, output variables, DFI setup, and all evaluation contracts
  unchanged;
- keep DFI reversible by excluding this irreversible lower-boundary source from
  the time-reversed DFI initializer, matching the accepted ocean-flux treatment;
- fall back exactly to the accepted incumbent source path if the split
  diagnostics are missing, nonfinite, or shape-incompatible.

The first implementation should not add SST, sea-ice weighting, stability
functions, land fluxes, drag, or coefficient tuning.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for the selector flag,
    exact split filter, forcing composition switch, and short-alias factory.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` for factory export.
  - `src/dynamaxx/dycore/registry.py` for the short model alias.
  - Focused tests under `tests/dycore/models/dinosaur/` plus
    `tests/dycore/test_registry.py`.
- Registry changes:
  - Add exactly one short side-by-side alias, for example `dino_obulk_exact`.
- API changes:
  - None. `DycoreModel.forecast`, forecast inputs, output variables, target
    variables, lead times, metrics, and split definitions remain fixed.
- Tests to update:
  - Verify zero ocean weight and zero exchange rate reproduce the incumbent.
  - Verify the exact update moves temperature monotonically toward the accepted
    anchor and is identical when temperature equals the anchor.
  - Verify the accepted single-step increment cap and finite fallback.
  - Verify non-temperature state leaves and output variable lists are unchanged
    by the split filter.
  - Verify the candidate factory differs from the incumbent only by the exact
    ocean-flux split selector and short name.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 2-15 if explicit source/cap ordering is damping or
    lagging the accepted ocean lower-boundary thermal correction.
  - Small secondary `geopotential_500` or `mean_sea_level_pressure` gains if the
    lower-column thermal state becomes less biased without changing wind.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be nearly neutral because no momentum
    tendency or wind diagnostic changes.
  - Land points should remain on the accepted incumbent path.
- Possible regressions:
  - The explicit RK treatment may have been empirically compensating for other
    missing physics, so an exact relaxation can be neutral or slightly worse.
  - A split source can alter operator-ordering error relative to the accepted
    composed tendency.

## Risks

- Numerical stability:
  - Low to moderate. The exact update is locally stable for positive exchange
    rates, but the source ordering changes a newly accepted mechanism.
- Compute cost:
  - Low. It adds local arithmetic per inner step and no new transforms,
    variables, workers, lead times, or output volume.
- Data leakage:
  - Low. It uses only the accepted lead-zero anchor, static land-sea mask, and
    forecast state.
- Physical plausibility:
  - High for the isolated source. Bulk sensible heat flux is a relaxation-like
    exchange, and exponential/source splitting is a standard numerical treatment
    for separable source terms.
- Rollback complexity:
  - Low. Remove one selector, one split-filter helper, one factory/export, one
    registry alias, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_obulk_exact`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_obulk_exact --workers 4`.
  - Support requires primary-score delta at least `+0.002` against the cached
    accepted incumbent, clean diagnostics, and no fixed early-lead or
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_obulk_exact --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show that source
    exactness is not a material remaining error source for the accepted ocean
    flux. Any early `2m_temperature`, MSLP, or Z500 guardrail failure would show
    the split ordering is too intrusive.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/decision.md`
  accepted the ocean bulk sensible heat-flux forcing with large fixed-protocol
  gains.
- Dynamaxx history:
  `.logbook/history/2026-06-22_07-54-50_sst-sea-ice-ocean-flux-anchor/decision.md`
  rejected changing the ocean anchor to SST/sea-ice with only
  `+0.0000030296370109317294` iteration delta; this proposal therefore keeps
  the accepted anchor and changes only source integration.
- Local source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_OceanBulkSensibleHeatFluxForcingSigma` as a capped explicit lowest-layer
  temperature tendency.
- Strang, G. 1968. "On the construction and comparison of difference schemes."
  SIAM Journal on Numerical Analysis, 5, 506-517.
  https://doi.org/10.1137/0705041
- Hochbruck, M. and Ostermann, A. 2010. "Exponential integrators." Acta
  Numerica, 19, 209-286. https://doi.org/10.1017/S0962492910000048
- Fairall, C. W., Bradley, E. F., Hare, J. E., Grachev, A. A., and Edson, J. B.
  2003. "Bulk Parameterization of Air-Sea Fluxes: Updates and Verification for
  the COARE Algorithm." Journal of Climate.
  https://doi.org/10.1175/1520-0442(2003)016%3C0571:BPOASF%3E2.0.CO;2
- NOAA PMEL Ocean Climate Stations flux documentation identifies the COARE bulk
  algorithm as estimating sensible heat flux from near-surface atmospheric and
  oceanic variables. https://www.pmel.noaa.gov/ocs/flux-documentation

## Researcher Notes

This is not a duplicate of the failed SST/sea-ice boundary-anchor variant
because it deliberately keeps the accepted lower-boundary temperature anchor and
ice/ocean weighting unchanged. It is also distinct from the rejected exact
weak-Held-Suarez integration experiment: that proposal changed an older analytic
thermal relaxation source, while this one targets the newly accepted
wind-dependent ocean heat-flux source and its per-step cap ordering.

## Evaluator Notes

### 2026-06-22T10:07:23Z

Decision: move to `staging`, ranked first among the two new proposals but not
ready for the next full iteration.

This is the stronger new proposal because it is tightly scoped to the accepted
ocean-bulk sensible heat-flux path and avoids the recently rejected SST/sea-ice
anchor change. Local source inspection confirms the accepted implementation is
a composed explicit tendency with a reusable ocean weight, thermal anchor, wind
diagnostic, finite fallback, and step cap, so an exact split filter is
implementable without changing the forecast API or fixed protocols.

The concern is expected score leverage. The accepted parameters are deliberately
weak: `DEFAULT_INNER_STEP_SECONDS = 900.0`,
`_OCEAN_BULK_SHF_MIN_EFOLDING_DAYS = 6.0`, and
`_OCEAN_BULK_SHF_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN = 0.05`. With those
scales, explicit Runge-Kutta treatment of the linear relaxation should be very
close to an exponential update unless the cap is active over large areas. The
prior exact-integration weak-HS experiment was clean but failed iteration with a
`-0.00017975977845352542` primary-score delta, which is negative evidence for
spending the next full evaluation on source-integration exactness alone.

External checks support the broad numerical and physical basis, but not the
claim that this should clear the fixed `+0.002` iteration gate in the current
incumbent. Hochbruck and Ostermann 2010 review exponential integrators for
stiff or highly oscillatory problems:
https://www.cambridge.org/core/journals/acta-numerica/article/exponential-integrators/8ED12FD70C2491C4F3FB7A0ACF922FCD.
Fairall et al. 2003 and NOAA PMEL support bulk air-sea fluxes as a physical
lower-boundary exchange, but the accepted model already contains that process:
https://journals.ametsoc.org/view/journals/clim/16/4/1520-0442_2003_016_0571_bpoasf_2.0.co_2.xml
and https://www.pmel.noaa.gov/ocs/flux-documentation.

Keep staged as a low-risk follow-up if later changes increase the ocean heat
flux rate, loosen the cap, lengthen the inner step, or reveal cap-ordering
artifacts. If promoted later, require a short alias such as `dino_obulk_exact`,
an exact incumbent fallback path, no SST/sea-ice anchor changes, and focused
tests proving zero ocean weight, zero exchange rate, and non-temperature state
leaves reproduce the incumbent path.
