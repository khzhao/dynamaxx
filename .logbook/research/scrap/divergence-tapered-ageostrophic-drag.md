---
schema_version: 1
slug: divergence-tapered-ageostrophic-drag
title: Divergence-Tapered Ageostrophic Drag
status: scrap
created_at: 2026-06-23T08:48:19Z
author_role: Researcher
target_model: dino_hsl2_theta
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

# Divergence-Tapered Ageostrophic Drag

## Hypothesis

The incumbent has output-only 10 m wind improvements but still no prognostic
lower-boundary momentum sink: `DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY` is zero.
Plain Rayleigh drag and broad momentum filters risk damaging balanced flow.
However, much of the problematic low-level wind error should live in
ageostrophic divergent motion rather than in the rotational/geostrophic
component. Damping only the lower-layer divergent wind component, with a taper
that avoids already-convergent cyclone cores, may improve 10 m wind and MSLP
without the pressure-gradient damage expected from full wind drag.

## Mechanism

Register a side-by-side model such as `dino_hsl2_theta_divdrag`. Preserve every
incumbent thermodynamic, HSL2 theta, pressure, DFI, residual, and output path.
Add one positive-time rollout step filter:

- decompose modal wind into rotational and divergent components using existing
  vorticity/divergence representation; leave vorticity unchanged;
- apply weak exact exponential damping only to lower-layer divergence modal
  coefficients, with a vertical taper strongest at the lowest layer and zero by
  roughly sigma `0.70`;
- reduce damping in grid columns where nodal low-level convergence is already
  strong, so the filter avoids directly suppressing realistic cyclone/frontal
  inflow;
- no-op in the tropics or where finite diagnostics fail if the Implementer
  needs a conservative first version;
- leave temperature, log surface pressure, tracers, HSL2 theta transport,
  ocean heat flux, weak-HS forcing, and pressure-level output interpolation
  unchanged;
- keep DFI on the incumbent path so the time-reversed initialization is not
  altered by irreversible drag.

This differs from full ageostrophic or Rayleigh drag: it damps only the
divergent wind degree of freedom already present in the prognostic state.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for `dino_hsl2_theta_divdrag`.
- API changes:
  - None. Forecast inputs, outputs, metrics, target variables, and lead times
    stay fixed.
- Tests to update:
  - Verify vorticity, temperature, log surface pressure, and tracers are
    unchanged by the filter.
  - Verify zero divergence is exactly no-op and finite divergence is damped by
    the fixed exponential factor.
  - Verify the vertical taper is applied only in lower layers.
  - Verify strong-convergence taper reduces damping and nonfinite diagnostics
    fall back to the incumbent state.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium leads if noisy divergent low-level wind
    projects into the accepted 10 m diagnostic.
  - `mean_sea_level_pressure` may improve if excessive divergent adjustment is
    feeding pressure noise while rotational flow is preserved.
- Expected neutral metrics:
  - `geopotential_500` should remain close because vorticity and thermodynamics
    are unchanged directly.
  - `2m_temperature` should be nearly neutral because no drag heating or
    thermal tendency change is introduced.
- Possible regressions:
  - Divergence is part of real baroclinic development; damping it can weaken
    cyclogenesis and worsen MSLP or wind phase.
  - If current wind error is mostly rotational/geostrophic, the candidate will
    be neutral.

## Risks

- Numerical stability:
  - Low to moderate. Exponential damping is stable, but the convergence taper
    and modal/nodal conversions need finite guards.
- Compute cost:
  - Low. Modal divergence damping is cheap; optional nodal convergence taper
    adds one transform.
- Data leakage:
  - None. It uses only the forecast state and fixed constants.
- Physical plausibility:
  - Moderate. Boundary-layer friction preferentially damps ageostrophic flow,
    and divergence-selective damping is a conservative surrogate, but it is not
    a full turbulent closure.
- Rollback complexity:
  - Low. Remove one filter flag/helper, one factory/export, one registry entry,
    and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_theta_divdrag`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_theta_divdrag --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no early wind or MSLP guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_theta_divdrag --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` and clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean neutral iteration delta would show divergence-selective drag is not
    a material remaining error source. Any early MSLP or 10 m wind guardrail
    failure would show the filter is suppressing real balanced development.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` sets
  `DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY = 0.0`, so the accepted weak-HS path has
  no lower-layer momentum friction.
- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` uses vorticity
  and divergence as the momentum prognostic variables, making divergent-only
  damping an isolated filter on one state leaf.
- Dynamaxx history:
  `.logbook/history/2026-06-21_16-05-39_helmholtz-projected-momentum-diffusion/decision.md`
  rejected a fixed momentum-diffusion projection as clean but effectively
  neutral, motivating a different trigger and a lower-layer-only damping target.
- Dynamaxx history:
  `.logbook/history/2026-06-23_06-13-46_coriolis-centered-hsl-theta-departure/decision.md`
  showed another HSL trajectory refinement was clean but only
  `+0.0000054512704017462`, motivating non-HSL mechanisms.
- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press. Boundary-layer friction is described as
  producing ageostrophic cross-isobaric flow.
- Vallis, G. K. 2017. Atmospheric and Oceanic Fluid Dynamics, second edition.
  Cambridge University Press. https://doi.org/10.1017/9781107588417

## Researcher Notes

This is not another plain HSL trajectory variant; it does not touch theta
departure geometry, remap order, or vertical theta transport. It also differs
from staged `geostrophic-sparing-boundary-layer-drag`, which reconstructs and
damps the full ageostrophic wind relative to an approximate geostrophic wind.
This proposal is narrower: damp the prognostic divergence leaf directly in
lower layers and preserve vorticity exactly.

It is not a duplicate of rejected divergence-selective gravity-wave damping
from the older incumbent path because the new mechanism is lower-boundary,
positive-time, and convergence-tapered, not a broad gravity-wave or external
mode damping change. The expected lesson is whether a small, reversible
prognostic momentum sink can move wind/MSLP after recent HSL refinements have
stalled.

## Evaluator Notes

### 2026-06-23T08:52:24Z

Decision: move to `scrap`; ranked 3 of 3 new proposals.

This is too close to active staged drag ideas to keep as another candidate.
`rotational-sparing-divergence-drag` already covers the core mechanism:
positive-time lower-layer damping of modal divergence while preserving
vorticity and excluding DFI. `geostrophic-sparing-boundary-layer-drag` covers
the broader ageostrophic-drag family. The new convergence taper adds another
diagnostic transform and threshold without changing the central question enough
to justify a separate implementation slot.

The empirical record also penalizes this family. Earlier divergence and
momentum filters were weak, neutral, or risky, including
`helmholtz-projected-momentum-diffusion`, first-step divergence filtering, and
older divergence-selective damping. Because this proposal directly modifies
positive-time mass-wind adjustment, it can spend scarce MSLP/Z500 guardrail
margin even if diagnostics remain finite.

If momentum damping becomes attractive later, promote the simpler already
staged rotational-sparing divergence-drag proposal first and require one fixed
conservative timescale with tests proving vorticity, temperature,
`log_surface_pressure`, tracers, and DFI are unchanged. Do not carry this
convergence-tapered variant forward unless new diagnostics show that suppressing
only divergent outflow outside convergent cyclone/frontal regions is materially
different from the staged simpler filter.
