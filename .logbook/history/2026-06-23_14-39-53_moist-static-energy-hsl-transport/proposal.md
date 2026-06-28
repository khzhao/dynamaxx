---
schema_version: 1
slug: moist-static-energy-hsl-transport
title: Moist Static Energy HSL Thermal Transport
status: ready
created_at: 2026-06-23T14:35:50Z
author_role: Researcher
target_model: dino_hsl2_theta_dse_hsl
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Moist Static Energy HSL Thermal Transport

## Hypothesis

The incumbent improved strongly by horizontally transporting dry static energy
with the accepted HSL2 departure. In humid regions, dry static energy is not the
most materially conserved thermodynamic quantity; moist static energy
`Cp T + Phi + L_v q` better follows moist adiabatic motion. If the fixed inputs
include specific humidity, transporting a bounded moist-static-energy anomaly
for the horizontal thermal tendency should reduce warm-sector and tropical
thermal phase errors without changing the forecast contract.

## Mechanism

Add an opt-in moist-static-energy branch on top of
`dino_hsl2_theta_dse_hsl`. When `specific_humidity` is available in
`state.tracers`, compute a layer-mean-removed moist static energy anomaly from
the current temperature, dry hydrostatic geopotential, and humidity. Advect it
with the same accepted HSL2 displacement and finite fallback used by the dry
static energy path. Convert the horizontal moist-static-energy tendency back to
temperature as `(dmse_dt - L_v dq_dt) / Cp`, using the incumbent finite humidity
horizontal tendency for `dq_dt`; if humidity is absent or diagnostics are
nonfinite, fall back exactly to incumbent dry-static-energy HSL transport.

## Implementation Scope

- Expected files: `primitive_equations.py` for a guarded
  `nodal_moist_static_energy_anomaly` helper and a moist-static-energy branch
  inside `temperature_tendency_potential_temperature_form`; `adapter.py`,
  `__init__.py`, and `registry.py` for a side-by-side short model alias such as
  `dino_hsl2_mse_hsl`.
- Registry changes: add one factory derived from
  `dry_static_energy_hsl_transport_dinosaur_dycore_model()` with a new boolean
  option for moist static energy transport.
- API changes: none; inputs and outputs remain the existing `WeatherState`
  contract.
- Tests to update: add finite/fallback unit tests in
  `tests/dycore/models/dinosaur/test_primitive_equations.py`, including no
  humidity fallback and finite humidity path coverage.

## Expected Metric Movement

- Expected improvements: `2m_temperature` and `geopotential_500` at days 2-10,
  especially for humid baroclinic and tropical initial states where latent
  energy gradients project onto thermal structure.
- Expected neutral metrics: `mean_sea_level_pressure` should remain close to
  incumbent because log surface pressure and pressure-gradient operators are not
  directly changed.
- Possible regressions: `10m_u_component_of_wind` could regress if latent
  heating-equivalent increments alter low-level stability and the Richardson
  wind diagnostic.

## Risks

- Numerical stability: humidity can contain sharp gradients; the branch must
  cap or fall back if `L_v q` produces nonfinite or overlarge thermal tendency.
- Compute cost: one extra scalar transport and humidity tendency conversion;
  expected to be similar to the accepted DSE branch and practical with
  `--workers 4`.
- Data leakage: uses only forecast initial humidity already present in the
  fixed input state; no future humidity or target metrics are introduced.
- Physical plausibility: converting moist static energy to temperature while
  humidity remains passive is an approximation; subtracting `L_v dq_dt` is
  required to avoid double-counting latent energy.
- Rollback complexity: low, because it is a side-by-side opt-in branch with
  incumbent fallback.

## Evaluation Plan

- Fast gate: run `uv run pytest` and
  `uv run dynamaxx-eval fast --model dino_hsl2_mse_hsl`; reject immediately on
  nonfinite diagnostics.
- Iteration gate: run
  `uv run dynamaxx-eval iteration --model dino_hsl2_mse_hsl --workers 4` and
  compare against cached `dino_hsl2_theta_dse_hsl`.
- Validation gate: run
  `uv run dynamaxx-eval validation --model dino_hsl2_mse_hsl --workers 4` only
  if fixed iteration promotion criteria pass.
- Outcome that would falsify the hypothesis: primary score fails to improve by
  the fixed threshold, or early `2m_temperature`/`geopotential_500` guardrails
  regress, indicating the latent-energy correction is not compatible with the
  passive humidity treatment.

## Citations

- Neelin, J. D. and Held, I. M. (1987), "Modeling Tropical Convergence Based on
  the Moist Static Energy Budget," Monthly Weather Review, 115, 3-12,
  https://doi.org/10.1175/1520-0493(1987)115<0003:MTCBOT>2.0.CO;2.
- Staniforth, A. and Cote, J. (1991), "Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review," Monthly Weather Review, 119, 2206-2223,
  https://doi.org/10.1175/1520-0493(1991)119<2206:SLISFA>2.0.CO;2.
- Local code reference:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`, accepted
  `nodal_dry_static_energy_anomaly` and HSL2 thermal transport path.

## Researcher Notes

This is not a pressure-work replacement and does not alter HSL departure
geometry. It follows the accepted transport-variable lesson from
`.logbook/history/2026-06-23_11-22-34_dry-static-energy-hsl-transport` while
using humidity as physically motivated thermodynamic information. It is
distinct from prior moist-virtual-temperature failures because it does not put
humidity into the pressure-gradient or geopotential dynamics; it only changes
the guarded horizontal thermal transport variable.

## Evaluator Notes

### 2026-06-23T14:38:43Z

Decision: move to `ready`.

This is the strongest next candidate. It directly extends the latest accepted
lesson: transporting dry static energy with the accepted HSL2 departure gave
large, broad iteration and validation gains with clean guardrails. The proposal
keeps the same forecast contract, the same HSL departure geometry, and the
same side-by-side rollback pattern while changing only the thermodynamic scalar
transported by the already-productive path.

The physical mechanism is credible: moist static energy is a standard budget
quantity for moist adiabatic and tropical thermodynamic structure, and the
proposal explicitly avoids the higher-risk route of putting humidity into the
pressure-gradient or geopotential dynamics. The finite fallback to incumbent
dry-static-energy HSL transport and the subtractive `L_v dq_dt` correction are
important safeguards against double-counting passive humidity advection.

Primary risks are implementation detail and passive-moisture approximation:
humidity gradients may be sharp, and the model does not have full moist
physics. Those risks are acceptable for a first ready experiment because the
implementation surface is narrow, the likely benefit can affect both
`2m_temperature` and `geopotential_500`, and a rejection would still teach
whether the accepted DSE-HSL gain is limited to dry thermodynamic structure or
can use analyzed humidity information.
