---
schema_version: 1
slug: seasonal-stability-surface-residual-decay
title: Gate Surface Residual Memory by Seasonal Static Stability
status: ready
created_at: 2026-06-20T02:44:49Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
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

# Gate Surface Residual Memory by Seasonal Static Stability

## Hypothesis

The current incumbent's largest accepted gain came from scale-separated
near-surface residual memory, especially for `2m_temperature`. The fixed
iteration artifact still has strongly negative `2m_temperature` skill at nearly
all leads, which means the lowest-sigma screen-temperature proxy still loses
useful near-surface information after the accepted residual decays.

The accepted residual memory is stationary in space and separated by horizontal
scale, but its low-mode decay does not know whether the initial screen-level
error is in a regime where surface-layer decoupling is likely to persist. Stable
winter or nocturnal-like lower columns should retain the broad low-mode
temperature residual longer, while well-mixed or weakly stable regimes should
decay toward the raw dycore output sooner. A fixed seasonal/static-stability
gate can exploit this without advecting residuals, changing phase, or altering
the forecast trajectory.

## Mechanism

Register a side-by-side candidate extending the incumbent with a suffix such as
`seasonal_stability_surface_residual`. Preserve the incumbent rollout, DFI,
weak Held-Suarez forcing, log-pressure and hydrostatic initialization, exact
Coriolis Strang split, theta tendency, theta mean recentering, off-centered
SIL3, Richardson 10 m wind diagnostic, scale-separated residual split, output
variables, lead schedule, and fixed protocols.

For the candidate only:

- keep the accepted spectral split of initial `2m_temperature` and
  `10m_u_component_of_wind` residuals unchanged;
- compute a deterministic stability gate from the forecast initialization time,
  latitude, and the existing lower-column potential-temperature stability proxy;
- for the low-mode `2m_temperature` residual only, lengthen the accepted
  low-mode decay in high-latitude winter hemispheres and locally stable lower
  columns, for example up to a fixed 144 hour cap;
- shorten that same low-mode decay in weakly stable, tropical, or summer
  high-latitude regimes, for example down toward 72 hours;
- leave high-mode `2m_temperature`, all `10m_u_component_of_wind` residuals,
  lead-zero exactness, non-corrected variables, and pressure-level diagnostics
  on the incumbent path;
- use only forecast initialization metadata and same-forecast state fields, with
  finite fallback to the incumbent scale-separated residual correction.

This is a decay-gating change, not a diurnal phase model, residual advection,
mass residual, or screen-temperature surface-layer extrapolation.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model extending the incumbent with the seasonal
    stability residual selector.
- API changes:
  - None. `DycoreModel.forecast`, inputs, outputs, target variables, lead times,
    and metrics stay fixed.
- Tests to update:
  - Verify winter/summer hemisphere gates are deterministic from
    `initial_times`, latitude, and fixed constants.
  - Verify the gate modifies only the low-mode `2m_temperature` residual decay.
  - Verify low plus high residual reconstruction, lead-zero exactness, and
    finite fallback still match the incumbent guarantees.
  - Verify non-corrected variables and `10m_u_component_of_wind` are unchanged
    relative to the incumbent residual helper.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 3 to 15, especially stable-season extratropical
    cases where broad screen-temperature bias memory should persist.
  - Primary score if the accepted low-mode residual is still under-retained in
    stable regimes.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500` should be unchanged because
    this is output-only and limited to a near-surface channel.
  - `10m_u_component_of_wind` should remain on the accepted residual path.
- Possible regressions:
  - Persisting winter high-latitude residuals too long can overfit initial
    surface anomalies and degrade synoptic air-mass changes.
  - If remaining `2m_temperature` error is not regime-dependent, this may be
    clean but subthreshold.

## Risks

- Numerical stability:
  - Very low. The candidate changes only saved output residual memory.
- Compute cost:
  - Low. It adds local latitude/time/stability algebra and no extra rollout.
- Data leakage:
  - Low. It uses only initialization time, grid latitude, initial analysis, and
    same-forecast diagnostics. No target truth, validation statistics, or tuned
    climatology are used.
- Physical plausibility:
  - Moderate. Stable boundary layers and screen-level diagnostics are
    regime-dependent, but this is a coarse fixed proxy without land, snow, or
    radiative fluxes.
- Rollback complexity:
  - Low. Remove one helper option, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that seasonal
    stability gating is not a material remaining `2m_temperature` error source.
    Any early `2m_temperature` guardrail failure would show the longer stable
    residual memory is too persistent.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-19_21-12-19_scale-separated-surface-residual-memory/decision.md`
  accepted scale-separated near-surface residual memory with iteration delta
  `+0.03993409285933447` and validation delta `+0.04067763036264238`.
- Dynamaxx history:
  `.logbook/history/2026-06-20_01-15-56_lagrangian-surface-residual-memory/decision.md`
  rejected advecting the residual with severe `2m_temperature` guardrail
  failures, so this proposal keeps the residual geographically stationary.
- ECMWF, "Improved two-metre temperature forecasts in the 2024 upgrade",
  describes 2 m temperature as a diagnostic derived with surface-layer
  stability information. https://www.ecmwf.int/en/newsletter/178/earth-system-science/improved-two-metre-temperature-forecasts-2024-upgrade
- Louis, J.-F. 1979. A parametric model of vertical eddy fluxes in the
  atmosphere. Boundary-Layer Meteorology.
  https://doi.org/10.1007/BF00117978
- ECMWF IFS Documentation, Part IV: Physical Processes, documents surface-layer
  and diagnostic near-surface quantities.
  https://www.ecmwf.int/sites/default/files/2023-06/Part-IV-Physical-Processes.pdf

## Researcher Notes

This is not a duplicate of staged `diurnal-surface-residual-memory`, which
changes temporal phase of the temperature residual. This proposal changes only
the low-mode decay lifetime using fixed seasonal and stability gates. It is also
not a retry of `lagrangian-surface-residual-memory`, because it does not move
the accepted residual in space. It avoids the recent low-mode mass residual
failure by leaving MSLP, Z500, and prognostic mass variables untouched.

## Evaluator Notes

### 2026-06-20T02:48:14Z

Decision: move to `ready`; ranked 1 of 3 fresh proposals and recommended as
the next Orchestrator selection.

This is the strongest fresh idea because it stays in the same output-only
near-surface residual family that has produced the two largest recent accepted
gains: stability-aware residual decay and scale-separated surface residual
memory. The current incumbent already applies a local stability-aware decay and
then a low/high spectral residual split, so this is not a first stability gate.
Its distinct test is narrower: add a deterministic initialization-time,
latitude, and seasonal/static-stability modulation to the low-mode
`2m_temperature` decay only, while leaving high-mode T2m, 10 m wind residuals,
MSLP, Z500, pressure-level outputs, DFI, weak-HS forcing, off-centering, and
the prognostic trajectory unchanged.

Recent history supports this priority. Scale-separated residual memory passed
iteration and validation with deltas of `+0.03993409285933447` and
`+0.04067763036264238`, dominated by 2 m temperature, while Lagrangian residual
advection was strongly rejected with a `2m_temperature` guardrail failure. This
proposal keeps the residual geographically stationary and does not introduce
mass-output memory, avoiding the rejected residual subfamilies. It is stronger
than staged `diurnal-surface-residual-memory` for immediate selection because
it uses a regime gate rather than mostly exploiting the fixed daily lead phase,
and it is more isolated than the fresh weak-HS or PV-filter ideas because it
cannot perturb the dycore trajectory.

Implementation constraints for promotion: constants must be fixed before
scoring; lead-zero exactness must remain exact; only the low-mode
`2m_temperature` residual decay may differ from the incumbent; all non-corrected
channels and 10 m wind must be incumbent-equivalent; finite fallback must return
the current scale-separated residual path.
