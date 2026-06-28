---
schema_version: 1
slug: zonal-mean-theta-recentering
title: Preserve Layerwise Zonal-Mean Theta During Rollout
status: ready
created_at: 2026-06-19T05:06:32Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
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

# Preserve Layerwise Zonal-Mean Theta During Rollout

## Hypothesis

The current incumbent's accepted theta recentering preserves one area-weighted
global mean per sigma layer. That controls a useful thermodynamic zero mode, but
the current iteration CSV still shows strongly negative average
`2m_temperature` skill and long-lead MSLP degradation. A remaining error source
may be drift in the meridional, zonal-mean thermal structure rather than only a
single global layer mean. The zonal-mean temperature field sets thermal-wind
shear and baroclinic thickness gradients, so preserving the previous step's
layerwise zonal-mean dry potential temperature should better protect large-scale
thermal balance while still leaving eddy anomalies free to evolve.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_zonal_recenter`.
Preserve the incumbent initialization, DFI, weak Held-Suarez forcing, theta-form
thermal tendency, area spectral resolution, symmetric exact Coriolis split,
stability-aware near-surface residual correction, Richardson 10 m wind
diagnostic, output variables, lead selection, and fixed evaluation protocols.

Replace the rollout-only global theta recentering filter with a zonal-mean
variant:

- diagnose previous-step and next-step nodal pressure, full temperature, and
  dry potential temperature exactly as the accepted theta recentering filter
  does;
- compute longitude means at each latitude, sigma layer, and step, using the
  existing quadrature latitude weights for finite checks but not collapsing the
  latitude dimension;
- compute a latitude-dependent theta increment that preserves the previous
  step's layerwise zonal-mean theta at every latitude;
- convert that theta increment to a temperature increment with the next-state
  pressure-to-theta conversion factor, averaged over longitude only;
- apply a conservative latitude smoother to the increment, for example a
  low-pass modal projection retaining only zonal wavenumber zero and low total
  wavenumbers, so grid-scale latitudinal striping is not introduced;
- add only the zonal-mean temperature increment to
  `temperature_variation`, leaving eddy temperature modes, vorticity,
  divergence, `log_surface_pressure`, tracers, and `sim_time` unchanged;
- apply the filter only in positive-time rollout, not in the DFI loop;
- fall back to the incumbent global theta recentering result if pressure,
  theta, conversion factors, or modal reconstruction are nonfinite.

This preserves the forecast contract. The model still emits the same
`WeatherState` variables and lead dimensions under the same fixed protocols.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, output channels, target variables, lead
    times, splits, and metrics remain unchanged.
- Tests to update:
  - Unit-test zonal-mean theta preservation on synthetic fields with a
    latitudinal theta gradient.
  - Verify only zonal-mean temperature modes change and non-temperature state
    leaves remain unchanged.
  - Verify the candidate preserves every incumbent option except the new
    recentering selector.
  - Verify finite fallback to the incumbent global recentering path.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3 to 15 if meridional thermal drift contributes to
    the incumbent's negative screen-temperature skill after residual decay.
  - `mean_sea_level_pressure` and `geopotential_500` at medium and long leads
    if preserving zonal-mean theta improves hydrostatic thickness and
    thermal-wind consistency.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be near neutral at early leads because the
    wind state, exact Coriolis split, and Richardson 10 m diagnostic are
    unchanged directly.
  - Lead-zero fields remain on the incumbent path because the filter is
    positive-time rollout only.
- Possible regressions:
  - The accepted global mean correction may be empirically better because it
    leaves zonal thermal gradients unconstrained.
  - Latitude-dependent thermal increments can alter pressure gradients and
    cause `10m_u_component_of_wind`, MSLP, or Z500 guardrail regressions.

## Risks

- Numerical stability:
  - Low to moderate. The filter is a bounded temperature-mode correction, but it
    preserves more structure than the accepted global zero-mode filter.
- Compute cost:
  - Low. It adds longitude means and one modal reconstruction per inner step,
    with no resolution, lead, output, or worker-count changes.
- Data leakage:
  - None. It uses only previous and next forecast states, sigma geometry,
    quadrature weights, and fixed constants.
- Physical plausibility:
  - Moderate. Zonal-mean thermal structure is dynamically important through
    hydrostatic thickness and thermal-wind balance, but exact preservation at
    every latitude is stronger than a conservation law.
- Rollback complexity:
  - Low. Remove one filter option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_zonal_recenter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_zonal_recenter --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_zonal_recenter --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that zonal-mean
    thermal drift is not a useful remaining error mode. Any early wind, MSLP, or
    Z500 guardrail failure would show the latitudinal correction disrupts
    balanced dynamics.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_theta_layer_mean_recenter_step_filter`, which currently preserves one
  area-weighted dry-theta mean per layer.
- Dynamaxx history:
  `.logbook/history/2026-06-19_00-02-28_theta-zero-mode-thermal-recentering/decision.md`
  accepted global theta recentering with iteration delta
  `+0.003997358805283291` and validation delta `+0.005185083087329123`.
- Dynamaxx research:
  `.logbook/research/staging/mass-weighted-theta-recentering.md` records a
  different global moment refinement; this proposal instead preserves zonal
  structure by latitude.
- Polichtchouk, I., Malardel, S., and Diamantakis, M. 2020. "Potential
  temperature as a prognostic variable in hydrostatic semi-implicit
  semi-Lagrangian IFS." ECMWF Technical Memorandum 869.
  https://www.ecmwf.int/en/elibrary/81180-potential-temperature-prognostic-variable-hydrostatic-semi-implicit-semi
- Held, I. M. and Suarez, M. J. 1994. "A Proposal for the Intercomparison of the
  Dynamical Cores of Atmospheric General Circulation Models." Bulletin of the
  American Meteorological Society, 75, 1825-1830.
  https://www.gfdl.noaa.gov/bibliography/related_files/ih9401.pdf
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to
  Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is intentionally a follow-up to the accepted theta recentering, but it is
not a duplicate. The accepted mechanism preserves a single global layer mean;
the active `mass-weighted-theta-recentering` proposal changes the weights of
that same global moment. This proposal changes the moment itself by preserving
zonal-mean theta structure as a function of latitude, targeting meridional
thermal-gradient drift and thermal-wind balance.

It is also not a repeat of rejected `theta-skew-symmetric-scalar-advection` or
`theta-consistent-held-suarez-forcing`: it does not alter scalar advection or
Held-Suarez forcing. The recent negative result for `theta-consistent-held-
suarez-forcing` is evidence against weak thermal-forcing bookkeeping changes,
so this proposal instead targets a resolved large-scale thermal mode.

## Evaluator Notes

### 2026-06-19T05:10:10Z

Decision: move to `ready`; ranked 1 of 3 new proposals.

This is the strongest current proposal because it extends the only recent
mechanism with a clearly material score gain: accepted layer-mean theta
recentering improved iteration by `+0.003997358805283291` and validation by
`+0.005185083087329123` with clean diagnostics. The new constraint is not a
duplicate of that accepted zero-mode filter or the staged
`mass-weighted-theta-recentering`: it tests whether meridional zonal-mean theta
drift, not just a global layer mean or weighting choice, is a remaining thermal
balance error.

The implementation can reuse the accepted rollout-only recentering hook and
remain side-by-side, with no forecast API, fixed protocol, output variable, or
DFI changes. It also offers a useful falsification: if preserving zonal-mean
theta is neutral or harmful, future theta recentering should retreat to weaker
global-moment refinements.

Risks are real. Exact latitude-by-latitude zonal-mean preservation is stronger
than a conservation law and can perturb pressure gradients and late wind skill,
which is already the accepted incumbent's largest remaining regression. The
Orchestrator should enforce a low-mode latitude smoother, finite fallback to
the accepted global recentering path, positive-time rollout only, and tests
showing that only zonal-mean thermal increments are applied.
