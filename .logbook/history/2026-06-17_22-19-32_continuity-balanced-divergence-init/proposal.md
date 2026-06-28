---
schema_version: 1
slug: continuity-balanced-divergence-init
title: Continuity-Balanced Divergence Initialization
status: ready
created_at: 2026-06-17T21:12:20Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Continuity-Balanced Divergence Initialization

## Hypothesis

The incumbent already benefits from digital filter initialization and
hydrostatic/log-pressure thermodynamic initialization, but the initial
pressure-level wind interpolation can still leave a sigma-coordinate mass
continuity residual. A minimal correction to the divergent wind component that
reduces the initial log-surface-pressure tendency may remove part of the
remaining fast gravity-wave adjustment without reconstructing vorticity,
temperature, pressure edges, or pole rows.

## Mechanism

After `weather_state_to_dinosaur_state` forms vorticity, divergence,
temperature variation, log surface pressure, and tracers, compute the sigma
mass-continuity residual using the same diagnostic relation as
`primitive_equations.compute_diagnostic_state_sigma`: the vertical integral of
`divergence + u dot grad(log_surface_pressure)` that drives the initial
log-surface-pressure tendency. Subtract a vertically uniform, layer-thickness
weighted divergence correction so the column-integrated tendency is closer to
zero at initialization. Apply the correction only to divergence and only before
DFI; leave vorticity, log surface pressure, humidity tracers, and temperature
unchanged.

To avoid repeating the rejected broad Helmholtz wind initialization, the
correction should be spatially smooth or modal-tail filtered, should preserve
the vorticity field exactly, and should solve only the continuity residual. DFI
then operates on the adjusted initial state using the incumbent settings.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` if a reusable
    residual helper is cleaner than duplicating diagnostic logic
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
- Registry changes:
  - Add a factory such as
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced`.
- API changes:
  - None. The forecast API and fixed WeatherBench2 protocols remain unchanged.
- Tests to update:
  - Verify the candidate is registered.
  - Verify the correction leaves vorticity and tracer arrays unchanged.
  - Verify the corrected initial state's column-integrated continuity residual
    is reduced on a deterministic synthetic state.
  - Verify forecast output shapes and finiteness on existing fixtures.

## Expected Metric Movement

- Expected improvements:
  - Early `mean_sea_level_pressure` and `geopotential_500` may improve if the
    incumbent still performs an initial mass-balance adjustment after pressure
    and wind interpolation.
  - Long-lead mass-field drift may improve through a cleaner balanced start.
- Expected neutral metrics:
  - `2m_temperature` should be mostly neutral because temperature
    initialization and the near-surface residual correction are unchanged.
- Possible regressions:
  - `10m_u_component_of_wind` may regress if the divergent correction changes
    low-level flow in regions where the analysis wind was already optimal for
    the fixed metric.
  - Aggregate skill may be neutral if DFI already removes this residual.

## Risks

- Numerical stability:
  - Medium. The correction is intended to reduce an initial tendency, but any
    wind-component adjustment can excite imbalance if applied too broadly.
- Compute cost:
  - Low. It adds one diagnostic pass at initialization, not a per-step solve.
- Data leakage:
  - None. The correction uses only the initial state and model equations.
- Physical plausibility:
  - Medium. Enforcing a continuity balance is physically motivated, but the
    vertically uniform correction is an approximation to a full normal-mode
    balance.
- Rollback complexity:
  - Low. It is a side-by-side flag and registry entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Require clean diagnostics, no RMSE guardrail failures, and at least
    `+0.002` iteration primary improvement.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4` only
    after iteration promotion.
  - Require clean diagnostics, no RMSE guardrail failures, and at least
    `+0.001` validation primary improvement.
- Outcome that would falsify the hypothesis:
  - A neutral result at roundoff scale, similar to passive humidity DFI bypass
    or pole taper, would indicate DFI already handles this residual.
  - A wind or mass-field guardrail failure would show the correction is too
    intrusive.

## Citations

- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
  digital filter. Monthly Weather Review, 120, 1019-1034.
  https://journals.ametsoc.org/view/journals/mwre/120/6/1520-0493_1992_120_1019_iothmu_2_0_co_2.xml
- Daley, R. 1981. Normal mode initialization. Reviews of Geophysics, 19,
  450-468. https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/RG019i003p00450
- Baer, F. and Tribbia, J. J. 1977. On complete filtering of gravity modes
  through nonlinear initialization. Monthly Weather Review, 105, 1536-1539.
  https://journals.ametsoc.org/view/journals/mwre/105/12/1520-0493_1977_105_1536_ocfogm_2_0_co_2.xml
- ECMWF. 1980. A review of the normal mode initialization method.
  https://www.ecmwf.int/sites/default/files/elibrary/1980/9149-review-normal-mode-initialization-method.pdf

## Researcher Notes

This is low confidence because `balanced-digital-filter-initialization` is
already accepted and because `helmholtz-wind-initialization` failed badly.
The distinct mechanism is narrow continuity residual removal: only divergence
is corrected, vorticity is preserved, and the objective is the model's own
initial log-surface-pressure tendency rather than a full wind re-projection,
pressure-edge remap, or pole-row cleanup.

## Evaluator Notes

### 2026-06-17_21-15-13Z

Decision: `staging`.

This is a physically coherent initialization-only idea, and it is more focused
than the rejected Helmholtz wind initialization because it leaves vorticity,
tracers, temperature, and log surface pressure unchanged. It also targets a
known sigma-coordinate continuity diagnostic that already exists in
`compute_diagnostic_state_sigma`, so it is implementable without changing the
forecast API or fixed evaluation protocols.

It is not the best immediate candidate. Recent history is strongly negative
for wind-control changes: Helmholtz wind initialization produced a large
primary-score regression and severe mass/geopotential guardrail failures, while
the pole-only wind taper was too small to matter. This proposal changes the
divergent wind component globally at initialization, and the vertically uniform
correction is an approximation rather than a balanced normal-mode solve. Stage
it for a future pass if the Orchestrator wants another narrow initialization
experiment, ideally with a clearly bounded correction amplitude and explicit
tests showing reduced column-integrated residual without materially changing
low-level winds.

### 2026-06-17_22-18-32Z

Decision: `ready`.

The new `nonlinear-tendency-exponential-dealiasing` result does not directly
falsify this proposal. That candidate was clean and slightly positive, but its
effect size was below the fixed iteration promotion threshold
(`+0.0007881219001772966` versus required `+0.002`). The lesson is that a
conservative numerical cleanup can be too small, not that every bounded
initialization residual correction is exhausted.

Promote this staged idea because it is the only current concrete proposal that
is distinct from the just-rejected dealiasing run and can be evaluated under
the existing fast, iteration, and validation gates. The mechanism is narrow:
alter only the initial modal divergence before DFI, preserve vorticity,
temperature, tracers, and log surface pressure exactly, and target the existing
sigma-coordinate continuity relation
`divergence + u dot grad(log_surface_pressure)`. The existing adapter and
diagnostic code provide a bounded implementation path without forecast API,
metric, split, target-variable, or lead-time changes.

The promotion is not a broad endorsement of wind rewriting. Prior
`helmholtz-wind-initialization` history remains strong negative evidence for
global wind-control changes, and the proposal should be implemented only with
explicit amplitude bounds and tests. Required bounds for the Implementer:
register a side-by-side candidate only; apply the correction only once during
`weather_state_to_dinosaur_state` before DFI; keep the correction vertically
layer-thickness weighted and spatially smooth or modal-tail filtered; cap the
correction relative to the incumbent divergence scale; verify vorticity,
temperature, tracers, and log surface pressure are unchanged; verify the
column-integrated continuity residual is reduced on a deterministic synthetic
state; and verify forecast finiteness and shapes. If these bounds cannot be
met cleanly, the idea should return to staging or scrap rather than expand into
a broader wind initialization experiment.
