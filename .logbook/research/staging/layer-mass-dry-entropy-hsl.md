---
schema_version: 1
slug: layer-mass-dry-entropy-hsl
title: Layer-Mass Dry-Entropy HSL Transport
status: staging
created_at: 2026-06-24T15:42:00Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Layer-Mass Dry-Entropy HSL Transport

## Hypothesis

The incumbent thermodynamic path already showed that potential-temperature HSL
and dry-static-energy HSL can matter. Dry entropy, proportional to
`Cp * log(theta)` for ideal dry air up to a constant, is another materially
conserved adiabatic scalar. Transporting a layer-mass-weighted dry-entropy
anomaly may reduce multiplicative thermal errors and protect temperature
positivity better than linear theta or DSE transport, while preserving the
incumbent forecast contract.

## Mechanism

Register a side-by-side candidate, for example `dino_hsl2_mass_entropy`.
Preserve DFI, weak-HS forcing, HSL2 midpoint departure geometry, ocean bulk
sensible heat flux, vertical theta tendency, adiabatic tendency, residual
corrections, output variables, and fixed evaluation protocols.

For the candidate only:

- compute dry potential temperature with the incumbent guarded pressure helper;
- compute `dry_entropy_anomaly = Cp * (log(theta_safe) - layer_mean_log_theta)`
  using area-weighted layer means and a conservative theta floor, such as the
  existing finite positive pressure/temperature guards;
- form `weighted_entropy_anomaly = delta_p * dry_entropy_anomaly`;
- transport the weighted entropy anomaly with the incumbent HSL2 midpoint remap;
- divide by guarded local `delta_p` to recover `ds/dt`;
- convert the entropy tendency to a temperature tendency by
  `dT/dt = T * ds/dt / Cp`, then add incumbent vertical theta transport and
  adiabatic temperature tendency;
- fall back to the accepted mass-DSE tendency if pressure, theta, entropy, or
  remap diagnostics are nonfinite or outside physical bounds.

This does not use humidity, latent heat, pressure-thickness product-rule
corrections, hydrostatic inversion, DSE initialization, vertical DSE transport,
or any ocean heat-flux redistribution.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model entry based on the incumbent.
- API changes:
  - None. Forecast contract, variables, leads, and fixed protocols stay
    unchanged.
- Tests to update:
  - Verify constant theta gives zero horizontal entropy tendency.
  - Verify layer-mean entropy anomaly is zero under quadrature.
  - Verify finite fallback for nonpositive theta, invalid pressure, and
    nonfinite remap diagnostics.
  - Verify candidate factory preserves all incumbent settings except the new
    entropy transport selector.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` and lower-tropospheric temperature-related score if
    multiplicative theta errors are a remaining source of drift.
  - `geopotential_500` may improve through smoother thermodynamic thickness
    evolution without changing pressure tendencies directly.
- Expected neutral metrics:
  - `mean_sea_level_pressure` should remain close if entropy transport does not
    introduce new mass-thickness shocks.
  - `10m_u_component_of_wind` should be mostly neutral except through balanced
    thermal-gradient feedback.
- Possible regressions:
  - Entropy weighting can overemphasize cold upper-level perturbations and may
    lose the hydrostatic coupling that made mass-DSE beneficial.

## Risks

- Numerical stability:
  - Low to moderate. The log transform requires strict positive-theta guards,
    but fallback preserves the accepted incumbent when diagnostics are invalid.
- Compute cost:
  - Low. It adds local logarithms and reuses the incumbent HSL2 remap.
- Data leakage:
  - None. It uses only forecast-state temperature and pressure.
- Physical plausibility:
  - High for dry adiabatic thermodynamics, with the caveat that the model still
    includes weak thermal relaxation and surface flux terms.
- Rollback complexity:
  - Low. Remove one helper/selector, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_entropy`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_entropy --workers 4`.
  - Compare to cached `dino_hsl2_mass_dse` incumbent metrics; do not rerun the
    incumbent.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_entropy --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show dry entropy is not a
    better transported scalar than the incumbent mass-DSE branch. Any early
    pressure or Z500 guardrail failure would show the log-theta tendency is
    disturbing hydrostatic balance.

## Citations

- Hauf, T. and Hoeller, H. 1987. Entropy and potential temperature.
  *Journal of the Atmospheric Sciences*.
  https://doi.org/10.1175/1520-0469(1987)044%3C2887:EAPT%3E2.0.CO;2
- Baumgartner, M., et al. 2020. Reappraising the appropriate calculation of a
  common meteorological quantity: potential temperature.
  *Atmospheric Chemistry and Physics*. https://doi.org/10.5194/acp-20-15585-2020
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: a review. *Monthly Weather Review*.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is not another theta-HSL departure proposal. The departure geometry and
HSL2 remap remain incumbent; the new mechanism is the dry-entropy scalar and
its layer-mass weighting. It is also not staged `static-stability-gated-hsl-
theta`, `mass-flux-theta-transport`, or `full-state-theta-thermodynamic-
tendency`, because it transports `Cp * log(theta)` anomalies rather than theta
or full-state temperature.

Recent DSE follow-ups give useful negative boundaries. This proposal avoids the
rejected pressure-thickness correction, hydrostatic inversion, vertical DSE
transport, DSE initialization, and ocean heat-flux distribution families. It is
a bounded scalar-choice experiment on top of the accepted incumbent, with the
accepted mass-DSE tendency as the finite fallback.

## Evaluator Notes

### 2026-06-24T15:18:56Z

Decision: move to `staging`; rank 2 of 3 new proposals; ready now: no.

This is scientifically plausible enough to preserve. The literature check
supports the thermodynamic premise that dry entropy is closely tied to
potential temperature, and the implementation would stay inside the accepted
mass-weighted HSL branch with finite fallback to `dino_hsl2_mass_dse`. It also
avoids the rejected pressure-thickness product-rule correction, hydrostatic
inversion, vertical DSE transport, DSE initialization, and ocean heat-flux
families.

Keep it staged rather than ready because the expected optimization signal is
less direct than the finite-volume mass-DSE remap. `Cp * log(theta)` is a
nonlinear reparameterization of the theta thermodynamic family, so this is
close to staged `full-state-theta-thermodynamic-tendency` and
`mass-flux-theta-transport`, while it may lose the hydrostatic `Cp*T + Phi`
coupling that made DSE-HSL and mass-DSE-HSL successful. The log transform adds
positive-theta guard and cold-layer sensitivity without clear evidence that
multiplicative theta error is the current dominant residual.

Recommendation: keep as a later scalar-choice experiment if conservation/remap
probes fail cleanly or diagnostics point to multiplicative thermal drift. Do
not promote ahead of the finite-volume mass-DSE remap under the current cached
incumbent baseline.
