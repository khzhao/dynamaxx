---
schema_version: 1
slug: lapse-rate-held-suarez-relaxation
title: Add a Weak Lapse-Rate Component to the Analysis-HS Thermal Relaxation
status: staging
created_at: 2026-06-21T12:19:53Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a Weak Lapse-Rate Component to the Analysis-HS Thermal Relaxation

## Hypothesis

The accepted analysis-offset Held-Suarez equilibrium anchors large-scale
absolute temperature anomalies, but hydrostatic height and MSLP errors are also
sensitive to vertical temperature gradients. Recent theta-recentering and
post-step variance guards were neutral or negative, which argues against more
state repair after each step. A weaker forcing-level mechanism can instead
retain the accepted absolute-temperature equilibrium while adding a bounded,
column-mean-neutral lapse-rate component diagnosed from the same initial
analysis.

Relaxing a small part of the lower- and mid-tropospheric vertical temperature
gradient toward the analyzed low-mode gradient should improve hydrostatic
thickness evolution without changing local pressure coupling, removing the
accepted analysis-HS offset, or adding broad timestep/startup changes.

## Mechanism

Register one side-by-side candidate with a suffix such as `_hs_lapse_rate`.
Preserve the incumbent analysis-HS equilibrium offset exactly, then add a
separate weak lapse-rate tendency inside the Held-Suarez forcing wrapper.

For this candidate only:

- at forecast initialization, diagnose the accepted nodal analysis temperature
  and standard Held-Suarez equilibrium temperature on sigma layers;
- compute the vertical first difference of the low-mode analysis-minus-HS
  temperature offset, using the same low-mode horizontal mask as the accepted
  analysis-HS offset;
- reconstruct a bounded column-mean-neutral temperature-offset component whose
  vertical differences match only a capped fraction of that analyzed lapse-rate
  anomaly;
- add this component to the thermal relaxation target with a separate weak
  multiplier, for example no more than `25%` of the accepted analysis-HS offset
  amplitude and the same fixed Kelvin cap family;
- keep local surface-pressure dependence in the standard HS equilibrium
  calculation unchanged;
- leave vorticity, divergence, `log_surface_pressure`, tracers, DFI,
  off-centering, Coriolis split, residual memory, 10 m wind diagnostic, and
  pressure-level outputs unchanged;
- fall back to the incumbent accepted analysis-HS equilibrium when the
  lapse-rate reconstruction is nonfinite or violates the fixed cap.

This is a forcing-target vertical-structure experiment, not theta-recentering,
not a post-step static-stability limiter, and not a fixed-pressure
analysis-HS-equilibrium variant.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/held_suarez.py` if a reusable forcing
    subclass is cleaner than adapter-local target construction
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate ending in `_hs_lapse_rate`.
- API changes:
  - None. The forecast contract, target variables, lead schedule, and fixed
    protocols stay unchanged.
- Tests to update:
  - Unit-test that the reconstructed lapse-rate component has near-zero
    column-mean temperature offset.
  - Verify vertical differences are capped and low-mode filtered.
  - Verify the standard accepted analysis-HS offset is unchanged when the new
    selector is disabled.
  - Verify finite fallback returns incumbent behavior.
  - Verify all non-forcing incumbent flags are preserved.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at days 3 to 15 if vertical thermal-gradient drift is a
    remaining source of hydrostatic thickness error.
  - `mean_sea_level_pressure` if improved thickness evolution reduces balanced
    mass-field drift without changing surface-pressure tendency.
  - `2m_temperature` should remain neutral to slightly positive because the
    accepted absolute lower-column thermal anchor remains present.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because wind tendencies,
    Coriolis treatment, and the 10 m diagnostic are unchanged.
- Possible regressions:
  - The accepted absolute-temperature offset may already encode the useful
    vertical structure, and adding a lapse-rate component could overconstrain
    baroclinic thermal evolution.

## Risks

- Numerical stability:
  - Low to moderate. The added forcing is bounded and thermal-only, but it
    changes the persistent relaxation target.
- Compute cost:
  - Low. It adds one vertical reconstruction while building the per-initial
    analysis-HS target.
- Data leakage:
  - None. It uses only same-time initial analysis fields already consumed by the
    incumbent analysis-HS equilibrium.
- Physical plausibility:
  - Moderate. Hydrostatic balance depends on vertical temperature gradients, but
    this is still a simplified relaxation target rather than a full radiation or
    convection closure.
- Rollback complexity:
  - Low. Remove one target-construction helper, one selector, one factory/export,
    one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run fixed `iteration` against the incumbent cache under the Orchestrator's
    worker policy.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failures.
- Validation gate:
  - Run fixed `validation` only after iteration promotion.
  - Support requires validation primary delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that lapse-rate
    structure in the accepted weak-HS target is not a material remaining error.
    Any early MSLP, Z500, or 10 m wind guardrail failure would show the added
    baroclinic thermal forcing disrupts balance.

## Citations

- Held, I. M., and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society, 75, 1825-1830.
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to
  Geophysics. Springer. Describes hydrostatic primitive-equation thermal
  coupling and the role of vertical temperature structure in pressure/geopotential
  balance.
- Code reference: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_analysis_offset_weak_held_suarez_equilibrium`; `held_suarez.py` implements
  the standard local-pressure-dependent thermal equilibrium.

## Researcher Notes

This accounts for the latest negative evidence by leaving local pressure
coupling in the accepted analysis-HS equilibrium unchanged and by avoiding
fixed-pressure HS targets. It is also not a theta-recentering weighting variant,
not a startup timestep/subcycling idea, and not a divergence cleanup. Compared
with staged `static-stability-limited-analysis-hs-offset`, this proposal adds a
small column-mean-neutral lapse-rate target rather than clipping the accepted
offset for stability after it is constructed.

## Evaluator Notes

### 2026-06-21T12:28:02Z

Decision: move to `staging`; physically plausible, but the family is crowded
and recent evidence raises the bar.

The mechanism is distinct from the latest rejected fixed-pressure
analysis-HS-equilibrium experiment because it keeps the accepted local surface
pressure coupling and changes only a bounded vertical-structure component of
the thermal relaxation target. Hydrostatic thickness is sensitive to vertical
temperature structure, so a small column-mean-neutral lapse-rate component is a
reasonable hypothesis and lower risk than post-step theta repair.

Keep staged rather than ready. The accepted analysis-HS offset was a strong
gain, but follow-ups have been weak or negative: rate masking was severely
bad, lead decay and smooth spectral taper were clean but far below promotion,
fixed-pressure analysis-HS regressed by `-0.0040528596151061524`, and
mass-weighted theta recentering was slightly negative. This proposal also
overlaps active staged `static-stability-limited-analysis-hs-offset`,
`virtual-temperature-analysis-hs-offset`, `column-neutral-weak-hs-heating-split`,
and `tropopause-capped-thermal-relaxation`. It should be revisited only after
there is diagnostic evidence of vertical thermal-gradient error or after
lower-risk output/diagnostic candidates are exhausted.
