---
schema_version: 1
slug: orographic-lift-adiabatic-tendency
title: Orographic Lift Adiabatic Thermal Tendency
status: ready
created_at: 2026-07-02T00:01:13Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth
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

# Orographic Lift Adiabatic Thermal Tendency

## Hypothesis

The current incumbent still rolls out with dynamically flat orography, while
local history shows terrain has unusually large mass-field leverage. The full
terrain experiment produced large aggregate gains but failed early Z500/MSLP
guardrails, and the later barotropic-envelope terrain tendency was stable but
too weak. A different terrain mechanism may recover part of the signal without
another pressure-gradient shock: use smoothed static terrain only to diagnose
terrain-following vertical motion from the forecast low-level wind, then apply a
bounded adiabatic potential-temperature tendency.

This targets forecast dynamics through thermal evolution. Air moving upslope is
cooled and air moving downslope is warmed in a statically stable atmosphere;
that thickness tendency can project onto `geopotential_500`,
`mean_sea_level_pressure`, and downstream wind phasing. It is not an output
height correction, not a terrain pressure-gradient tendency, and not another
Ekman/DFI/WTG cap variant.

## Mechanism

Register one side-by-side candidate such as
`dino_ri2m_ekman_depth_orolift_theta`, preserving every incumbent flag and
diagnostic unless the new selector is enabled.

Add a positive-time-only step filter after the incumbent dynamics and scalar
filters, before the symmetric Coriolis wrapper is reapplied:

- load the fixed WeatherBench2 surface geopotential, convert to height, and
  fall back to exact zero terrain if the constant is unavailable, nonfinite, or
  shape-incompatible;
- keep only a smooth low-mode terrain envelope, for example total wavenumber
  below about `12` with a taper to zero by `20`, avoiding small-scale mountain
  wave forcing and Gibbs structure;
- diagnose low-level wind from the current `vorticity`/`divergence` state and
  compute an orographic vertical-velocity proxy
  `w_terrain = u_low * dh/dx + v_low * dh/dy`;
- taper the proxy to zero near the equator and in weak-flow columns, and apply a
  raised-cosine forecast-time ramp that is zero at initialization and full only
  after roughly 48 hours;
- convert the proxy into a dry-theta tendency
  `dtheta_dt = -w_terrain * dtheta/dz` over the lower and middle troposphere,
  with a smooth sigma envelope such as `0.35 <= sigma <= 0.90`;
- remove the layerwise area mean of the thermal increment so the filter changes
  stationary-wave and regional thickness structure without adding a global heat
  source;
- cap the equivalent per-step temperature increment, e.g. at or below
  `0.05 K`, and finite-fallback to the incumbent next state if terrain, wind,
  stability, or transformed increments are invalid;
- leave `vorticity`, `divergence`, `log_surface_pressure`, humidity tracers,
  Ekman stress, WTG, DFI, MSLP reduction, Z500 output, 2 m temperature output,
  and 10 m wind output directly unchanged.

The central distinction from the rejected terrain pressure-gradient family is
that terrain never enters the primitive-equation geopotential, surface pressure,
or divergence pressure-gradient path. The first candidate tests only the
adiabatic thermal response to forecast flow over smoothed terrain.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` for the dataclass selector,
    terrain-loading helper reuse, low-mode terrain-gradient helper, adiabatic
    thermal step filter, and side-by-side factory.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py` for export.
  - `src/dynamaxx/dycore/registry.py` for one registry key.
  - Focused tests under `tests/dycore/models/dinosaur/` plus
    `tests/dycore/test_registry.py`.
- Registry changes:
  - Add one side-by-side model such as `dino_ri2m_ekman_depth_orolift_theta`.
- API changes:
  - None. The mechanism uses static constants, forecast state, and existing
    output variables.
- Tests to update:
  - Missing, zero, or invalid terrain is an exact no-op.
  - Uniform terrain or zero low-level wind gives zero thermal increment.
  - Synthetic upslope and downslope flow over a simple height gradient gives the
    expected cooling/warming sign.
  - The layerwise area-mean thermal increment is removed.
  - The sigma envelope, forecast-time ramp, and per-step cap are finite and
    deterministic.
  - Only `temperature_variation` changes directly; winds, log surface pressure,
    tracers, and `sim_time` are preserved except for the normal incumbent step.
  - Candidate factory preserves all `dino_ri2m_ekman_depth` settings except the
    new selector and model name.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and late leads if
    missing terrain-following adiabatic thickness tendencies are part of the
    remaining stationary-wave and storm-track error.
  - Secondary `10m_u_component_of_wind` gains are possible through improved
    pressure-gradient phasing, without directly post-processing U10.
  - `2m_temperature` may improve over and downstream of elevated terrain if
    lower-column thermal evolution is currently too flat.
- Expected neutral metrics:
  - Lead-zero outputs, because the ramp is zero at initialization.
  - Direct MSLP/Z500 output operators, because the proposal changes the
    forecast thermodynamic state rather than output reduction formulas.
- Possible regressions:
  - A crude terrain-lift proxy can introduce phase errors or excessive
    mountain-adjacent thermal gradients.
  - The mechanism may be too weak to clear the fixed `+0.002` iteration gate if
    the earlier terrain signal came mostly from mass-coordinate or pressure
    diagnostics rather than thermal lift.

## Risks

- Numerical stability:
  - Moderate. The filter changes the prognostic thermal state every positive
    inner step, but the terrain is low-mode, ramped, area-mean neutral, capped,
    and finite-guarded.
- Compute cost:
  - Low to moderate. It adds static terrain gradients, one wind diagnostic, and
    pointwise thermal algebra per inner step; this fits the reported 4-worker
    iteration envelope.
- Data leakage:
  - None. Static orography and forecast state are available at forecast time;
    no future truth, learned coefficients, validation residuals, or protocol
    changes are used.
- Physical plausibility:
  - Moderate to high. Terrain-forced vertical motion and adiabatic cooling are
    standard mechanisms, but this is a reduced large-scale surrogate, not a full
    terrain-following primitive-equation model.
- Rollback complexity:
  - Low. Remove one selector, helper/filter, factory/export, registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_theta`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_theta --workers 4`.
  - Compare against cached `dino_ri2m_ekman_depth` artifacts under the protocol
    cache rules.
  - Inspect early `geopotential_500` and `mean_sea_level_pressure` guardrails
    explicitly because full terrain failed there.
- Validation gate:
  - Run validation only if iteration promotes under the fixed gate.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show terrain-following
    adiabatic thermal lift is not a material remaining error source.
  - Any early Z500/MSLP guardrail failure would show the thermal terrain proxy
    is still too disruptive despite avoiding pressure-gradient orography.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography/decision.md`
  recorded a large aggregate terrain signal but severe early Z500/MSLP guardrail
  failures.
- Dynamaxx history:
  `.logbook/history/2026-07-01_12-14-39_barotropic-envelope-orography-tendency/decision.md`
  found a reduced low-mode terrain divergence tendency stable but subthreshold.
- Dynamaxx research:
  `.logbook/research/staging/orographic-lapse-screen-temperature.md` is an
  output-only T2m height correction; this proposal instead changes positive-time
  thermal dynamics.
- Wallace, J. M., Tibaldi, S., and Simmons, A. J. 1983. Reduction of systematic
  forecast errors in the ECMWF model through the introduction of an envelope
  orography. *Quarterly Journal of the Royal Meteorological Society*.
  https://doi.org/10.1002/qj.49710946202
- Roe, G. H. 2005. Orographic precipitation. *Annual Review of Earth and
  Planetary Sciences*. https://doi.org/10.1146/annurev.earth.33.092203.122541
- Smith, R. B. and Barstad, I. 2004. A linear theory of orographic
  precipitation. *Journal of the Atmospheric Sciences*.
  https://doi.org/10.1175/1520-0469(2004)061%3C1377:ALTOOP%3E2.0.CO;2
- Durran, D. R. and Klemp, J. B. 1983. A compressible model for the simulation
  of moist mountain waves. *Monthly Weather Review*.
  https://doi.org/10.1175/1520-0493(1983)111%3C2341:ACMFTS%3E2.0.CO;2

## Researcher Notes

This proposal is intentionally narrower than full orography and materially
different from the recently rejected `barotropic-envelope-orography-tendency`.
The rejected reduced terrain candidate altered divergence through a prescribed
barotropic pressure-gradient-like forcing; this one leaves momentum and pressure
directly unchanged and tests a forecast-wind-dependent adiabatic thermal
response. It is also distinct from staged `orographic-wave-drag-split` and
`mountain-blocking-form-drag`, which are momentum sinks, and from staged
`analysis-omega-vertical-motion-spinup` / `theta-omega-spinup`, which use
same-time analyzed vertical velocity rather than terrain-induced vertical motion
from the model's own low-level wind.

Do not follow a failed clean result with ramp/cap/truncation tuning. The fixed
question is whether smoothed terrain-following adiabatic thermal evolution has
enough aggregate WeatherBench2 leverage on top of `dino_ri2m_ekman_depth`.

## Evaluator Notes

### 2026-07-02T00:04:15Z

Decision: move to `ready`; ranked 1 of 1 current ready proposals for
Orchestrator selection.

This is a credible next experiment despite the terrain warning history. The old
`terrain-aware-surface-pressure-orography` run showed unusually large terrain
leverage, with iteration `+0.19845155161644534`, but failed the fixed early
mass-field guardrails badly: day-1-through-day-5 mean RMSE regressed by about
`+36%` for `geopotential_500` and `+32%` for `mean_sea_level_pressure`, with
day-1 `geopotential_500` worse by about `+209%`. The recent
`barotropic-envelope-orography-tendency` result then showed that a reduced
low-mode terrain divergence tendency was numerically clean but effectively
neutral, with iteration delta only `+0.000027916764764990276`.

This proposal is materially different from both failures. It keeps terrain out
of primitive-equation orography, pressure-gradient forcing, surface-pressure
initialization, MSLP reduction, Z500 output, and momentum updates. The tested
mechanism is instead forecast-flow-dependent adiabatic thermal evolution over
smoothed static terrain. That gives a clearer physical path to thickness,
stationary-wave, MSLP, Z500, and possibly T2m changes without reintroducing the
pressure-gradient shock that broke full terrain or repeating the too-weak
barotropic divergence increment.

Implementation is moderate but compatible with the current adapter. Source
inspection confirms the incumbent still builds flat modal `orography`, while the
adapter already has precedent for private WeatherBench2 constant loading,
low-mode spectral masks, rollout-only thermal filters, bounded per-step thermal
increments, layerwise area-mean removal, wind diagnostics from
vorticity/divergence, and side-by-side registry factories. The local terrain
constant should be `geopotential_at_surface` when available, converted to height
by dividing by gravity; if constants are missing, nonfinite, shape-incompatible,
or grid-misaligned, the candidate must be an exact no-op relative to the
incumbent.

Ready constraints for the Implementer:

- Use one fixed candidate only, e.g. `dino_ri2m_ekman_depth_orolift_theta`,
  preserving every `dino_ri2m_ekman_depth` option except the new selector and
  required forecast-time tracking.
- Pin constants before scoring: low-mode terrain full strength through total
  wavenumber `12` with taper to zero by `20`; raised-cosine ramp zero at
  initialization and full at `48` forecast hours; sigma envelope spanning
  `0.35 <= sigma <= 0.90`; per-step equivalent temperature cap no larger than
  `0.05 K`.
- If `sim_time` is required for the ramp, enable it only for this selector and
  prove incumbent-equivalent behavior when the new filter is off.
- Do not tune ramp, cap, terrain truncation, weak-flow threshold, or vertical
  envelope after a clean failed result. A subthreshold or negative iteration
  delta should falsify this specific terrain-lift thermal mechanism.
- Keep fixed evaluation protocols unchanged and inspect early
  `geopotential_500`/`mean_sea_level_pressure` guardrails explicitly because
  those were the decisive failure modes for full terrain.

Ranked recommendation: select this as the next Orchestrator implementation
target if no already-ready higher-priority proposal exists outside this
triage request. It is the strongest terrain candidate currently reviewed
because it is lower risk than ramped pressure-gradient terrain, more directly
thermodynamic than terrain drag ideas, and materially more distinct from the
recent neutral barotropic-envelope test.
