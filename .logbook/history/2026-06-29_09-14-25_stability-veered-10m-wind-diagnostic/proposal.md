---
schema_version: 1
slug: stability-veered-10m-wind-diagnostic
title: Stability-Veered 10m Wind Diagnostic
status: ready
created_at: 2026-06-29T09:08:33Z
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

# Stability-Veered 10m Wind Diagnostic

## Hypothesis

The incumbent already has a bulk-Richardson 2 m temperature diagnostic and a
coupled Ekman stress-pumping step, but the emitted `10m_u_component_of_wind`
still comes from a scalar stability reduction of the lowest model wind. A
surface-layer wind is not only slower than the lowest resolved wind; in a
rotating boundary layer it is also directionally veered relative to the flow
aloft. A tightly capped, output-only veering correction using the two lowest
sigma-layer winds and the already diagnosed bulk Richardson number can improve
the scored 10 m zonal wind without feeding back into stress, pumping, mass, or
thermal tendencies.

## Mechanism

Add an opt-in diagnostic on top of `dino_ri2m_ekman_coupled`, for example
`dino_ri2m_ekman_veered_10m`. Reuse the same lower-column pressure, potential
temperature, shear, and finite checks already used by `_surface_layer_richardson_10m_wind`.

For the new candidate only:

- compute the accepted Richardson-scaled 10 m wind first;
- compute a bounded directional tendency from the vector difference between the
  two lowest sigma-layer winds;
- map stable columns toward a slightly stronger near-surface veering angle and
  unstable columns toward little or no veering;
- apply a hemisphere-aware rotation with a small fixed cap, such as single-digit
  degrees to about 12 degrees, and a speed-preserving rescale so the accepted
  Richardson speed reduction is not retuned;
- emit the corrected `10m_u_component_of_wind` and `10m_v_component_of_wind`
  when requested, while leaving vorticity, divergence, temperature,
  log-surface pressure, tracers, MSLP, Z500, 2 m temperature, residual memory,
  and the coupled Ekman stress-pumping step unchanged;
- fall back exactly to the incumbent wind diagnostic for invalid pressure,
  temperature, shear, or latitude diagnostics.

This is deliberately not a new surface-stress or Ekman-pumping closure. It is a
screen-level wind observation-operator refinement after the forecast trajectory
has already been generated.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side descendant of `dino_ri2m_ekman_coupled`.
- API changes:
  - None. Inputs, outputs, target variables, lead times, and protocols stay
    fixed.
- Tests to update:
  - Synthetic Northern and Southern Hemisphere cases verifying opposite veering
    signs.
  - Neutral and unstable cases verifying small or zero angle.
  - Speed-preservation test relative to the accepted Richardson wind magnitude.
  - Finite fallback tests and a test proving non-wind outputs are unchanged.
  - Factory and registry tests proving all incumbent flags are preserved except
    the new diagnostic selector.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind`, especially medium and late leads where scalar
    speed reduction alone misses boundary-layer directional structure.
- Expected neutral metrics:
  - `2m_temperature`, `mean_sea_level_pressure`, and `geopotential_500` should be
    unchanged except for aggregation noise.
- Possible regressions:
  - If the fixed angle cap is too large, zonal wind can regress in strong
    synoptic flow or in the tropics. The candidate should use a latitude taper
    and exact fallback for weak or invalid shear.

## Risks

- Numerical stability:
  - Very low, because this is output-only.
- Compute cost:
  - Negligible local algebra on already available sigma-level winds,
    temperature, surface pressure, and latitude.
- Data leakage:
  - None. It uses only same-lead forecast state and fixed constants.
- Physical plausibility:
  - Moderate to high. Surface-layer similarity and Ekman turning support a
    direction as well as speed correction, but the 1.5 degree grid cannot
    resolve a full boundary-layer spiral.
- Rollback complexity:
  - Low. Remove one diagnostic flag/helper, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_ekman_veered_10m`.
  - Require finite outputs and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_veered_10m --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no day-1-through-day-5 or single-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_ekman_veered_10m --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that directional
    veering is not a material remaining 10 m wind error after the accepted
    Richardson and coupled Ekman paths. Any early wind guardrail failure would
    show the fixed veering cap is too intrusive.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` already
  computes surface-layer Richardson wind diagnostics from the two lowest sigma
  layers and has all required fields available.
- Dynamaxx history:
  `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/decision.md`
  accepted `dino_ri2m_ekman_coupled`; this proposal preserves that stress and
  pumping mechanism unchanged.
- Monin, A. S. and Obukhov, A. M. 1954. Basic laws of turbulent mixing in the
  surface layer of the atmosphere. Trudy Geofizicheskogo Instituta AN SSSR.
- Businger, J. A., Wyngaard, J. C., Izumi, Y., and Bradley, E. F. 1971.
  Flux-profile relationships in the atmospheric surface layer. Journal of the
  Atmospheric Sciences. https://doi.org/10.1175/1520-0469(1971)028%3C0181:FPRITA%3E2.0.CO;2
- Stull, R. B. 1988. An Introduction to Boundary Layer Meteorology. Springer.
  https://doi.org/10.1007/978-94-009-3027-8

## Researcher Notes

This is not coupled Ekman stress-pumping: no wind stress, mass pumping, or
surface-pressure tendency is changed. It is also not bulk Richardson T2m, since
it touches only the emitted 10 m wind vector. It differs from prior scalar 10 m
wind diagnostics by adding only a bounded directional veering correction while
preserving the accepted Richardson speed magnitude.

## Evaluator Notes

### 2026-06-29T09:13:07Z

Decision: move to `ready`; rank 1 of 1 ready proposal.

This is implementable now and is the best of the two reviewed proposals for the
next experiment. Source inspection confirms the current incumbent
`dino_ri2m_ekman_coupled` already preserves the Richardson 10 m wind diagnostic
and adds the coupled Ekman surface closure, so a side-by-side output diagnostic
can reuse the existing lower-column pressure, theta, shear, wind, latitude, and
finite-fallback machinery without changing the forecast trajectory or fixed
evaluation contract.

The idea is not a duplicate of the accepted Richardson 10 m wind diagnostic,
which mainly changed scalar speed reduction, and it is not a duplicate of the
accepted coupled Ekman stress-pumping candidate, which feeds a bounded
surface-stress closure back into mass and momentum. This proposal tests a
different boundary-layer observation-operator signal: small, capped,
hemisphere-aware directional turning while preserving the accepted Richardson
wind speed.

Local history still warrants caution. Several output-only wind follow-ups were
clean but subthreshold or negative, including `monotone-shear-10m-wind`,
`virtual-theta-richardson-10m-wind`, `roughness-aware-surface-wind-diagnostic`,
and `land-sea-wind-residual-memory`. The closest rotation history,
`coriolis-rotated-surface-wind-residual`, failed an early day-1 wind guardrail.
This proposal is stronger than those repeats because it rotates the diagnosed
wind vector by a fixed, small surface-layer veering angle instead of rotating a
lead-zero residual or retuning the scalar speed factor. The implementer should
fix the angle cap, latitude taper, stability mapping, and weak-shear fallback
before scoring and should treat any early `10m_u_component_of_wind` guardrail
movement as decisive.
