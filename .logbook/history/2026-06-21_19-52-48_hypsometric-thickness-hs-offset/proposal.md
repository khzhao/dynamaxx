---
schema_version: 1
slug: hypsometric-thickness-hs-offset
title: Build the Analysis-HS Equilibrium Offset from Hypsometric Thickness
status: ready
created_at: 2026-06-21T19:46:17Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Build the Analysis-HS Equilibrium Offset from Hypsometric Thickness

## Hypothesis

The accepted incumbent's largest recent gain came from shifting the weak
Held-Suarez equilibrium toward a bounded low-wavenumber analysis temperature
offset. That offset is computed from initialized sigma temperature. The same
initial state also contains pressure-level geopotential, and the accepted
hydrostatic initialization path already showed that geopotential thickness
contains useful balanced thermal information.

A hypsometric-thickness-derived equilibrium offset may improve the weak thermal
target in a different way: condition the relaxation on large-scale analyzed
layer thickness rather than on pointwise temperature residuals. This remains a
trajectory forcing change, not a pressure-level output reconstruction.

## Mechanism

Register a side-by-side candidate suffix such as `_thickness_hs_eq`. Preserve
the incumbent DFI, log-pressure/hydrostatic layer initialization, Strang
Coriolis split, theta tendency/recentering, offcentering, surface residuals, and
fixed evaluation protocols.

For the candidate only:

- during `forecast`, use the single initial `WeatherState` to compute a
  pressure-level hypsometric dry-temperature estimate from analyzed
  geopotential thickness using the same finite guards as the accepted
  hydrostatic layer initialization;
- interpolate that thickness-derived thermal field to sigma levels through the
  existing log-pressure initialization path;
- compute the weak-HS equilibrium offset from the thickness-derived sigma
  temperature minus the standard HS equilibrium at the initialized surface
  pressure;
- apply the same low-wavenumber mask and Kelvin cap used by the accepted
  analysis-HS offset;
- feed that offset into the weak-HS forcing for DFI and positive-time rollout;
- fall back exactly to the accepted temperature-residual analysis-HS offset if
  pressure-level geopotential is missing, shape-incompatible, or nonfinite.

The emitted pressure-level outputs remain on the incumbent interpolation path.
No output pressure reconstruction, metric change, split change, or lead-time
change is involved.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused adapter tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate that differs only in the analysis-HS offset
    source.
- API changes:
  - None. The helper uses channels already present in the forecast initial
    state when available and has an incumbent fallback.
- Tests to update:
  - Verify missing geopotential falls back to the accepted offset.
  - Verify the low-mode mask and Kelvin cap match the incumbent analysis-HS
    offset path.
  - Verify output variables and pressure-level interpolation are unchanged.
  - Add registry and finite smoke coverage.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` if large-scale thickness balance is a better weak-HS
    target than raw initialized sigma temperature.
  - `mean_sea_level_pressure` if improved thickness relaxation reduces mass
    adjustment around days 3-10.
  - `2m_temperature` may improve after the surface residual decays if lower-
    tropospheric thickness anchors thermal drift.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral except through balanced
    mass/height feedback.
- Possible regressions:
  - The accepted temperature-residual offset may already be the best target;
    replacing it with thickness information can underfit lower-level thermal
    anomalies.
  - Any mismatch between analyzed pressure-level geopotential and flat-sigma
    rollout can worsen MSLP/Z500.

## Risks

- Numerical stability:
  - Low to moderate. The same low-mode mask and cap as the accepted offset
    should bound the forcing, but the offset source changes.
- Compute cost:
  - Low. The added work occurs once per initial condition.
- Data leakage:
  - Low. It uses only same-time initial analysis channels, not future targets or
    validation statistics.
- Physical plausibility:
  - Moderate to high. Hypsometric thickness is the hydrostatic link between
    temperature and geopotential, and the accepted initialization already uses
    that relationship.
- Rollback complexity:
  - Low. Remove one offset-source helper and the side-by-side factory/registry
    entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and no diagnostic issue increase.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and fixed guardrail compliance.
- Validation gate:
  - Run validation with `--workers 4` only after iteration promotion and require
    validation delta at least `+0.001`.
- Outcome that would falsify the hypothesis:
  - A negative or subthreshold iteration delta would show the accepted
    temperature-residual analysis-HS offset is already better than the
    thickness-derived target. A Z500 or MSLP guardrail failure would show the
    thickness source is incompatible with the flat-sigma rollout.

## Citations

- Repository code: `src/dynamaxx/dycore/models/dinosaur/adapter.py:421`
  implements the accepted bounded low-mode analysis-HS equilibrium offset from
  initialized sigma temperature.
- Repository code: `src/dynamaxx/dycore/models/dinosaur/adapter.py:891`
  performs pressure-level to sigma initialization and optionally replaces
  analyzed temperature with a hydrostatic thickness-derived temperature.
- Repository history:
  `.logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium/decision.md:24`
  accepted the analysis-HS offset with large iteration and validation gains.
- Repository history:
  `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted layer-mean hydrostatic temperature initialization, supporting
  pressure-level geopotential thickness as useful initialization information.
- Repository history:
  `.logbook/history/2026-06-21_18-05-20_theta-hydrostatic-pressure-output-reconstruction/decision.md:32`
  exhausted pressure-level output reconstruction variants; this proposal avoids
  output reconstruction and changes only the weak-HS forcing target.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society.

## Researcher Notes

This is materially different from the rejected theta-hydrostatic pressure-output
reconstruction because it does not alter emitted pressure-level temperature,
geopotential, or interpolation. It is also different from accepted
`analysis-offset-held-suarez-equilibrium`: the forcing target is derived from
large-scale hydrostatic thickness rather than pointwise initialized temperature
residuals. It is not another fixed-pressure, barotropic, rate-mask, or lead-
decayed analysis-HS variant; the new mechanism is the physical source of the
equilibrium offset.

## Evaluator Notes

### 2026-06-21T19:51:53Z

Decision: move to `ready`; ranked first of the current proposals.

This is the strongest immediate candidate because it is low-surface-area,
forecast-contract preserving, and uses information already handled by the
accepted hydrostatic layer initialization path. The recent pressure-level
output reconstruction rejection exhausts output reconstruction variants, but
this proposal does not alter emitted pressure-level variables; it changes only
the bounded weak-HS equilibrium target used during the trajectory. The existing
adapter already contains both the accepted low-mode analysis-HS offset path and
geopotential-thickness temperature initialization helpers, so feasibility is
high and the fallback to the incumbent offset can be tested cleanly.

The main caution is that several nearby analysis-HS variants have already
failed or landed subthreshold: DFI-balanced source ordering was effectively
neutral, fixed-pressure coupling regressed, lead decay was subthreshold, and
mask smoothing was subthreshold. This proposal is ready despite that negative
neighborhood because the physical source is materially different from those
knobs: it asks whether large-scale hydrostatic thickness is a better thermal
equilibrium target than initialized sigma temperature residuals. The
implementation should preserve the incumbent cap and low-mode mask exactly, use
no validation-tuned constants, and fall back bytewise or tolerance-equivalently
to the incumbent offset whenever pressure-level geopotential is missing or
nonfinite.
