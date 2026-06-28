---
schema_version: 1
slug: ramped-column-neutral-theta-pressure-work
title: Ramped Column-Neutral Theta Pressure Work
status: ready
created_at: 2026-06-23T08:48:19Z
author_role: Researcher
target_model: dino_hsl2_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Ramped Column-Neutral Theta Pressure Work

## Hypothesis

The rejected `dino_hsl2_theta_pw` experiment is useful positive evidence, not
just a failed branch: it improved the iteration primary score by
`+0.08765828083613111` but failed fixed short-lead guardrails, especially
`mean_sea_level_pressure` at 24 h and day-1-to-5 `geopotential_500`. That
pattern suggests the theta/Exner pressure-work conversion has real medium-lead
score leverage, but the full-amplitude term shocks the mass/thickness balance
too early. A deterministic spin-up ramp plus column-neutral thermal projection
should retain some pressure-work benefit after the first synoptic adjustment
period while protecting 24 h MSLP and early Z500.

## Mechanism

Register a side-by-side model such as `dino_hsl2_theta_pw_ramp`. Preserve every
`dino_hsl2_theta` option except an opt-in constrained pressure-work branch.

For this candidate only:

- reuse the rejected candidate's hydrostatic theta/Exner pressure-work
  diagnostic, but apply it as an increment relative to the accepted incumbent
  pressure-work term rather than replacing unrelated transport;
- multiply that increment by a fixed deterministic time ramp from zero at model
  start through 24 h, then smoothly to a conservative maximum weight such as
  `0.25` by 72 h;
- remove the mass-weighted column mean of the added temperature increment at
  every grid point, so the candidate changes vertical thermal structure more
  than column-integrated thickness;
- clip only the added increment to a broad fixed bound in K/day-equivalent
  model units and fall back to the accepted incumbent tendency on any nonfinite
  pressure, sigma-dot, or converted tendency diagnostic;
- leave HSL2 theta departure geometry, vertical theta advection, momentum,
  surface pressure tendency, DFI, residual corrections, surface fluxes, output
  variables, target variables, lead times, and metrics unchanged.

The time ramp uses `state.sim_time` or the integration step context already
available in the Dinosaur state. It does not change the forecast contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for `dino_hsl2_theta_pw_ramp`.
- API changes:
  - None. Forecast inputs, outputs, splits, metrics, target variables, and lead
    schedule remain unchanged.
- Tests to update:
  - Verify the ramp is exactly zero through the first 24 h and reaches the fixed
    maximum after the declared spin-up interval.
  - Verify column-mean removal leaves the pressure-weighted column temperature
    increment near zero for a synthetic finite state.
  - Verify nonfinite diagnostics and nonpositive pressure fall back to the
    accepted `dino_hsl2_theta` temperature tendency.
  - Verify the candidate factory preserves every incumbent flag except the new
    constrained pressure-work selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - Medium and late `geopotential_500`, `mean_sea_level_pressure`, and
    `2m_temperature` if the rejected pressure-work signal reflected useful
    thermodynamic conversion after initial adjustment.
  - Aggregate primary score should improve if even a fraction of the rejected
    pressure-work gain survives the guardrails.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should stay close because momentum and the
    Richardson 10 m wind diagnostic are unchanged.
  - 24 h MSLP should be close to incumbent because the pressure-work increment
    is zero during the first day.
- Possible regressions:
  - The primary-score gain may collapse if the rejected improvement came mostly
    from the full-amplitude first-day response.
  - Column-neutral projection can remove physically real compressional heating
    and hurt Z500 or MSLP at later leads.

## Risks

- Numerical stability:
  - Moderate. The candidate touches the thermodynamic tendency every inner step,
    but the ramp, column projection, cap, and incumbent fallback are all
    stabilizing.
- Compute cost:
  - Low. The change adds local reductions and elementwise algebra only.
- Data leakage:
  - None. It uses only forecast-state diagnostics and fixed constants.
- Physical plausibility:
  - Moderate. Pressure work is physical; the ramp and column-neutral projection
    are numerical balance safeguards motivated by the measured guardrail
    failure rather than a full conservation theorem.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_theta_pw_ramp`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_theta_pw_ramp --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failure against cached `dino_hsl2_theta`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_theta_pw_ramp --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` and clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the pressure-work
    gain does not survive conservative balance constraints. Any 24 h MSLP or
    early Z500 guardrail failure would show the ramp/projection is insufficient.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-23_03-46-01_hydrostatic-balanced-theta-pressure-work/decision.md`
  rejected `dino_hsl2_theta_pw` after a large positive iteration delta
  `+0.08765828083613111` but failed 24 h MSLP and early Z500 guardrails.
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` contains
  `temperature_tendency_potential_temperature_form`,
  `nodal_temperature_adiabatic_tendency`, `_t_omega_over_sigma_sp`, and the HSL2
  theta transport hooks used by the incumbent.
- Laprise, R. 1992. The Euler equations of motion with hydrostatic pressure as
  an independent variable. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C0197:TEEOMW%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Polichtchouk, I., Malardel, S., and Diamantakis, M. 2020. Potential
  temperature as a prognostic variable in hydrostatic semi-implicit
  semi-Lagrangian IFS. ECMWF Technical Memorandum 869.
  https://www.ecmwf.int/en/elibrary/81180-potential-temperature-prognostic-variable-hydrostatic-semi-implicit-semi

## Researcher Notes

This is not a rerun of rejected unconstrained `hydrostatic-balanced-theta-pressure-work`.
It uses that failure as measured evidence and changes the mechanism in three
ways: no added pressure-work during the first 24 h, reduced fixed amplitude
after spin-up, and pressure-weighted column-neutral projection to reduce
mass/thickness shock.

It is also not a duplicate of staged `bounded-pressure-work-thermal-tendency`,
which clips the existing local pressure-work contribution, or staged
`energy-conserving-omega-alpha-coupling`, which changes the discrete operator
pairing. This proposal tests a score-producing constrained version of the
specific high-signal theta/Exner branch that already ran.

## Evaluator Notes

### 2026-06-23T08:52:24Z

Decision: move to `ready`; ranked 1 of 3 new proposals and recommended first.

This is the only proposal in the batch with direct recent evidence for material
primary-score leverage: the rejected hydrostatic theta pressure-work candidate
improved iteration primary by `+0.08765828083613111` against cached
`dino_hsl2_theta` but failed short-lead `mean_sea_level_pressure` and
`geopotential_500` guardrails. The proposed revision is a separate candidate,
not an in-place post hoc validation tweak: validation was never run, golden is
not involved, and the incumbent comparison should reuse the current
leaderboard cache unless those artifacts are concretely invalid.

The mechanism is bounded enough for one immediate implementation. Pressure work
is a physical thermodynamic conversion term, and the safeguards are fixed before
the run: zero added increment through 24 h, a conservative maximum ramp, local
finite fallback, clipping only the added increment, and pressure-weighted
column-neutral projection to reduce column thickness shocks. Source inspection
shows the needed hooks are local: `_t_omega_over_sigma_sp`,
`nodal_temperature_adiabatic_tendency`, `State.sim_time`, and side-by-side
registry factories already exist.

The main risk is overfitting the failed iteration guardrail by hiding a tuned
pressure-work amplitude behind a ramp. The Implementer should therefore keep
the constants fixed from this proposal, avoid sweeps, preserve HSL2 theta
transport and all fixed evaluation protocols, and test that every non-thermal
state path remains on the incumbent branch. A clean near-zero result would still
be useful because it would show the large rejected pressure-work gain came from
the same short-lead imbalance that the guardrails correctly blocked.
