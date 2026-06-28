---
schema_version: 1
slug: hypsometric-target-geopotential-diagnostic
title: Diagnose Target-Level Geopotential by Hypsometric Integration
status: ready
created_at: 2026-06-18T04:29:16Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
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

# Diagnose Target-Level Geopotential by Hypsometric Integration

## Hypothesis

The incumbent computes hydrostatic geopotential on sigma centers and then uses
the generic sigma-to-pressure interpolation path for pressure-level outputs.
Accepted history shows that hydrostatic thickness consistency is high leverage,
while the rejected log-pressure output remap showed that changing every
pressure-level output interpolation is too broad and not sufficiently strong.

A narrower geopotential-only diagnostic can use the hypsometric relation to
compute geopotential directly at requested pressure levels, such as 500 hPa,
from the forecast sigma-column virtual temperature and pressure geometry. This
targets the remaining Z500 mass-field diagnostic without changing dynamics,
winds, temperature outputs, MSLP, near-surface residuals, or the forecast
contract.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z`.
Preserve the incumbent rollout, DFI, weak Held-Suarez forcing, exact Coriolis
split, pressure-to-sigma initialization, near-surface residual correction, and
all non-geopotential output diagnostics.

Add an optional geopotential output path:

- reconstruct sigma-center temperature, humidity if present, surface pressure,
  and sigma-center pressure for each forecast time and column;
- compute sigma-center geopotential as the incumbent already does;
- for each requested pressure-level geopotential channel, locate the bracketing
  sigma-center pressures in that column;
- integrate from the nearer bracket to the target pressure using the local
  hypsometric increment `R_d * Tv_layer * log(p_start / p_target)`, where
  `Tv_layer` is a bounded average of forecast virtual temperature over the
  bracket;
- fall back to the incumbent finite interpolation when a target pressure is
  outside the usable sigma pressure range or any required value is nonfinite;
- leave pressure-level temperature, pressure-level winds, humidity outputs,
  MSLP, 2 m temperature, and 10 m wind on the incumbent path.

This is an output diagnostic refinement, not a residual correction and not a
metric or protocol change.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z`.
- API changes:
  - None. Output variable names, shapes, lead times, and fixed target variables
    remain unchanged.
- Tests to update:
  - Unit-test the hypsometric helper on an isothermal column where the analytic
    log-pressure increment is known.
  - Verify fallback to incumbent interpolation for out-of-range targets and
    nonfinite inputs.
  - Verify only geopotential pressure-level channels change when the option is
    enabled.
  - Verify the candidate factory preserves all incumbent flags, including the
    accepted exact Coriolis split.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` across early to medium leads if part of the remaining
    error is interpolation of geopotential rather than trajectory error.
  - Primary score may improve modestly through Z500 without spending near-surface
    wind or temperature guardrail margin.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and
    `mean_sea_level_pressure` should be effectively unchanged because their
    output paths are unchanged.
- Possible regressions:
  - If the current finite sigma-to-pressure interpolation is empirically better
    for the coarse vertical grid, Z500 RMSE may regress.
  - The mechanism may be too narrow to clear the primary-score gate even if Z500
    improves slightly.

## Risks

- Numerical stability:
  - Low. This is output-only and has explicit finite fallbacks.
- Compute cost:
  - Low. It adds per-output-column vertical arithmetic for requested
    geopotential pressure levels only and fits the existing `--workers 4`
    evaluation budget.
- Data leakage:
  - None. It uses only forecast-state temperature, humidity, pressure, and fixed
    constants.
- Physical plausibility:
  - High. The hypsometric relation is the hydrostatic pressure-coordinate link
    between layer virtual temperature and geopotential thickness.
- Rollback complexity:
  - Low. Remove one diagnostic option, one factory/export, one registry entry,
    and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split_hypsometric_z`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split_hypsometric_z --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day 1-5 RMSE guardrail failure, and no variable+lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split_hypsometric_z --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, or any Z500 guardrail failure,
    would show that the incumbent geopotential interpolation is preferable under
    the fixed WeatherBench2 contract.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` computes
  sigma-level geopotential with `primitive_equations.get_geopotential_on_sigma`
  and then calls `_interp_sigma_to_pressure_by_time` for pressure-level outputs.
- History: `.logbook/history/2026-06-17_02-11-52_log-pressure-output-interpolation/decision.md`
  rejected broad log-pressure output interpolation as sub-threshold, so this
  proposal changes only geopotential diagnosis.
- History: `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted layer-mean hydrostatic initialization, motivating a similarly
  hydrostatic but output-only Z500 diagnostic.
- AMS Glossary of Meteorology. Hypsometric equation.
  https://glossary.ametsoc.org/wiki/hypsometric-equation/
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of rejected `log-pressure-output-interpolation`: that
candidate changed the generic pressure-level interpolation of temperature,
winds, humidity, and geopotential. This proposal changes only pressure-level
geopotential and uses the hypsometric relation rather than a blanket
coordinate remap.

It is also distinct from rejected mass residuals, terrain/orography, and
dry-consistent geopotential. It does not add a learned or decaying residual, does
not alter surface pressure or orography, and does not remove humidity from the
virtual-temperature geopotential calculation.

## Evaluator Notes

### 2026-06-18T04:36:51Z

Decision: move to `staging`.

The mechanism is physically coherent. Source inspection confirms the incumbent
currently computes sigma-level geopotential with virtual temperature and then
uses the generic sigma-to-pressure interpolation path for pressure-level
geopotential. Literature checks against the AMS hypsometric-equation reference
support the proposal's core relation between layer mean virtual temperature,
pressure ratio, and hydrostatic thickness.

Do not make this the top ready item now. The proposal is narrow and
geopotential-only, and the accepted Coriolis incumbent already carried the
largest remaining variable+lead regression in day-1 `geopotential_500` at about
`+6.7%`, leaving limited short-lead guardrail margin for output diagnostics.
Earlier output-only experiments are cautionary: broad log-pressure output
interpolation had a sub-threshold aggregate gain with many guardrail failures,
and dry-consistent geopotential damaged day-1 Z500. This proposal is more
targeted and physically stronger than those failures, so it remains staged as a
good fallback after the Coriolis-ordering follow-up.

### 2026-06-18T06:07:51Z

Decision: keep in `staging`, ranked as the strongest fallback after the current
ready idea.

I updated the front matter target model from the accepted Lie Coriolis split to
the accepted Strang incumbent. The mechanism remains coherent and source-backed:
the adapter computes sigma-level geopotential hydrostatically using virtual
temperature, then passes geopotential through the generic sigma-to-pressure
interpolation path. A geopotential-only hypsometric diagnostic is narrower than
the rejected broad log-pressure output remap and cleaner than the scrapped
lead-zero geopotential datum residual.

Do not promote it over DFI-Coriolis consistency. Output-only pressure-level
changes have a poor recent history, including 54 guardrail failures for broad
log-pressure output interpolation and a day-1 Z500 guardrail failure for the
dry-consistent geopotential diagnostic. This proposal is low-cost and useful as
a focused Z500 fallback, but it directly changes a scored output channel and
should wait behind the more causal initialization/rollout consistency test.

### 2026-06-18T07:28:25Z

Decision: keep in `staging`; rank as a strong fallback behind the new
sigma-native hydrostatic initialization.

The new sigma-native proposal uses the same hydrostatic relation but targets
initial condition balance rather than a scored output channel, so it should be
implemented first. If sigma-native initialization fails cleanly or is rejected,
this geopotential-only diagnostic remains a plausible low-cost fallback because
it changes only pressure-level geopotential output and leaves dynamics,
near-surface residuals, MSLP, winds, and temperature outputs on the incumbent
path.

The cautions from prior output-only history still apply. Broad log-pressure
output interpolation produced many guardrail failures, and dry-consistent
geopotential damaged day-1 Z500. Any later implementation must keep finite
fallbacks to the incumbent interpolation and treat 24 h `geopotential_500` as
the key early guardrail.

### 2026-06-18T08:53:53Z

Decision: keep in `staging`; rank as the strongest non-ready fallback.

The latest sigma-native hydrostatic initialization rejection weakens another
initialization-focused hydrostatic refinement, but it does not directly falsify
this output-only diagnostic. The proposal still has a coherent hypsometric
mechanism and a localized adapter surface: pressure-level geopotential is
currently produced by interpolating sigma-level geopotential, while this
candidate would compute the target-level thickness relation more directly for
geopotential channels only.

Do not promote it over the ready residual-rotation candidate. The history of
output-path geopotential changes is fragile: broad log-pressure output
interpolation caused 54 variable+lead guardrail failures, and dry-consistent
geopotential produced a day-1 Z500 guardrail failure. If this is selected
later, first fix the proposal's candidate name to reference the Strang
incumbent, keep finite fallback to incumbent interpolation, and treat 24 h
`geopotential_500` as the decisive early warning channel.

### 2026-06-18T10:25:42Z

Decision: keep in `staging`; current staged rank 1 and strongest fallback if
the ready initialization candidate fails or is consumed.

The surface-wind residual rejection removes the prior ready item that this was
waiting behind, but it does not make this the best immediate run. The proposal
is still low cost and physically clean: it uses a hypsometric target-level
geopotential diagnostic, changes only pressure-level geopotential channels, and
does not touch dynamics, MSLP, 2 m temperature, or 10 m wind output paths. I
also corrected the candidate name in the proposal text to target the accepted
Strang incumbent rather than the older Lie split name.

Keep it staged behind `variable-selective-pressure-initialization` because it
directly changes a scored output channel and is likely to move only Z500,
whereas the ready candidate is an initialization-only test with potential
cross-variable impact. Prior output-path evidence remains fragile: broad
log-pressure output interpolation had many guardrail failures, and
dry-consistent geopotential damaged day-1 Z500. This remains the best fallback
because it is narrower and more physically constrained than those failures.

### 2026-06-18T11:49:28Z

Decision: keep in `staging`, staged fallback rank 1.

The variable-selective pressure initialization has since failed with a broad
negative iteration delta, so this remains the strongest non-ready fallback
rather than an immediate implementation target. It is low-cost and localized to
pressure-level geopotential output, but it directly changes a scored channel
and prior output-path Z500 experiments were fragile. Keep it behind the two
ready rollout-ordering/continuity candidates, and require finite fallback to
the incumbent interpolation if later selected.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 1.

The new bounded-humidity diagnostic is weaker than this because it is another
humidity-tracer cleanup with poor direct history, while this proposal tests the
hydrostatic pressure-level diagnosis itself. The new log-sigma adiabatic
proposal is more dynamically invasive and has unresolved quadrature-consistency
risk. Keep this as the strongest staged fallback, but do not promote it while
ready remains small and the lower-risk symmetric diffusion split is available.

### 2026-06-18T14:37:31Z

Decision: promote to `ready`; ranked recommendation 1 for the next
implementation target.

Ready is empty and the current proposal pool has no lower-risk candidate with
a clearer expected score path. This proposal is the best next experiment
because it is implementable, low surface area, output-only, and physically
grounded in the hydrostatic hypsometric relation. It targets the scored
`geopotential_500` channel directly while leaving the accepted initialization,
rollout dynamics, DFI, Strang Coriolis split, near-surface residuals, MSLP,
temperature outputs, and wind outputs on the incumbent path.

Ranking rationale: place this ahead of the new monotone-theta initialization
because the latest initialization variants regressed and this diagnostic does
not perturb the model state. Place it ahead of passive-humidity mass fixing
because prior humidity-only tests were near-neutral or negative and there is no
evidence that global passive-humidity mass drift is the remaining Z500 error
source. Place it ahead of quasi-monotone pressure-output interpolation because
that proposal changes all pressure-level variables, while this one changes
only pressure-level geopotential. Among existing staged ideas, keep it ahead of
omega spinup, diffusion heating, scalar skew advection, log-sigma adiabatic
tendency, Simmons-Burridge weights, RK4, upwind vertical advection, and
momentum skew forms because those alter positive-time dynamics or broad
operator balance after several recent pressure, sigma, diffusion, wind, and
continuity experiments failed or were subthreshold.

This is not a duplicate of rejected output candidates. Unlike
`log-pressure-output-interpolation`, it does not remap every pressure-level
output or change the interpolation coordinate family. Unlike
`dry-consistent-geopotential-diagnostic`, it keeps virtual-temperature humidity
in the hydrostatic thickness relation rather than removing a diagnostic
component that protected day-1 Z500. Unlike humidity-bound or humidity-mass
fixer proposals, it targets the vertical hydrostatic integration itself, not
passive tracer cleanup. The implementation should retain finite fallback to
the incumbent interpolation and treat short-lead `geopotential_500` as the
main guardrail risk.
