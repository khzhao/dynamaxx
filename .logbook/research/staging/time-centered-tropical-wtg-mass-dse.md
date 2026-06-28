---
schema_version: 1
slug: time-centered-tropical-wtg-mass-dse
title: Time-centered tropical WTG mass-DSE relaxation
status: staging
rank: 2
priority: medium
created_at: 2026-06-25T08:59:45Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg
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

# Time-centered tropical WTG mass-DSE relaxation

## Hypothesis

The accepted `dino_hsl2_mass_dse_wtg` gain shows that a bounded tropical
free-tropospheric WTG mass-DSE correction helps the fixed WeatherBench2 target
surface. The current implementation applies the full WTG correction as a
post-step filter after each primitive-equation step. That first-order operator
placement can introduce a small phase lag between the thermal relaxation and the
mass, wind, and hydrostatic responses. A symmetric half-step WTG correction
before and after the primitive-equation step should preserve the accepted
spatial support and nominal timescale while reducing split-operator error.

## Mechanism

Add a side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_centered`, derived from
`dino_hsl2_mass_dse_wtg`. Refactor the accepted WTG filter so the same bounded
state transform can be applied with a `relaxation_fraction_scale` of `0.5`.
When the centered selector is enabled, wrap each rollout inner step as:

- apply a half-strength WTG transform to the input state;
- run the incumbent primitive-equation step and existing filters;
- apply a half-strength WTG transform to the resulting state.

The accepted WTG latitude envelope, sigma envelope, low-mode mask, increment
cap, finite fallback, and layer-neutral shape remain unchanged. Lead-zero
output remains the input state because trajectory generation starts with the
input before any positive-time inner step.

## Implementation Scope

- Expected files: add one opt-in selector and one centered WTG step wrapper in
  `adapter.py`; expose one factory through `__init__.py`; add one registry key
  in `registry.py`; add focused unit tests for the factory, registry, no-op
  disabled path, and half-step finite behavior.
- Registry changes: add `dino_hsl2_mass_dse_wtg_centered`; keep
  `dino_hsl2_mass_dse_wtg` byte-for-byte equivalent when the selector is
  disabled.
- API changes: none. The forecast inputs, outputs, lead handling, and metrics
  remain unchanged.
- Tests to update: Dinosaur dependency/factory tests, registry tests, and WTG
  filter tests covering zero anomaly, invalid diagnostics fallback, and that
  two half-strength applications are close to one full application for a small
  synthetic anomaly.

## Expected Metric Movement

- Expected improvements: `geopotential_500`, `mean_sea_level_pressure`, and
  `10m_u_component_of_wind` at day 1 to day 5 if post-step WTG timing is adding
  a small tropical mass-field phase error.
- Expected neutral metrics: `2m_temperature` should remain close to the
  incumbent because the spatial WTG mask and increment cap are unchanged and
  the operator stays above the boundary layer.
- Possible regressions: the accepted post-step placement may be empirically
  better tuned to the semi-implicit step; centered application could weaken the
  score gain or double the cost of WTG diagnostics.

## Risks

- Numerical stability: low to moderate. The same capped transform is reused,
  but it is applied twice per inner step.
- Compute cost: moderate. The WTG diagnostic path roughly doubles unless the
  implementer factors shared diagnostics carefully.
- Data leakage: none. The transform uses only the current forecast state and
  fixed grid geometry.
- Physical plausibility: moderate. Symmetric splitting is numerically motivated,
  and WTG remains a tropical free-tropospheric balance approximation.
- Rollback complexity: low. The change should be isolated behind one model
  selector and registry key.

## Evaluation Plan

- Fast gate: run `uv run pytest` plus `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_centered`.
- Iteration gate: run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_centered --workers <worker_count>` and compare only against compatible cached `dino_hsl2_mass_dse_wtg` incumbent metrics.
- Validation gate: run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_centered --workers <worker_count>` only if iteration promotes under the fixed protocol.
- Outcome that would falsify the hypothesis: a negative or subthreshold
  iteration delta, or a day-1 to day-5 `geopotential_500` or MSLP guardrail
  regression, would show that post-step WTG timing is not the limiting error.

## Citations

- Sobel, A. H., J. Nilsson, and L. M. Polvani, 2001: The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences. https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Strang, G., 1968: On the Construction and Comparison of Difference Schemes.
  SIAM Journal on Numerical Analysis. https://doi.org/10.1137/0705041
- Local code reference:
  `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements the accepted
  `_tropical_wtg_mass_dse_relaxation_step_filter`.
- Local history reference:
  `.logbook/history/2026-06-25_01-45-51_tropical-wtg-mass-dse-relaxation/decision.md`.

## Researcher Notes

This is not a repeat of the rejected
`ocean-weighted-tropical-wtg-mass-dse` support-narrowing experiment. It keeps
the accepted WTG spatial and vertical support intact and targets a different
failure mode: first-order time placement of a useful thermal balance operator.
It is also distinct from staged `zonal-anomaly-tropical-wtg-mass-dse` and
`first-baroclinic-tropical-wtg-mass-dse`, which change the anomaly subspace
rather than the operator splitting.

## Evaluator Notes

### 2026-06-25T09:05:19Z

Decision: move to `staging`; ranked 2 of 3 new WTG follow-up proposals.

This is a valid, bounded side-by-side model-selection idea. It preserves the
accepted WTG support, keeps the forecast and evaluation contracts unchanged,
and asks a real numerical question: whether the accepted post-step WTG
operator is losing skill through first-order time placement. The cited WTG and
Strang-splitting literature supports the broad mechanism, and this is not a
repeat of the recent failed ocean-weighted support narrowing.

It should not be the next ready item because the cost-risk tradeoff is weaker
than the mass-neutral closure. Applying WTG before and after every inner step
obviously doubles the WTG diagnostic path unless the implementer can reuse
state diagnostics, and the last iteration was already slow. The implementation
also needs more care than a closure change: the current WTG filter is appended
as a post-step filter, so a centered wrapper would have to preserve lead-zero
behavior, DFI separation, finite fallback behavior, and exact incumbent
equivalence when disabled.

Local timing/splitting evidence is mixed. The staged Strang-split mass-DSE HSL
idea was held for larger implementation surface, and the implemented
Coriolis-centered HSL departure was clean but effectively neutral. Keep this
proposal staged as the best WTG operator-timing follow-up, but do not spend the
next full rollout slot on it ahead of the cheaper mass-neutral clipped closure.
