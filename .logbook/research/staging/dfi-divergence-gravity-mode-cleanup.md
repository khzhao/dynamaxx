---
schema_version: 1
slug: dfi-divergence-gravity-mode-cleanup
title: Apply DFI-Only Divergence Gravity-Mode Cleanup
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

# Apply DFI-Only Divergence Gravity-Mode Cleanup

## Hypothesis

Digital filter initialization is already accepted in the incumbent, but the
initial state can still retain small high-wavenumber divergent gravity-wave
components after pressure-level to sigma projection, hydrostatic temperature
initialization, and Coriolis splitting. Prior positive-time damping and broad
solver changes were either too weak or harmful. A DFI-only, divergence-only
spectral cleanup can remove initialization noise while leaving the accepted
positive-time rollout dynamics untouched.

The intended signal is early `geopotential_500` and MSLP spinup reduction
without applying persistent divergence damping during days 1 to 15.

## Mechanism

Add an opt-in candidate that modifies only the state returned by digital filter
initialization:

- keep the incumbent DFI time span, cutoff, equation, rollout solver,
  offcentering, Coriolis Strang split, weak-HS equilibrium, theta tendency,
  theta mean recentering, and surface residual correction unchanged;
- after DFI produces its initialized state, apply a very weak high-wavenumber
  exponential filter to `divergence` only;
- preserve vorticity, temperature variation, log surface pressure, passive
  tracers, and `sim_time` exactly from the DFI output;
- use a taper that is zero or near-zero for low total wavenumbers and active
  only near the spectral edge, with finite fallback to the unfiltered DFI state;
- do not add any positive-time rollout filter beyond the incumbent horizontal
  diffusion and existing step filters.

Suggested registered name:
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_dfi_div_clean`.

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
  - Verify the DFI cleanup changes only the divergence leaf.
  - Verify low wavenumbers are preserved and high wavenumbers are no larger in
    magnitude after cleanup.
  - Verify nonfinite cleanup output falls back to the unfiltered DFI state.
  - Verify the rollout filter list and incumbent flags are unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 1 to 5 if residual
    divergent gravity-wave spinup remains after incumbent DFI.
  - Possible small `2m_temperature` gains through reduced early pressure and
    thickness adjustment.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be less exposed than in wind-initialization
    proposals because vorticity and rotational wind are preserved, and the
    cleanup is DFI-only.
  - Long leads should stay close to the incumbent because the positive-time
    equation and filters are unchanged.
- Possible regressions:
  - Divergence contains balanced ageostrophic flow as well as gravity-wave
    noise; excessive filtering could degrade MSLP phase or wind evolution.

## Risks

- Numerical stability:
  - Low if the filter is weak, high-wavenumber-only, and finite-guarded.
- Compute cost:
  - Negligible. It adds one modal scaling after DFI initialization.
- Data leakage:
  - None. It uses only the initialized model state generated from the same
    initial analysis.
- Physical plausibility:
  - Moderate to good. DFI is designed to suppress high-frequency imbalance, and
    divergent gravity modes are a plausible initialization-noise component.
- Rollback complexity:
  - Low. Remove one DFI wrapper option, one helper, one factory/export, one
    registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_dfi_div_clean`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run fixed `iteration` against the cached incumbent baseline.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failure.
- Validation gate:
  - Run fixed `validation` only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with the same
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta would show that residual high-wavenumber
    divergent imbalance is not material after the incumbent DFI. Any early wind
    or MSLP guardrail failure would show the filter removed balanced divergence.

## Citations

- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
  digital filter. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Jablonowski, C. and Williamson, D. L. 2006. A baroclinic instability test
  case for atmospheric model dynamical cores. Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1256/qj.06.12
- ECMWF IFS Documentation CY49R1, Part III: Dynamics and Numerical Procedures,
  describes hydrostatic spectral dynamics and initialization-relevant
  divergence-vorticity formulations. https://www.ecmwf.int/sites/default/files/elibrary/112024/81625-ifs-documentation-cy49r1-part-iii-dynamics-and-numerical-procedures.pdf
- Dynamaxx history:
  `.logbook/history/2026-06-16_19-57-46_divergence-selective-gravity-wave-damping/decision.md`
  rejected positive-time divergence damping; this proposal is DFI-only.
- Dynamaxx history:
  `.logbook/history/2026-06-18_00-44-09_vorticity-preserving-dfi-increment/decision.md`
  warns against broad DFI state merging; this proposal preserves all non-
  divergence leaves and does not merge raw and filtered states.

## Researcher Notes

This is not a duplicate of `divergence-selective-gravity-wave-damping`,
`equatorial-gravity-wave-divergence-sponge`, or
`vertical-normal-mode-gravity-wave-filter`. Those are positive-time or broader
gravity-wave controls. It is also not a repeat of
`vorticity-preserving-dfi-increment` or `low-mode-preserving-dfi-initialization`
because it does not blend raw and DFI states; it applies a narrow high-mode
cleanup to the DFI divergence leaf only.

## Evaluator Notes

### 2026-06-21T00:50:17Z

Decision: move to `staging`; not selected for the next model-selection run.

The proposal is physically coherent and narrower than prior positive-time
divergence damping, but it is still in a recently weak family: divergence
damping produced a clean negative result, and partial DFI state changes also
failed after clean diagnostics. This version is DFI-only and divergence-only,
so it is not a direct duplicate, but the current logbook has no read-only
evidence that the incumbent retains harmful high-wavenumber divergent gravity
noise after accepted DFI.

Keep staged as a plausible fallback if diagnostics later show a residual
divergent imbalance at initialization. Do not promote ahead of the smooth
analysis-HS taper without such evidence, because it adds new initialization
filter machinery and risks removing balanced ageostrophic divergence while
testing a weaker measured signal.
