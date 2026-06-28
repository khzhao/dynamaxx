---
schema_version: 1
slug: mass-weighted-theta-recentering
title: Preserve Mass-Weighted Layer-Mean Theta During Recentering
status: ready
created_at: 2026-06-19T01:47:32Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
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

# Preserve Mass-Weighted Layer-Mean Theta During Recentering

## Hypothesis

The accepted theta layer-mean recentering preserves area-weighted layer means of
dry potential temperature. That was strong enough to improve both fixed
selection splits, but an area mean does not represent the conserved layer heat
content on a sigma grid when surface pressure varies horizontally. A
mass-weighted recentering target, using local sigma-layer dry mass proportional
to surface pressure, should preserve the useful theta-drift control while
better respecting column mass and hydrostatic thickness. This may reduce
pressure and geopotential side effects without changing output diagnostics or
evaluation protocols.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_mass_weighted`.
Preserve the incumbent initialization, DFI isolation, weak Held-Suarez forcing,
theta-form thermodynamic tendency, symmetric exact Coriolis split, horizontal
diffusion, stability-aware near-surface residual correction, Richardson 10 m
wind diagnostic, output variables, WeatherBench2 splits, lead times, metrics,
and deterministic gates.

For the candidate only, replace the area-weighted theta recentering filter with
a mass-weighted variant:

- diagnose previous and next sigma-layer pressure and full temperature exactly
  as the accepted theta recentering filter does;
- compute dry potential temperature from full temperature and local sigma-layer
  pressure;
- use quadrature weights multiplied by a dry-mass proxy proportional to local
  surface pressure and fixed sigma-layer thickness;
- preserve each layer's previous mass-weighted theta mean by changing only the
  horizontally uniform modal component of the next state's
  `temperature_variation`;
- compute the uniform temperature increment using the same mass weights applied
  to the next-state temperature-to-theta conversion factor;
- leave nonzero thermal modes, vorticity, divergence, `log_surface_pressure`,
  tracers, `sim_time`, Coriolis split, output interpolation, near-surface
  residual correction, and 10 m diagnostic unchanged;
- apply the filter only to positive-time rollout, not inside time-reversed DFI;
- fall back to the accepted area-weighted next state if mass weights, pressure,
  theta, conversion factors, or corrected modal temperature are nonfinite.

This is a trajectory-level thermodynamic-balance proposal, not an output-only
MSLP or Z500 adapter. It keeps the accepted recentering idea but changes the
conserved horizontal moment from area mean to layer dry-mass mean.

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
  - None. `DycoreModel.forecast`, inputs, outputs, target variables, lead times,
    splits, metrics, and deterministic gates stay unchanged.
- Tests to update:
  - Unit-test area-weighted and mass-weighted recentering separately on
    synthetic fields with horizontally varying surface pressure.
  - Verify the mass-weighted filter preserves the layer mass-weighted theta
    mean while changing only the modal zero component of `temperature_variation`.
  - Verify it leaves nonzero temperature modes and all non-temperature state
    leaves unchanged.
  - Verify DFI filter lists remain on the incumbent path and positive-time
    rollout receives the candidate filter.
  - Verify the candidate factory preserves every incumbent option except the
    recentering weighting selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at early to medium leads if
    area-mean theta preservation slightly misweights columns over different
    surface pressures.
  - `2m_temperature` should keep most of the accepted recentering gain if
    layer-mean theta drift remains the useful controlled mode.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to the incumbent because the
    candidate does not change the 10 m diagnostic, wind state, or residual
    correction directly.
  - Lead-zero outputs should remain unchanged except for normal incumbent
    residual behavior because the filter is positive-time rollout only.
- Possible regressions:
  - The accepted area-weighted recentering may be empirically better aligned
    with the fixed spectral representation, and mass weighting can make the
    uniform correction respond too strongly to surface-pressure anomalies.
  - If the accepted thermal gain depends on preserving geometric rather than
    mass-weighted layer means, the primary score may regress.

## Risks

- Numerical stability:
  - Low to moderate. The operation is still a bounded zero-mode thermal
    correction, but the weighting changes every inner step with the surface
    pressure field.
- Compute cost:
  - Low. It adds local mass-weighted reductions and no extra forecast steps,
    resolution, workers, or output volume.
- Data leakage:
  - None. It uses only previous and next forecast states, sigma geometry,
    quadrature weights, and fixed physical constants.
- Physical plausibility:
  - Moderate to high. Potential temperature is the dry thermodynamic variable,
    and on sigma coordinates layer heat content should be weighted by local
    column mass rather than only area.
- Rollback complexity:
  - Low. Remove one weighting option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_mass_weighted`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_mass_weighted --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_mass_weighted --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that mass-weighted
    theta preservation is not a better moment constraint than the accepted area
    mean. Any early MSLP, Z500, or 10 m wind guardrail failure would show that
    the mass-weighted correction disrupts balance.

## Citations

- Citation or source:
  - Dynamaxx source:
    `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
    `_theta_layer_mean_recenter_step_filter`, currently preserving area-weighted
    layer theta means through a modal zero-temperature increment.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_00-02-28_theta-zero-mode-thermal-recentering/decision.md`
    accepted theta recentering with iteration delta
    `+0.003997358805283291` and validation delta `+0.005185083087329123`.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_17-43-05_global-mean-pressure-anchor/decision.md`
    found a pure global pressure-mode anchor stable but too weak, indicating
    that mass-balance proposals need a stronger thermodynamic mechanism.
  - Polichtchouk, I., Malardel, S., and Diamantakis, M. 2020. Potential
    temperature as a prognostic variable in hydrostatic semi-implicit
    semi-Lagrangian IFS. ECMWF Technical Memorandum 869.
    https://www.ecmwf.int/en/elibrary/81180-potential-temperature-prognostic-variable-hydrostatic-semi-implicit-semi
  - Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
    conserving vertical finite-difference scheme and hybrid vertical
    coordinates. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
  - Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP
    and climate models. Journal of Computational Physics.
    https://doi.org/10.1016/j.jcp.2006.08.016
  - ECMWF. Dry mass versus total mass conservation in the IFS.
    https://www.ecmwf.int/sites/default/files/elibrary/2019/19114-dry-mass-versus-total-mass-conservation-ifs.pdf

## Researcher Notes

This is intentionally a close follow-up to the accepted theta recentering, but
it is not a duplicate. The accepted filter preserves geometric layer means. The
new candidate tests a different conservation target, mass-weighted layer theta,
which is more directly connected to heat content and hydrostatic thickness on a
sigma grid. It is not the rejected global pressure anchor, because it does not
edit `log_surface_pressure` directly and is not a single zero-wavenumber mass
mode. It is also not the scrapped dry static-stability adjustment, because it
does not perform local column mixing or monotonicity repair.

## Evaluator Notes

### 2026-06-19T01:51:18Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

The mechanism is scientifically plausible and preserves the forecast contract:
on a sigma grid, a pressure-weighted dry-mass proxy is a different conserved
moment from the accepted area-weighted layer theta mean, and it could help
pressure or geopotential balance without output-only metric targeting. The
implementation surface is also moderate because the accepted
`_theta_layer_mean_recenter_step_filter` already provides a clean hook and the
candidate can remain rollout-only outside DFI.

Keep it staged rather than ready because it is a close follow-up to the
just-accepted theta recentering. The current incumbent already gained
`+0.003997358805283291` on iteration and `+0.005185083087329123` on validation
from area-weighted theta recentering, while the limiting regression is now late
10 m wind rather than pressure or geopotential. Replacing the weighting with a
surface-pressure-dependent moment may be physically cleaner, but it could also
erase the accepted thermal gain or perturb mass fields enough to lose the
small remaining margin over the fixed thresholds.

Orchestrator enforcement if selected later: treat this as a replacement of the
accepted recentering moment, not an additional filter stacked after it; keep it
positive-time only and excluded from DFI; do not add MSLP/Z500 output adapters;
predeclare mass weights and finite fallback behavior; and require exact tests
that only the thermal zero mode is changed.

### 2026-06-21T06:22:22Z

Decision: move to `ready`; ranked 1 of the currently reviewed ideas.

Ready is empty, and the new proposal batch is weaker than this staged candidate.
The recent history now contains several negative or subthreshold analysis-HS
follow-ups, a failed surface wind diagnostic, a subthreshold spectral taper, a
neutral vector-wind initialization, and a negative fixed-pressure variant. That
history argues against another scored-channel diagnostic, another simple
analysis-HS knob change, or a direct pressure tendency edit as the next
experiment.

This idea remains mechanistically close to a known accepted gain: theta
zero-mode recentering improved both iteration and validation, while mass
weighting changes only the conserved horizontal moment used by that accepted
filter. It is lower risk than the new dry-static-energy proposal because it
replaces the accepted recentering target instead of stacking a second global
thermodynamic constraint. Implement it, if selected, only as a side-by-side
candidate on the current incumbent named with the `_mass_weighted` suffix above,
and preserve the current off-centered rollout, scale-separated surface
residual, and analysis-HS equilibrium behavior unchanged.
