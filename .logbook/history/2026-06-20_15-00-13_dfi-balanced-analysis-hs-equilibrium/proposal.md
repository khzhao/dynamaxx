---
schema_version: 1
slug: dfi-balanced-analysis-hs-equilibrium
title: Compute the Analysis-Offset Held-Suarez Equilibrium From the DFI-Balanced State
status: ready
created_at: 2026-06-20T14:53:43Z
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

# Compute the Analysis-Offset Held-Suarez Equilibrium From the DFI-Balanced State

## Hypothesis

The accepted analysis-offset Held-Suarez equilibrium improved both iteration
and validation by shifting the weak thermal equilibrium toward the low-mode
initial thermal state. In the current adapter, that offset is diagnosed from the
raw initialized Dinosaur state before digital filter initialization (DFI)
removes high-frequency imbalance from the actual rollout state. This can leave
the weak thermal forcing anchored to a slightly different mass/thermal balance
than the state being advanced after DFI.

Computing the same bounded low-wavenumber equilibrium offset from the
DFI-balanced initial state should preserve the accepted physical signal while
removing gravity-wave and interpolation spinup contamination from the forcing
anchor. The expected gain is small but plausible because the incumbent score is
now close to the accepted analysis-offset candidate, and the latest theta
variance guard showed that post-step theta variance preservation is not the
limiting mechanism.

## Mechanism

Register a side-by-side candidate that keeps every incumbent option but changes
the source state for `_analysis_offset_weak_held_suarez_equilibrium`.

The implementation should:

- factor DFI initialization so the candidate can obtain the accepted
  DFI-balanced state once at forecast start;
- compute the low-mode, clipped equilibrium temperature offset from that
  DFI-balanced state instead of the raw pre-DFI state;
- start the positive-time trajectory from the same DFI-balanced state, avoiding
  a second DFI pass;
- keep the accepted offset cap, low-mode mask, weak-HS timescales, theta
  tendency, theta mean recentering, off-centering, Coriolis Strang split, and
  scale-separated surface residuals unchanged;
- apply the same behavior in all initial cases and fall back to the current raw
  offset path if the DFI-balanced state or offset is nonfinite;
- preserve the forecast contract: one deterministic trajectory in the existing
  `WeatherState` shape.

This changes the ordering and balance of an accepted forcing anchor. It does
not change weak-HS strength, target variables, lead times, validation policy,
surface residual memory, or theta variance constraints.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory with a suffix such as `_dfi_hs_eq`.
- API changes:
  - None. `DycoreModel.forecast`, output variables, lead handling, and metric
    protocols remain fixed.
- Tests to update:
  - Verify the candidate preserves all incumbent flags except the DFI-balanced
    HS-equilibrium selector.
  - Unit-test that the offset computed from a supplied balanced state uses the
    accepted low-mode mask and Kelvin cap.
  - Verify no double-DFI occurs in the candidate path.
  - Verify nonfinite balanced offsets fall back to the incumbent raw-offset
    behavior.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 2 to 10 if the
    raw-offset anchor is retaining a small DFI-removed thermal imbalance.
  - `2m_temperature` may improve modestly if lower-tropospheric weak thermal
    relaxation is better aligned with the balanced initial column.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should stay close to incumbent because wind
    diagnostics, Coriolis splitting, off-centering, and residual correction are
    unchanged.
- Possible regressions:
  - The raw initial offset may contain useful analysis information that DFI
    removes. If so, the candidate can lose part of the accepted
    analysis-offset gain.
  - Factoring DFI ordering incorrectly could alter the accepted initialization
    more broadly than intended.

## Risks

- Numerical stability:
  - Low to moderate. The rollout remains on the accepted equations, but DFI and
    forcing-anchor ordering are delicate and must not double-filter.
- Compute cost:
  - Low. The candidate should reuse the DFI state already needed for rollout.
- Data leakage:
  - None. The offset uses only same-time initial state and deterministic DFI,
    with no future analyses, validation statistics, or `golden` data.
- Physical plausibility:
  - High. Digital filters are used to reduce initialization imbalance, and weak
    Held-Suarez forcing is a standard dry-dycore thermal relaxation. Anchoring
    the forcing to the balanced state is more internally consistent than using
    a pre-filtered gravity-wave-contaminated state.
- Rollback complexity:
  - Low. Remove one selector, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_name> --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the accepted raw
    analysis-offset equilibrium is already the better anchor. Any early MSLP,
    Z500, or wind guardrail failure would show the ordering change disrupts the
    accepted initialization balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` computes
  `_analysis_offset_weak_held_suarez_equilibrium` before building the
  DFI-enabled trajectory.
- Dynamaxx history:
  `.logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium/decision.md`
  accepted the current raw-state analysis-offset equilibrium with iteration
  delta `+0.016990568302663656` and validation delta
  `+0.01745893975367474`.
- Dynamaxx history:
  `.logbook/history/2026-06-20_12-57-53_baroclinic-theta-variance-guard/decision.md`
  rejected theta variance preservation as numerically clean but slightly
  negative, so this proposal changes the forcing anchor rather than adding a
  post-step theta guard.
- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of
  the dynamical cores of atmospheric general circulation models. Bulletin of
  the American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
  digital filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Lynch, P. 1997. The Dolph-Chebyshev window: A simple optimal filter. Monthly
  Weather Review.
  https://doi.org/10.1175/1520-0493(1997)125%3C0655:TDCWAS%3E2.0.CO;2

## Researcher Notes

This is not a repeat of rejected zonal-mean weak-HS relaxation: it keeps the
accepted full low-mode analysis offset and only changes whether the offset is
diagnosed before or after DFI. It is not a surface residual memory variant, a
theta variance guard, a CN-RK3 rollout, or absolute-vorticity dealiasing.

The prior accepted result is positive evidence that analysis-conditioned weak
thermal equilibrium matters. The new mechanism tests a narrower consistency
question: should the accepted equilibrium offset be tied to the state the model
actually rolls out after DFI?

## Evaluator Notes

### 2026-06-20T14:57:48Z

Decision: move to `ready`.

Rank: 1 of 1 ready proposals.

This is the strongest next experiment in the batch. It is a narrow
single-mechanism refinement of the accepted analysis-offset Held-Suarez
equilibrium, which improved iteration by `+0.016990568302663656` and validation
by `+0.01745893975367474` over the prior incumbent. Source inspection confirms
the current adapter computes `_analysis_offset_weak_held_suarez_equilibrium`
from the raw initialized Dinosaur state before `digital_filter_initialization`
is applied inside `build_trajectory`, so the proposed ordering change is real
and implementable.

The idea preserves the forecast contract, fixed protocols, weak-HS strength,
surface residuals, theta tendency, theta mean recentering, Coriolis split, and
off-centered SIL3. The main implementation risk is DFI factoring: the candidate
must compute the balanced state once, use that same state to start the
positive-time rollout, and avoid a double DFI pass. That risk is localized and
testable. It is distinct from the scrapped low-mode DFI merge because it does
not preserve raw modes or change the DFI output; it only uses the actual
balanced rollout state as the accepted weak-HS equilibrium anchor.
