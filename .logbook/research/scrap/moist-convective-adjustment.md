---
schema_version: 1
slug: moist-convective-adjustment
title: Moist Convective Adjustment Toward a Moist-Adiabatic Profile
status: scrap
created_at: 2026-06-22T15:03:39Z
author_role: Researcher
target_model: dino_hsl_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/held_suarez.py
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

# Moist Convective Adjustment Toward a Moist-Adiabatic Profile

## Hypothesis

The dycore carries humidity (now horizontally semi-Lagrangian transported) but
has **no convective heat source**: temperature is driven only by Newtonian
relaxation, surface sensible flux, and resolved advection. In the real
atmosphere, moist convection is the dominant diabatic heating in conditionally
unstable, near-saturated columns; it redistributes heat vertically toward a
moist adiabat and is the primary driver of the tropical and warm-season divergent
circulation, which in turn shapes the large-scale geopotential and pressure
fields. A bounded **moist convective adjustment** -- relaxing conditionally
unstable, sufficiently moist columns toward a moist-adiabatic temperature profile
on a fixed convective timescale -- adds this missing heating and should improve
the thermal structure and the divergent circulation that feeds `geopotential_500`
and `mean_sea_level_pressure`.

## Mechanism

Register a side-by-side candidate named `dino_hsl_theta_convadj`. Preserve every
incumbent setting; add one bounded explicit heating term.

- Each step, in nodal space, test each column for conditional instability: where
  the lapse rate exceeds the moist-adiabatic lapse rate and the column humidity
  exceeds a fixed threshold fraction of saturation, compute a target
  moist-adiabatic temperature profile anchored to the column's lower-level state.
- Relax the column temperature toward that moist-adiabatic target on a fixed
  convective timescale (order hours), conserving column dry static energy so the
  adjustment redistributes heat vertically without adding net column energy.
- Bound the per-step heating magnitude and apply only where the instability and
  humidity criteria are met; leave stable or dry columns untouched.
- Do not alter winds, pressure, geopotential, the spectral dynamics, or the
  semi-Lagrangian transport; the adjustment acts on the prognostic temperature
  (theta) only.
- Apply identically in DFI and positive-time rollout; fall back to no adjustment
  if the target profile or humidity is nonfinite.

## Implementation Scope

- Expected files: `held_suarez.py` or a companion forcing (convective-adjustment
  tendency), `adapter.py` (compose the forcing and supply humidity), `__init__.py`,
  `registry.py`, tests under `tests/dycore/`.
- Registry changes: add only the side-by-side candidate.
- API changes: none.
- Tests to update: a conditionally unstable saturated column relaxes toward a
  moist adiabat with conserved column dry static energy; a stable or dry column is
  unchanged; the per-step bound and nonfinite fallback hold; non-temperature
  fields unchanged; registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements: `geopotential_500` and `mean_sea_level_pressure` through
  a better divergent circulation; `2m_temperature` in convective regimes.
- Expected neutral metrics: `10m_u_component_of_wind`.
- Possible regressions: spurious heating if the instability/humidity thresholds
  trigger too readily; the bounds and conservation constraint limit this.

## Risks

- Numerical stability: moderate; convective relaxation is stiff but bounded and
  energy-conserving, with a finite fallback.
- Compute cost: low-to-moderate; one column diagnosis and adjustment per step.
- Data leakage: none; uses the model's own temperature and humidity.
- Physical plausibility: high; moist convective adjustment is a classic
  convective closure.
- Rollback complexity: low.

## Evaluation Plan

- Fast gate: `uv run pytest`; `uv run dynamaxx-eval fast --model dino_hsl_theta_convadj`;
  finite forecasts, zero diagnostic issues.
- Iteration gate: `uv run dynamaxx-eval iteration --model dino_hsl_theta_convadj --workers 4`;
  support is primary-score delta at least `+0.002`, clean diagnostics, no guardrail failure.
- Validation gate: `uv run dynamaxx-eval validation --model dino_hsl_theta_convadj --workers 4`
  only after iteration promotion; require validation delta at least `+0.001`.
- Falsification: a clean near-zero or negative delta would show that adding moist
  convective heating does not help these extratropics-weighted surface/mid-level
  targets, consistent with the earlier rejection of large-scale saturation
  adjustment.

## Citations

- Citation or source:
  - Dynamaxx source: `held_suarez.py` provides only Newtonian relaxation and
    Rayleigh drag; humidity is transported (`horizontal-semilagrangian-passive-humidity`)
    but never feeds back as heating.
  - Dynamaxx history: `bounded-saturation-adjustment` was rejected; see Researcher
    Notes for why this differs in mechanism.
  - Manabe, S., Smagorinsky, J., Strickler, R. F. 1965. Simulated climatology of a
    general circulation model with a hydrologic cycle. Monthly Weather Review
    (moist convective adjustment).
    https://doi.org/10.1175/1520-0493(1965)093%3C0769:SCOAGC%3E2.3.CO;2
  - Betts, A. K. and Miller, M. J. 1986. A new convective adjustment scheme.
    Quarterly Journal of the Royal Meteorological Society.
    https://doi.org/10.1002/qj.49711247308

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-22 as an
orthogonal physics-process lever, decorrelated from the proven surface-flux
(surface, sensible) and semi-Lagrangian (transport numerics) veins.

Negative-evidence treatment (required by RESEARCHER.md): `bounded-saturation-adjustment`
was rejected, but it is a **different mechanism** -- large-scale removal of
grid-point supersaturation (condensation), which acts at each level independently
and does not restructure the column. Moist convective adjustment instead
**redistributes heat vertically** toward a moist adiabat in conditionally
unstable columns, supplying the convective heating that drives the divergent
circulation; its expected effect is on the large-scale `geopotential_500` /
`mean_sea_level_pressure` structure, not grid-point precipitation. This is the
mechanism-and-outcome distinction the role requires before revisiting a nearby
family. Honest expectation: medium risk given the saturation-adjustment rejection
and the extratropics-weighted metric; the falsification outcome cleanly settles
whether moist heating is recoverable skill here.

## Evaluator Notes

### 2026-06-22T17:26:11Z

Decision: move to `scrap`; rank 2 of 2 current proposals; not recommended for
implementation.

Reject this against the current `dino_hsl2_theta` incumbent. The proposal is
stale relative to the accepted state: it targets `dino_hsl_theta` and assumes
humidity is already horizontally semi-Lagrangian transported, but
`horizontal-semilagrangian-passive-humidity` is only staged, not accepted into
the `dino_hsl2_theta` incumbent. That makes the convective-adjustment premise
partly dependent on an unaccepted staged idea.

The physical family also has strong negative local evidence. Active moist
virtual-temperature dynamics failed or later regressed badly even after
finite-output repairs, bounded saturation adjustment regressed iteration by
`-0.026391567842939834` and failed early MSLP, Z500, and 10 m wind guardrails,
and the scrapped humidity-weighted radiative relaxation note already rejected a
weaker humidity-coupled thermal forcing as too empirical. This proposal is more
complex and more intrusive than those: it would diagnose conditional
instability, build a moist-adiabatic target, redistribute column heat, and
choose fixed thresholds/timescales in a dycore that has no accepted moist
closure or precipitation budget.

Moist convective adjustment is a physically real class of parameterization, but
as submitted it has too many closure constants, too much balance risk, and too
little evidence that latent heating can improve the fixed extratropics-weighted
WeatherBench2 targets without disturbing mass, height, and wind. It should be
scrapped rather than staged until a separately accepted passive-humidity
transport or moist-diagnostic result creates stronger local evidence.
