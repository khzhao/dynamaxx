---
schema_version: 1
slug: divergence-selective-gravity-wave-damping
title: Add Divergence-Selective Gravity-Wave Damping
status: ready
created_at: 2026-06-16T19:54:27Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add Divergence-Selective Gravity-Wave Damping

## Hypothesis

The current incumbent already combines DFI, near-surface diagnostic residuals,
and weak wind-sparing thermal relaxation. Its accepted score record shows that
weak thermal relaxation improved temperature and mass fields, but its largest
remaining guardrail cost is long-lead `10m_u_component_of_wind`. A further
all-state diffusion change would be poorly targeted because the earlier
scale-selective hyperdiffusion candidate degraded the fixed selection score and
spent wind margin.

A more selective mechanism is to damp only the divergent horizontal component
represented by the primitive-equation `divergence` prognostic variable. This
targets high-frequency gravity-wave and compressional adjustment noise left
after initialization while leaving vorticity, temperature, log surface pressure,
and passive tracers unchanged by the added filter. If the remaining Z500/MSLP
growth is partly driven by divergent imbalance rather than useful rotational
flow, the candidate should improve medium- and long-lead mass fields without
the broad wind degradation seen in all-variable damping.

## Mechanism

Add an optional step filter after the existing incumbent step construction. The
filter should apply the repository's horizontal diffusion scaling only to
`primitive_equations.State.divergence`, then rebuild the state with the original
`vorticity`, `temperature_variation`, `log_surface_pressure`, `tracers`, and
`sim_time` leaves. Use one fixed side-by-side setting for selection:

- candidate model name: `dinosaur_dfi_surface_residual_weak_hs_div_damp`
- preserve incumbent DFI, near-surface residual correction, weak thermal
  Held-Suarez relaxation, default inner step, and default all-state filter
- add a weak divergence-only top-mode e-folding time of `24.0` hours
- use fourth-order horizontal diffusion semantics by setting the operator order
  to `2`, matching the incumbent's existing horizontal diffusion order

This is not a forecast-contract change. The candidate still returns one
deterministic trajectory with the same WeatherBench2 variables, leads, metrics,
and splits.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - registry tests under `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate name
    `dinosaur_dfi_surface_residual_weak_hs_div_damp`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` and all output variables
    remain unchanged.
- Tests to update:
  - Verify the factory preserves incumbent flags and enables only the new
    divergence-selective damping flag.
  - Unit-test the filter on a small `primitive_equations.State` so divergence
    changes while vorticity, temperature, log surface pressure, tracers, and
    `sim_time` are preserved.
  - Verify registry exposure and a finite, non-JIT smoke forecast for the
    candidate.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at leads day 5-15 if
    divergent imbalance contributes to the incumbent's long-lead mass-field
    growth.
  - Primary score should improve through broad medium- and long-lead RMSE
    reductions rather than a single lead.
- Expected neutral metrics:
  - `2m_temperature` should be nearly neutral because the added filter does not
    directly alter thermal tendencies.
  - Early day 1-5 means should remain close to the incumbent because DFI and the
    accepted weak thermal forcing are unchanged.
- Possible regressions:
  - `10m_u_component_of_wind` can regress if useful irrotational flow is damped.
    This is the key guardrail risk because the incumbent already has a long-lead
    wind regression margin of roughly 8 percent against its previous baseline.
  - Z500 can regress if the divergent component is physically meaningful
    baroclinic adjustment rather than noise.

## Risks

- Numerical stability:
  - Low to moderate. The filter is dissipative and uses existing modal
    diffusion machinery, but selective state reconstruction must preserve tree
    shapes exactly.
- Compute cost:
  - Low. The filter adds one modal scaling of the divergence array per inner
    step and does not increase lead count or evaluation size.
- Data leakage:
  - Low. The filter uses fixed numerical coefficients and no validation truth,
    future state, climatology, or target-specific fitting.
- Physical plausibility:
  - Moderate. Divergence damping is a standard dynamical-core stabilization
    idea, but excessive damping can suppress real gravity-wave adjustment.
- Rollback complexity:
  - Low. The implementation can be isolated behind one adapter flag and one
    side-by-side factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_div_damp`.
  - Require clean diagnostics and finite outputs.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_div_damp --workers 4`.
  - Compare only against `dinosaur_dfi_surface_residual_weak_hs` records by
    exact model name.
  - Require primary delta at least `+0.002`, clean diagnostics, no early
    day 1-5 mean RMSE regression above 2 percent, and no variable-lead RMSE
    regression above 10 percent.
- Validation gate:
  - Run validation only if iteration promotes:
    `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_div_damp --workers 4`.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with sub-threshold primary gain, or a
    wind-regression guardrail failure, would show that selective divergence
    damping does not improve the incumbent under the fixed WeatherBench2
    selection protocol.

## Citations

- Whitehead, J. P., Jablonowski, C., Rood, R. B., and Lauritzen, P. H. 2011.
  "A Stability Analysis of Divergence Damping on a Latitude-Longitude Grid."
  Monthly Weather Review, 139(9), 2976-2993.
  https://doi.org/10.1175/2011MWR3607.1
- Ullrich, P. A., Jablonowski, C., Kent, J., Lauritzen, P. H., Nair, R.,
  Reed, K. A., Zarzycki, C. M., et al. 2017. "DCMIP2016: a review of
  non-hydrostatic dynamical core design and intercomparison of participating
  models." Geoscientific Model Development, 10, 4477-4509.
  https://doi.org/10.5194/gmd-10-4477-2017
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  stores the horizontal flow in separate `vorticity` and `divergence`
  prognostic fields, making a divergence-selective filter locally implementable.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  and `src/dynamaxx/dycore/models/dinosaur/filtering.py` already provide
  modal horizontal diffusion filters and Runge-Kutta step-filter composition.

## Researcher Notes

This is not a duplicate of rejected `scale-selective-hyperdiffusion`: that
candidate changed broad horizontal damping and degraded the fixed score, while
this proposal adds only a weak filter on the divergent component and leaves the
rotational vorticity field untouched. It is also distinct from `global-mean-
pressure-anchor`, which constrained one zero-wavenumber pressure coefficient and
was effectively neutral. The mechanism here acts on spatially structured
divergent adjustment modes rather than on a single conserved mass mode.

The proposal deliberately does not tune Held-Suarez coefficients, change the
fixed evaluation protocol, introduce ensembles, or run golden. If accepted for
implementation, it should be scored as exactly one side-by-side candidate.

## Evaluator Notes

2026-06-16T19:57:10Z - Move to `ready`.

This is the best next single experiment for the current incumbent
`dinosaur_dfi_surface_residual_weak_hs`. The mechanism is targeted: it damps
only the prognostic divergence leaf, leaving vorticity, temperature,
log-surface-pressure, tracers, DFI, near-surface residual correction, weak
thermal Held-Suarez forcing, the forecast contract, and the fixed evaluation
protocol unchanged. Source inspection confirms the model state separates
vorticity and divergence, and the existing horizontal diffusion filter can be
wrapped to rebuild only the divergence field.

This is not a duplicate of rejected `scale-selective-hyperdiffusion`, which
changed broad damping behavior and failed the iteration score plus early 10 m
wind gate. The key risk is still wind: the accepted weak-Held-Suarez incumbent
already has its largest validation variable-lead RMSE regression in long-lead
10 m zonal wind, about `8.25%` versus a `10%` cap. The proposal acknowledges
that risk and keeps the damping fixed, weak, side-by-side, and falsifiable
under the normal fast and iteration gates.

Ranked recommendation: 1. implement
`divergence-selective-gravity-wave-damping` next as the only ready iteration 13
candidate; 2. keep `vertical-advection-suppression` staged as a broader
ablation if this candidate fails cleanly or if later evidence points to
vertical-transport error.
