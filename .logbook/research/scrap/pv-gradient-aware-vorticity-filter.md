---
schema_version: 1
slug: pv-gradient-aware-vorticity-filter
title: Add a PV-Gradient-Aware Vorticity Filter
status: scrap
created_at: 2026-06-20T02:44:49Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/filtering.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a PV-Gradient-Aware Vorticity Filter

## Hypothesis

The current incumbent improved mass fields through off-centered semi-implicit
gravity-wave damping and improved near-surface fields through residual memory,
but long-lead `geopotential_500`, MSLP, and 10 m wind errors still grow. A
plain horizontal diffusion filter damps all resolved structures by wavenumber,
including balanced Rossby-wave vorticity gradients that help maintain synoptic
phase. Prior broad diffusion and log-pressure filters were either negative or
too weak, suggesting that any new filter must distinguish balanced potential
vorticity structure from small-scale rotational noise.

A dry PV-gradient-aware vorticity filter should damp only high-wavenumber
rotational noise where a local dry isentropic PV proxy indicates weak or noisy
PV gradients, while sparing coherent extratropical PV-gradient zones. This may
reduce late noisy wind/mass coupling without erasing planetary and synoptic wave
phase.

## Mechanism

Register a side-by-side candidate extending the incumbent with a suffix such as
`pv_vorticity_filter`. Preserve the incumbent DFI, weak Held-Suarez forcing,
log-pressure and hydrostatic initialization, exact Coriolis split, theta
tendency, theta recentering, off-centered SIL3, scale-separated surface residual
memory, target variables, lead schedule, and fixed protocols.

For positive-time rollout only, add a step filter after the existing horizontal
diffusion and before theta recentering:

- compute nodal absolute vorticity from the next state and the grid Coriolis
  parameter;
- compute a dry lower/mid-tropospheric static-stability proxy from the incumbent
  sigma-layer potential temperature fields;
- form a bounded dry PV-like proxy `absolute_vorticity * static_stability` on
  sigma layers, using finite fallback to the incumbent state;
- derive a smooth mask that is near zero where the large-scale meridional PV
  gradient is coherent and near one where high-wavenumber PV curvature/noise is
  large relative to the large-scale gradient;
- apply an additional very weak high-wavenumber taper to `vorticity` only under
  that mask, leaving total wavenumber `n <= 10` unchanged;
- leave divergence, temperature variation, log surface pressure, tracers,
  `sim_time`, DFI filters, Coriolis rotation, residual correction, and output
  packing unchanged;
- fall back to the incumbent next state if the PV proxy, mask, or modal
  transform is nonfinite.

The filter should use fixed constants before scoring: protected wavenumber,
taper width, maximum per-step vorticity damping, and PV-gradient mask
thresholds. It is not a Leith viscosity, not a full-state diffusion retune, and
not a mass/log-pressure smoother.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the PV-gradient vorticity-filter candidate.
- API changes:
  - None. The public forecast contract and fixed evaluation protocols remain
    unchanged.
- Tests to update:
  - Unit-test that protected low wavenumbers are unchanged.
  - Verify only `vorticity` changes in the filter and all other state leaves
    are preserved.
  - Verify coherent large-scale PV-gradient synthetic fields receive less
    damping than noisy high-wavenumber perturbations.
  - Verify finite fallback returns the incumbent next state.
  - Verify the candidate factory preserves every incumbent option except the new
    positive-time vorticity filter.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 5 to 15 if noisy
    rotational modes are feeding balanced mass-field phase errors.
  - `10m_u_component_of_wind` at medium and late leads if reduced rotational
    noise improves low-level wind phase without touching the screen-wind
    diagnostic.
- Expected neutral metrics:
  - `2m_temperature` should remain close to the incumbent because thermal
    tendency, theta recentering, and residual memory are unchanged.
  - Day-1 behavior should be near neutral because low modes are protected and
    the maximum per-step damping is small.
- Possible regressions:
  - Excess vorticity damping can weaken cyclones and degrade 10 m wind or Z500.
  - A crude dry PV proxy may misidentify useful tropopause gradients or tropical
    wave structures as noise.

## Risks

- Numerical stability:
  - Low to moderate. The filter is bounded and positive-time only, but it edits
    a prognostic rotational field every step.
- Compute cost:
  - Low to moderate. It adds local PV-proxy diagnostics plus modal/nodal work
    during rollout, but no extra trajectories or output volume.
- Data leakage:
  - None. The filter uses only forecast state, fixed grid geometry, and fixed
    constants.
- Physical plausibility:
  - Moderate. PV gradients organize balanced atmospheric flow, but this is a
    pragmatic dry proxy rather than a full Ertel PV inversion.
- Rollback complexity:
  - Low. Remove one filter option/helper, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that remaining
    late-lead errors are not controlled by PV-aware rotational noise filtering.
    Any early Z500, MSLP, or 10 m wind guardrail failure would show the filter
    damages balanced wave structure.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected broad hyperdiffusion, so this proposal avoids a uniform full-state
  diffusion retune.
- Dynamaxx history:
  `.logbook/history/2026-06-18_13-26-11_symmetric-horizontal-diffusion-split/decision.md`
  found symmetric diffusion splitting effectively neutral, motivating a more
  state-selective mechanism.
- Hoskins, B. J., McIntyre, M. E., and Robertson, A. W. 1985. On the use and
  significance of isentropic potential vorticity maps. Quarterly Journal of the
  Royal Meteorological Society. https://doi.org/10.1002/qj.49711147002
- Frederiksen, J. S. and Davies, A. G. 1997. Eddy viscosity and stochastic
  backscatter parameterizations on the sphere for atmospheric circulation
  models. Journal of the Atmospheric Sciences.
  https://doi.org/10.1175/1520-0469(1997)054%3C2475:EVASBP%3E2.0.CO;2
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is distinct from staged `leith-nonlinear-eddy-viscosity`, which uses a
flow-dependent eddy viscosity strength, and from staged `vorticity-sparing-
horizontal-diffusion`, which broadly spares rotational flow. This proposal uses
a dry PV-gradient proxy to decide where extra high-wavenumber vorticity damping
is allowed. It also avoids the recent low-mode mass residual and log-pressure
smoother negative evidence by not editing saved mass outputs or prognostic
`log_surface_pressure`.

## Evaluator Notes

### 2026-06-20T02:48:14Z

Decision: move to `scrap`; dominated by active staged diffusion/vorticity
proposals and not recommended for implementation.

The mechanism is scientifically plausible in broad terms, but it is a poor
fresh addition to the active queue. The staged `vorticity-sparing-horizontal-
diffusion` proposal already tests the cleaner isolated question of whether the
incumbent over-damps rotational flow while preserving divergence,
temperature, log-surface-pressure, and tracer damping. Staged
`leith-nonlinear-eddy-viscosity` already covers the more ambitious
state-dependent dissipation family using an established enstrophy-cascade
closure. This PV-gradient idea sits between them: it is more complex and less
directly testable than the fixed vorticity-sparing filter, but less standard
and harder to calibrate than the Leith closure.

Local evidence also argues against promoting another diffusion-family variant
now. Prior scale-selective hyperdiffusion regressed strongly, symmetric
horizontal diffusion splitting was effectively neutral/slightly negative, and
the active staging queue already contains spectral, vertical, component-wise,
and state-dependent diffusion tests. The proposed dry PV-like proxy would edit a
prognostic rotational field every step, and misclassifying balanced PV-gradient
zones could damage the exact Z500/MSLP/10 m wind phase that the proposal seeks
to preserve. Because simpler staged experiments dominate the same hypothesis
surface with lower implementation risk, this should be scrapped rather than
kept as another staged fallback.
