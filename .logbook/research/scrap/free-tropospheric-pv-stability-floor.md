---
schema_version: 1
slug: free-tropospheric-pv-stability-floor
title: Apply a Weak Free-Tropospheric PV Stability Floor
status: scrap
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

# Apply a Weak Free-Tropospheric PV Stability Floor

## Hypothesis

The incumbent has strong near-surface diagnostics and thermal anchoring, but it
can still develop balanced-flow errors in Z500 and MSLP through small
free-tropospheric static-stability inversions or unrealistically weak
isentropic stratification. Prior theta variance and zonal-mean fixes were
either neutral or too aggressive because they preserved broad moments. A local,
weak potential-vorticity stability floor can act only where both static
stability and absolute-vorticity context indicate an unphysical balanced-flow
defect, leaving normal baroclinic variance and surface diagnostics alone.

## Mechanism

Add a side-by-side positive-time step filter, for example suffixing the
incumbent with `_pv_stability_floor`. Preserve the full incumbent equation,
DFI, weak-HS rates, analysis-HS offset, Coriolis split, off-centering,
scale-separated residuals, target variables, and fixed evaluation protocols.

For the candidate only:

- after the accepted positive-time filters, diagnose dry potential temperature
  on sigma layers and finite-difference vertical static stability;
- diagnose absolute vorticity from modal vorticity plus planetary vorticity;
- apply a tiny local theta adjustment only in free-tropospheric layers, for
  example sigma centers between 0.2 and 0.8, where static stability falls below
  a fixed floor and absolute vorticity has the expected hemispheric sign;
- conserve each affected column's mass-weighted mean theta by applying equal
  and opposite bounded adjustments to adjacent layers;
- leave vorticity, divergence, log surface pressure, tracers, DFI initialization,
  residual correction, and output diagnostics unchanged except through the
  adjusted thermal state;
- fall back to the incumbent next state if any diagnosed stability or adjusted
  theta is nonfinite.

This is not a theta-variance preservation filter, not a zonal-mean recentering
rule, and not a PV-gradient vorticity filter. It only repairs local
free-tropospheric static-stability defects that are inconsistent with balanced
PV sign.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - possibly `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` for
    reusable theta/stability helpers
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate only.
- API changes:
  - None.
- Tests to update:
  - Unit-test no-op behavior for stable columns and for tropical/weak-vorticity
    columns.
  - Unit-test column-mean theta conservation and bounded finite fallback.
  - Verify non-thermal state leaves are unchanged by the filter.
  - Verify the candidate factory preserves every incumbent flag except the PV
    stability-floor selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if small
    static-stability defects are feeding balanced thickness and pressure errors.
  - `2m_temperature` should be mostly neutral because the filter excludes the
    boundary layer and the accepted residual path is unchanged.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close unless mass-field balance
    changes feed back onto low-level winds.
- Possible regressions:
  - Real baroclinic growth can involve sharp vertical theta gradients; even a
    weak floor can damp useful thermal structure.
  - Local theta adjustment can alter hydrostatic thickness enough to regress
    MSLP or Z500 if the floor is too active.

## Risks

- Numerical stability:
  - Low to moderate. The adjustment is bounded and column-neutral in theta, but
    it changes the positive-time thermal state.
- Compute cost:
  - Low; local vertical algebra plus existing transforms already available in
    the adapter.
- Data leakage:
  - None; it uses only current forecast state and fixed physical constants.
- Physical plausibility:
  - Moderate. Ertel PV and static stability are standard balanced-flow
    diagnostics, but this is a numerical safeguard rather than a full PV
    inversion.
- Rollback complexity:
  - Low.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that local
    PV/static-stability defects are not a material remaining error source. Any
    early wind, MSLP, or Z500 guardrail failure would show the safeguard is too
    intrusive.

## Citations

- Hoskins, B. J., McIntyre, M. E., and Robertson, A. W. 1985. On the use and
  significance of isentropic potential vorticity maps. Quarterly Journal of the
  Royal Meteorological Society. https://doi.org/10.1002/qj.49711147002
- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Dynamaxx history:
  `.logbook/history/2026-06-20_12-57-53_baroclinic-theta-variance-guard/decision.md`
  found broad theta variance preservation neutral; this proposal uses local
  static-stability and PV-sign gating instead.
- Dynamaxx research:
  `.logbook/research/scrap/pv-gradient-aware-vorticity-filter.md` targeted
  vorticity filtering; this proposal leaves vorticity unchanged and adjusts
  only bounded free-tropospheric theta pairs.

## Researcher Notes

This proposal is intentionally narrower than previous theta-family guards. It
does not preserve zonal means, global variance, or all-layer monotonicity. It
acts only on local free-tropospheric static-stability failures under a PV-sign
gate, which changes the expected evidence relative to rejected broad
thermal-moment filters.

## Evaluator Notes

### 2026-06-20T22:47:09Z

Decision: move to `scrap`; ranked third of the three triaged proposals.

The physical vocabulary is credible, but the local model-selection evidence is
poor for spending a run on another positive-time stability/filter edit. The
recent baroclinic theta-variance guard was numerically clean yet essentially
neutral to slightly negative, indicating that the accepted theta mean
recentering plus analysis-HS equilibrium is not presently limited by that class
of layerwise thermal repair. The scrapped PV-gradient vorticity filter also
shows that adding dry PV-proxy gating around a prognostic filter is a complex,
hard-to-calibrate variant in a family already crowded by staged diffusion and
vorticity ideas.

This proposal is narrower than broad theta variance preservation, but it still
edits the prognostic thermal state every positive-time step using fixed floors,
layer masks, vorticity-sign gates, and bounded pair adjustments. That puts the
risk directly on hydrostatic thickness, MSLP, Z500, and wind balance. The
Orchestrator's recent evidence also penalizes broad divergence/gravity-wave
damping, rollout filters, pressure-gradient/dealiasing, and thermal-wind/wind
diagnostic families unless materially different; this idea is materially
different in details but not enough in risk profile or expected signal. It
should require read-only diagnostics showing frequent accepted-incumbent
free-tropospheric static-stability defects before being reconsidered.
