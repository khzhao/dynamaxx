---
schema_version: 1
slug: divergence-selective-offcentering
title: Divergence-Selective Semi-Implicit Off-Centering
status: staging
created_at: 2026-06-19T15:49:06Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
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

# Divergence-Selective Semi-Implicit Off-Centering

## Hypothesis

The accepted `si_offcenter` change off-centers the semi-implicit average with a
single weight `0.5 + epsilon` applied to the entire linear implicit operator.
That produced a large mass-field improvement (`mean_sea_level_pressure` and
`geopotential_500` at medium-to-long leads) by damping spurious gravity-inertia
waves. But a uniform off-centering also adds `O(dt)` damping to the **balanced**
modes, because the implicit operator couples the divergent (gravity-wave) and
the geopotential/temperature response that the rotational flow is in balance
with. The spurious energy that needed damping lives in the **divergent**
component; the synoptic skill lives in the rotational component, which is
already the model's best field at short lead (`geopotential_500` skill `+0.59`
at 24 h). Applying the off-centering **only to the divergence equation and its
coupled gravity-wave terms**, while keeping the rotational/vorticity evolution
centered, should damp the same spurious fast modes with less penalty to the
balanced flow, recovering additional `geopotential_500` and
`mean_sea_level_pressure` skill at medium leads.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_div_offcenter`.
Preserve incumbent initialization, DFI, weak-HS forcing, exact symmetric
Coriolis split, horizontal diffusion, potential-temperature tendency, theta mean
recentering, stability-aware residual decay, Richardson 10 m wind diagnostic,
output variables, WeatherBench2 splits, lead times, metrics, and deterministic
gates.

For the candidate only:

- the primitive-equations state is already carried in spectral
  vorticity/divergence form (`PrimitiveEquationsSigma` with `vorticity` and
  `divergence` modal fields), so the divergent gravity-wave subsystem is cleanly
  separable from the rotational subsystem;
- apply the implicit off-centering weight `0.5 + epsilon` **only** to the
  divergence equation and the geopotential/temperature/surface-pressure terms
  that form the implicit gravity-wave block solved by `implicit_inverse`;
- keep the vorticity (rotational) evolution at the centered weight `0.5`,
  i.e. `epsilon = 0` for that component;
- reuse the incumbent's accepted off-centering magnitude as the starting
  `epsilon` for the divergent block so the candidate is a strict structural
  refinement of the accepted scheme, not a re-tuning of its strength;
- apply the identical treatment in DFI and positive-time rollout;
- fall back to the incumbent uniform off-centering if the divergence-selective
  solve produces nonfinite values.

This changes **which modes** the accepted off-centering damps, not **how much**.
It is distinct from `divergence-selective-gravity-wave-damping` (history), which
adds an explicit diffusion term to the divergence tendency; this proposal adds
no dissipation and only restricts the existing implicit time-average centering
to the divergent block.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` (per-component
    off-centering weight)
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` (route the
    weight to the divergence/gravity-wave implicit block only)
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
  - Unit-test that off-centering the divergent block only, with the same epsilon
    on both blocks, equals the incumbent uniform off-centering (consistency
    bridge).
  - Unit-test on a linear normal-mode problem that a fast gravity mode is damped
    while a balanced rotational mode is preserved more accurately than under
    uniform off-centering.
  - Verify the candidate factory preserves every incumbent setting except the
    per-component off-centering routing.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 3-10, beyond the
    accepted uniform off-centering, by sparing the balanced modes.
- Expected neutral metrics:
  - `2m_temperature`, governed by surface diagnostics and HS forcing.
  - `10m_u_component_of_wind`, near incumbent.
- Possible regressions:
  - If the divergent and rotational responses are tightly coupled through the
    geopotential term, sparing vorticity may reintroduce a small amount of the
    noise the uniform scheme removed.
  - The benefit over uniform off-centering may be near zero if the accepted
    scheme already captured essentially all the available gain.

## Risks

- Numerical stability:
  - Low-to-moderate. Damping the fast divergent modes is the stabilizing part of
    the accepted scheme; this retains it. Centering vorticity cannot destabilize
    the rotational modes, which are non-stiff.
- Compute cost:
  - Negligible. A per-component weight in the existing implicit solve; no extra
    transforms, resolution, lead count, or worker changes.
- Data leakage:
  - None. Uses only the model state and fixed numerical constants.
- Physical plausibility:
  - High. Selective treatment of the divergent gravity-wave subsystem versus the
    rotational balanced subsystem is standard in semi-implicit dynamical cores.
- Rollback complexity:
  - Trivial. Restore the single uniform off-centering weight.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_div_offcenter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_div_offcenter --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` with
    clean diagnostics and no early-lead or variable-by-lead RMSE guardrail
    failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_div_offcenter --workers 4`
    only after iteration promotion; require validation primary delta at least
    `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the accepted
    uniform off-centering already captured the available gain and that the
    balanced modes were not being meaningfully penalized.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
    carries spectral `vorticity` and `divergence` modal fields and solves the
    gravity-wave terms through `implicit_inverse`.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md`
    accepted uniform off-centering with iteration delta `+0.259`; this proposal
    refines which modes that scheme damps.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_19-57-46_divergence-selective-gravity-wave-damping`
    added explicit divergence diffusion; this proposal adds no dissipation.
  - Simmons, A. J. and Temperton, C. 1997. Stability of a two-time-level
    semi-implicit integration scheme for gravity-wave motion. Monthly Weather
    Review.
    https://doi.org/10.1175/1520-0493(1997)125%3C0600:SOATTL%3E2.0.CO;2
  - Temperton, C. 1997. Treatment of the Coriolis terms in semi-Lagrangian
    spectral models. Atmosphere-Ocean (separable treatment of rotational and
    divergent components).
    https://doi.org/10.1080/07055900.1997.9687359

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-19 to follow
up the accepted `offcentered-semi-implicit-gravity-wave` win; recorded here for
provenance honesty in the autonomous loop.

This is distinct from the accepted uniform off-centering because it changes the
mode selectivity, not the strength, and from
`divergence-selective-gravity-wave-damping` (history) because it adds no
explicit diffusion. The same-epsilon-on-both-blocks consistency test makes the
change auditable as a strict structural refinement of the accepted scheme. The
hypothesis is directly motivated by the per-variable breakdown of the accepted
win: the gain was almost entirely in the mass field, with the rotational-skill
`geopotential_500` already strong at short lead and therefore the component most
worth sparing from added implicit damping.

## Evaluator Notes

### 2026-06-19T17:53:23Z

Decision: move to `staging`; ranked 1 of 2 fresh proposals, but not ready.

The proposal has the better lineage of the two fresh ideas because the accepted
SIL3 off-centering result was a large, clean mass-field improvement, and a
mode-selective follow-up could be useful if formulated precisely. It should not
be the next ready implementation as written. Source inspection shows that the
current primitive-equation implicit operator already has
`vorticity_implicit = zeros_like(state.vorticity)`, and both sigma and hybrid
`implicit_inverse` paths carry vorticity through unchanged. The accepted
off-centering in `time_integration.imex_rk_sil3` shifts the implicit tableau,
so its nonzero direct action is already the coupled
`divergence`/`temperature_variation`/`log_surface_pressure` gravity block, not
a separate rotational/vorticity implicit block.

That means the stated implementation rule, "apply off-centering only to the
divergence equation and coupled gravity-wave terms while keeping vorticity
centered," is likely equivalent to the incumbent or close to a no-op if applied
literally. A genuinely different version would require a custom per-component
or per-row treatment inside the coupled implicit gravity solve, which is a
broader solver/matrix change than the proposal presents. The recent
theta-consistent implicit gravity operator rejection is direct negative
evidence against spending the next implementation slot on broad implicit-block
matrix changes, and earlier divergence-selective explicit damping was clean
but slightly negative.

Keep staged rather than scrapping because the accepted off-centering result
still makes this family scientifically relevant. Before promotion, the idea
needs a precise non-noop formulation and an offline or unit-level demonstration
that the candidate differs from the incumbent without rewriting the coupled
gravity operator in a way that repeats the recent failed matrix experiment.
