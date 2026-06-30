---
schema_version: 1
slug: coriolis-scaled-ekman-depth-coupling
title: Coriolis-Scaled Depth For The Coupled Ekman Closure
status: staging
created_at: 2026-06-30T00:57:29Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
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

# Coriolis-Scaled Depth For The Coupled Ekman Closure

## Hypothesis

The accepted `dino_ri2m_ekman_coupled` incumbent showed that a tightly bounded
surface stress plus mass-neutral Ekman pumping is a high-value missing process.
The current implementation still uses a globally fixed 2000 m boundary-layer
depth and a fixed two-layer vertical taper. That makes the stress projection
geometrically uniform even though real Ekman-layer depth depends on friction
velocity, rotation, and stability, and therefore varies strongly with latitude
and flow regime.

Recent negative evidence argues against nearby coefficient tweaks: static
roughness weighting was essentially neutral, output-only wind veering regressed,
and pressure-work thermal coupling was subthreshold. This proposal changes the
geometry of the accepted closure instead of its strength. A bounded,
Coriolis-scaled effective Ekman depth can keep the accepted stress-pumping
coupling while placing the same surface stress into a more realistic vertical
mass of air: shallower and more bottom-confined at high latitudes and in weak
flow, deeper and weaker per unit mass where the Coriolis constraint is smaller.

## Mechanism

Register a side-by-side candidate, for example `dino_ri2m_ekman_depth`, derived
from `ekman_coupled_dinosaur_dycore_model()`.

Inside `_ekman_coupled_surface_step_filter` only:

- keep the incumbent drag coefficient, stress formula, wind increment caps,
  log-pressure caps, equatorial pumping taper, area-neutral projections, and
  finite fallback behavior;
- diagnose a local friction velocity proxy from the same incumbent bulk stress,
  `u_star = sqrt(C_D) * |V_lowest|`, using the already guarded lowest-layer wind;
- compute a bounded neutral effective depth
  `h_ek = clip(C_h * u_star / max(|f|, f_floor), 500 m, 2500 m)`, with one fixed
  coefficient chosen before implementation so the global mean depth is near the
  incumbent 2000 m for typical midlatitude winds;
- build a smooth vertical weight over the lowest sigma layers using the
  hypsometric height of layer centers above the surface; normalize the weights
  so the vertically integrated acceleration equals the incumbent surface-stress
  impulse divided by `h_ek`;
- compute the Ekman-transport/log-pressure increment from the actually applied
  lowest-layer stress acceleration, preserving the accepted stress-pumping
  coupling;
- fall back exactly to the incumbent fixed-depth Ekman filter if depth,
  hypsometric height, wind, pressure, or projection diagnostics are nonfinite.

This is not a drag-amplitude sweep, a roughness class, a Helmholtz projection,
or a thermal pressure-work add-on. The only intended change is the vertical
projection/depth of the already accepted stress impulse.

## Implementation Scope

- Expected files:
  - `adapter.py`: add a default-false
    `use_coriolis_scaled_ekman_depth` flag, local depth/vertical-weight helper,
    and side-by-side factory.
  - `__init__.py`: export the candidate factory.
  - `registry.py`: register one short candidate key.
  - tests: focused helper, fallback, and registry coverage.
- Registry changes: one new key such as `dino_ri2m_ekman_depth`.
- API changes: none.
- Tests to update:
  - Fixed-depth mode reproduces the incumbent helper output.
  - `h_ek` is finite, positive, bounded, and monotone increasing with `u_star`
    and decreasing with `|f|` outside the floor.
  - Vertical weights are nonnegative, lower-layer confined, and normalized so
    the applied stress impulse is conserved before caps.
  - Nonfinite depth or pressure diagnostics fall back to the incumbent fixed
    depth path.
  - Candidate factory preserves all `dino_ri2m_ekman_coupled` flags and changes
    only the depth selector.

## Expected Metric Movement

- Expected improvements: `10m_u_component_of_wind` from a more realistic
  lower-layer momentum sink; `mean_sea_level_pressure` and `geopotential_500` if
  the accepted pumping signal is retained while vertical stress placement is
  less globally uniform.
- Expected neutral metrics: `2m_temperature`, because RI2m, residual memory,
  ocean heat flux, and thermal tendencies are untouched.
- Possible regressions: if the accepted fixed 2000 m depth is acting as an
  empirical compensator, redistributing the same stress can give back part of
  the large accepted Ekman gain; high-latitude U10 and early MSLP need close
  guardrail inspection.

## Risks

- Numerical stability: low to moderate. The filter remains capped and finite
  guarded, but it changes an accepted high-signal closure.
- Compute cost: low. It adds local depth/height arithmetic inside an existing
  filter and no new spectral transforms beyond the incumbent path.
- Data leakage: none; uses only forecast state, latitude, sigma geometry, and
  fixed constants.
- Physical plausibility: high as a first-order Ekman-layer scaling test, while
  still much simpler than a full turbulent boundary-layer scheme.
- Rollback complexity: low; one flag/helper branch, one factory/export, one
  registry entry, and tests.

## Evaluation Plan

- Fast gate: run `uv run pytest`, then
  `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth`; require finite
  forecasts and zero diagnostic issues.
- Iteration gate: run
  `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth --workers 4`;
  support requires at least `+0.002` over cached incumbent iteration primary
  `-0.16500618979404214`, clean diagnostics, and all fixed RMSE guardrails.
- Validation gate: only after iteration promotion, run
  `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth --workers 4`;
  require at least `+0.001` over cached incumbent validation primary
  `-0.16591150807771451`.
- Outcome that would falsify the hypothesis: a clean subthreshold or negative
  iteration delta would show that the accepted fixed-depth projection is already
  close to optimal for this coarse WeatherBench2 target. Any early U10, MSLP, or
  Z500 guardrail failure would show the geometry change breaks the accepted
  stress-pumping balance.

## Citations

- Tan, B. 2000. "Ekman Pumping for Stratified Planetary Boundary Layers Adjacent
  to a Free Surface or Topography." Journal of the Atmospheric Sciences.
  https://doi.org/10.1175/1520-0469(2000)057%3C3334:EPFSPB%3E2.0.CO;2
- de Roode, S. R. and Siebesma, A. P. 2020. "A Bound on Ekman Pumping."
  Journal of Advances in Modeling Earth Systems.
  https://doi.org/10.1029/2019MS001976
- Troen, I. and Mahrt, L. 1986. "A Simple Model of the Atmospheric Boundary
  Layer; Sensitivity to Surface Evaporation." Boundary-Layer Meteorology.
  https://doi.org/10.1007/BF00122760
- Vickers, D. and Mahrt, L. 2004. "Evaluating Formulations of Stable Boundary
  Layer Height." Journal of Applied Meteorology.
  https://doi.org/10.1175/JAM2160.1
- ECMWF IFS Documentation, Part IV: Physical Processes, sections on boundary
  layer diffusion, friction velocity, and near-surface diagnostics.
  https://www.ecmwf.int/sites/default/files/2023-06/Part-IV-Physical-Processes.pdf
- Local positive evidence:
  `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/decision.md`
  accepted the fixed-depth coupled stress-pumping closure with iteration delta
  `+0.04799113626142959` and validation delta `+0.04683104652127085`.
- Local negative evidence:
  `.logbook/history/2026-06-29_21-03-42_static-roughness-weighted-ekman-coupling/decision.md`
  found static roughness redistribution effectively neutral, so this proposal
  avoids roughness weights and changes the vertical depth geometry instead.

## Researcher Notes

This is intentionally near the accepted mechanism but not a near-duplicate of
the rejected roughness, pressure-work, or output-veering ideas. It preserves the
accepted stress-pumping pair and tests whether the remaining error is from
putting a good stress into a globally fixed vertical mass. It is also distinct
from staged `helmholtz-projected-ekman-coupling`: that proposal changes which
wind component receives the stress increment, while this proposal keeps the
full vector increment and changes only the bounded vertical depth/weighting.

## Evaluator Notes

### 2026-06-30T01:04:27Z

Decision: move to `staging`; plausible but not the next implementation target.

The scientific premise is credible. A neutral boundary-layer depth scale
proportional to friction velocity over Coriolis frequency is standard
first-order PBL dimensional reasoning, and the proposal preserves the accepted
stress-pumping pair, caps, equatorial taper, area-neutral projections, and finite
fallback. It is also not the same as the rejected static roughness experiment:
roughness redistributed stress using fixed surface classes, while this proposal
uses forecast-state wind speed and latitude to vary the effective stress depth.

Do not promote it to `ready` in this triage batch. The accepted
`dino_ri2m_ekman_coupled` closure is the current incumbent because it produced a
large iteration and validation gain. The immediately subsequent Ekman-adjacent
history is cautionary: output wind veering regressed, pressure-work thermal
coupling was stable but subthreshold, and static roughness weighting was almost
exactly neutral. This candidate changes the geometry and local amplitude of the
same high-signal accepted closure, so a negative or subthreshold result would
likely spend another run on nearby coefficient/geometry refinement rather than
testing a more independent remaining error source.

Keep staged because it is still differentiated from Helmholtz-projected Ekman
coupling and from roughness weighting. Promotion would need either diagnostics
showing that the fixed 2000 m projection is a remaining leading error source, or
exhaustion of more orthogonal ready ideas. If promoted later, the coefficient
setting must be fixed before implementation, the mean-depth calibration must not
use validation feedback, and tests should prove depth bounds, monotonicity with
`u_star` and `|f|`, stress-impulse normalization, exact incumbent fallback, and
preservation of every non-depth Ekman option.
