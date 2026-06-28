---
schema_version: 1
slug: near-surface-stability-heat-mixing
title: Bounded Stability-Dependent Near-Surface Vertical Heat Mixing
status: scrap
created_at: 2026-06-19T15:49:30Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Bounded Stability-Dependent Near-Surface Vertical Heat Mixing

## Hypothesis

`2m_temperature` is now the dominant remaining error: after the accepted
off-centering win, its area-weighted skill is roughly `-1.67`, far worse than
persistence at every lead, while the mass and wind fields are near or above
persistence at short lead. The model has **no vertical heat mixing** -- the only
boundary-layer process is the Held-Suarez Rayleigh **momentum** drag
(`held_suarez.py`, coefficient `kf` and 3D `kv`). The near-surface temperature
column is therefore pinned by idealized HS thermal relaxation and repaired only
by an output diagnostic. Without any turbulent heat exchange between the lowest
model layers, the surface-layer temperature structure cannot respond to
stability, so the lead-zero residual correction decays into a large standing
error. A minimal **stability-dependent vertical heat diffusion** in the lowest
sigma layers would let near-surface temperature mix toward the column under
unstable stratification and stay stratified when stable, attacking the
`2m_temperature` error at its physical source rather than post hoc.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_pbl_heat_mix`.
Preserve incumbent initialization, DFI, weak-HS forcing, exact symmetric
Coriolis split, horizontal diffusion, potential-temperature tendency, theta mean
recentering, stability-aware residual decay, Richardson 10 m wind diagnostic,
Rayleigh momentum drag, output variables, WeatherBench2 splits, lead times,
metrics, and deterministic gates.

For the candidate only, add an opt-in vertical heat-mixing tendency confined to
the lowest few sigma layers:

- compute a bounded bulk Richardson number between adjacent lower sigma layers
  from the existing potential-temperature and wind state (reuse the diagnostic
  machinery already added for the Richardson 10 m wind candidate);
- form a stability-dependent vertical eddy diffusivity `K_h` for temperature
  that increases under unstable stratification (negative Richardson number) and
  decays to a small floor under stable stratification, with a fixed upper bound
  and a fixed maximum sigma-level depth (for example the lowest two or three
  layers only);
- apply `K_h` as an implicit or sub-stepped vertical diffusion of temperature
  (and optionally specific humidity) using a tridiagonal solve over the affected
  layers, with zero heat flux at the model top of the mixed region and a
  bounded surface-layer flux consistent with the diagnosed stability;
- conserve column dry static energy within the mixed layers to machine
  precision so no net heating is introduced;
- do not modify momentum (Rayleigh drag is unchanged), do not modify the free
  troposphere above the mixed region, and keep horizontal diffusion and forcing
  unchanged;
- use the identical mixing in DFI and positive-time rollout, since vertical
  diffusion is a reversible parameterized process, not an output correction;
- fall back to the incumbent (no heat mixing) if the tendency produces nonfinite
  values or violates the dry-static-energy conservation check.

This is a prognostic boundary-layer **heat** process. It is distinct from the
staged `bulk-richardson-2m-temperature-diagnostic` (an output-only 2 m diagnostic),
from `exponential-boundary-layer-rayleigh-drag` and `surface-drag-theta-dissipation`
(staged momentum/drag ideas), and from the surface residual corrections in the
incumbent (output post-processing).

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` (vertical
    heat-mixing tendency)
  - `src/dynamaxx/dycore/models/dinosaur/held_suarez.py` (optional shared
    stability/diffusivity helper)
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, input/output/target variables, lead times,
    splits, metrics, and deterministic gates are unchanged.
- Tests to update:
  - Unit-test that an unstable lower column relaxes toward a well-mixed profile
    and a stable column is nearly unchanged.
  - Unit-test that column dry static energy in the mixed layers is conserved to
    tolerance and the free troposphere is untouched.
  - Unit-test the upper-bound clip on `K_h` and the finite-fallback path.
  - Verify the candidate factory preserves every incumbent setting except the
    heat-mixing tendency.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 1-10 if the standing near-surface temperature error
    is partly due to the absence of turbulent heat exchange.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500`, since only lower-layer
    temperature is mixed and column energy is conserved.
  - `10m_u_component_of_wind`, since momentum is unchanged.
- Possible regressions:
  - Over-mixing can warm or cool the screen level the wrong way if the diagnosed
    stability is biased, degrading `2m_temperature` instead.
  - Coupling the mixed temperature back through hydrostatic geopotential could
    perturb early `geopotential_500`/`mean_sea_level_pressure` if energy
    conservation is imperfect.

## Risks

- Numerical stability:
  - Moderate. Vertical diffusion is stiff; an implicit tridiagonal solve over a
    few layers with a bounded diffusivity keeps it stable, and the
    finite-fallback and conservation checks guard failures.
- Compute cost:
  - Low. A short tridiagonal solve over a few layers per step; no change to
    resolution, lead count, output volume, or worker count.
- Data leakage:
  - None. Uses only forecast temperature, wind, and sigma geometry with fixed
    constants; no verification-time information.
- Physical plausibility:
  - High. Stability-dependent vertical eddy diffusion of heat is a standard
    boundary-layer closure; the model presently lacks it entirely.
- Rollback complexity:
  - Low. Remove one tendency term and helper, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_pbl_heat_mix`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_pbl_heat_mix --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` with
    clean diagnostics and no early-lead or variable-by-lead RMSE guardrail
    failure. Because `2m_temperature` carries the largest deficit, even a
    moderate per-variable improvement there can clear the gate.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_pbl_heat_mix --workers 4`
    only after iteration promotion; require validation primary delta at least
    `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the standing
    `2m_temperature` error is set by the HS thermal forcing and the surface
    diagnostic rather than by missing turbulent heat exchange, indicating that
    near-surface temperature skill is not recoverable without changing the
    forcing itself.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
    implements only Rayleigh momentum drag (`kf`, `kv`); no vertical heat
    diffusion exists in the dycore.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic`
    showed a bulk-Richardson surface-layer treatment substantially improved
    `10m_u_component_of_wind`; this proposal applies surface-layer stability as a
    prognostic heat process for the analogous, larger `2m_temperature` deficit.
  - Louis, J. F. 1979. A parametric model of vertical eddy fluxes in the
    atmosphere. Boundary-Layer Meteorology.
    https://doi.org/10.1007/BF00117978
  - Holtslag, A. A. M. and Boville, B. A. 1993. Local versus nonlocal
    boundary-layer diffusion in a global climate model. Journal of Climate.
    https://doi.org/10.1175/1520-0442(1993)006%3C1825:LVNBLD%3E2.0.CO;2
  - Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of
    the dynamical cores of atmospheric general circulation models. Bulletin of
    the American Meteorological Society.
    https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-19; recorded
here for provenance honesty in the autonomous loop.

This targets the dominant remaining error revealed by the post-`si_offcenter`
per-variable breakdown: `2m_temperature` near `-1.67` while the mass field is
near or above persistence at short lead. It is distinct from prior near-surface
work because every accepted or staged near-surface idea so far is either an
output diagnostic (`surface-layer-richardson-wind-diagnostic`,
`stability-aware-surface-residual-decay`, staged
`bulk-richardson-2m-temperature-diagnostic`) or a momentum process
(`exponential-boundary-layer-rayleigh-drag`, `surface-drag-theta-dissipation`).
None add a prognostic vertical heat-mixing tendency. It is intentionally
confined to the lowest layers and conserves column dry static energy so the
already-good mass field is protected; the falsification outcome cleanly
separates "missing physics" from "HS forcing ceiling" as the cause of the
`2m_temperature` deficit.

## Evaluator Notes

### 2026-06-19T17:53:23Z

Decision: move to `scrap`; ranked 2 of 2 fresh proposals.

The physical mechanism is not invalid: stability-dependent boundary-layer heat
diffusion is a standard closure family, and the incumbent still has a large
`2m_temperature` deficit. The cost-risk tradeoff is unfavorable for the current
optimization loop. This proposal adds a prognostic lower-column heat-mixing
tendency, a bounded Richardson-dependent diffusivity, an implicit or sub-stepped
vertical solve, dry-static-energy checks, DFI and positive-time wiring, and new
fallback behavior. That is a materially larger implementation surface than the
bounded output diagnostics and local residual mechanisms that have actually
worked in recent history.

Local evidence favors safer near-surface work first. The accepted
stability-aware residual decay and accepted Richardson 10 m wind diagnostic
were bounded diagnostic/output changes with negligible mass-field side effects.
The earlier surface-layer diagnostic extrapolation was strongly negative for
near-surface guardrails, showing that even output-only surface-layer changes can
fail badly. Active staged alternatives already test lower-risk `2m_temperature`
paths, including bounded Richardson screen-temperature diagnostics, diurnal
surface residual memory, and lower-column thermal IAU. A prognostic PBL heat
mixing tendency would couple directly into hydrostatic thickness, MSLP, Z500,
and wind evolution, spending guardrail margin that the accepted off-centered
incumbent just improved.

Scrap this version for current model selection. A future revisit should start
as an offline column or diagnostic study that estimates whether the lower
sigma-layer thermal bias is actually correctable by conservative vertical heat
mixing before adding a new prognostic PBL tendency to the dycore.
