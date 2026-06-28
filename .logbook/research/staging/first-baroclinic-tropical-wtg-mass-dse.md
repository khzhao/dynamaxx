---
schema_version: 1
slug: first-baroclinic-tropical-wtg-mass-dse
title: First-internal-mode tropical WTG mass-DSE relaxation
status: staging
rank: 3
priority: medium-low
created_at: 2026-06-25T05:42:00Z
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

# First-internal-mode tropical WTG mass-DSE relaxation

## Hypothesis

The accepted WTG filter relaxes each sigma layer's low-mode mass-DSE anomaly
independently. That is robust and bounded, but it can damp vertically uniform
free-tropospheric heat-content anomalies as well as baroclinic thermal
structure. Tropical convective and gravity-wave adjustment is often organized
by a small number of vertical internal modes. Projecting the WTG relaxation onto
a fixed zero-column-mean first internal vertical mode should retain the accepted
horizontal WTG balance signal while reducing unwanted column heat-content and
surface-pressure side effects.

## Mechanism

Add a side-by-side model, for example `dino_hsl2_mass_dse_wtg_vmode`, derived
from `dino_hsl2_mass_dse_wtg`. Keep the accepted WTG latitude envelope,
low-mode horizontal projection, positive-time-only placement, relaxation
timescale, temperature cap, finite fallback checks, and output contract.

Change only the vertical structure of the mass-DSE anomaly passed to the WTG
increment. Build a fixed smooth vertical basis from the incumbent WTG sigma
envelope and sigma centers. The basis should be zero outside the accepted
free-tropospheric WTG region, have zero pressure-thickness-weighted vertical
mean under the fixed sigma grid, and be normalized by its squared norm. Project
the accepted low-mode tropical mass-DSE anomaly onto that single vertical basis
at each horizontal point, reconstruct the projected anomaly, and apply the
accepted WTG relaxation to that projected field.

If the vertical basis norm, projection coefficient, pressure thickness, DSE
diagnostics, or reconstructed increment is nonfinite, the filter must fall back
exactly to the incumbent `dino_hsl2_mass_dse_wtg` state. The candidate must not
become a vertical-mode family or coefficient sweep.

## Implementation Scope

- Expected files: add one optional vertical-mode projection selector in
  `adapter.py`, expose the factory in `__init__.py`, register a new model key
  in `registry.py`, and add focused tests under `tests/dycore/models/dinosaur/`.
- Registry changes: add `dino_hsl2_mass_dse_wtg_vmode`; keep the incumbent
  model byte-for-byte equivalent when the selector is disabled.
- API changes: none to `ForecastInput`, `WeatherState`, evaluation protocols,
  target variables, or lead schedules.
- Tests to update: registry construction; fixed vertical basis has zero
  pressure-thickness-weighted mean; vertically uniform synthetic WTG anomalies
  are suppressed; first-mode synthetic anomalies are retained and capped; finite
  fallback preserves the incumbent state on invalid diagnostics.

## Expected Metric Movement

- Expected improvements: `mean_sea_level_pressure` and `geopotential_500` if
  the accepted WTG gain is partly offset by column heat-content changes that
  project onto hydrostatic thickness and surface pressure.
- Expected neutral metrics: `2m_temperature` should remain near incumbent
  because the WTG mask stays in the free troposphere and the surface flux path
  is unchanged.
- Possible regressions: the accepted layerwise WTG filter may need vertically
  uniform tropical warming or cooling components to improve the fixed metrics.
  Removing those components could make the candidate too weak.

## Risks

- Numerical stability: low to moderate; the operation is a bounded projection,
  but poor vertical normalization could amplify small layer anomalies if not
  tested carefully.
- Compute cost: low; one vertical projection and reconstruction per WTG filter
  call, with no extra forecast steps.
- Data leakage: none; uses only fixed sigma geometry and the current forecast
  state.
- Physical plausibility: moderate; internal-mode truncations are standard in
  reduced tropical dynamics, but a single fixed dry mode may be too crude for
  the full primitive-equation column.
- Rollback complexity: low; one selector, one helper, one model key, and
  focused tests.

## Evaluation Plan

- Fast gate: run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vmode`
  and reject on nonfinite diagnostics, failed basis-normalization tests, or any
  broken finite fallback.
- Iteration gate: compare fixed iteration against cached
  `dino_hsl2_mass_dse_wtg` metrics and require at least `+0.002` primary-score
  movement with clean diagnostics and fixed guardrails.
- Validation gate: run fixed validation only after iteration promotion and
  require at least `+0.001` improvement over the cached incumbent.
- Outcome that would falsify the hypothesis: a clean near-zero or negative
  iteration delta would show layerwise WTG damping is already better than a
  first-mode projection; any early MSLP or Z500 guardrail failure would show the
  projection damages hydrostatic balance.

## Citations

- Sobel, A. H. and C. S. Bretherton, 2000: Modeling Tropical Precipitation in a
  Single Column. Journal of Climate, 13, 4378-4392.
  https://doi.org/10.1175/1520-0442(2000)013%3C4378:MTPIAS%3E2.0.CO;2
- Sobel, A. H., J. Nilsson, and L. M. Polvani, 2001: The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences, 58, 3650-3665.
  https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Neelin, J. D. and N. Zeng, 2000: A Quasi-Equilibrium Tropical Circulation
  Model: Formulation. Journal of the Atmospheric Sciences, 57, 1741-1766.
  https://doi.org/10.1175/1520-0469(2000)057%3C1741:AQETCM%3E2.0.CO;2
- UCLA Climate Systems Interactions Group: QTCM overview, noting a single deep
  convective mode in the vertical thermodynamic structure.
  https://atmos.ucla.edu/csi/qtcm/
- Code reference: `src/dynamaxx/dycore/models/dinosaur/adapter.py` contains the
  accepted WTG sigma envelope and mass-DSE filter; this proposal changes only
  the vertical projection of the anomaly inside that helper.

## Researcher Notes

This is not a duplicate of staged `column-neutral-mass-dse-increment` or
`column-dry-static-energy-recentering`. Those ideas alter the accepted mass-DSE
HSL increment or column DSE state more broadly. This proposal acts only inside
the accepted WTG filter, after the incumbent mass-DSE HSL forecast step, and
projects only the tropical WTG anomaly before applying the same bounded
relaxation.

It is also different from the rejected `vertical-dse-transport-mass-hsl`, which
added a new vertical DSE transport tendency and produced a short-lead MSLP
shock. This candidate adds no vertical transport. It asks whether the accepted
WTG thermal correction should have a more physically constrained vertical
structure.

## Evaluator Notes

### 2026-06-25T05:45:55Z

Decision: move to `staging`; ranked 3 of 3 new WTG follow-up proposals.

This proposal satisfies the high-level loop constraints: it is one bounded
side-by-side WTG variant, keeps the forecast and evaluation contracts fixed,
uses no future observations, and proposes focused tests for basis normalization,
fallbacks, and increment caps. The physical motivation is reasonable because
reduced tropical dynamics often represent convective adjustment with a small
number of internal vertical modes.

The reason to stage rather than ready it is implementation and guardrail risk.
It adds a new vertical projection inside a recently accepted thermodynamic
filter, and the loop history shows vertical DSE transport produced a large
short-lead MSLP guardrail failure even though that was a different mechanism.
The accepted WTG incumbent also already has layer-mean neutrality and clean
Z500/MSLP guardrails, so the first-mode projection may be a more complex way to
weaken a working correction. Reconsider after simpler WTG support/projection
variants have been tested, or if future scorer notes show column heat-content
side effects from WTG as the limiting issue.
