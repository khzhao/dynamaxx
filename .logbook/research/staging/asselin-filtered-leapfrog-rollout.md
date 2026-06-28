---
schema_version: 1
slug: asselin-filtered-leapfrog-rollout
title: Asselin-filtered semi-implicit leapfrog rollout
status: staging
created_at: 2026-06-28T02:51:54Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

## Hypothesis

Evaluate a candidate Dinosaur dycore that keeps the incumbent physics and diagnostics but swaps the positive-time rollout integrator from the current SIL3/off-centered path to the existing semi-implicit leapfrog machinery with a small Robert-Asselin filter.

The goal is to test whether the incumbent is losing score through time-integration phase or damping errors in balanced large-scale modes. This is a state-evolution proposal for MSLP/Z500/U10 and secondarily T2m, not an output-contract or final-diagnostic change.

## Mechanism

The repository already contains unused leapfrog support in `src/dynamaxx/dycore/models/dinosaur/leapfrog_utils.py`, including `semi_implicit_leapfrog`, `robert_asselin_leapfrog_filter`, and an exponential filter variant. The current incumbent instead follows the SIL3/off-centered integration path. A filtered leapfrog test is attractive because it changes the temporal numerics without disturbing the hard-won incumbent physics stack: HSL, mass DSE, tropical WTG, vertical-DSE ramping, land/ocean low-mode T2m memory, and Richardson 2m diagnostics.

The proposed mechanism is to bootstrap a two-time-level state, advance the positive-time rollout with semi-implicit leapfrog, apply a fixed Robert-Asselin filter after each leapfrog step to suppress the computational mode, and emit the current physical state at the same lead times as the incumbent.

## Implementation Scope

1. Add a narrowly scoped integrator option in the Dinosaur adapter, for example `time_integrator="sil3"` versus `"asselin_leapfrog"`, defaulting to the incumbent path.
2. Bootstrap the two-time-level leapfrog state with one incumbent semi-implicit SIL3/off-centered step from the initial state. This avoids changing initialization, DFI, or spinup logic before the candidate reaches the normal forward rollout.
3. Use `time_integration.semi_implicit_leapfrog(equation, time_step, alpha=0.5)` for the forward scan after bootstrapping.
4. Apply `time_integration.robert_asselin_leapfrog_filter(r)` with a small fixed coefficient such as `r=0.03` after each leapfrog step. The value should be fixed before evaluation and not tuned per metric.
5. Keep the same Dinosaur equation, filters, output diagnostics, target variables, and forecast `WeatherState` contract as the incumbent. DFI should remain on the incumbent solver unless the implementer verifies the leapfrog tuple state through DFI separately.
6. Add one candidate factory derived from `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`, changing only the rollout integrator path.

The implementation will likely need a custom trajectory scan because the leapfrog step carries `(previous_state, current_state)` while normal Dinosaur trajectory helpers expect a single state. The scan should emit the current physical state at the same forecast times as the incumbent.

## Expected Metric Movement

- Z500 and MSLP may improve if the current integrator has excessive phase lag or damping in balanced planetary-scale modes.
- U10 may improve through a cleaner pressure-gradient/divergence evolution rather than direct surface-wind shaping.
- T2m should be neutral unless the changed evolution improves boundary-layer winds and near-surface stratification feeding the existing Richardson diagnostic.

The proposal is higher implementation risk than a one-line physics coefficient change, but the expected code surface is still practical because leapfrog utilities already exist. A useful success threshold is an iteration improvement of at least `+0.002` without a major T2m or U10 component regression.

## Risks

- The computational mode may leak into diagnostics if the filter coefficient is too weak.
- Robert-Asselin filtering is dissipative and can harm amplitude-sensitive fields if the coefficient is too strong.
- Bootstrapping with one SIL3 step can introduce a startup transient, especially around DFI or any state filters that assume one-time-level trajectories.
- Existing filters and physics tendencies may have been implicitly tuned around SIL3 behavior, so a cleaner integrator on paper may still score worse.

## Evaluation Plan

Run fixed protocols unchanged:

1. `fast` to catch non-finite states, tuple-scan mistakes, and obvious oscillatory artifacts.
2. `iteration` with standard metrics, targets, splits, and golden data unchanged.
3. `validation` only after a positive iteration result with acceptable component behavior.

Abort or reject if the candidate shows sawtooth time-level noise, if the first forecast step has a large startup shock, if U10/T2m components regress sharply, or if total iteration delta is not convincingly positive.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/leapfrog_utils.py` provides `semi_implicit_leapfrog`, `robert_asselin_leapfrog_filter`, and leapfrog-specific filter adapters.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently builds Dinosaur trajectories through a single-state SIL3 step and `time_integration.trajectory_from_step`.
- Dynamaxx history: `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md` accepted fixed SIL3 implicit off-centering with a large positive iteration and validation delta.
- Dynamaxx history: `.logbook/history/2026-06-20_07-31-40_williamson-cn-rk3-rollout/decision.md` rejected a broad positive-time solver swap despite clean diagnostics.
- Asselin, R. 1972. "Frequency Filter for Time Integrations." https://www.coaps.fsu.edu/pub/gouillon/NUM_METHOD/AsselinFilter.pdf
- Williams, P. D. 2009. "A Proposed Modification to the Robert-Asselin Time Filter." Monthly Weather Review. https://doi.org/10.1175/2009MWR2724.1
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0

## Duplicate Check

This differs from prior and staged time-integration ideas:

- `fourth-order-imex-rk-rollout` changes to a higher-order Runge-Kutta family, not a two-time-level leapfrog scheme with computational-mode filtering.
- `split-explicit-nonlinear-advection-subcycle` subcycles selected nonlinear tendencies rather than replacing the whole positive-time stepper.
- `barotropic-external-mode-phase-correction` mentions leapfrog-style phase concerns for an external mode correction, but it is not a full filtered-leapfrog rollout candidate.
- Timestep and startup proposals such as shorter inner-step variants do not test the existing leapfrog utilities or Robert-Asselin filter behavior.

## Researcher Notes

This proposal is decorrelated from the rejected lower-tropospheric air-mass T2m diagnostic: it never blends final T2m and never changes target/output definitions. It is also decorrelated from the momentum-only semi-Lagrangian proposal because it changes temporal integration globally while preserving the incumbent spatial/physical tendencies.

## Evaluator Notes

### 2026-06-28T02:56:36Z

Decision: move to `staging`; plausible broad-numerics fallback, not the next implementation target.

I repaired the section headings and added a standalone `Citations` section so the proposal satisfies the protocol schema while preserving the scientific idea. The original schema defect would have blocked `ready` promotion if left uncorrected.

The mechanism is scientifically recognizable: leapfrog needs filtering to control the computational mode, and the repository does expose leapfrog utilities. However, source inspection shows the Dinosaur adapter currently builds single-state SIL3 trajectories, applies DFI through the same single-state solver API, and threads accepted rollout filters around that structure. A leapfrog candidate would need a bootstrapped two-time-level trajectory scan, filtered tuple-state carry, current-state emission at forecast leads, and careful treatment of DFI and symmetric Coriolis splitting. That is a larger implementation surface than the momentum-only vertical-advection proposal.

Local history argues against promoting another global solver-family swap now. Off-centered SIL3 was a major accepted win, while the Williamson CN-RK3 rollout replacement was clean but strongly negative and the 600 s timestep experiment was clean but slightly negative. This proposal is different from CN-RK3 because it adds Robert-Asselin filtering, but it still replaces the accepted positive-time integrator and could lose the off-centered damping that the incumbent depends on. Keep staged until narrower dynamical ideas are exhausted or diagnostics specifically implicate SIL3 phase error despite the accepted off-centering.
