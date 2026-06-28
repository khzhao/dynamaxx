---
schema_version: 1
slug: pressure-work-balance-diagnostic-sidecar
title: Pressure-Work Balance Diagnostic Sidecar
status: staging
created_at: 2026-06-23T06:08:19Z
author_role: Researcher
target_model: dino_hsl2_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
---

# Pressure-Work Balance Diagnostic Sidecar

## Hypothesis

The rejected `dino_hsl2_theta_pw` result is strong evidence that pressure-work
conversion has real aggregate score leverage, but that unconstrained coupling
damages the short-lead mass and thickness fields. Its iteration primary delta
was large and positive, while the fixed guardrails failed on 24 h MSLP and
day-1-to-5 Z500. Before another pressure-work model-selection candidate is
worth running, the loop needs a read-only diagnostic that localizes whether the
guardrail failure came from amplitude, vertical placement, horizontal phase, or
operator mismatch.

## Mechanism

Add an opt-in diagnostic sidecar that can be enabled in a non-ranking smoke run
or unit-level probe, without changing forecast outputs, target variables, lead
times, metrics, or the incumbent trajectory. For the incumbent
`dino_hsl2_theta`, compute and summarize these internal quantities at saved
lead times or at a low-frequency debug cadence:

- column integral of the incumbent sigma-coordinate pressure-work tendency;
- layerwise pressure-work contribution to temperature tendency in K/day units;
- local Exner/theta conversion residual that the rejected pressure-work branch
would have added, but do not apply it to the state;
- column dry-static-energy tendency proxy, paired with hydrostatic thickness
change;
- area-weighted correlations between the diagnostic residuals and short-lead
MSLP/Z500 increments available from the model state, not from truth fields.

The sidecar should write a small JSON or CSV artifact under `outputs/diagnostics/`
only when explicitly enabled. It must leave `WeatherState` unchanged and must
not add fields to the forecast output schema.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - focused tests under `tests/dycore/models/dinosaur/`
- Registry changes:
  - None required for model selection. If a smoke alias is useful, it must be
    clearly marked diagnostic-only and should not be submitted as a candidate
    against the fixed leaderboard.
- API changes:
  - No forecast-contract changes. The sidecar is off by default and writes only
    auxiliary artifacts when explicitly enabled.
- Tests to update:
  - Verify default `dino_hsl2_theta` forecasts are bitwise or tolerance-equal
    with diagnostics disabled.
  - Verify sidecar arrays are finite for a non-JIT smoke forecast.
  - Verify no diagnostic field is appended to returned `WeatherState`.
  - Verify pressure-work unit conversion is documented and fixed.

## Expected Metric Movement

- Expected improvements:
  - No direct metric movement is expected from this infrastructure proposal.
    Its purpose is to produce evidence for a later constrained pressure-work or
    operator-consistency proposal.
- Expected neutral metrics:
  - All fixed metrics should be unchanged when diagnostics are disabled.
- Possible regressions:
  - None in default mode. An explicitly enabled diagnostic run may be slower or
    write extra artifacts, but should not alter forecasts.

## Risks

- Numerical stability:
  - Low. The proposal observes existing tendencies and rejected-branch residuals
    without feeding them back into the state.
- Compute cost:
  - Low to moderate when enabled, depending on how often diagnostics are saved.
    The default path must remain unchanged.
- Data leakage:
  - Low if diagnostics use only forecast state and internal tendencies. Do not
    compute truth-error correlations inside the dycore.
- Physical plausibility:
  - High as a diagnostic. It does not assert that pressure-work should be
    applied; it measures the balance terms needed to design a safer candidate.
- Rollback complexity:
  - Low. Remove the diagnostic helper, opt-in adapter plumbing, and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Optionally run `uv run dynamaxx-eval fast --model dino_hsl2_theta` with the
    sidecar disabled to verify no default-output change. A diagnostic-enabled
    fast smoke run is only for artifact sanity, not model selection.
- Iteration gate:
  - Do not run iteration as a model-selection experiment for this proposal.
    The output is diagnostic evidence, not a leaderboard candidate.
- Validation gate:
  - Do not run validation.
- Outcome that would falsify the hypothesis:
  - If the diagnostic residuals are numerically tiny, nonlocalizable, or
    dominated by already-accepted incumbent terms, then the rejected pressure
    work failure should be treated as negative evidence against further
    pressure-work variants rather than a tuning target.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-23_03-46-01_hydrostatic-balanced-theta-pressure-work/decision.md`
  rejected `dino_hsl2_theta_pw` after a positive iteration primary delta
  `+0.08765828083613111` but failed short-lead MSLP and Z500 guardrails.
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` contains
  `temperature_tendency_potential_temperature_form`,
  `nodal_temperature_adiabatic_tendency`, and `_t_omega_over_sigma_sp`, the
  relevant pressure-work and theta-conversion hooks.
- Laprise, R. 1992. The Euler equations of motion with hydrostatic pressure as
  an independent variable. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C0197:TEEOMW%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This directly learns from the pressure-work guardrail failure without rerunning
unconstrained pressure work and without duplicating staged
`bounded-pressure-work-thermal-tendency` or
`energy-conserving-omega-alpha-coupling`. Those are candidate mechanisms. This
proposal is diagnostic infrastructure intended to decide which, if any,
pressure-work constraint is scientifically justified.

It also respects the forecast-contract rule: the sidecar must not add forecast
channels, change target variables, alter lead times, or adjust deterministic
gates. Any later forecast-contract-changing idea should be proposed separately
as infrastructure before being considered for model selection.

## Evaluator Notes

### 2026-06-23T06:12:09Z

Decision: move to `staging`; ranked 3 of 3 new proposals.

This is a coherent and useful diagnostic response to the rejected
`hydrostatic-balanced-theta-pressure-work` run: that candidate had a large
positive iteration primary delta (`+0.08765828083613111`) but failed fixed
short-lead guardrails, especially `mean_sea_level_pressure` at 24h
(`+26.501130746134606%`) and day-1-to-5 `geopotential_500`
(`+2.409417583035754%`). A read-only pressure-work sidecar could help localize
whether the failure is amplitude, vertical placement, phase, or operator
coupling before another pressure-work candidate is selected.

It should not be `ready` for this loop pass. The proposal is explicitly
infrastructure-only and expects no candidate dycore score, while the current
process needs one ready model-selection candidate when possible. It also
overlaps the broader staged `read-only-balance-diagnostic-sidecar` and nearby
pressure-work candidates such as `bounded-pressure-work-thermal-tendency` and
`energy-conserving-omega-alpha-coupling`. Keep staged for a later
infrastructure-approved pass or if pressure-work/operator proposals continue
to be blocked by missing internal balance evidence. Do not use validation or
golden truth to tune this diagnostic, and keep incumbent cached metrics reused
for actual model-selection comparisons.
