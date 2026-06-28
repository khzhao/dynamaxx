---
schema_version: 1
slug: virtual-static-energy-tropical-wtg
title: Virtual-static-energy tropical WTG relaxation
status: scrap
rank: 3
priority: low
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

# Virtual-static-energy tropical WTG relaxation

## Hypothesis

The accepted WTG filter relaxes dry mass-DSE anomalies, but WTG balance in the
tropics is closely tied to moist buoyancy and hydrostatic thickness. The current
incumbent carries specific humidity as a tracer while leaving full moist
dynamics disabled. A bounded WTG diagnostic that uses virtual-temperature
thickness information, but still converts the final correction to the existing
temperature state, may better target humid tropical mass-field errors without
changing the forecast contract.

## Mechanism

Add a side-by-side candidate, for example `dino_hsl2_mass_dse_wtg_vstatic`,
derived from `dino_hsl2_mass_dse_wtg`. In the WTG filter only, when a finite
specific-humidity tracer is present:

- compute a guarded virtual-temperature factor from the current humidity
  tracer using the existing dry-air and water-vapor gas constants;
- diagnose a virtual hydrostatic geopotential and a virtual static energy
  anomaly for the tropical WTG mask;
- relax the low-mode virtual-static-energy anomaly toward its tropical layer
  mean with the accepted WTG timescale and temperature increment cap;
- convert the bounded virtual-static-energy increment back to a temperature
  increment by `Cp`, while preserving the accepted dry fallback if humidity is
  absent, nonfinite, or outside conservative bounds.

The humidity tracer is used as a same-time diagnostic only. It is not nudged,
scored differently, or exposed as a new output.

## Implementation Scope

- Expected files: add one optional virtual-static-energy WTG branch in
  `adapter.py`; expose one factory through `__init__.py`; add one registry key
  in `registry.py`; add focused tests for dry fallback, missing humidity,
  finite humidity bounds, and registry construction.
- Registry changes: add `dino_hsl2_mass_dse_wtg_vstatic`; keep the incumbent
  `dino_hsl2_mass_dse_wtg` unchanged when the selector is disabled.
- API changes: none. Inputs and outputs remain the same WeatherState contract;
  the fixed evaluation protocols remain unchanged.
- Tests to update: synthetic WTG tests proving the dry limit matches the
  incumbent, missing humidity falls back exactly, finite virtual diagnostics
  remain capped, and invalid humidity cannot alter the state.

## Expected Metric Movement

- Expected improvements: `mean_sea_level_pressure`, `geopotential_500`, and
  `10m_u_component_of_wind` in humid tropical and subtropical cases if dry WTG
  is undercorrecting moist thickness anomalies.
- Expected neutral metrics: dry extratropical columns and runs without humidity
  should be identical to the accepted WTG incumbent.
- Possible regressions: passive humidity may have phase or amplitude errors
  relative to the simplified dry dynamics, so using it in a thermal balance
  diagnostic could degrade MSLP or Z500 despite clean numerical diagnostics.

## Risks

- Numerical stability: moderate. Humidity enters only a capped diagnostic, but
  bad humidity outliers must be guarded tightly.
- Compute cost: low to moderate. The branch adds one virtual hydrostatic
  diagnostic inside the WTG filter.
- Data leakage: none. The humidity tracer is part of the same forecast state
  already passed through the model.
- Physical plausibility: moderate. Virtual temperature is directly tied to
  moist density and geopotential thickness, but this dry dycore has no complete
  moist physics closure.
- Rollback complexity: low. One selector and factory should isolate the branch.

## Evaluation Plan

- Fast gate: run `uv run pytest` plus `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vstatic`.
- Iteration gate: run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vstatic --workers <worker_count>` and compare against compatible cached `dino_hsl2_mass_dse_wtg` incumbent metrics.
- Validation gate: run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vstatic --workers <worker_count>` only if iteration promotes.
- Outcome that would falsify the hypothesis: a negative or subthreshold
  iteration delta, especially with tropical MSLP or Z500 degradation, would
  show that humidity-aware WTG diagnostics are not helpful in the current dry
  mass-DSE dycore.

## Citations

- Sobel, A. H., J. Nilsson, and L. M. Polvani, 2001: The Weak Temperature
  Gradient Approximation and Balanced Tropical Moisture Waves. Journal of the
  Atmospheric Sciences. https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Raymond, D. J. and X. Zeng, 2005: Modelling tropical atmospheric convection
  in the context of the weak temperature gradient approximation. Quarterly
  Journal of the Royal Meteorological Society. https://doi.org/10.1256/qj.03.97
- NOAA/NWS training material on thickness and virtual temperature:
  https://www.weather.gov/source/zhu/ZHU_Training_Page/Miscellaneous/Heights_Thicknesses/thickness_temperature.htm
- Local code reference:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` already
  contains virtual-temperature humidity adjustments for moist dynamics, while
  `adapter.py` keeps humidity as an optional tracer in the incumbent chain.

## Researcher Notes

This is materially narrower than rejected and scrapped humidity proposals such
as broad moist-static-energy HSL transport or full virtual-temperature dynamics:
humidity affects only the accepted WTG diagnostic branch and must fall back to
the dry incumbent when unsafe. It is also not a support-narrowing follow-up to
the rejected ocean-weighted WTG iteration; the accepted tropical mask remains
intact while the diagnosed balance variable changes.

## Evaluator Notes

### 2026-06-25T09:05:19Z

Decision: move to `scrap`; ranked 3 of 3 new WTG follow-up proposals.

The proposal is bounded and keeps the external forecast contract unchanged,
but it is a poor next use of the loop. It would feed passive humidity into an
active thermal correction every WTG-filtered step. That is narrower than full
moist dynamics, but it still changes the prognostic temperature path through a
humidity-coupled balance diagnostic rather than remaining a read-only output
diagnostic.

Local evidence is unfavorable. `bounded-moist-virtual-temperature-dynamics`
ran cleanly but regressed iteration by `-0.055193744700895`; moist-static-energy
HSL transport was effectively neutral to slightly negative; passive humidity
positivity was numerical-scale; and `virtual-geopotential-mass-dse-hsl` was
already scrapped because passive humidity in active thermal transport had weak
upside and clear MSLP/Z500 risk. The cited WTG and virtual-temperature
literature makes the mechanism physically recognizable, but it does not
override this repository-specific history.

The compute and implementation cost is also higher than the mass-neutral
closure because it adds humidity validation plus a virtual hydrostatic/static
energy diagnostic inside WTG. Reconsider only if a future read-only diagnostic
shows that dry-vs-virtual WTG static-energy mismatch is a material remaining
error source under the current accepted WTG incumbent.
