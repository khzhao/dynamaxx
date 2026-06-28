---
schema_version: 1
slug: full-grid-spectral-truncation
title: Use Full-Grid T120 Spectral Truncation
status: ready
created_at: 2026-06-16T21:09:23Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs
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

# Use Full-Grid T120 Spectral Truncation

## Hypothesis

The current incumbent projects WeatherBench2 1.5 degree initial states onto a
T80-like spherical harmonic truncation even though the 240 longitude by 121
latitude grid can support a higher total wavenumber in the local coordinate
builder. After DFI, near-surface residual correction, and weak wind-sparing
thermal relaxation have removed the largest initialization and drift errors,
some remaining negative skill may come from under-resolving balanced synoptic
and near-surface gradients before the forecast begins.

A single fixed full-grid truncation candidate should test whether retaining more
resolved modal structure improves forecast evolution without changing physics
coefficients, time steps, output variables, metrics, or splits.

## Mechanism

Register a side-by-side candidate that preserves the incumbent configuration but
sets `spectral_wavenumbers=120`. On the fixed WeatherBench2 grid, local
`grid_metadata` caps this to the maximum supported longitudinal wavenumber for
240 longitudes and a total wavenumber below the 121 latitude-node limit. The
model keeps the same 900 second inner step, DFI setup, weak thermal Held-Suarez
forcing, near-surface diagnostic residual correction, vertical advection,
humidity handling, and horizontal diffusion formulation.

This is a resolution/discretization experiment, not a time-step sweep or a
damping variant. The candidate should be named
`dinosaur_dfi_surface_residual_weak_hs_t120`.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for
    `dinosaur_dfi_surface_residual_weak_hs_t120`.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` remains unchanged.
- Tests to update:
  - Assert the incumbent keeps `spectral_wavenumbers=80`.
  - Assert the new factory preserves DFI, weak Held-Suarez relaxation,
    near-surface residual correction, and the 900 second inner step while using
    `spectral_wavenumbers=120`.
  - Add registry/dependency smoke coverage for the new model name.
  - Add a small finite forecast smoke test if existing Dinosaur test fixtures can
    run it cheaply.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `10m_u_component_of_wind` at early and medium leads
    if the T80 projection is discarding balanced gradients that the dynamics can
    otherwise carry.
  - `2m_temperature` at medium leads if sharper low-level thermal gradients
    survive initialization and interact better with the accepted weak thermal
    relaxation.
- Expected neutral metrics:
  - `mean_sea_level_pressure` should remain close to incumbent at early leads
    because no surface-pressure forcing, mass anchor, or orography change is
    introduced.
- Possible regressions:
  - High-wavenumber noise may worsen long-lead `10m_u_component_of_wind`, whose
    validation guardrail margin is already tight after the accepted weak
    Held-Suarez candidate.
  - Runtime and memory can increase materially because modal arrays grow from
    the incumbent truncation; scoring should keep the Orchestrator's worker
    budget rather than increasing workers.

## Risks

- Numerical stability:
  - Moderate. The same filters and IMEX stepper are retained, but more high-wave
    content is prognosed and may expose stability or aliasing sensitivity.
- Compute cost:
  - Moderate. The fixed evaluations will be slower than the incumbent because
    spherical harmonic transforms and modal state size increase. The reported
    local resources are sufficient for a single candidate, but the Evaluator
    should consider cost when ranking.
- Data leakage:
  - Low. The truncation is fixed from grid geometry and does not use validation
    statistics, target residuals, or future truth.
- Physical plausibility:
  - Moderate. Increasing horizontal spectral resolution is a standard dynamical
    core convergence axis, but higher resolution is not guaranteed to improve a
    short-range weather score when physics is idealized.
- Rollback complexity:
  - Low. The change is isolated to a factory, export, registry entry, and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_t120`.
  - Require finite outputs and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_t120 --workers 4`.
  - Support for the hypothesis requires the fixed primary score to improve by at
    least `+0.002` over `dinosaur_dfi_surface_residual_weak_hs`, with clean
    diagnostics and all RMSE guardrails passing.
- Validation gate:
  - Run validation only after iteration promotion:
    `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_t120 --workers 4`.
  - Accept only if validation improves primary by at least `+0.001` with clean
    diagnostics and unchanged fixed guardrails.
- Outcome that would falsify the hypothesis:
  - A diagnostic-clean iteration run with negative or sub-threshold primary
    delta, or any early wind guardrail failure, would show that extra spectral
    resolution is not beneficial under the current fixed WeatherBench2 contract.

## Citations

- Local source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` sets
  `DEFAULT_SPECTRAL_WAVENUMBERS = 80` and defines the accepted weak-Held-Suarez
  incumbent factory.
- Local source: `src/dynamaxx/dycore/models/dinosaur/coordinates.py` derives the
  maximum supported wavenumbers from the input longitude/latitude grid and caps
  requested `spectral_wavenumbers` accordingly.
- Machenhauer, B. 1991. "Spectral Methods." ECMWF Seminar on Numerical Methods
  in Atmospheric Models, 9-13 September 1991. ECMWF eLibrary:
  https://www.ecmwf.int/en/elibrary/75510-spectral-methods
- Jablonowski, C. and Williamson, D. L. 2006. "A baroclinic instability test
  case for atmospheric model dynamical cores." Quarterly Journal of the Royal
  Meteorological Society, 132, 2943-2975. https://doi.org/10.1256/qj.06.12
- Schaeffer, N. 2013. "Efficient Spherical Harmonic Transforms Aimed at
  Pseudospectral Numerical Simulations." Geochemistry, Geophysics, Geosystems,
  14, 751-758. https://doi.org/10.1002/ggge.20071

## Researcher Notes

This is not a duplicate of `six-hundred-second-inner-step`: it keeps the time
integration step fixed and changes only the horizontal modal truncation. It is
not a damping variant: the existing horizontal diffusion formulation is
preserved rather than strengthened, weakened, or made variable selective. It is
also distinct from pressure-grid, reference-profile, or orography proposals
because the vertical coordinate, mass variable, and output diagnostics are left
unchanged.

The main reason to let the Evaluator consider this despite higher cost is that
the last several cheap conservation, time-step, and damping candidates were
neutral or negative. A single fixed resolution candidate is a bounded way to
test whether the incumbent is now limited by retained modal structure rather
than by another missing forcing coefficient.

## Evaluator Notes

2026-06-16T21:12:45Z - Move to `staging` for Iteration 15 ranking against
`dinosaur_dfi_surface_residual_weak_hs` at
`4756cc9a4b69c41eec60e2177fb03a73974f0e2d`.

Keep this active but do not make it the next implementation target. The
proposal is scientifically legitimate and not a duplicate of the rejected 600 s
time-step or divergence-damping experiments: it changes horizontal modal
truncation while keeping the step size, DFI, weak Held-Suarez forcing,
near-surface residual correction, output contract, metrics, splits, and
guardrails unchanged. Local source inspection confirms that the 240 longitude by
121 latitude grid can support `spectral_wavenumbers=120` under the existing
coordinate cap.

The reason to stage rather than promote is cost-risk balance. T120 materially
increases modal state size and spectral-transform work, so it is more expensive
than the alternative ready proposal and may need closer resource supervision at
the fixed `--workers 4` budget. It also retains more high-wavenumber structure
in an incumbent whose accepted weak-Held-Suarez validation run already spent
most of the available long-lead 10 m wind guardrail margin. Prior
spectral-side experiments also argue for caution: broad hyperdiffusion and
divergence-selective damping both ran cleanly but degraded primary score. If the
ready humidity diagnostic limiter fails cleanly, this remains a reasonable
follow-up because it tests a distinct resolution/convergence axis with a simple
rollback path.

Ranked recommendation: 1. promote
`passive-humidity-positivity-limiter`; 2. keep
`full-grid-spectral-truncation` staged as the next plausible fallback if no
lower-cost, more targeted idea remains.

## Evaluator Notes

2026-06-16T22:10:42Z - Move to `ready` for Iteration 16 ranking against
`dinosaur_dfi_surface_residual_weak_hs` at
`4756cc9a4b69c41eec60e2177fb03a73974f0e2d`.

Promote this proposal as the sole ready candidate. The Iteration 15 passive
humidity limiter was a clean rejection by lack of signal: fast and iteration
diagnostics were clean, fixed guardrails passed, and the primary-score delta
was `-0.0000019440828125105725`, far below the required `+0.002`. That result
removes the lower-cost active alternative without adding evidence against the
separate horizontal-resolution hypothesis.

The T120 experiment remains a bounded side-by-side model-selection candidate:
it preserves the forecast contract, fixed WeatherBench2 protocols, target
variables, lead times, metrics, DFI, near-surface residual correction, weak
thermal Held-Suarez forcing, 900 second inner step, vertical advection, and
humidity handling. It is not a repeat of the rejected 600 second time-step
candidate, divergence-selective damping candidate, passive humidity diagnostic
limiter, or vertical-advection ablation. The implementation surface is still
small enough to roll back cleanly through one factory, export, registry entry,
and focused tests.

Promote with two explicit cautions for the Orchestrator and Scorer: keep the
configured `--workers 4` resource budget because T120 will increase modal state
size and spectral-transform cost, and watch the fixed long-lead 10 m wind
guardrails because the accepted weak-Held-Suarez incumbent already used much
of that margin. These cautions do not require any evaluation-protocol change
and do not justify staging now that the ready queue is empty.

Recommendation: implement exactly one candidate next,
`dinosaur_dfi_surface_residual_weak_hs_t120`, from this ready proposal. Do not
run `golden`, do not change fixed metrics or splits, and run validation only if
the fixed iteration promotion gate passes.
