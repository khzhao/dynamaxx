---
schema_version: 1
slug: centered-dfi-offcenter-rollout
title: Use Centered DFI with Off-Centered Positive Rollout
status: ready
created_at: 2026-06-19T10:11:34Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
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

# Use Centered DFI with Off-Centered Positive Rollout

## Hypothesis

The accepted off-centered SIL3 incumbent applies the same dissipative implicit
tableau during digital-filter initialization and during positive-time rollout.
That is numerically consistent in the narrow sense, but DFI is a forward/backward
low-pass initialization procedure whose purpose is to estimate a balanced initial
state. Off-centering is intentionally time-asymmetric and dissipative. Applying
it inside the DFI window may remove balanced thermal or wind amplitude before the
forecast even starts, while the positive-time forecast still needs off-centering
to suppress continuously regenerated gravity-wave noise.

Using the centered SIL3 solver only inside DFI, then retaining the accepted
off-centered solver for the forecast rollout, should preserve the large
mass-field benefit of the incumbent while reducing the late `2m_temperature`
and `10m_u_component_of_wind` costs noted in the accepted scoring record.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_centered_dfi`.
Preserve the incumbent initialization, weak-HS forcing, stability-aware
near-surface residual correction, Richardson 10 m wind diagnostic, theta
tendency, theta layer-mean recentering, exact symmetric Coriolis split,
horizontal diffusion, output variables, lead times, splits, metrics, and
off-centered positive-time rollout.

For the candidate only:

- keep `semi_implicit_offcentering=0.05` in the positive-time rollout path;
- use `time_integration.imex_rk_sil3` with `implicit_offcentering=0.0` for the
  `digital_filter_initialization` solver only;
- keep the current DFI equation and DFI filters otherwise unchanged, including
  the current handling of Coriolis during DFI;
- do not change DFI span, cutoff, filter weights, inner step length, or the
  accepted nonfinite fallback behavior;
- preserve the existing off-centered solver for every positive-time inner step
  after DFI.

This changes where the accepted dissipative fast-mode treatment is applied. It
does not tune the off-centering strength and does not change the public forecast
contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast`, accepted inputs, emitted variables, target
    variables, lead times, and metrics remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent flag except the new
    centered-DFI selector.
  - Verify positive-time rollout still constructs the off-centered SIL3 solver.
  - Verify DFI receives the centered solver when the selector is enabled.
  - Verify the default incumbent path still uses the current single solver
    wiring.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` and `10m_u_component_of_wind` at medium-to-late leads if
    off-centered DFI over-damps balanced initial thermal or wind amplitude.
  - Early aggregate RMSE may improve slightly if the initial state is less
    dissipatively biased before rollout.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500` should retain most of the
    accepted off-centering gain because positive-time gravity-wave damping is
    unchanged.
- Possible regressions:
  - If the accepted gain came partly from extra DFI damping, centered DFI may
    give back some early MSLP or Z500 improvement.
  - If DFI imbalance is not the source of the late temperature and wind costs,
    the score movement may be near neutral.

## Risks

- Numerical stability:
  - Low to moderate. Centered DFI is the older incumbent behavior and should be
    finite, but it may pass more fast-mode content into the forecast start.
- Compute cost:
  - Negligible. This changes solver selection inside existing DFI calls without
    adding transforms, steps, outputs, or workers.
- Data leakage:
  - None. The change uses no future data, validation artifacts, fitted
    constants, or target statistics.
- Physical plausibility:
  - High. DFI is intended as a balanced initialization filter, while off-centering
    is an irreversible damping device for positive-time fast modes.
- Rollback complexity:
  - Low. Remove one adapter flag, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_centered_dfi`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_centered_dfi --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_centered_dfi --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, especially with MSLP/Z500
    degradation, would show that off-centered DFI is either beneficial or
    harmless for the current incumbent.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
    passes the selected `ode_solver` into both positive-time rollout and
    `time_integration.digital_filter_initialization`.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md`
    accepted off-centered SIL3 with iteration delta
    `+0.25891536186185515` and validation delta `+0.2522585257774621`, while
    noting modest late `2m_temperature` regressions.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_09-54-58_balanced-digital-filter-initialization/decision.md`
    accepted DFI as a useful initialization filter before later off-centering.
  - Lynch, P. and Huang, X. 1992. Initialization of the HIRLAM Model Using a
    Digital Filter. Monthly Weather Review.
    https://journals.ametsoc.org/view/journals/mwre/120/6/1520-0493_1992_120_1019_iothmu_2_0_co_2.xml
  - Peckham, S. E. et al. 2016. Implementation of a Digital Filter
    Initialization in the WRF Model and Its Application in the Rapid Refresh.
    Monthly Weather Review. https://doi.org/10.1175/MWR-D-15-0219.1
  - Simmons, A. J. and Temperton, C. 1997. Stability of a Two-Time-Level
    Semi-Implicit Integration Scheme for Gravity Wave Motion. Monthly Weather
    Review. https://doi.org/10.1175/1520-0493(1997)125%3C0600:SOATTL%3E2.0.CO;2

## Researcher Notes

This proposal targets the new off-centered incumbent directly and is not a
duplicate of the accepted off-centering experiment. It keeps the accepted
positive-time off-centering strength fixed and changes only the solver used
inside the initialization filter.

It is also distinct from rejected `coriolis-split-dfi-initialization`, which
changed Coriolis treatment during DFI, and from rejected
`vorticity-preserving-dfi-increment`, which merged raw and filtered state
leaves. This proposal keeps the DFI state merge and Coriolis path intact; the
only hypothesis is that a dissipative, time-asymmetric off-centered tableau is
better reserved for positive-time rollout than for the DFI filtering window.

## Evaluator Notes

### 2026-06-19T10:15:47Z

Decision: move to `ready`; ranked 1 of 3 new proposals.

This is the strongest next experiment against the off-centered incumbent. The
proposal targets the new baseline directly, is narrowly scoped, and isolates a
specific numerical question: whether the accepted off-centered SIL3 damping
should apply only to positive-time rollout rather than also inside the DFI
window. The current adapter wires the same `ode_solver` into rollout and
`digital_filter_initialization`, and existing tests explicitly confirm that the
off-centered candidate currently threads the positive epsilon into DFI. That
makes the proposed split feasible without changing lead times, outputs, DFI
span, filters, or fixed protocols.

Prior DFI follow-ups are mixed: the original balanced DFI was accepted, while
weak-HS DFI splitting was neutral, vorticity-preserving DFI was negative, and
Coriolis-consistent DFI was clean but below promotion threshold. This proposal
is still worth one ready slot because it is not another operator-consistency
cleanup. It tests a new interaction introduced by the accepted off-centering
commit, whose scoring showed large MSLP/Z500 gains but a modest late
`2m_temperature` cost. The main risk is giving back some of the accepted
mass-field gain if off-centered DFI was contributing useful initialization
damping, so the Scorer should watch late MSLP/Z500 and early wind guardrails.
