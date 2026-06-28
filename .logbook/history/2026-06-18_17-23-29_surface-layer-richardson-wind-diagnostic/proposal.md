---
schema_version: 1
slug: surface-layer-richardson-wind-diagnostic
title: Use a Richardson-Bounded Surface-Layer Wind Diagnostic
status: ready
created_at: 2026-06-18T17:18:05Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use a Richardson-Bounded Surface-Layer Wind Diagnostic

## Hypothesis

The incumbent emits `10m_u_component_of_wind` from the lowest sigma-layer wind
and then applies the accepted stability-aware residual correction. That leaves
the positive-lead 10 m diagnostic tied to a model layer rather than to a
surface-layer similarity estimate. A bounded bulk-Richardson diagnostic should
reduce low-level wind-amplitude error after the accepted residual decays while
leaving prognostic winds, pressure, geopotential, DFI, Coriolis splitting, and
thermal forcing unchanged.

This is intentionally narrower than the rejected surface-layer extrapolation
candidate: do not change `2m_temperature`, do not use a two-layer linear shear
extrapolation, and do not alter the forecast trajectory. Only convert the
lowest model-layer wind to a 10 m wind using a physically bounded stability
factor.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind`.
Preserve all incumbent initialization, DFI, weak Held-Suarez, horizontal
diffusion, exact Coriolis Strang splitting, stability-aware near-surface
residual decay, lead handling, and output variables.

Add an opt-in diagnostic path in `dinosaur_state_to_weather_state`:

- compute potential temperature on the lowest two sigma layers and horizontal
  wind speed on those layers;
- estimate a bounded bulk Richardson number from lower-layer static stability,
  vertical wind shear, nominal pressure-height separation from the hypsometric
  relation, and fixed floors for weak shear;
- compute a neutral log-law-like attenuation from the lowest sigma-layer
  nominal height to 10 m, then multiply it by a bounded stable/unstable
  correction that damps diagnosed 10 m wind in stable stratification and relaxes
  toward the layer wind in unstable mixing;
- apply the same scalar factor to `10m_u_component_of_wind` and
  `10m_v_component_of_wind` when requested, without rotating direction;
- leave pressure-level winds, prognostic vorticity/divergence, temperature,
  humidity, surface pressure, MSLP, and Z500 unchanged;
- continue to apply the incumbent stability-aware residual correction after
  diagnostic packing, so lead zero remains exactly corrected by the accepted
  residual path.

Use conservative fixed bounds, such as an attenuation range of 0.55 to 1.05,
and fall back to the incumbent lowest-layer wind when the required lower-column
levels are unavailable or nonfinite.

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
  - None. `DycoreModel.forecast`, input variables, output variables, leads, and
    fixed evaluation protocols remain unchanged.
- Tests to update:
  - Verify the candidate factory preserves every incumbent flag except the new
    surface-layer wind diagnostic option.
  - Unit-test the Richardson diagnostic for stable, neutral, and unstable
    synthetic lower columns, including finite fallback behavior.
  - Verify `2m_temperature`, pressure-level fields, surface pressure, MSLP, and
    Z500 are bitwise or near-bitwise identical to the incumbent before residual
    correction.
  - Verify the lead-zero residual correction still exactly matches the initial
    10 m wind channel.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at days 2 to 15 if the lowest sigma wind is too
    high or too weak under stable/unstable surface-layer regimes after the
    residual decays.
  - Primary score may improve without disturbing mass fields because the change
    is output-diagnostic only.
- Expected neutral metrics:
  - `geopotential_500` and `mean_sea_level_pressure` should remain unchanged
    except for aggregate metric bookkeeping noise.
  - `2m_temperature` should remain governed by the accepted stability-aware
    residual path.
- Possible regressions:
  - The fixed nominal layer height and no-roughness approximation may worsen
    10 m wind amplitude regionally.
  - The accepted 10 m residual already improved early wind skill, so a second
    diagnostic transform can overcorrect if the lowest model layer was already
    the best empirical proxy.

## Risks

- Numerical stability:
  - Low. This is an output diagnostic and should not feed back into rollout.
- Compute cost:
  - Low. It adds local algebra on packed output fields only.
- Data leakage:
  - Low. The diagnostic uses only the forecast state, fixed constants, and the
    same initial analysis already used by the accepted residual correction. It
    must not inspect future targets or validation artifacts.
- Physical plausibility:
  - Moderate. Monin-Obukhov theory is the standard surface-layer framework, but
    this candidate uses a dry, roughness-free, bounded bulk-Richardson proxy
    rather than a full land/ocean surface scheme.
- Rollback complexity:
  - Low. Remove one adapter option/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the lowest
    sigma-layer wind plus accepted residual is already the better diagnostic.
    Any day-1 10 m wind guardrail failure would show the bounded similarity
    correction is still too intrusive.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  emits `10m_u_component_of_wind` and `10m_v_component_of_wind` from the lowest
  sigma-layer wind and then applies the accepted near-surface residual path.
- History: `.logbook/history/2026-06-17_13-35-18_surface-layer-diagnostic-extrapolation/decision.md`
  rejected a simple two-layer extrapolation after large near-surface RMSE
  regressions; this proposal avoids changing 2 m temperature and uses bounded
  stability-dependent wind scaling instead of linear extrapolation.
- History: `.logbook/history/2026-06-18_15-57-11_stability-aware-surface-residual-decay/decision.md`
  accepted residual decay with large 2 m temperature gains and small wind
  gains; this proposal keeps that residual mechanism unchanged and tests a
  distinct surface-layer diagnostic signal.
- ECMWF OpenIFS documentation notes that IFS surface-layer turbulent fluxes use
  first-order K-diffusion based on Monin-Obukhov similarity theory:
  https://confluence.ecmwf.int/display/OIFS/3.2%2BOpenIFS%3A%2BPhysical%2BProcesses
- Beljaars, A. C. M. and Holtslag, A. A. M. 1991. Flux Parameterization over
  Land Surfaces for Atmospheric Models. Journal of Applied Meteorology.
  https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2
- Dyer, A. J. 1974. A review of flux-profile relationships.
  Boundary-Layer Meteorology. https://doi.org/10.1007/BF00240838

## Researcher Notes

This is not a duplicate of the accepted stability-aware residual decay because
it does not tune residual timescales or residual amplitudes. It changes the raw
10 m diagnostic using a lower-column Richardson signal, after which the accepted
residual correction still operates.

It is also not a duplicate of the rejected Coriolis-rotated wind residual,
Helmholtz wind initialization, continuity-balanced divergence initialization,
or polar wind taper. Those changed residual direction, initialized winds, or
prognostic wind controls. This proposal is output-only, scalar, bounded, and
confined to the 10 m wind diagnostic.

## Evaluator Notes

### 2026-06-18T17:21:29Z

Decision: move to `ready` as the single recommended next implementation target.

Ranking rationale: this is the strongest current candidate because it is
output-only, low surface area, directly targets the only non-temperature
near-surface channel that still has measurable headroom after the accepted
stability-aware residual decay, and should leave MSLP and Z500 unchanged except
for bookkeeping noise. The accepted incumbent gained strongly through
near-surface residual physics with effectively neutral mass fields, so another
carefully bounded near-surface diagnostic test is a better next experiment than
the broader staged prognostic ideas.

This ranks ahead of the staged `analysis-omega-vertical-motion-spinup`,
`dissipative-heating-from-horizontal-diffusion`, and scalar-advection/dealiasing
fallbacks because those candidates alter positive-time prognostic tendencies,
transport, or energy budgets and have larger balance-risk attribution costs. It
also ranks ahead of the new solar-thermal proposal because recent
Held-Suarez/solar thermal forcing variants produced large 2 m temperature
regressions, and ahead of pressure-output remapping because recent Z500/output
diagnostic evidence is unfavorable.

This is not a duplicate of the accepted
`stability-aware-surface-residual-decay`: the accepted change controls residual
decay amplitudes/timescales after packing, while this proposal changes the raw
10 m wind diagnostic using a bounded lower-column Richardson signal and then
lets the accepted residual path operate unchanged. It is also not a duplicate
of the rejected `surface-layer-diagnostic-extrapolation`, which used a crude
two-layer extrapolation and damaged both 2 m temperature and 10 m wind; this
candidate leaves 2 m temperature untouched, avoids directional rotation, uses a
scalar bounded factor, and preserves lead-zero residual correction. The recent
`coriolis-rotated-surface-wind-residual` rejection is relevant wind-guardrail
caution, but it rotated the residual direction rather than testing a bounded
surface-layer amplitude diagnostic.
