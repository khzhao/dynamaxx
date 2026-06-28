---
schema_version: 1
slug: hydrostatic-inverted-mass-dse-hsl
title: Invert Mass-DSE HSL Tendencies Through the Hydrostatic Operator
status: ready
created_at: 2026-06-24T01:38:14Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Invert Mass-DSE HSL Tendencies Through the Hydrostatic Operator

## Hypothesis

The incumbent `dino_hsl2_mass_dse` transports layer-mass-weighted dry static
energy and then converts the horizontal dry-static-energy tendency back to a
temperature tendency by dividing by `c_p`. That is a useful first-order
conversion, and it was accepted, but dry static energy is `c_p T + Phi`. In a
hydrostatic sigma column, changing temperature also changes the geopotential
part of dry static energy through the same vertical matrix used by
`get_geopotential_diff_sigma`.

The next cleaner test is to keep the accepted transported scalar and HSL
trajectory unchanged, but invert the diagnosed mass-DSE horizontal tendency
through the discrete hydrostatic response `c_p I + G`. This should make the
thermal tendency more consistent with the DSE variable that is actually being
transported, without adding the rejected pressure-thickness product-rule term.

## Mechanism

Register a side-by-side candidate such as `dino_mass_dse_hydroinv` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- preserve the accepted HSL2 departure, bilinear remap, layer-pressure-thickness
  weighting, vertical theta tendency, adiabatic tendency, pressure tendency,
  momentum tendencies, residual corrections, output variables, and fixed
  evaluation protocols;
- after the incumbent mass-DSE branch computes
  `layer_mass_dse_dt_horizontal_nodal`, solve a small vertical linear system per
  horizontal grid point:
  `(c_p I + G_sigma) dT_dt = layer_mass_dse_dt_horizontal_nodal`, where
  `G_sigma` is the existing hydrostatic geopotential weight matrix for dry
  sigma columns;
- add the incumbent vertical theta tendency and adiabatic tendency exactly as
  `dino_hsl2_mass_dse` does;
- fall back exactly to the accepted `dino_hsl2_mass_dse` temperature tendency if
  the matrix, solved tendency, pressure thickness, or converted modal tendency
  is nonfinite.

This changes only the DSE-to-temperature conversion. It does not use
`d(delta_p) / dt`, does not alter log-surface-pressure continuity, and does not
change the forecast contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry key for
    `dino_mass_dse_hydroinv`.
- API changes:
  - None.
- Tests to update:
  - Verify the candidate preserves every `dino_hsl2_mass_dse` setting except
    the new conversion selector and model name.
  - Verify a zero DSE tendency solves to zero temperature tendency.
  - Verify a synthetic one-column tendency matches a direct dense
    `(c_p I + G_sigma)` solve.
  - Verify nonfinite solve diagnostics fall back to the accepted mass-DSE
    tendency.
  - Verify registration and unchanged output variables.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 2-10 if the
    current `1 / c_p` conversion leaves hydrostatic thickness response
    inconsistent with the transported DSE.
  - `2m_temperature` at medium leads if lower-column thermal increments become
    better vertically balanced.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, except through balanced pressure-gradient
    feedback, because no momentum or 10 m diagnostic path changes directly.
- Possible regressions:
  - The accepted `1 / c_p` conversion may be empirically optimal because it
    avoids feeding upper-level hydrostatic response back into the thermal
    tendency.
  - Short-lead MSLP/Z500 could regress if the vertical solve over-amplifies
    upper-column temperature increments.

## Risks

- Numerical stability:
  - Moderate. The vertical solve is deterministic and low dimensional, but it
    changes every thermodynamic horizontal tendency.
- Compute cost:
  - Low to moderate. It adds one small vertical matrix solve or precomputed
    inverse per thermal tendency evaluation and no new remaps.
- Data leakage:
  - None. It uses only current forecast state variables and fixed sigma
    coordinate matrices.
- Physical plausibility:
  - High as a discrete hydrostatic consistency test for a DSE-transport
    incumbent.
- Rollback complexity:
  - Low. Remove one selector/helper, factory/export, registry key, and focused
    tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_mass_dse_hydroinv`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_mass_dse_hydroinv --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure against cached `dino_hsl2_mass_dse`.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_mass_dse_hydroinv --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the accepted
    `1 / c_p` conversion already captures the useful mass-DSE signal. Any
    short-lead MSLP/Z500 guardrail failure would show the hydrostatic inversion
    is too aggressive for this sigma core.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements `get_geopotential_weights_sigma`, `get_geopotential_diff_sigma`,
  and the accepted mass-DSE branch in `temperature_tendency_potential_temperature_form`.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted `dino_hsl2_mass_dse` with iteration delta `+0.005725334705943053`
  and validation delta `+0.00546393735603079`.
- Dynamaxx history:
  `.logbook/history/2026-06-23_22-01-24_pressure-thickness-corrected-mass-dse-hsl/decision.md`
  rejected the pressure-thickness product-rule correction, so this proposal
  deliberately leaves pressure-thickness tendency out of the mechanism.
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Thuburn, J. 2008. Some Conservation Issues for the Dynamical Cores of NWP and
  Climate Models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This is not a duplicate of staged `area-neutral-mass-dse-hsl`, which removes a
horizontal zero mode from the HSL tendency, or staged
`static-stability-gated-mass-dse-hsl`, which chooses between two existing
thermal paths with a local stability mask. This proposal keeps the incumbent
mass-DSE tendency amplitude and location, but changes the vertical conversion
from DSE tendency to temperature tendency.

It also differs from the rejected pressure-work candidates. Those added or
bounded new pressure-work thermal increments and either failed MSLP/Z500
guardrails or became neutral. Here the pressure-work and log-pressure equations
remain untouched; the only new operator is the hydrostatic DSE inversion
required by the definition of dry static energy.

## Evaluator Notes

### 2026-06-24T01:43:04Z

Decision: move to `ready`; rank 1 of 3 new proposals.

This is the strongest next experiment. It tests a specific inconsistency in the
accepted incumbent: `dino_hsl2_mass_dse` transports a mass-weighted dry static
energy anomaly but converts the horizontal tendency back to temperature with a
plain `1 / c_p` factor. The repository already defines the sigma hydrostatic
geopotential weight matrix, so inverting `c_p I + G_sigma` is a direct,
local consistency check rather than a new forcing or a protocol-facing metric
adjustment. The mechanism is also carefully separated from the latest rejected
pressure-thickness product-rule correction, whose iteration delta was
`-0.006172261163569502` against this incumbent.

The literature and source checks support the framing: Simmons and Burridge-style
vertical-coordinate energy consistency, Thuburn-style conservation concerns, and
the local `get_geopotential_weights_sigma` implementation all point to the
hydrostatic operator as the right discrete object to test. This does not prove
the score will improve; the accepted `1 / c_p` approximation may already be the
best empirical compromise. The candidate is still worth the next ready slot
because it is low surface-area, rollbackable, uses no validation tuning, and
will produce a useful lesson about whether the mass-DSE gain survives a more
faithful DSE-to-temperature inversion.

Ranked recommendation: implement first. Keep the fixed fast, iteration, and
validation gates unchanged; do not run validation unless the iteration gate
promotes. If iteration is clean but negative or near zero, treat hydrostatic
inversion of the mass-DSE increment as negative evidence and move on to the
lower-amplitude conservation projections in staging.
