---
schema_version: 1
slug: static-roughness-weighted-ekman-coupling
title: Static Roughness-Weighted Coupled Ekman Closure
status: ready
created_at: 2026-06-29T20:56:12Z
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

# Static Roughness-Weighted Coupled Ekman Closure

## Hypothesis

The accepted `dino_ri2m_ekman_coupled` candidate showed that a weak coupled
surface-stress and Ekman-pumping closure is a material missing mechanism under
the fixed WeatherBench2 protocols. Its drag coefficient is still spatially
uniform. That asks the same near-surface turbulent exchange over open ocean,
coastlines, vegetated land, and rough continental surfaces, even though
surface-layer momentum transfer is strongly controlled by roughness and land
surface heterogeneity.

A bounded static roughness multiplier applied inside the accepted prognostic
Ekman stress path should preserve the incumbent's globally tuned mean drag
while moving the stress and pumping response toward locations where the fixed
uniform closure is physically least representative. This targets remaining
`10m_u_component_of_wind`, `mean_sea_level_pressure`, and indirect
`geopotential_500` errors without changing the final wind diagnostic, adding
thermal pressure-work, or changing evaluation protocols.

## Mechanism

Register one side-by-side candidate such as `dino_ri2m_ekman_z0`. Preserve the
incumbent HSL, mass-DSE, WTG, vertical-DSE ramp, low-mode T2m memory, RI2m
diagnostic, accepted Ekman stress-pumping caps, pressure/wind ratio cap,
equatorial taper, output variables, lead schedule, and fixed evaluation
protocols.

For this candidate only:

- load static `land_sea_mask` and, if present in the same WeatherBench2
  constants path, `soil_type` or `geopotential_at_surface` as bounded roughness
  proxies;
- build a smooth dimensionless roughness multiplier from broad classes only:
  ocean near the accepted baseline, fractional coastlines blended continuously,
  rough land modestly above baseline, and high-terrain or rough-soil classes
  softly capped;
- normalize the multiplier by its area-weighted global mean so the candidate
  preserves the accepted global mean drag coefficient
  `_EKMAN_COUPLED_DRAG_COEFFICIENT`;
- multiply the accepted same-step stress coefficient by this normalized map
  before both the momentum increment and same-stress Ekman pumping diagnostic;
- keep all incumbent wind-increment caps, log-pressure caps, global zonal
  acceleration removal, mass-neutral log-pressure projection, finite fallback,
  and pressure/wind response cap unchanged;
- fall back exactly to `dino_ri2m_ekman_coupled` if static fields are missing,
  nonfinite, shape-incompatible, or fail the bounded range checks.

The first implementation should not sweep coefficients. Use one declared
roughness map, one conservative multiplier range such as `0.75` to `1.35`
before area normalization, and the incumbent mean drag after normalization.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory derived from
    `ekman_coupled_dinosaur_dycore_model()`.
- API changes:
  - None. Forecast inputs, forecast outputs, target variables, lead times,
    metrics, and fixed protocols remain unchanged.
- Tests to update:
  - Verify an all-one roughness multiplier reproduces the incumbent Ekman
    stress and pumping path.
  - Verify area normalization preserves the accepted global mean drag on a
    representative static mask.
  - Verify ocean, coastline, land, and rough-terrain examples are ordered and
    bounded.
  - Verify invalid or missing static fields fall back exactly to the incumbent.
  - Verify the candidate factory differs from the incumbent only by the new
    roughness-weighted Ekman selector and model name.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` where the uniform accepted drag under-damps rough
    land or over-damps smooth ocean.
  - `mean_sea_level_pressure` if spatially placed stress convergence improves
    cyclone and anticyclone boundary-layer pressure tendencies.
  - `geopotential_500` through better lower-boundary mass and wind balance at
    medium leads.
- Expected neutral metrics:
  - `2m_temperature`, because the RI2m diagnostic, low-mode T2m memory, and
    thermal tendencies are unchanged directly.
- Possible regressions:
  - If the accepted global drag coefficient already compensates for missing
    spatial roughness, redistributing it can worsen regional wind and pressure
    phase.
  - Static roughness proxies from `soil_type` or terrain can be too coarse at
    T80 and may add stationary texture to MSLP.

## Risks

- Numerical stability:
  - Low to moderate. The candidate changes an accepted rollout filter, but all
    accepted caps, mean removals, and finite fallbacks remain active.
- Compute cost:
  - Low. The roughness map is static and local; runtime adds one multiply in an
    already active stress path.
- Data leakage:
  - None. Static constants are forecast-time fields and no truth, validation
    statistics, or future targets are used.
- Physical plausibility:
  - Moderate to high. Surface-layer turbulent drag depends on roughness length
    and surface heterogeneity, but this is a reduced static proxy rather than a
    full Monin-Obukhov surface-layer scheme.
- Rollback complexity:
  - Low. Remove one selector, one static-map helper, one factory/export, one
    registry key, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_ekman_z0`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_z0 --workers 4`.
  - Compare against cached incumbent iteration primary
    `-0.16500618979404214`; support requires primary-score delta at least
    `+0.002`, clean diagnostics, and no fixed guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_ekman_z0 --workers 4`
    only after iteration promotion.
  - Compare against cached incumbent validation primary
    `-0.16591150807771451`; require validation delta at least `+0.001`.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the accepted
    spatially uniform Ekman closure already captures the useful mean stress
    signal. Any early U10 or MSLP guardrail failure would show the static
    roughness redistribution is too intrusive.

## Citations

- Local evidence:
  `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/decision.md`
  accepted `dino_ri2m_ekman_coupled` with iteration delta
  `+0.04799113626142959` and validation delta `+0.04683104652127085`.
- Local negative evidence:
  `.logbook/history/2026-06-26_04-36-24_roughness-aware-surface-wind-diagnostic/decision.md`
  rejected an output-only roughness-aware 10 m wind diagnostic. This proposal
  therefore changes only the prognostic accepted stress-pumping closure and
  keeps final wind diagnostics unchanged.
- Local staging evidence:
  `.logbook/research/staging/helmholtz-projected-ekman-coupling.md` tests a
  rotational/divergent split of the accepted Ekman increment. This proposal
  does not project winds or alter divergence routing.
- Beljaars, A. C. M. and Holtslag, A. A. M. 1991. "Flux Parameterization over
  Land Surfaces for Atmospheric Models." Journal of Applied Meteorology.
  https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2
- Garratt, J. R. 1992. The Atmospheric Boundary Layer. Cambridge University
  Press. https://www.cambridge.org/gb/universitypress/subjects/earth-and-environmental-science/atmospheric-science-and-meteorology/atmospheric-boundary-layer
- ECMWF Forecast User Guide, Section 9.3, notes that roughness-length
  parameterization is used for realistic area-averaged turbulent drag over
  different underlying surfaces.
  https://confluence.ecmwf.int/display/FUG/Section+9.3+Surface+Wind
- ECMWF IFS Documentation Part IV, Physical Processes, documents turbulent
  transport and surface interactions as represented physical processes.
  https://www.ecmwf.int/en/elibrary/79989-ifs-documentation-cy43r1-part-iv-physical-processes

## Researcher Notes

This is intentionally not a near-duplicate of the rejected roughness-aware
surface-wind diagnostic: no output wind channel is rescaled, no RI10m or RI2m
diagnostic is changed, and no final diagnostic correction is added. It is also
not a drag-amplitude tuning retry because the area-weighted mean drag is held
at the accepted incumbent value.

It differs from staged `helmholtz-projected-ekman-coupling` because the full
accepted vector wind increment, pumping path, caps, and divergence treatment
remain intact. The only tested mechanism is spatial placement of the already
accepted stress-pumping closure using static roughness evidence.

## Evaluator Notes

### 2026-06-29T21:02:16Z

Decision: move to `ready`; ready ranking `1 of 1`.

This is the strongest proposal in the current batch. The accepted
`dino_ri2m_ekman_coupled` history shows the coupled lower-layer stress and
mass-neutral pumping path is high leverage, with broad iteration and validation
gains across `10m_u_component_of_wind`, `mean_sea_level_pressure`, and
`geopotential_500`. This proposal changes the spatial placement of that
accepted stress-pumping response while preserving the incumbent global mean
drag, vector increment, pressure-pumping route, caps, mean removals, equatorial
taper, finite fallback, output contract, and fixed evaluation protocols. That
is a clearer bounded mechanism than another output wind diagnostic or drag
coefficient sweep.

The proposal is not a duplicate of the rejected roughness-aware 10 m wind
diagnostic. That experiment only changed the final wind observation operator
and moved iteration by `-0.00023691303605483105`; this proposal instead applies
a static, area-normalized roughness multiplier inside the prognostic Ekman
stress and pumping branch, leaving RI10m/RI2m output diagnostics unchanged. It
is also better suited for the next slot than staged
`helmholtz-projected-ekman-coupling`: the Helmholtz idea removes the accepted
divergent wind increment from the rollout state, while this proposal preserves
the accepted wind/mass routing and only redistributes a mean-preserving
coefficient.

Implementation risk is moderate because it still touches the accepted rollout
filter. The Orchestrator should require one predeclared conservative roughness
map, no coefficient sweep, exact fallback to `dino_ri2m_ekman_coupled` when
static fields are missing or invalid, and tests proving that an all-one
multiplier reproduces the incumbent and that area normalization preserves the
accepted global mean drag. Terrain or soil proxies should be softly capped and
used only after strict shape, finite-value, and range checks because older
terrain/orography history showed early MSLP/Z500 guardrail sensitivity when
static lower-boundary structure is allowed to affect mass fields too strongly.

Recommendation to the Orchestrator: implement this proposal first from the
current research set, using cached incumbent artifacts unless the protocol
cache checks find a concrete incompatibility.
