---
schema_version: 1
slug: pressure-thickness-ri2m-temperature
title: "Pressure-thickness weighted lower-column state for RI2m temperature"
status: ready
created_at: 2026-07-08T02:10:00Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth_orolift_lwind_twork_drag
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

## Hypothesis

The incumbent 2 m temperature diagnostic is still sensitive to single-level lower-column noise because `_bulk_richardson_2m_temperature` uses the lowest and next-lowest sigma levels as its thermal and wind reference pair. Replacing those point samples with a shallow pressure-thickness-weighted lower-column state should make the Richardson correction respond to the resolved boundary-layer mean rather than to one sigma interface, improving the 2m_temperature component without changing the forecast trajectory or adding a second integration.

This is deliberately different from the rejected monotone RI2m bracket and dry Richardson wind-exchange work: it does not tune the limiter, add a wind exchange tendency, or alter prognostic winds. It changes only the diagnostic inputs that feed the existing capped RI2m temperature formula.

## Mechanism

Within `_bulk_richardson_2m_temperature`, compute lower and upper reference states from pressure-thickness weights over the bottom part of the column instead of taking two individual sigma levels. A conservative implementation would:

- derive positive layer weights from the local pressure thickness represented by adjacent sigma interfaces and surface pressure;
- form a lower reference temperature and horizontal wind from the bottom shallow layer, for example the lowest 50-75 hPa equivalent or the lowest sigma mass interval;
- form an upper reference from the next shallow pressure-thickness band above it;
- pass those mass-weighted reference temperatures, winds, and heights through the existing Richardson stability algebra, departure cap, and residual-memory correction unchanged.

This keeps the diagnostic local, deterministic, and cheap. The expected physical effect is to reduce spurious stable/unstable flips caused by a single noisy near-surface level while preserving the Monin-Obukhov style link between low-level shear, stratification, and 2 m temperature.

## Implementation Scope

The implementation should stay inside the dinosaur adapter near `_bulk_richardson_2m_temperature` and any small helper needed for pressure-thickness weights. The incumbent registry entry should receive a new model factory only if the loop requires a distinct candidate key; otherwise the change can be isolated behind a new adapter flag.

No source-data changes, evaluation-protocol changes, ensembles, output post-processing outside the model, or lead-time filtering are needed. The existing near-surface residual correction should remain downstream so the proposal tests only whether the diagnostic state entering RI2m is better conditioned.

## Expected Metric Movement

Primary expected gain is a modest 2m_temperature improvement across days 1-15 from reduced lower-column representativeness error. Mean sea level pressure, Z500, and 10 m wind should be nearly neutral because this is diagnostic-only for T2m and does not change the trajectory. A plausible iteration delta is +0.001 to +0.003 if the single-level RI2m diagnostic is a material remaining error source; anything below +0.001 would indicate the incumbent residual memory already absorbs the noise.

The fast protocol should first check finite outputs and early-lead T2m guardrails. Iteration should be run only if fast shows no early warm/cold shock or large 10 m wind side effect.

## Risks

The main risk is that pressure-thickness averaging blunts a real inversion signal and slightly worsens nighttime or polar T2m. There is also a risk of duplicating the effect of the incumbent residual-memory correction, producing only a subthreshold delta like the monotone RI2m bracket. To reduce that risk, the averaging depth should be shallow and fixed by pressure thickness rather than a broad column mean.

Another risk is shape complexity around sigma-coordinate endpoints. The helper should be written with explicit clipping, normalized weights, and finite fallbacks to the existing two-level values when a column lacks enough valid thickness.

## Evaluation Plan

Use the fixed loop protocols unchanged:

- Fast: verify finite forecasts, no target-shape changes, and no early T2m guardrail failure.
- Iteration: compare against incumbent primary score and inspect per-target RMSE, with special attention to 2m_temperature by lead day and neutral movement in MSLP/Z500/U10.
- Validation: run only if iteration clears the +0.002 gate or shows a convincing, stable T2m improvement without collateral degradation.

Diagnostic checks should include the distribution of RI2m departures before and after the change, especially the fraction clipped by `_SURFACE_LAYER_TEMPERATURE_MAX_DEPARTURE_KELVIN`.

## Citations

- Monin, A. S. and Obukhov, A. M. (1954). Basic laws of turbulent mixing in the surface layer of the atmosphere. Trudy Geofizicheskogo Instituta AN SSSR.
- Beljaars, A. C. M. and Holtslag, A. A. M. (1991). Flux parameterization over land surfaces for atmospheric models. Journal of Applied Meteorology. https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2
- Stull, R. B. (1988). An Introduction to Boundary Layer Meteorology. https://doi.org/10.1007/978-94-009-3027-8
- Local evidence: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements the incumbent `_bulk_richardson_2m_temperature` from the lowest two sigma levels, while `.logbook/history/2026-07-05_12-24-37_monotone-bracketed-ri2m-temperature` and `.logbook/history/2026-07-06_10-20-30_dry-richardson-lower-column-wind-exchange` show limiter and wind-exchange variants were subthreshold.

## Evaluator Notes

### 2026-07-08T02:21:03Z

Decision: move to `ready`; rank 1 of 2 current proposals.

This is the stronger candidate for the next cycle because it is local to the
existing RI2m 2 m temperature diagnostic, forecast-contract preserving, cheap,
and cleanly rollbackable. Source inspection confirms the incumbent
`_bulk_richardson_2m_temperature` in `adapter.py` currently uses only the
lowest and next-lowest sigma centers for temperature, wind, pressure, and
height, while `SigmaCoordinates` exposes layer `boundaries` and
`layer_thickness`, so a shallow pressure-thickness weighted lower/upper
reference state is implementable without changing evaluation protocols or the
prognostic trajectory.

The literature check supports the general surface-layer premise rather than
the exact proposed averaging rule: Monin-Obukhov/Bulk-Richardson style
surface-layer diagnostics connect near-surface shear and stratification, and
Beljaars-Holtslag is a reputable surface-flux parameterization reference. The
proposal should therefore be implemented as a bounded diagnostic-input
conditioning test, not as a retuned limiter or new boundary-layer physics.

The main reservation is expected score size. Recent local evidence is
unfavorable for narrow RI2m followups: `monotone-bracketed-ri2m-temperature`
was clean but only `+0.0003237450779904061`, and
`dry-richardson-lower-column-wind-exchange` was clean but only
`+0.0007767197993275021`, both below the `+0.002` iteration gate. Keep this as
the single `ready` proposal only because it changes the representativeness of
the diagnostic state entering RI2m rather than repeating the rejected limiter,
humidity, or wind-exchange mechanisms. If implemented, the averaging depth
must be fixed before scoring, shallow, finite-fallback guarded, and limited to
the RI2m diagnostic path.
