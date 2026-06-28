---
schema_version: 1
slug: energy-normalized-coriolis-rotation
title: Normalize Exact Coriolis Rotation to Preserve Layer Kinetic Energy
status: staging
created_at: 2026-06-20T08:56:40Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
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

# Normalize Exact Coriolis Rotation to Preserve Layer Kinetic Energy

## Hypothesis

The accepted Strang Coriolis split is based on an exact local wind-vector
rotation. In continuous dynamics, Coriolis acceleration changes wind direction
but does no work. The adapter rotates winds in nodal space and then projects the
result back to spectral vorticity/divergence. That projection and truncation can
introduce small layerwise horizontal kinetic-energy drift at every inner step.

A bounded kinetic-energy normalization inside the exact Coriolis rotation filter
should preserve the intended no-work property of the split without changing
phase, off-centered SIL3 damping, residual correction, or thermodynamics. If
small projection energy drift accumulates into wind or mass-field error, this
should improve `10m_u_component_of_wind`, `geopotential_500`, or
`mean_sea_level_pressure`.

## Mechanism

Register a side-by-side model named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_coriolis_ke_norm`.

For this candidate only:

- keep the incumbent symmetric exact Coriolis split and non-Coriolis primitive
  equation exactly as currently configured;
- in `_exact_coriolis_rotation_step_filter`, compute layerwise horizontal
  kinetic energy of the input wind using the existing quadrature weights;
- apply the existing exact nodal Coriolis rotation and modal reconstruction;
- reconstruct the post-projection wind from the candidate modal vorticity and
  divergence, compute its layerwise kinetic energy, and scale only the
  candidate vorticity/divergence pair by a bounded factor
  `sqrt(previous_ke / projected_ke)`;
- cap the scale factor tightly, for example to `[0.98, 1.02]`, and use the
  unnormalized rotation if the energies are nonfinite or too small;
- leave temperature, `log_surface_pressure`, tracers, DFI, weak-HS forcing,
  theta recentering, offcentering, diffusion, output interpolation, and
  near-surface residual memory unchanged.

The normalization is positive-time only because the accepted incumbent keeps DFI
on the unsplit Coriolis equation. It is not a new time integrator.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry entry for the candidate model name
    above.
- API changes:
  - None. The forecast API, target variables, lead schedule, fixed protocols,
    and worker policy remain unchanged.
- Tests to update:
  - Verify the factory preserves all incumbent options except the kinetic-energy
    normalization selector.
  - Unit-test that the normalized rotation preserves non-wind state leaves.
  - Unit-test that finite synthetic winds preserve layer kinetic energy more
    closely than the unnormalized projection path.
  - Unit-test cap and fallback behavior for zero, tiny, and nonfinite energy.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and long leads if Coriolis projection
    energy drift is degrading wind amplitude after the accepted Strang split.
  - `geopotential_500` and `mean_sea_level_pressure` if wind amplitude errors
    feed back onto balanced mass and thickness evolution.
- Expected neutral metrics:
  - `2m_temperature` should remain near incumbent because no thermal tendency,
    theta recentering, weak-HS, or residual-memory path is changed.
- Possible regressions:
  - The projection energy drift may be a useful implicit damping source; adding
    it back can worsen noisy wind modes or pressure gradients.
  - Scaling both vorticity and divergence can slightly alter divergent wind
    amplitude, so early MSLP and Z500 guardrails must be watched.

## Risks

- Numerical stability:
  - Moderate. The cap bounds amplification, but restoring wind energy can oppose
    stabilizing numerical damping.
- Compute cost:
  - Low to moderate. It adds kinetic-energy reductions and one extra wind
    reconstruction inside each Coriolis rotation filter.
- Data leakage:
  - None. It uses only current model state and fixed grid quadrature.
- Physical plausibility:
  - High for the target invariant. Coriolis acceleration is perpendicular to
    velocity, so a pure Coriolis update should conserve kinetic energy.
- Rollback complexity:
  - Low. Remove one option, one helper branch, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_coriolis_ke_norm`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_coriolis_ke_norm --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_coriolis_ke_norm --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show that Coriolis
    projection energy drift is either immaterial or beneficial as damping. Any
    early wind, MSLP, or Z500 guardrail failure would show that the normalization
    injects harmful energy into the accepted solution.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_exact_coriolis_rotation_step_filter` and wraps the accepted Strang split.
- Dynamaxx tests: `tests/dycore/models/dinosaur/test_primitive_equations.py`
  already checks the exact Coriolis rotation sign and small-angle kinetic-energy
  behavior, providing a local test surface for this proposal.
- History: `.logbook/history/2026-06-18_03-03-20_exact-coriolis-rotation-split/decision.md`
  and `.logbook/history/2026-06-18_04-38-06_symmetric-coriolis-rotation-split/decision.md`
  accepted exact Coriolis splitting, so this proposal refines that accepted
  mechanism rather than replacing it.
- History: `.logbook/research/scrap/barotropic-angular-momentum-fixer.md` was
  a broad angular-momentum fixer; this proposal targets only the layerwise
  kinetic-energy invariant of the Coriolis rotation filter.
- James F. Price, "A Coriolis Tutorial", Woods Hole Oceanographic Institution,
  describes Coriolis deflection without changing speed:
  https://www2.whoi.edu/staff/jprice/wp-content/uploads/sites/199/2019/01/aCt_2003.pdf
- MIT OpenCourseWare rotating-flow notes state that Coriolis force is
  perpendicular to velocity and does no work:
  https://ocw.mit.edu/courses/res-12-001-topics-in-fluid-dynamics-fall-2024/mitres_12_001_f24_essay3_pt1.pdf
- Williamson, D. L., Drake, J. B., Hack, J. J., Jakob, R., and Swarztrauber,
  P. N. 1992. A standard test set for numerical approximations to the shallow
  water equations in spherical geometry. Journal of Computational Physics.
  https://doi.org/10.1016/S0021-9991(05)80016-6

## Researcher Notes

This is not another Coriolis phase or residual-rotation proposal. It does not
change the Strang ordering, rotation sign, DFI Coriolis treatment, or
near-surface residual. It also avoids the recent `williamson-cn-rk3-rollout`
failure by keeping the accepted off-centered SIL3 positive-time damping.

The main negative evidence is that narrow post-acceptance refinements can be
too small, as shown by `absolute-vorticity-flux-dealiasing`. This proposal is
therefore intentionally one invariant-preserving change with tight caps and a
clear rollback path.

## Evaluator Notes

### 2026-06-20T09:01:44Z

Decision: move to `staging`; ranked 2 of 3 proposals in this triage batch.

The invariant claim is physically sound: a pure Coriolis acceleration does no
work, and the accepted exact rotation already improved both fixed gates. The
implementation surface is also reasonably local because the existing
`_exact_coriolis_rotation_step_filter` already reconstructs winds, rotates
them, and projects back to vorticity/divergence, with tests covering sign,
non-wind leaves, and small-angle kinetic-energy behavior.

Keep it staged rather than ready. The accepted Coriolis mechanism has already
had the high-value Lie and Strang ordering gains, while the DFI Coriolis
follow-up was clean but only `+0.0008926584240389612` and recent
absolute-vorticity dealiasing was only `+0.00017069712459116815`, both below
the `+0.002` iteration threshold. Normalizing layer kinetic energy after modal
projection could also restore energy that truncation, projection, diffusion, or
the accepted offcentered SIL3 damping are usefully removing. The tight cap and
finite fallback make this worth preserving as a later low-surface-area
follow-up, but it should not displace the zonal-mean weak-HS proposal as the
single ready experiment.
