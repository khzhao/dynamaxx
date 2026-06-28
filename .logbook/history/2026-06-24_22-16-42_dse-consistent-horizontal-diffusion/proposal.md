---
schema_version: 1
slug: dse-consistent-horizontal-diffusion
title: DSE-Consistent Horizontal Diffusion
status: ready
created_at: 2026-06-24T22:43:00Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# DSE-Consistent Horizontal Diffusion

## Hypothesis

`dino_hsl2_mass_dse` improved the incumbent by transporting horizontal thermal
structure as a layer-mass-weighted dry-static-energy anomaly, but the
positive-time horizontal diffusion filter still damps the stored
`temperature_variation` modal coefficients directly. That means transport and
diffusion act on different thermodynamic variables: advection sees
`c_p T + Phi`, while diffusion sees only `T`.

A candidate that applies the existing horizontal diffusion strength to the DSE
anomaly, then converts the filtered DSE change back to temperature with the same
guarded `1 / c_p` approximation used by the accepted HSL branch, may reduce
thermal thickness noise without repeating failed remap, initialization, or
hydrostatic-inversion mechanisms.

## Mechanism

Register one side-by-side candidate such as `dino_mass_dse_diff`.

For the candidate only:

- keep the incumbent diffusion timescale, diffusion order, HSL2 midpoint
  departure, mass-DSE transport, weak-HS forcing, ocean sensible heat flux, DFI,
  residuals, and output contract;
- replace only the diffusion treatment of `temperature_variation` in the
  positive-time rollout filter:
  - diagnose the incumbent dry static energy anomaly from the next state using
    the existing dry hydrostatic path;
  - transform that anomaly to modal space, apply the same horizontal diffusion
    scaling used for scalar fields, and transform back to nodal space;
  - convert the filtered DSE anomaly change to a temperature increment with
    `dT = dDSE / c_p`, leaving vorticity, divergence, log-surface pressure,
    tracers, and `sim_time` on the incumbent diffusion path;
  - preserve layerwise DSE-anomaly mean neutrality and fall back to incumbent
    temperature diffusion if any diagnostic is nonfinite or shape-incompatible.

This should not add dissipative heating, retune the diffusion strength, alter
momentum diffusion, or run inside time-reversed DFI until the positive-time
candidate has promoted. Keep it as one fixed model-selection candidate.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` if a shared
    DSE diagnostic helper is needed
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model alias, for example `dino_mass_dse_diff`.
- API changes:
  - None.
- Tests to update:
  - Verify the candidate preserves all incumbent settings except the DSE
    diffusion selector and model name.
  - Verify a horizontally constant DSE anomaly is unchanged by the candidate
    thermal diffusion.
  - Verify non-thermal leaves match the incumbent diffusion path.
  - Verify nonfinite DSE diagnostics fall back to incumbent temperature
    diffusion.
  - Verify registry construction and a finite smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if thermal
    diffusion is currently damping temperature in a way that is inconsistent
    with the accepted DSE transport variable.
  - `2m_temperature` if lower-layer smoothing better respects geopotential
    thickness.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close because momentum diffusion and
    the Richardson 10 m diagnostic are unchanged.
- Possible regressions:
  - Direct temperature diffusion may be empirically better because it damps
    lower-layer temperature noise without coupling to hydrostatic thickness.
  - DSE-based diffusion may weaken a beneficial thermal damping path and degrade
    `2m_temperature`.

## Risks

- Numerical stability:
  - Low to moderate. The change is a guarded post-step filter, but it edits the
    prognostic thermal state every positive-time inner step.
- Compute cost:
  - Moderate. It adds DSE diagnostics and transforms inside the filter, but no
    new forecast steps or remaps.
- Data leakage:
  - None. Uses only current forecast state and fixed grid operators.
- Physical plausibility:
  - Moderate to high. Dry static energy is a standard thermodynamic energy
    variable, and spectral diffusion/filtering is standard in spectral models.
- Rollback complexity:
  - Low. Remove one selector/helper, factory/export, registry key, and focused
    tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_mass_dse_diff`.
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_mass_dse_diff --workers 4`.
  - Compare against cached `dino_hsl2_mass_dse` artifacts when valid.
  - Require primary-score delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_mass_dse_diff --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show scalar temperature
    diffusion remains the better empirical damping variable. Any early MSLP or
    Z500 guardrail failure would show DSE diffusion perturbs mass balance too
    much.

## Citations

- Thuburn, J. 2008. Some Conservation Issues for the Dynamical Cores of NWP and
  Climate Models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Gottlieb, D. and Shu, C.-W. 1997. On the Gibbs Phenomenon and Its Resolution.
  SIAM Review. https://doi.org/10.1137/S0036144596301390
- Hou, T. Y. and Li, R. 2007. Computing Nearly Singular Solutions Using
  Pseudo-Spectral Methods. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2007.04.014
- Chavas, D. R. 2023. Static Energy Deserves Greater Emphasis in the Meteorology
  Community. Bulletin of the American Meteorological Society.
  https://doi.org/10.1175/BAMS-D-22-0013.1
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted DSE as the useful horizontal thermal transport variable, while
  `.logbook/history/2026-06-24_01-58-03_hydrostatic-inverted-mass-dse-hsl/decision.md`
  rejected hydrostatic inversion. This proposal keeps the accepted `1 / c_p`
  conversion and changes only the diffusion variable.

## Researcher Notes

This is not a duplicate of staged diffusion ideas such as
`vorticity-sparing-horizontal-diffusion`, `planetary-wave-preserving-horizontal-diffusion`,
`sigma-tapered-horizontal-diffusion`, or diffusion-heating proposals: those
change momentum damping, vertical/dynamical masks, or add heat returned from
dissipation. Here the diffusion strength, order, and non-thermal leaves stay on
the incumbent path; only the thermal scalar being diffused is changed from
temperature anomaly to dry-static-energy anomaly.

It also avoids the recent DSE failures. It does not alter sigma initialization,
HSL remap quadrature, pressure-thickness product rules, or vertical DSE
transport.

## Evaluator Notes

### 2026-06-24T22:15:03Z

Decision: move to `ready`; ranked 1 of 3 new proposals and the only ready
recommendation from this triage pass.

This is the strongest current implementation candidate because it asks a
mechanistically direct question left by the accepted `dino_hsl2_mass_dse`
incumbent: the rollout now advects a layer-mass dry-static-energy anomaly, but
the positive-time horizontal diffusion still damps the stored temperature
variation. Changing only the thermal scalar seen by the existing diffusion
filter is novel against the active staged diffusion backlog, which mostly
changes spectral selectivity, vertical masks, momentum damping, or dissipative
heating rather than thermodynamic variable consistency.

The proposal is not low risk: prior diffusion-family results are weak or
negative, including the strongly rejected scale-selective hyperdiffusion and
the essentially neutral symmetric diffusion split and Helmholtz momentum
diffusion. It also touches the positive-time state every inner step, so the
Implementer should keep the incumbent diffusion order, timescale, non-thermal
leaves, DFI route, and fallback behavior fixed. Still, compared with the other
new proposals, this one has the best chance of producing score-scale movement
across `geopotential_500`, `mean_sea_level_pressure`, and `2m_temperature`
without repeating the recent initialization, remap, or hydrostatic-inversion
failures.

Recommendation: Orchestrator may select this if choosing a next ready target.
Require side-by-side registration, conservative finite guards, focused tests
showing non-thermal leaves remain incumbent-equivalent, and fixed fast,
iteration, then validation gates only if iteration promotes.
