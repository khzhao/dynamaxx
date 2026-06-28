---
schema_version: 1
slug: mountain-blocking-form-drag
title: Add a Bounded Low-Level Mountain-Blocking Form Drag
status: staging
created_at: 2026-06-23T12:00:00Z
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

# Add a Bounded Low-Level Mountain-Blocking Form Drag

## Hypothesis

The incumbent runs on a flat boundary and has no orographic momentum sink. The
key historical lesson is that simply adding mean orography
(`terrain-aware-surface-pressure-orography`) produced a large aggregate skill
gain but catastrophic early Z500/MSLP RMSE failures: terrain forced stationary
waves and a pressure-gradient response with no compensating drag, so it did not
stick. In the real Lott & Miller (1997) scheme the dominant low-level momentum
sink near high terrain is NOT the vertically propagating wave (the staged
`orographic-wave-drag-split`), but **blocked-flow form drag**: when the
low-level Froude number is small, flow below the dividing-streamline height
`Z_blk` cannot ascend the obstacle, goes around it, and feels a strong bluff-body
form drag proportional to `|U|U`. This is exactly the missing "compensating
drag" that should let effective terrain coexist with the resolved flow. A
bounded, momentum-only form drag concentrated in the lowest layers should slow
the over-fast free-slip low-level jets over mountain belts and reduce the
synoptic phase/amplitude errors that feed MSLP and Z500, without ever touching
surface pressure, geopotential, or the pressure-gradient lower boundary that
broke the earlier terrain candidate.

## Mechanism

Register a side-by-side candidate (suffix `_mtn_block_drag`) that preserves all
accepted incumbent components (DFI, weak-HS analysis-offset equilibrium, Strang
Coriolis split, theta transport/recentering, off-centering, fixed horizontal
diffusion, surface residual memory, surface sensible heat flux, Richardson 10 m
diagnostic, output remap). The lower boundary stays modally flat
(`orography = 0` in `adapter.py:311`) so mass and pressure-gradient balance are
untouched.

Add a positive-time-only step filter after the non-Coriolis dynamics and before
the symmetric Coriolis half-step:

- Build a **static, smooth effective sub-grid orographic standard deviation**
  `mu` and a slope/anisotropy proxy from a fixed low-order spherical-harmonic
  representation of a coarse terrain field. Use a strong spectral taper
  (`truncated_modal_orography`/`filtered_modal_orography` already exist in
  `primitive_equations.py:673-704`) so only large-scale terrain envelope
  survives. Critically, `mu` enters ONLY the drag coefficient, never the
  geopotential or surface pressure.
- Diagnose nodal low-level wind `(u, v)` from vorticity/divergence (the
  transform path exists, used for output at `adapter.py:~1020`) and a
  lower-column Brunt-Vaisala frequency `N` from the current theta profile.
- Compute the dividing-streamline / blocking height `Z_blk = max(0, mu*(1 - Fr_c/Fr))`
  with `Fr = |U_low| / (N*mu)` and fixed critical `Fr_c ~ 0.5`. Below `Z_blk`
  (mapped to the lowest sigma layers via a smooth vertical weight) apply a
  bounded form-drag deceleration
  `dU/dt = -C_d * (sigma_blocking_fraction) * |U| U / mu`, anti-parallel to the
  local wind, with `C_d` a fixed O(1) constant.
- Hard-cap the per-step speed reduction (e.g. <= a few percent of `|U|` per
  900 s inner step) so the drag can never reverse wind direction, and apply a
  no-op taper where `|f|` is small or any diagnostic is nonfinite.
- Write the momentum increment back through the wind->vorticity/divergence path.
  Temperature, log surface pressure, tracers, DFI, forcing, recentering,
  residuals, MSLP, and geopotential diagnostics are all unchanged.

This is a `|U|U` bluff-body sink active only in blocked, low-Froude lowest-layer
flow over effective terrain. It is mechanistically the complement of the staged
wave-drag split, which is a linear `|U|`-scaled deceleration for the
*unblocked, vertically propagating* regime.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` (dataclass flag,
    effective-`mu` helper, blocking-drag step filter).
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` (export).
  - `src/dynamaxx/dycore/registry.py` (side-by-side factory).
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`,
    `test_dependency.py`, `tests/dycore/test_registry.py`.
- Registry changes:
  - One side-by-side model with suffix `_mtn_block_drag`.
- API changes:
  - None. The terrain proxy is a fixed static field bundled as a model constant
    (a coarse, smoothed sigma-harmonic envelope), NOT a new evaluation input
    channel, avoiding the dynamic pressure-level terrain dependency the
    Evaluator flagged for the wave-drag split.
- Tests to update:
  - Zero effective `mu` -> exact no-op.
  - High-Froude (unblocked) flow -> `Z_blk = 0` -> no-op.
  - Cap cannot reverse wind direction in one step.
  - Only vorticity/divergence change; temperature/log-ps/tracers identical.
  - Finite fallback on nonfinite `N`, wind, or Froude.
  - Registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` (~-0.05) at days 2-15: blocked-flow form drag
    slows excessive free-slip low-level flow over mountain belts; this is the
    most directly targeted variable.
  - `mean_sea_level_pressure` (~-0.27) at medium/late leads: removing the
    missing mountain torque should reduce systematic synoptic phase/amplitude
    drift.
  - `geopotential_500` (~+0.08) modestly at late leads via improved storm-track
    placement.
- Expected neutral metrics:
  - `2m_temperature` (~-1.01): no thermal forcing changed (no drag heating
    returned in the first candidate).
  - Day-1/lead-0 fields: small under the per-step cap.
- Possible regressions:
  - Over-drag can under-speed jets and worsen `10m_u_component_of_wind`.
  - Momentum removal can shift storm tracks and indirectly worsen MSLP/Z500.

## Risks

- Numerical stability:
  - Low to moderate. `|U|U` drag is dissipative and capped; finite-guarded.
- Compute cost:
  - Low. One wind transform pair plus local nodal ops per inner step; the static
    `mu` field is precomputed once.
- Data leakage:
  - None. Uses only forecast state, a fixed static terrain envelope, geometry,
    and fixed constants; no truth at valid leads, no validation statistics.
- Physical plausibility:
  - Moderate to high. Blocked-flow form drag is the standard low-level branch of
    Lott-Miller-type subgrid orographic drag in operational GCMs; this is a
    bounded resolved-grid surrogate of it.
- Rollback complexity:
  - Low. One flag, one helper, one factory, one registry entry, focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`; `uv run dynamaxx-eval fast --model <name>_mtn_block_drag`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model <name>_mtn_block_drag --workers 4`.
  - Support requires primary-score delta >= +0.002, clean diagnostics, no early
    day 1-5 RMSE guardrail failure, with special inspection of
    `10m_u_component_of_wind` and MSLP over days 5-15 and of early Z500/MSLP
    (the variables that broke the mean-orography candidate).
- Validation gate:
  - `uv run dynamaxx-eval validation --model <name>_mtn_block_drag --workers 4`
    only after iteration promotion; require >= +0.001 with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that low-level
    blocked-flow form drag is not the missing momentum sink. An early
    Z500/MSLP guardrail failure would show even momentum-only effective terrain
    still excites unbalanced response.

## Citations

- Lott, F. and Miller, M. J. 1997. A new subgrid-scale orographic drag
  parametrization: its formulation and testing. Q. J. R. Meteorol. Soc.
  https://doi.org/10.1002/qj.49712353704
  (Sections on the dividing-streamline height and the low-level blocked-flow
  form drag `~ C_d |U|U`, distinct from the propagating-wave stress.)
- Scinocca, J. F. and McFarlane, N. A. 2000. The parametrization of drag induced
  by stratified flow over anisotropic orography. Q. J. R. Meteorol. Soc.
  https://doi.org/10.1002/qj.49712656802
- ECMWF IFS Documentation CY49R1, Part IV: Physical Processes, subgrid-scale
  orographic drag (blocking + wave stress).
  https://www.ecmwf.int/en/elibrary/81626-ifs-documentation-cy49r1-part-iv-physical-processes

## Researcher Notes

Not a duplicate of staged `orographic-wave-drag-split`: that proposal is the
*vertically propagating mountain-wave* branch (a linear `|U|`-scaled
deceleration, parallel to the wind, gated on stability that *supports* wave
propagation). This proposal is the complementary *blocked-flow* branch, active
only when the low-level Froude number is small (`Z_blk > 0`), using a nonlinear
`|U|U` bluff-body form drag below the dividing-streamline height. In Lott-Miller
these are two physically separate terms; the orchestrator's note that mean
orography "did not stick (likely excited noise without the compensating
drag/blocking)" points specifically at this blocking branch.

Not a duplicate of `deformation-rate-momentum-damping` (strain-tensor eddy
viscosity, terrain-blind) or of the boundary-layer Rayleigh / geostrophic-sparing
drags (uniform low-level linear friction with no terrain gating). It avoids the
failure mode of `terrain-aware-surface-pressure-orography` by keeping the modal
orography flat and never feeding terrain into pressure, MSLP, or geopotential.
It avoids the Evaluator's concern about the wave-drag split's dynamic terrain
proxy by using a fixed static smoothed terrain envelope as a model constant.

## Evaluator Notes

### 2026-06-23T03:03:08Z

Decision: move to `staging`; ranked 3 of 4 current proposals.

This is physically distinct from staged `orographic-wave-drag-split` because it
targets the low-Froude blocked-flow form-drag branch rather than propagating
wave stress. It also avoids the known failure mode of mean-orography pressure
experiments by keeping terrain out of surface pressure, geopotential, and MSLP
diagnostics. That makes it worth preserving as a future momentum-only terrain
candidate.

Do not mark it ready now. The proposal still depends on a static smoothed
terrain envelope being available or bundled cleanly as a model constant. If that
requires new terrain data, static-data plumbing, or evaluation input support, it
must be handled as infrastructure rather than as a model-selection experiment.
It also competes with an already staged orographic-drag idea and would spend
guardrail margin on low-level momentum, storm-track phase, MSLP, and Z500 while
leaving the dominant `2m_temperature` error largely untouched. A future
promotion should first pin down the terrain source already available in-repo,
prove zero/missing-terrain no-op behavior, and keep the cap and constants fixed
before iteration scoring.
