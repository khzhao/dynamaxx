---
schema_version: 1
slug: semi-lagrangian-vertical-transport
title: Use Split Semi-Lagrangian Vertical Transport
status: scrap
created_at: 2026-06-16T22:26:22Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Use Split Semi-Lagrangian Vertical Transport

## Hypothesis

The rejected `vertical-advection-suppression` candidate showed that simply
removing explicit sigma-dot vertical advection is unstable: the fixed fast gate
became nonfinite by lead hour 264. That is negative evidence against ablation,
not against changing the vertical transport discretization.

The current incumbent preserves centered explicit vertical advection for wind,
temperature, and passive tracers inside the sigma-coordinate primitive
equations after DFI, weak Held-Suarez relaxation, near-surface residuals,
log-pressure initialization, and layer-mean hydrostatic initialization. A split
semi-Lagrangian vertical remap should retain vertical
transport while reducing sensitivity to vertical Courant errors and pressure-
level-to-sigma projection noise. This is a different, stabilizing mechanism from
removal: the vertical transport remains active, but it is represented by the
local semi-Lagrangian helper already present in the Dinosaur source.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_semilag_vadv`
with these fixed choices:

- preserve accepted DFI, weak wind-sparing Held-Suarez thermal relaxation,
  near-surface residuals, log-pressure initialization, layer-mean hydrostatic
  initialization, default T80 truncation, 900 s inner step, and default
  horizontal diffusion
- preserve the accepted DFI path for initialization rather than passing the
  semi-Lagrangian remap through the time-reversed DFI filter
- during the scored forward rollout, build the primitive-equation object with
  centered explicit vertical advection disabled to avoid double-counting
- after each forward IMEX inner step, apply
  `primitive_equations.semi_lagrangian_vertical_advection_step_sigma` with the
  positive forecast time step

This keeps the forecast contract unchanged. It does not introduce new variables,
new metrics, new data, validation tuning, or golden selection.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_semilag_vadv`.
- API changes:
  - None.
- Tests to update:
  - Verify the candidate preserves incumbent DFI, weak Held-Suarez, near-surface
    residuals, default step size, and default spectral wavenumbers.
  - Verify the forward rollout path applies one semi-Lagrangian vertical remap
    per inner step and disables centered vertical advection in the rollout
    equation.
  - Verify the DFI initializer is not given the semi-Lagrangian remap as a
    time-reversed filter.
  - Add a non-JIT smoke forecast test for finite shape-preserving output.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and long leads if
    centered sigma-coordinate vertical transport is amplifying column-structure
    error after pressure-level initialization.
  - `2m_temperature` may improve if lower-tropospheric thermal structure is
    less noisy after the split vertical remap.
  - `10m_u_component_of_wind` may remain neutral or improve if vertical momentum
    transport is stabilized without adding drag.
- Expected neutral metrics:
  - Day-1 fields should remain near the incumbent because DFI, horizontal
    dynamics, thermal relaxation, residual diagnostics, step size, and spectral
    truncation are unchanged.
- Possible regressions:
  - Operator splitting may introduce phase or amplitude error in baroclinic
    development.
  - The semi-Lagrangian interpolation can be more diffusive than the centered
    explicit tendency, especially near sharp vertical gradients.
  - Runtime may increase enough that the Evaluator should rank this behind
    lower-cost ideas unless the vertical-transport mechanism is considered
    scientifically important.

## Risks

- Numerical stability:
  - Moderate. Semi-Lagrangian vertical transport is generally stabilizing, but
    this candidate changes a core transport discretization in a model that
    already failed when vertical transport was removed.
- Compute cost:
  - Moderate. The remap adds vertical interpolation and diagnostic-state work
    every inner step. The proposal assumes the reported `--workers 4` resource
    budget on this machine.
- Data leakage:
  - Low. The mechanism uses only the forecast state and fixed source-code
    numerics.
- Physical plausibility:
  - Moderate to high. The proposal keeps vertical advection as a physical
    process, unlike the rejected suppression candidate, and uses a standard
    atmospheric-model transport family.
- Rollback complexity:
  - Low to moderate. The side-by-side factory can be removed cleanly, but the
    adapter needs a small step-construction branch.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_semilag_vadv`.
  - Require finite forecasts and zero diagnostic issues. A nonfinite fast
    artifact should scrap the idea immediately.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_semilag_vadv --workers 4`.
  - Compare against exact incumbent records for
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
  - Support for the hypothesis is primary-score delta at least `+0.002` with
    clean diagnostics and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_semilag_vadv --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - Fast nonfinite behavior, large runtime blow-up, a clean but negative
    iteration delta, or any early mass/wind guardrail failure would show that
    split semi-Lagrangian vertical transport is not an improvement for this
    incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  provides `semi_lagrangian_vertical_advection_step_sigma` and uses
  `include_vertical_advection` to control centered sigma-dot vertical tendencies.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  constructs the current IMEX SIL3 stepper and supports wrapping step functions
  before trajectory generation.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lin, S.-J. and Rood, R. B. 1996. Multidimensional Flux-Form
  Semi-Lagrangian Transport Schemes. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2
- Whitaker, J. S. and Kar, S. K. 2013. Implicit-Explicit Runge-Kutta Methods
  for Fast-Slow Wave Problems. Monthly Weather Review. https://doi.org/10.1175/MWR-D-13-00132.1
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This proposal explicitly accounts for the failed
`vertical-advection-suppression` experiment. The prior candidate disabled a real
transport process and became nonfinite; this proposal keeps vertical advection
active through a semi-Lagrangian remap. It should still be treated as higher
risk than `dry-dfi-weak-hs-split` because it changes the forecast rollout
discretization.

This is not a repeat of time-step sweeps, divergence or hyperdiffusion damping,
T120 resolution, pressure-grid/reference-profile/orography changes, mass or
near-surface output residual tuning, Held-Suarez coefficient changes, or passive
humidity diagnostic floors. It targets the remaining vertical-transport
numerics after those axes supplied negative evidence.

The Evaluator should scrap or stage this if implementation cost is judged too
high relative to the expected signal. It is included because the repository
already contains the semi-Lagrangian helper, and the failed removal experiment
specifically said future vertical-transport proposals need a separate
stabilizing mechanism.

## Evaluator Notes

2026-06-16T22:29:56Z - Move to `staging`; rank 2 of 2 for iteration 17.

This is plausible but not the next implementation target. Source inspection
confirms that the local helper
`primitive_equations.semi_lagrangian_vertical_advection_step_sigma` exists and
that the primitive-equation constructors expose `include_vertical_advection`.
The proposal is therefore implementable without a new dependency or forecast
API change. It is also scientifically distinct from the rejected
vertical-advection-suppression ablation because it retains vertical transport
through a replacement remap rather than simply removing the process.

The reason to stage rather than ready this proposal is risk and implementation
surface. The current incumbent already failed a closely related vertical
transport ablation at the fast gate: disabling explicit vertical advection
produced `nonfinite_forecast` and `nonfinite_metric` diagnostics, with the first
nonfinite records at lead hour `264` for all four target variables. This
proposal tries to avoid that failure with a semi-Lagrangian remap, but it still
requires disabling the centered vertical-advection tendency in the scored
forecast equation and inserting a new operator-split remap after every positive
IMEX inner step. That changes core forecast transport, can add interpolation
diffusion or phase error, and will likely cost more runtime than the dry-DFI
split. Prior rejected time-step, damping, pressure-grid, T120, and
vertical-advection-removal experiments all warn against spending a full
iteration on broad numerics changes when a lower-surface mechanism is available.

Negative and positive evidence were both accounted for. Accepted finite-output
infrastructure, DFI, near-surface residuals, and weak wind-sparing Held-Suarez
should all be preserved if this is revisited. The proposal is not a duplicate
of rejected hyperdiffusion, divergence damping, 600 s stepping, pressure-aware
sigma grid, terrain orography, humidity positivity, or T120 truncation. It does,
however, touch the same stability-sensitive vertical transport axis as the
fast-nonfinite suppression experiment, so it should not displace the lower-risk
dry-DFI split in `ready`.

Citations and evidence checked: local source
`src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` for the
semi-Lagrangian vertical remap and vertical-advection flag, local
`src/dynamaxx/dycore/models/dinosaur/time_integration.py` for the step wrapper
shape, and relevant history decisions/scoring notes for vertical-advection
suppression, pressure-grid, time-step, divergence-damping, T120, and accepted
incumbent components. The cited semi-Lagrangian literature supports the general
transport family, but the repository history does not yet show that this
particular split improves the fixed WeatherBench2 gates.

Implementation constraints if Orchestrator later promotes it: keep it
side-by-side as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_semilag_vadv`;
preserve
the incumbent DFI path and do not pass the semi-Lagrangian step through
time-reversed DFI; apply exactly one positive-time semi-Lagrangian remap per
forward inner step after the existing IMEX step and filters; avoid
double-counting by disabling centered vertical advection only for the forward
rollout equation; add a non-JIT finite smoke test and scrutinize fast artifacts
around 264h before any iteration run.

2026-06-16T23:39:41Z - Keep in `staging`; rank 2 of 2 for iteration 18.

The dry-DFI failure changes the queue state but not this proposal's risk rank.
`dry-dfi-weak-hs-split` was clean and stable yet far below the iteration
promotion threshold, so bookkeeping-only initialization changes should no longer
block more physical ideas. However, the newly triaged
`calendar-aware-solar-relaxation` proposal offers a lower implementation
surface, lower runtime cost, and a direct extension of the largest accepted
mechanism. It should be implemented before this vertical-transport remap.

This proposal remains plausible enough to stage rather than scrap. Local source
still supports feasibility: `primitive_equations.py` exposes
`semi_lagrangian_vertical_advection_step_sigma`, the primitive-equation
constructors expose `include_vertical_advection`, and `time_integration.py`
supports step wrapping before trajectory generation. The cited
Staniforth-Cote review supports semi-Lagrangian advection as a standard
atmospheric-model transport family with attention to accuracy, stability, and
efficiency. That is enough scientific support to keep the idea alive if the
lower-risk thermal-forcing queue is exhausted.

The reason it stays below ready is empirical risk. The incumbent has already
shown sensitivity on nearby broad-numerics axes: vertical-advection suppression
failed fast with nonfinite forecasts at 264 h, T120 truncation failed fast at
24 h, and 600 s stepping, divergence damping, pressure-grid changes, and
hyperdiffusion all regressed primary score or guardrails. This proposal is not
the same as removal, but it still disables centered vertical advection in the
forward equation and inserts an operator-split interpolation remap every inner
step. That is a larger rollback and runtime surface than the seasonal weak-HS
candidate and could add diffusion, phase error, or a new long-lead stability
failure.

If promoted later, keep the previous constraints unchanged: side-by-side model
only, no forecast API changes, no validation tuning, no DFI-time-reversed remap,
exactly one positive-time semi-Lagrangian remap per forward inner step, and a
hard stop on any fast nonfinite or large runtime blow-up.

2026-06-17T00:46:27Z - Keep in `staging`; rank 2 of 2 for iteration 19.

The ready queue was empty before this triage pass, but the new
`log-pressure-sigma-initialization` proposal is a lower-risk next experiment
than this transport rewrite. The latest calendar-aware solar relaxation result
does not directly weaken this proposal's mechanism, but it does reinforce that
clean fast diagnostics are not enough: that candidate was finite and
diagnostic-clean, then regressed iteration primary score by
`-0.040271379533892704` and failed 2 m temperature guardrails. A broad forward
transport change should therefore remain behind any narrower side-by-side
candidate with comparable physical support.

Source and literature checks still support staging rather than scrapping. Local
source provides `semi_lagrangian_vertical_advection_step_sigma`, and
`PrimitiveEquations` exposes the `include_vertical_advection` switch needed to
avoid double-counting centered vertical tendencies. The Staniforth-Cote
semi-Lagrangian review supports the general atmospheric advection method family
with attention to accuracy, stability, and efficiency. Feasibility is therefore
real, but local adapter structure also confirms the implementation is not a
one-line toggle: preserving the incumbent DFI path while applying the
semi-Lagrangian remap only in the positive-time forecast requires a separate
forward equation or careful step wrapper.

The empirical risk remains high. Vertical-advection suppression failed the fast
gate with nonfinite forecasts and metrics beginning at lead hour 264 for all
four fixed target variables. T120 truncation failed at 24 h, while 600 s
stepping, divergence-selective damping, hyperdiffusion, pressure-grid changes,
humidity limiting, and pressure/mass anchors all failed to promote or regressed.
This proposal is not a duplicate of those experiments because it retains
vertical transport through a replacement remap, but it still changes core
forecast transport every inner step, can add interpolation diffusion or phase
error, and likely costs more runtime than the log-pressure initialization
candidate.

Keep the prior promotion constraints unchanged if the Orchestrator later exhausts
lower-surface ideas: side-by-side model only; preserve DFI, near-surface
residuals, weak Held-Suarez, T80, 900 s inner step, and fixed diffusion; do not
run the semi-Lagrangian remap through time-reversed DFI; apply exactly one
positive-time remap per forward inner step; stop immediately on any fast
nonfinite or material runtime blow-up.

2026-06-17T02:02:53Z - Keep in `staging`; rank 3 of 3 active ideas for iteration 20.

The accepted log-pressure initialization and the two new proposals change this
idea's relative rank downward, not its absolute plausibility. The new incumbent
shows that a narrow pressure-coordinate initialization projection can improve
primary score cleanly, and the new log-pressure output-remap proposal extends
that same accepted coordinate mechanism without perturbing the forecast
trajectory. Hydrostatic-thickness initialization is also narrower than this
transport rewrite because it is initialization-only, even though it changes the
thermal profile.

This semi-Lagrangian proposal should remain staged rather than scrapped because
local source still provides the necessary helper,
`semi_lagrangian_vertical_advection_step_sigma`, and the
`include_vertical_advection` switch needed to avoid double-counting centered
vertical tendencies. Literature support for semi-Lagrangian transport as a
standard atmospheric-model method remains credible. The proposal is also still
scientifically distinct from the rejected vertical-advection-suppression
ablation because it retains vertical transport through a replacement remap.

It remains the riskiest active idea. It disables the centered vertical-advection
tendency in the forward equation and inserts an operator-split remap every inner
step, so it touches core transport, runtime, interpolation diffusion, and
long-lead stability. Prior broad-numerics history is negative: vertical-
advection suppression failed fast with nonfinite forecasts and metrics at 264 h,
T120 failed fast at 24 h, and 600 s stepping, divergence damping,
hyperdiffusion, pressure-grid changes, and humidity limiting did not promote.
Do not promote this ahead of narrower adapter/initialization ideas unless those
queues are exhausted or new diagnostics specifically implicate centered
vertical transport as the remaining dominant error.

2026-06-17T03:11:14Z - Keep in `staging`; rank 4 of 4 active ideas.

The two new ready proposals and the still-staged hydrostatic initialization
remain better next experiments under the protocol rubric. This semi-Lagrangian
proposal is still scientifically distinct from the rejected vertical-advection
suppression ablation and local source still provides the required helper and
`include_vertical_advection` switch, so it should not be scrapped merely because
the related ablation failed.

It remains the highest-risk active idea because it changes core forward
transport at every inner step, requires disabling the centered vertical
advection tendency to avoid double-counting, and can introduce interpolation
diffusion, phase error, runtime cost, or a new long-lead stability failure.
Recent history strengthens the preference for narrower candidates: accepted
log-pressure sigma initialization succeeded as a small initialization
projection, while the log-pressure output-remap rejection and earlier T120,
time-step, damping, pressure-grid, and vertical-advection failures all warn that
broad numerics changes can be clean in fast checks yet fail iteration gates or
guardrails. Revisit only after lower-surface adapter and initialization ideas
are exhausted or new diagnostics point specifically to centered vertical
transport as the dominant remaining error source.

2026-06-17T05:24:11Z - Keep in `staging`; rank 2 of 2 active staged ideas after
the ready queue was exhausted.

This proposal remains scientifically plausible but should not be the immediate
next implementation target. The local code still exposes both
`semi_lagrangian_vertical_advection_step_sigma` and the
`include_vertical_advection` switch, so the idea remains implementable without a
new dependency or public API change. It is also still distinct from the rejected
vertical-advection-suppression ablation because it keeps vertical transport
active through a replacement remap.

The latest history makes the cost-risk tradeoff worse relative to the promoted
hydrostatic-thickness initialization. `helmholtz-wind-initialization` showed
that finite, diagnostic-clean initialization changes can still severely damage
mass/geopotential evolution, and `layer-mean-thermal-recentering` showed that a
large primary improvement can still fail a tight early wind guardrail. A
semi-Lagrangian vertical-transport split has a broader behavioral surface than
either: it disables centered vertical advection in the forward equation and
adds an operator-split interpolation remap every inner step, with possible
runtime cost, diffusion, phase error, and long-lead stability failure.

Keep this staged as a later broad-numerics experiment only if lower-surface
initialization ideas are exhausted or diagnostics directly identify centered
vertical transport as the dominant remaining error source. Before promotion, the
proposal should be retargeted to the current incumbent
`dinosaur_dfi_surface_residual_weak_hs_logp_init`, and the implementation plan
should explicitly preserve the accepted log-pressure initialization path.

2026-06-17T06:41:34Z - Keep in `staging`; rank 4 of 4 active ideas after
acceptance of hydrostatic-thickness initialization.

The new incumbent lowers this proposal's relative priority. It is still
scientifically distinct from rejected vertical-advection suppression because it
retains vertical transport through a semi-Lagrangian remap, and local source
still exposes both `semi_lagrangian_vertical_advection_step_sigma` and the
`include_vertical_advection` switch. However, the current best evidence points
to initialization physics rather than core transport replacement: accepted
log-pressure initialization and hydrostatic-thickness initialization produced
clean gains, while pressure-aware sigma-grid changes, T120 truncation, 600 s
stepping, divergence damping, hyperdiffusion, and vertical-advection
suppression all failed to promote or failed the fast gate.

Keep this staged only as a later broad-numerics fallback. Before any promotion,
the proposal must be rewritten against
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init`, preserving
DFI, near-surface residuals, weak Held-Suarez relaxation, log-pressure
initialization, hydrostatic temperature initialization, T80 truncation, 900 s
inner step, and finite output extrapolation. Its current implementation sketch
would still disable centered vertical advection in the forward equation and add
an operator-split remap every inner step, so runtime, interpolation diffusion,
phase error, and long-lead stability remain materially higher risks than the
adapter-initialization proposals triaged today.

2026-06-17T08:00:01Z - Keep in `staging`; retargeted to current incumbent and
rank 4 of 5 active ideas.

I updated the front matter and main implementation/evaluation text to target
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init` and
the side-by-side candidate
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_semilag_vadv`.
Older Evaluator notes are preserved above because they document how this idea
was repeatedly staged against earlier incumbents.

The proposal remains scientifically distinct from rejected vertical-advection
suppression because it retains vertical transport through a semi-Lagrangian
remap. Local source still exposes both
`semi_lagrangian_vertical_advection_step_sigma` and the
`include_vertical_advection` switch needed to avoid double-counting centered
vertical tendencies. That is enough feasibility to keep it staged.

It remains a broad fallback, not a near-term ready idea. The current accepted
history points to initialization geometry, not core transport replacement:
log-pressure initialization, hydrostatic-thickness initialization, and
layer-mean hydrostatic initialization all promoted, while vertical-advection
suppression failed fast with nonfinite metrics from 264 h, pressure-aware sigma
grid lost `-0.10322710509965427`, hyperdiffusion damaged early 10 m wind, and
time-step/divergence-damping changes both lost primary. Do not promote this
unless narrower initialization and output-datum ideas are exhausted or new
diagnostics specifically implicate centered vertical transport.

2026-06-17T09:09:07Z - Keep in `staging`; rank 4 of 5 active ideas.

The latest conservative-remap rejection does not directly test vertical
transport, but it reinforces the current queue preference for narrow,
diagnostic-isolated experiments over broad changes to column structure. This
proposal remains scientifically distinct from the rejected
vertical-advection-suppression ablation because it retains vertical transport
through a semi-Lagrangian remap, and local source still exposes both
`semi_lagrangian_vertical_advection_step_sigma` and
`include_vertical_advection`.

The cost-risk tradeoff remains too high for ready. Implementing this requires
disabling centered vertical advection in the forward equation and inserting an
operator-split interpolation remap every positive inner step. Prior nearby
numerics experiments are mostly negative: vertical-advection suppression failed
fast with nonfinite metrics from lead 264 h, pressure-aware sigma grid lost
`-0.10322710509965427`, hyperdiffusion damaged early 10 m wind, and both
time-step and divergence-damping changes lost primary. Keep staged only as a
later broad-numerics fallback after the narrower dry-geopotential,
surface-layer, and edge-extrapolation ideas are exhausted or contradicted.

2026-06-17T10:13:20Z - Keep in `staging`; rank 5 of 5 active ideas.

This remains scientifically distinct from vertical-advection suppression, but
it is still the highest-risk active idea. The vertical-advection suppression
candidate failed the fast gate with nonfinite forecasts from lead hour 264, and
nearby broad-numerics experiments have repeatedly disappointed: pressure-aware
sigma grid regressed primary by `-0.10322710509965427`, hyperdiffusion by
`-0.051242100653831`, 600 s stepping by `-0.0002549284092885351`, and
divergence damping by `-0.00020461043258523937`.

The source hook exists, so the idea should not be scrapped solely for
feasibility. But it changes core transport every inner step, likely increases
runtime, and has a larger blast radius than the current initialization and
diagnostic candidates. Leave it staged as a later research option only after
lower-risk ideas are exhausted.

2026-06-17T11:23:24Z - Keep in `staging`; rank 6 of 6 active ideas.

No new evidence promotes this above the narrower queue. It remains
scientifically distinct from the rejected vertical-advection-suppression
ablation because it retains vertical transport through a semi-Lagrangian remap,
and local source still exposes both the remap helper and the
`include_vertical_advection` switch needed to avoid double-counting.

It is still the broadest and riskiest active idea. It would disable centered
vertical advection in the forward equation and add an operator-split remap every
positive inner step, with runtime, diffusion, phase, and long-lead stability
risk. Recent clean-but-negative candidates reinforce that fast stability does
not justify broad core-numerics changes when smaller adapter or diagnostic
ideas remain. Keep staged only as a later fallback after the thermal limiter,
passive humidity DFI bypass, surface diagnostic, polar initialization, and
edge-only extrapolation ideas are exhausted or contradicted by new diagnostics.

2026-06-17T13:33:51Z - Keep in `staging`; rank 4 of 4 active ideas.

The latest failures do not directly test semi-Lagrangian vertical transport,
but they reinforce the queue preference for smaller adapter and diagnostic
changes. Passive humidity was neutral, the upper thermal limiter lost skill,
and theta initialization lost skill despite clean diagnostics. Those results
do not justify a broader core-transport rewrite.

Keep this only as a later fallback. Before promotion, require a clear
diagnostic reason to suspect centered vertical transport is the dominant
remaining error source, and preserve the existing constraints: side-by-side
model, no DFI-time-reversed remap, exactly one positive-time remap per forward
inner step, centered vertical advection disabled only to avoid double-counting,
and hard stop on fast nonfinite or material runtime blow-up.

2026-06-17T14:41:49Z - Move to `scrap`; rank removed from active queue.

Fresh triage scraps this idea under the requested rubric. It remains
scientifically recognizable as a semi-Lagrangian transport mechanism, but it is
no longer a good model-selection candidate for this loop: it changes core
forward transport at every inner step, requires disabling the incumbent
centered vertical-advection tendency to avoid double counting, likely increases
runtime, and is tied to a repeatedly negative broad-numerics family. The
nearest direct history is severe: vertical-advection suppression failed the
fast gate with nonfinite forecasts and metrics beginning at lead hour 264.
Other broad numerics candidates also failed to promote or triggered guardrails,
including T120 truncation, pressure-aware sigma grid, hyperdiffusion, 600 s
inner stepping, and divergence-selective damping.

The latest surface-layer diagnostic rejection further raises the bar for
diagnostic-clean but behaviorally broad changes. That candidate passed
diagnostics yet regressed primary by `-0.10115079559414197`, demonstrating
again that fast sanity is not a reliable proxy when the changed mechanism is
large relative to the fixed WeatherBench2 gates. Without a new diagnostic that
specifically implicates centered vertical transport as the dominant remaining
error source, spending another iteration on this broad transport rewrite is a
poor cost-risk tradeoff compared with the smaller active ideas. Do not revive
without a new proposal that materially narrows the implementation surface or
adds direct evidence for vertical-transport error.
