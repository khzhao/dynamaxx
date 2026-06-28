---
schema_version: 1
slug: ocean-weighted-tropical-wtg-mass-dse
title: Ocean-weighted tropical WTG mass-DSE relaxation
status: ready
rank: 1
priority: high
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

# Ocean-weighted tropical WTG mass-DSE relaxation

## Hypothesis

The current incumbent's tropical WTG mass-DSE relaxation produced validated
gains, but it applies the same free-tropospheric temperature-gradient constraint
over tropical land and ocean. WTG balance is most defensible over the maritime
deep-convective tropics, while land columns retain stronger local thermal,
orographic, and boundary-layer gradients. Weighting the accepted WTG operator by
the already available ocean fraction should preserve the accepted tropical ocean
mass-field benefit while reducing over-relaxation of tropical land thermal
structure.

## Mechanism

Add a side-by-side model, for example `dino_hsl2_mass_dse_wtg_ocean`, derived
from `dino_hsl2_mass_dse_wtg`. Keep the accepted WTG latitude envelope, sigma
envelope, low-mode projection, 5-day relaxation time, temperature increment cap,
layer-mean neutrality, finite fallbacks, and positive-time-only placement.

The only changed behavior is the WTG spatial mask. Pass the land-sea fraction
already loaded for the incumbent land-sea residual and ocean bulk sensible heat
flux paths into the WTG filter, form `ocean_weight = 1 - land_fraction` in
Dinosaur latitude order, and multiply the WTG mask and tropical mean weights by
that ocean weight. If the land-sea mask is unavailable, has an incompatible
shape, or is nonfinite, fall back exactly to the accepted incumbent WTG mask
rather than introducing a new data dependency.

This is not a new surface flux and does not change the ocean heat-flux anchor.
It only changes where the accepted free-tropospheric thermodynamic balance
filter is allowed to act.

## Implementation Scope

- Expected files: add one opt-in WTG mask selector in `adapter.py`, expose a
  factory in `__init__.py`, register a new model key in `registry.py`, and add
  focused tests under `tests/dycore/models/dinosaur/`.
- Registry changes: add `dino_hsl2_mass_dse_wtg_ocean`; keep
  `dino_hsl2_mass_dse_wtg` unchanged when the selector is disabled.
- API changes: none to `ForecastInput`, `WeatherState`, output variables,
  lead handling, or evaluation protocols.
- Tests to update: registry construction; disabled-selector equivalence; ocean
  points retain the accepted WTG increment; land-only synthetic masks suppress
  the extra WTG increment; invalid land-sea masks fall back to incumbent WTG;
  finite smoke forecast.

## Expected Metric Movement

- Expected improvements: `2m_temperature` over tropical land-adjacent regions,
  `mean_sea_level_pressure`, and `10m_u_component_of_wind` if land over-relaxation
  currently offsets part of the accepted WTG mass-field gain.
- Expected neutral metrics: open-ocean tropical `geopotential_500` and MSLP
  should remain close to the incumbent because the accepted WTG operator is
  preserved there.
- Possible regressions: the accepted WTG score gain may depend on land as well
  as ocean columns, especially over the Maritime Continent, Amazon, and Africa.
  Suppressing land WTG could reduce the validated MSLP and wind gains.

## Risks

- Numerical stability: low; this multiplies an existing bounded temperature
  increment by a bounded mask and preserves incumbent finite fallbacks.
- Compute cost: low; one additional nodal mask multiplication and weighted
  reduction inside the existing WTG filter.
- Data leakage: low; uses the same static land-sea mask path already used by
  the incumbent's residual and ocean flux features, not future observations.
- Physical plausibility: moderate; WTG is a tropical free-tropospheric balance,
  and ocean weighting narrows it toward maritime deep-convective columns, but
  continental convection can also support WTG-like adjustment.
- Rollback complexity: low; one selector, one factory, one registry entry, and
  focused tests.

## Evaluation Plan

- Fast gate: run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_ocean`
  and reject on nonfinite diagnostics or any land-sea mask fallback that changes
  shapes or output channels.
- Iteration gate: compare the fixed iteration protocol against the cached
  `dino_hsl2_mass_dse_wtg` incumbent metrics and require at least `+0.002`
  primary-score movement with clean diagnostics and guardrails.
- Validation gate: run fixed validation only after iteration promotion and
  require at least `+0.001` improvement over the cached incumbent.
- Outcome that would falsify the hypothesis: a clean near-zero or negative
  iteration delta, or any early tropical MSLP or `2m_temperature` guardrail
  regression, would indicate land columns were not the limiting error in the
  accepted WTG implementation.

## Citations

- Sobel, A. H. and C. S. Bretherton, 2000: Modeling Tropical Precipitation in a
  Single Column. Journal of Climate, 13, 4378-4392.
  https://doi.org/10.1175/1520-0442(2000)013%3C4378:MTPIAS%3E2.0.CO;2
- Sobel, A. H., J. Nilsson, and L. M. Polvani, 2001: The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences, 58, 3650-3665.
  https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Gill, A. E., 1980: Some simple solutions for heat-induced tropical
  circulation. Quarterly Journal of the Royal Meteorological Society, 106,
  447-462. https://doi.org/10.1002/qj.49710644905
- Code reference: `src/dynamaxx/dycore/models/dinosaur/adapter.py` already
  loads land-sea fraction for surface residual and ocean bulk heat-flux paths,
  and implements the accepted `_tropical_wtg_mass_dse_relaxation_step_filter`.

## Researcher Notes

This is a narrow restatement of the accepted WTG mechanism, not an incumbent
rerun and not a coefficient sweep. It differs from the rejected
`sst-sea-ice-ocean-flux-anchor`, `distributed-ocean-heat-flux`, and staged
`exact-ocean-bulk-heat-flux-split` ideas because it does not add or move a
lower-boundary heat source. The surface flux path remains incumbent-compatible;
only the geographic support of the accepted free-tropospheric WTG relaxation
changes.

It is also distinct from active thermal-residual and land-sea diagnostic ideas:
this proposal does not change output diagnostics, residual decay, or
near-surface anchors. It tests whether the newly accepted WTG balance should be
limited to the regime where the physical approximation is strongest.

## Evaluator Notes

### 2026-06-25T05:45:55Z

Decision: move to `ready`; ranked 1 of 3 new WTG follow-up proposals.
Recommendation: best next implementation target if the Orchestrator wants one
side-by-side candidate derived from `dino_hsl2_mass_dse_wtg`.

This is the cleanest bounded model-selection idea in the batch. It changes only
the geographic support of the accepted positive-time WTG mass-DSE filter while
preserving the incumbent relaxation timescale, low-mode projection, sigma and
latitude envelopes, increment cap, layer-neutral correction, finite fallback,
forecast contract, and fixed evaluation protocols. Source inspection confirms
the current incumbent lineage already carries the land-sea/ocean-weight path
for lower-boundary features, so the implementation can be a small opt-in mask
selector plus a side-by-side registry entry and focused tests rather than a new
adapter or data dependency.

The expected score signal is plausible and more targeted than the other two
variants. The accepted WTG run improved iteration by `+0.003136` and validation
by `+0.002978`, mainly through wind and MSLP with clean guardrails; this
candidate tests whether that gain can be retained over maritime convection
while reducing possible tropical-land over-relaxation. Main risk is that the
accepted gain may depend on continental and Maritime Continent land columns as
well as open-ocean columns. That risk is acceptable because the fallback and
rollback surface are narrow and the fixed guardrails should catch a loss of the
accepted MSLP/wind benefit.
