---
schema_version: 1
slug: fourth-order-imex-rk-rollout
title: Use the Existing Fourth-Order Low-Storage IMEX Rollout
status: staging
created_at: 2026-06-18T00:39:09Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use the Existing Fourth-Order Low-Storage IMEX Rollout

## Hypothesis

The current incumbent uses `time_integration.imex_rk_sil3`, which is third-order
for explicit terms and second-order for implicit terms. A simple 600 s time-step
change was stable but slightly negative, so remaining temporal error is unlikely
to be solved by a one-value time-step sweep. The vendored Dinosaur code already
contains a Carpenter-Kennedy style five-stage fourth-order low-storage
Runge-Kutta / Crank-Nicolson stepper. Using that existing higher-order explicit
quadrature at the same 900 s inner step may reduce nonlinear phase and amplitude
error without changing resolution, forcing, initialization, filters, or the
forecast contract.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_rk4`.
Preserve the incumbent model state, DFI, weak Held-Suarez forcing, near-surface
residual correction, log-pressure and hydrostatic initialization, horizontal
diffusion filter, T80 truncation, 900 s inner step, vertical advection, output
variables, and evaluation protocols.

Add a small adapter option for the time-stepper used in `_trajectory_function`:

- keep `"sil3"` as the default incumbent path;
- select `time_integration.crank_nicolson_rk4` for the candidate forward step;
- pass the same selected stepper into `digital_filter_initialization` so the DFI
  spinup uses the same dynamics as the rollout;
- keep the existing step filters after each complete RK step;
- do not change `inner_step_seconds`, `horizontal_diffusion_order`, diffusion
  timescale, DFI span, DFI cutoff, target variables, or lead times.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` only if exposing
    a stable stepper lookup is cleaner than direct adapter selection
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_rk4`.
- API changes:
  - None. `DycoreModel.forecast` and all WeatherBench2 fixed protocol inputs and
    outputs remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves all incumbent options except the
    selected stepper.
  - Verify a non-JIT smoke forecast is finite and has the same variables/shapes
    as the incumbent.
  - Unit-test the stepper selector rejects unknown names and leaves the incumbent
    default exactly on `imex_rk_sil3`.
  - Add registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and long leads if
    temporal phase error in nonlinear mass/wind coupling is a remaining source
    of drift.
  - `10m_u_component_of_wind` may improve if higher-order explicit advection
    reduces accumulated wind phase error without extra damping.
- Expected neutral metrics:
  - Early `2m_temperature` should remain close to incumbent because accepted
    near-surface residual and weak-HS thermal forcing are unchanged.
- Possible regressions:
  - The RK4/CN composition may have a different stability envelope for this
    fast-slow split and could fail the fast gate.
  - Additional stages may interact with the existing diffusion filter so that
    the effective damping differs from the incumbent even at the same step size.
  - The primary delta may be small if spatial, forcing, or missing-physics error
    dominates temporal truncation.

## Risks

- Numerical stability:
  - Moderate. The stepper exists in source, but has not been scored in this
    adapter with the accepted DFI and weak-HS path.
- Compute cost:
  - Moderate. The five-stage stepper should be more expensive than SIL3, but it
    does not change grid size, lead count, or worker count and fits the reported
    48 CPU / 175 GiB / 4 L4 resource envelope.
- Data leakage:
  - None. This uses no truth data, fitted parameters, validation feedback, or
    metric changes.
- Physical plausibility:
  - Moderate to high as a numerical discretization improvement; it is not a new
    physical parameterization.
- Rollback complexity:
  - Low. Remove one stepper option, one factory, one registry entry, and focused
    tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_rk4`.
  - Require finite forecasts and zero diagnostic issues before any long run.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_rk4 --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the incumbent, clean diagnostics, no early day 1-5 RMSE guardrail failure,
    and no variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_rk4 --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A fast nonfinite result would show the stepper is unstable in this adapter.
    A clean negative or near-zero iteration delta would show temporal scheme
    order is not a material remaining error source under the fixed protocol.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  constructs the forward step with `time_integration.imex_rk_sil3`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  already defines `crank_nicolson_rk4` with Carpenter-Kennedy coefficients and
  documents `imex_rk_sil3` as the current fast-slow IMEX scheme.
- History: `.logbook/history/2026-06-16_18-41-23_six-hundred-second-inner-step/decision.md`
  rejected a simple 600 s time-step change with iteration delta
  `-0.0002549284092885351`, so this proposal changes the integration scheme
  rather than sweeping the same step size family.
- History: `.logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing/decision.md`
  found a clean but sub-threshold `+0.0007881219001772966` signal from a
  nonlinear tendency cleanup, motivating a stronger numerical mechanism that is
  not another filter.
- Whitaker, J. S. and Kar, S. K. 2013. Implicit-Explicit Runge-Kutta Methods
  for Fast-Slow Wave Problems. Monthly Weather Review.
  https://doi.org/10.1175/MWR-D-13-00132.1
- Carpenter, M. H. and Kennedy, C. A. 1994. Fourth-order 2N-storage Runge-Kutta
  schemes. NASA Technical Memorandum 109112.
  https://ntrs.nasa.gov/citations/19940028444
- Canuto, C., Hussaini, M. Y., Quarteroni, A., and Zang, T. A. 2007. Spectral
  Methods: Evolution to Complex Geometries and Applications to Fluid Dynamics.
  Springer. https://doi.org/10.1007/978-3-540-30728-0

## Researcher Notes

This is not a duplicate of `six-hundred-second-inner-step`, because it keeps the
accepted 900 s step and changes the available low-storage RK/CN scheme. It is
also distinct from rejected hyperdiffusion, divergence damping, and nonlinear
tendency dealiasing because it does not add dissipation or modal filtering.

The proposal is deliberately not a time-step or time-scheme sweep. It names one
source-supported candidate, keeps fixed protocols unchanged, and expects the
Evaluator to rank it lower than cheaper initialization ideas if runtime becomes
the dominant concern.

## Evaluator Notes

### 2026-06-18T00:43:07Z

Decision: move to `staging`.

Source inspection confirms `time_integration.crank_nicolson_rk4` exists and
uses the documented Carpenter-Kennedy low-storage coefficients, while
`digital_filter_initialization` already accepts the ODE solver as an argument.
The proposal is therefore implementable with a small adapter selector and a
side-by-side registry entry.

Hold it behind the DFI component experiment because the expected gain is less
focused and the cost is higher. The five-stage stepper would change both DFI
spinup and every rollout step, increasing runtime and broadening the numerical
surface. A prior `600 s` inner-step change was clean but slightly negative
(`-0.0002549284092885351`), and nonlinear tendency cleanup was clean but
sub-threshold (`+0.0007881219001772966`). Those results do not falsify this
stepper proposal, but they make a full time-discretization change a weaker next
implementation than the cheaper vorticity-preserving DFI increment.

### 2026-06-18T01:56:57Z

Decision: keep in `staging`, ranked below the exact weak-HS ready item and the
exact Coriolis staged fallback.

The vorticity-preserving DFI increment has now failed cleanly with a negative
iteration delta, so the previous reason to hold RK4 behind that DFI component
test is obsolete. However, the broader ranking remains conservative: this
proposal changes every positive-time step and DFI spinup step, uses a more
expensive five-stage scheme, and is still weakened by the clean negative
`600 s` time-step result plus the sub-threshold nonlinear-tendency cleanup.

Keep it staged because source inspection still confirms
`crank_nicolson_rk4` and the DFI solver hook are available, making the
implementation straightforward if cheaper source-splitting ideas fail. It is
not the next best run under the current evidence.

### 2026-06-18T03:02:30Z

Decision: keep in `staging`, ranked below the exact Coriolis ready item.

The exact weak-HS thermal-source split failed cleanly and is no longer ahead
of this proposal. That new evidence mainly argues against very small
source-formulation refinements; it does not resolve whether temporal
truncation in the full dynamics is a remaining error source.

Keep RK4 staged because it is still implementable with existing
`crank_nicolson_rk4` and DFI solver hooks, but it changes every DFI and rollout
step and is expected to cost more than the Coriolis split. Prior time/numerics
experiments remain weak evidence for only small effect sizes: the 600 s step
candidate was slightly negative and nonlinear-tendency dealiasing was clean
but sub-threshold. This is a later fallback if the targeted wind-phase
candidate fails or if future diagnostics point more strongly to time
discretization error.

### 2026-06-18T04:36:51Z

Decision: keep in `staging`.

The latest accepted Coriolis split makes this a later fallback rather than the
best next run. Source inspection still confirms `crank_nicolson_rk4` exists and
`digital_filter_initialization` accepts a solver hook, so the candidate is
implementable. The risk is that it changes every DFI and positive-time rollout
step, costs more than SIL3, and would need careful integration with the accepted
rollout-only exact Coriolis split rather than reverting to the older
pre-Coriolis incumbent named in the original proposal.

Prior numerical-timing evidence remains weak for a large score gain: the 600 s
inner-step candidate was slightly negative and nonlinear-tendency dealiasing was
positive but sub-threshold. Keep this staged below the symmetric Coriolis split
and the more targeted geopotential diagnostic.

### 2026-06-18T06:07:51Z

Decision: keep in `staging`.

I updated the front matter target model to the accepted Strang incumbent. The
proposal remains implementable because `time_integration.crank_nicolson_rk4`
exists and DFI accepts a solver hook, but it is still too broad for the next
implementation. It would change every DFI and rollout step, increase runtime,
and need explicit composition with the accepted exact Coriolis Strang wrapper.

The new DFI-Coriolis and symmetric-diffusion proposals are better split-order
tests with smaller surface area. Prior timing/numerics evidence also remains
weak for a large gain: the 600 s inner-step candidate was slightly negative and
nonlinear tendency dealiasing was positive but below promotion. Keep RK4 as a
later fallback only if narrower split-order ideas fail cleanly.

### 2026-06-18T07:28:25Z

Decision: keep in `staging`, ranked as a late broad-numerics fallback.

The new proposals do not make this infeasible, but they do push it farther
down the queue. `crank_nicolson_rk4` and the DFI solver hook remain available,
yet this candidate would still change every DFI and positive-time rollout
step, increase runtime, and require careful composition with the accepted exact
Coriolis Strang wrapper.

The latest DFI-Coriolis rejection and the earlier 600 s step rejection both
argue against spending the next iteration on a broad time-discretization
change. Keep this staged only after more targeted initialization,
geopotential-output, tendency-filtering, and diffusion-placement tests are no
longer better candidates.

### 2026-06-18T08:53:53Z

Decision: keep in `staging`; rank as a late broad-numerics fallback.

The new proposals do not change feasibility: `crank_nicolson_rk4` and the DFI
solver hook remain available, and the candidate can still be registered
side-by-side. The ranking remains low because it changes every DFI and
positive-time rollout step, increases runtime, and must be composed carefully
with the accepted exact Coriolis Strang wrapper.

Recent scoring continues to argue against broad numerics as the next move. The
600 s step was slightly negative, DFI-Coriolis consistency was only
sub-threshold positive, sigma-native initialization was negative, and the
smooth tendency cleanup was positive but below promotion. Keep this as a later
fallback only after localized output/residual and operator-placement ideas fail
cleanly.

### 2026-06-18T10:25:42Z

Decision: keep in `staging`; current staged rank 7 as a late broad-numerics
fallback.

The candidate remains implementable because the source has
`crank_nicolson_rk4` and DFI accepts a solver hook. It is not related to the
failed surface-wind residual family. The ranking stays low because it changes
every DFI and positive-time rollout step, increases runtime, and would need
careful composition with the accepted exact-Coriolis Strang wrapper.

Recent evidence continues to favor localized tests first: DFI-Coriolis
consistency was clean but subthreshold, sigma-native hydrostatic initialization
was negative, and the prior 600 s step experiment was slightly negative. Use
this only after cheaper initialization, output-diagnostic, split-placement, and
transport-product-form candidates have been scored.

### 2026-06-18T11:49:28Z

Decision: keep in `staging`, staged fallback rank 8.

The candidate remains feasible because the RK4/CN stepper and DFI solver hook
already exist, but new continuity and diffusion-ordering candidates are more
localized and cheaper to interpret. Keep RK4 as a late broad-numerics fallback:
it changes every DFI and positive-time rollout step, increases runtime, and is
weakened by the slightly negative 600 s step result plus subthreshold
nonlinear-tendency cleanup.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 9.

The current queue still has several narrower tests with clearer attribution.
This RK4/CN rollout remains feasible, but it changes the whole time integrator
and would need careful composition with the accepted Strang Coriolis split.
Keep it as a late fallback behind output diagnostics, transient spinup,
diffusion placement/heating, anti-aliasing, and localized thermodynamic
quadrature tests.
