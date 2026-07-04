---
schema_version: 1
slug: terrain-work-form-drag-heating
title: Terrain-Work Form Drag with Local Heat Return
status: ready
created_at: 2026-07-04T04:52:27Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth_orolift_lwind
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

# Terrain-Work Form Drag with Local Heat Return

## Hypothesis

The accepted incumbent improved by making the terrain-lift wind a shallow
lower-column wind, but the same flow still crosses smoothed terrain without any
momentum sink. Real orographic parameterizations represent low-level blocking
and form drag as a momentum loss when flow does mechanical work against terrain.
A weak drag tied to the incumbent's own resolved terrain-work diagnostic should
reduce low-level wind and mass-field drift without reopening pressure-gradient
or thermal-only terrain-lift variants. Returning the dissipated kinetic energy
as a capped local thermal increment should avoid the fully cold, momentum-only
drag bias risk.

## Mechanism

Add a side-by-side candidate such as
`dino_ri2m_ekman_depth_orolift_lwind_twork_drag`. Preserve every incumbent
selector, including lower-column orographic-lift wind.

For the candidate only, add a positive-time step filter after the existing
Ekman and orographic-lift filters:

- reuse the accepted smoothed terrain, terrain-gradient, equatorial taper,
  lower-column terrain wind, and `w_terrain = u_eff dh/dx + v_eff dh/dy`
  calculation from `_orographic_lift_theta_tendency_step_filter`;
- apply an anti-flow momentum increment only where `abs(w_terrain)` and terrain
  slope exceed fixed weak thresholds, with a smooth cap so one inner step cannot
  reverse the wind or exceed a small fraction of the incumbent wind-increment
  cap;
- distribute the momentum sink over the same lower-column layers used by the
  accepted effective wind rather than damping all levels or spectral modes;
- transform the wind increment through the existing nodal wind to modal
  vorticity/divergence path, preserving `log_surface_pressure` and tracers;
- diagnose dissipated kinetic energy from the applied wind decrement and return
  a small capped heat increment inside the existing orographic-lift sigma
  envelope, with layerwise area-mean removal;
- finite-fallback exactly to the incumbent when terrain, wind, projection, heat
  return, or transformed modal increments are invalid.

This is not another orographic-lift thermal-strength change. The new process is
a direct lower-column momentum sink with a thermodynamic energy return, driven by
the same accepted terrain-work estimate that already proved useful.

## Implementation Scope

- Expected files: `adapter.py` for a boolean selector, terrain-work drag helper,
  heat-return helper, and factory; `__init__.py` and `registry.py` for export and
  side-by-side registration; focused dycore and registry tests.
- Registry changes: add one candidate key derived from
  `dino_ri2m_ekman_depth_orolift_lwind`.
- API changes: none.
- Tests to update: zero terrain and flat terrain exact no-op; zero wind exact
  no-op; cap cannot reverse wind; heat return is capped and area-mean neutral;
  only vorticity/divergence/temperature may change; finite fallback; factory and
  registry coverage.

## Expected Metric Movement

- Expected improvements: `10m_u_component_of_wind` at days 2-15 from reduced
  excessive cross-terrain low-level flow; `mean_sea_level_pressure` and
  `geopotential_500` from weaker terrain-induced phase drift.
- Expected neutral metrics: lead-zero outputs and non-terrain oceanic columns.
- Possible regressions: over-drag can slow useful low-level jets; heat return
  can damage `2m_temperature` if applied too close to the surface or too
  broadly.

## Risks

- Numerical stability: moderate; wind increments are dissipative and capped, but
  the filter edits prognostic momentum every positive step.
- Compute cost: low; it reuses wind transforms and terrain-gradient helpers
  already present in the incumbent.
- Data leakage: none; it uses static terrain, geometry, and forecast state only.
- Physical plausibility: high enough for a reduced test; form drag and
  dissipative heating are established subgrid-orography and frictional-energy
  concepts.
- Rollback complexity: low; one opt-in selector, helper/filter, factory/export,
  registry entry, and tests.

## Evaluation Plan

- Fast gate: `uv run pytest` and
  `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag`.
- Iteration gate:
  `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag --workers 4`.
- Validation gate:
  `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag --workers 4`
  only after iteration promotion.
- Outcome that would falsify the hypothesis: clean iteration delta below the
  promotion threshold, `10m_u_component_of_wind` regression, or any early
  `2m_temperature`/MSLP/Z500 guardrail failure.

## Citations

- Lott, F. and Miller, M. J. 1997. "A new subgrid-scale orographic drag
  parametrization: its formulation and testing." Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1002/qj.49712353704
- ECMWF IFS Documentation CY49R1, Part IV: Physical Processes, subgrid-scale
  orographic drag. https://www.ecmwf.int/en/elibrary/81626-ifs-documentation-cy49r1-part-iv-physical-processes
- Scinocca, J. F. and McFarlane, N. A. 2000. "The parametrization of drag
  induced by stratified flow over anisotropic orography." Quarterly Journal of
  the Royal Meteorological Society. https://doi.org/10.1002/qj.49712656802
- Code reference: `src/dynamaxx/dycore/models/dinosaur/adapter.py`,
  `_orographic_lift_theta_tendency_step_filter`,
  `_orographic_lift_lower_column_weighted_wind`, and
  `_ekman_coupled_surface_step_filter`.

## Researcher Notes

This rewrites the under-tested mountain-drag family into a sharper incumbent
follow-up. It is not staged `mountain-blocking-form-drag`, which introduces a
separate subgrid `mu`, Froude-number blocking height, and no heat return. This
proposal deliberately uses the already accepted terrain-work path and lower
column wind so it is side-by-side, smaller, and tied to positive evidence.

It avoids the recent failed orographic variants: low-mode orographic wind
smoothed the accepted thermal forcing and broke T2m; hypsometric layer height
changed thermal geometry only; product dealiasing was a cleanup filter. This is
a momentum-plus-energy process, not another thermal lift tuning.

## Evaluator Notes

### 2026-07-04T04:55:44Z

Decision: move to `ready`; ranked 1 of 1 ready proposals in this triage.

This is the strongest current proposal because it is side-by-side,
implementable inside the existing Dinosaur adapter, and tests a distinct
momentum mechanism rather than another small orographic-lift thermal geometry
change. Local code already computes the accepted smoothed terrain, terrain
gradient, lower-column terrain wind, `w_terrain`, vertical envelope, wind
projection path, caps, and finite fallbacks in the Ekman and orographic-lift
filters, so the proposed implementation can be bounded without new data
channels or source-code infrastructure.

The scientific basis is credible: Lott-Miller-style and ECMWF orographic-drag
documentation distinguish low-level blocking/form drag and gravity-wave drag,
and recent ECMWF work explicitly treats low-level flow blocking and turbulent
orographic form drag as separate contributors to the momentum budget. This
proposal also avoids the static-data weakness of staged
`mountain-blocking-form-drag` by reusing the already accepted terrain-work
diagnostic instead of introducing a new subgrid terrain envelope.

The risks are real but acceptable for one ready experiment. Recent terrain-lift
follow-ups were mostly neutral or negative, and the rejected
`ekman-dissipative-heat-return` is negative evidence against assuming thermal
energy return will help. The difference is that the primary tested signal here
is a terrain-gated lower-column momentum sink, while heat return is deliberately
capped and area-mean-neutral. If implemented, keep constants fixed before
scoring, cap the wind decrement so it cannot reverse flow, preserve exact
incumbent behavior over flat terrain or invalid diagnostics, and treat any
`2m_temperature` guardrail movement as the key failure channel.
