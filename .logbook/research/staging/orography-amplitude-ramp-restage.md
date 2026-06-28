---
schema_version: 1
slug: orography-amplitude-ramp-restage
title: Ramped Large-Scale Orography to Beat the Day-1 Shock (Revised Restage)
status: staging
created_at: 2026-06-25T03:49:03Z
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

# Ramped Large-Scale Orography to Beat the Day-1 Shock (Revised Restage)

## Hypothesis

This is a revised restage of `terrain-aware-surface-pressure-orography` (history
2026-06-16), which gave a large reproducible aggregate gain (iteration
**+0.1985**, validation **+0.1822**) but was rejected for failing the early-lead
RMSE guardrail. The path-dependency signal is real: the model still runs with
`orography = 0`, so it lacks the first-order orographic forcing of stationary
waves / blocking that shapes `mean_sea_level_pressure` and `geopotential_500`.

**What the prior restage got wrong** (caught by the Evaluator, and corrected
here): the original rejected run **already had DFI enabled and already passed
filtered modal terrain** into the primitive-equation path, so "balance through
DFI" is NOT a new mitigation -- and DFI plus filtered terrain did not prevent a
**catastrophic day-1 shock**: early-lead RMSE worsened by +36% (`geopotential_500`)
and +32% (`mean_sea_level_pressure`), with **day-1 `geopotential_500` worsening by
+209%**. That is an impulsive lead-0 adjustment, not a marginal guardrail miss, so
the modern damping (off-centering, DSE-HSL transport, matured init) is necessary
but on its own unlikely to be sufficient.

The genuinely new mechanism here is an explicit attack on that impulse: introduce
orography through a **time amplitude ramp** (terrain grows from zero to full over
the first day or two of each forecast) using a **large-scale-only (very low
truncation) terrain field**. A quasi-statically growing, smooth lower boundary
adjusts the flow gradually rather than shocking a terrain-free initial state, so
the day-1 spike that caused the rejection is structurally removed while the
slow-accruing medium/long-lead stationary-wave benefit is largely retained.

## Mechanism

Register a side-by-side candidate named `dino_hsl2_mass_dse_orogramp`. Preserve
every incumbent setting.

- Load static `geopotential_at_surface` via `read_constants`, convert to height,
  and build **large-scale-only modal orography**: truncate to a low total
  wavenumber so only continental/planetary-scale terrain (the part that forces
  stationary waves) is retained and small-scale gravity-wave generation is
  minimized. The truncation is a fixed bounded parameter.
- Apply a **time amplitude ramp** `r(t)` to the modal orography wherever it enters
  the trajectory construction (`adapter.py`) and `get_geopotential_on_sigma`:
  `orography_effective(t) = r(t) * orography_largescale`, with `r(0) = 0` rising
  smoothly (e.g. raised-cosine) to `r = 1` over a fixed ramp window of order
  24-48 forecast hours, then held at 1. The lower boundary therefore evolves
  quasi-statically over the first day or two instead of appearing impulsively at
  lead 0.
- Do NOT change the MSLP reduction diagnostic (kept on the incumbent path to
  isolate the dynamics-orography effect, as in the prior restage).
- Off-centered semi-implicit damping, DSE mass-weighted HSL transport, surface
  flux, DFI, and all diagnostics stay on the incumbent path; finite-fallback to
  flat orography if terrain loading or the ramped field is nonfinite.

The ramp window and truncation are the two knobs that trade day-1 safety against
how quickly the orographic benefit accrues; both are fixed, bounded, and chosen
conservatively (slow ramp, low truncation) to prioritize clearing the early-lead
guardrail.

## Implementation Scope

- Expected files: `adapter.py` (large-scale modal terrain + time-ramped amplitude
  threaded into the trajectory/geopotential path), `__init__.py`, `registry.py`,
  tests.
- Registry changes: add only the side-by-side candidate.
- API changes: none.
- Tests to update: `r(0)=0` reproduces the incumbent flat-orography lead-0 state
  exactly; `r` rises monotonically to 1 over the window and holds; the modal
  terrain is low-truncation, finite, and bounded; flat-fallback reproduces the
  incumbent; an early-lead smoke check that day-1 area-weighted Z500/MSLP RMSE on
  the fast set does not exceed the incumbent by more than the guardrail threshold;
  registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements: `mean_sea_level_pressure` and `geopotential_500` at
  medium-to-long lead from large-scale orographic stationary-wave forcing, with a
  positive aggregate primary delta.
- Expected neutral metrics: `2m_temperature`; `10m_u_component_of_wind` may shift
  modestly via orographic pressure gradients.
- Possible regressions: the early-lead RMSE guardrail remains the central risk. If
  even a slow-ramped, large-scale-only terrain perturbs days 1-5 beyond the
  guardrail, the candidate fails again -- but with the day-1 impulse removed, the
  failure (if any) should be far smaller than the prior +209% day-1 spike, which
  is itself the informative result.

## Risks

- Numerical stability: moderate; a slowly growing, smooth, large-scale lower
  boundary is much gentler than impulsive full terrain, and the incumbent
  off-centering damps residual fast modes; finite-fallback guards failures.
- Compute cost: low (one cached static field, a low-truncation modal terrain, and
  a scalar time ramp).
- Data leakage: none (static terrain + a fixed time schedule).
- Physical plausibility: high; large-scale orographic forcing is first-order
  missing physics, and gradual spin-up of a boundary forcing is a standard way to
  avoid initialization shock.
- Rollback complexity: low.

## Evaluation Plan

- Fast gate: `uv run pytest`; `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_orogramp`;
  finite forecasts, zero diagnostic issues.
- Iteration gate: `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_orogramp --workers 4`;
  support is primary delta >= +0.002, clean diagnostics, and -- the decisive
  criterion -- the early day-1-to-5 mean-RMSE and per-variable-lead guardrails must
  now PASS (they failed catastrophically at +209% day-1 Z500 in 2026-06-16).
- Validation gate: `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_orogramp --workers 4`
  only after iteration promotion; require validation delta >= +0.001 with the same
  guardrails.
- Falsification: if the early-lead guardrail still fails despite removing the
  day-1 impulse (ramp) and the small scales (low truncation), then orographic
  forcing is intrinsically too disruptive for the early window at this
  resolution/step, the rejection was NOT recoverable by path dependency, and the
  idea should return to scrap.

## Citations

- Citation or source:
  - Dynamaxx history: `.logbook/history/2026-06-16_13-17-17_terrain-aware-surface-pressure-orography`
    -- iteration delta +0.1985, validation +0.1822, rejected on the early-lead RMSE
    guardrail; its Evaluator/score record documents day-1 Z500 worsening +209% and
    early-lead Z500/MSLP worsening +36% / +32%, and that DFI + filtered terrain were
    already present.
  - Dynamaxx source: `adapter.py` builds the trajectory with `orography = 0`.
  - Wallace, J. M., Tibaldi, S. & Simmons, A. J. 1983. Reduction of systematic
    forecast errors in the ECMWF model through the introduction of an envelope
    orography. QJRMS 109(462), 683-717. https://doi.org/10.1002/qj.49710946202
  - Lynch, P. & Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
    digital filter. Mon. Wea. Rev. 120(6), 1019-1034 (gradual suppression of
    spurious initialization transients).
    https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-25 as a REVISED
restage of `terrain-orography-restage-damped-core` (which the Evaluator held in
staging). Corrections versus that prior version, in the spirit of RESEARCHER.md's
negative-evidence rule: (1) the prior proposal wrongly claimed DFI as a new
mitigation -- the original rejected run already had DFI enabled and already passed
filtered terrain, so DFI is removed from the novelty argument; (2) the original
failure was catastrophic (day-1 Z500 +209%), not marginal, so this version adds a
genuinely new mechanism aimed squarely at that impulse -- a time amplitude ramp of
a large-scale-only terrain field -- rather than relying on the modern core's damping
alone. Honest success probability is **low** (the day-1 shock was severe), but the
ramp + low-truncation directly target the documented failure mode and the
falsification outcome cleanly settles whether orographic forcing is recoverable here.
The original +0.18 gain was measured against a -1.32 incumbent; the absolute delta
against today's -0.26 incumbent is unknown and plausibly smaller.

## Evaluator Notes

### 2026-06-25T05:37:58Z

Decision: move to `staging`; not ready against the current incumbent
`dino_hsl2_mass_dse_wtg`.

The useful part of this proposal is real and distinct from the rejected
`terrain-aware-surface-pressure-orography` run: a smooth amplitude ramp and a
very low-order terrain field directly target the documented day-1 impulse rather
than relying again on DFI or generic damping. The scientific premise is credible
but also cautionary. The cited envelope-orography literature supports possible
medium/long-lead large-scale flow improvements while also reporting short-range
degradation from orography changes, which is consistent with the local
guardrail failure pattern. DFI literature supports filtering initialization
oscillations, but the rejected local terrain run already used DFI and still
failed the fixed early Z500/MSLP RMSE guards.

Do not move this to `ready` in its current form. The proposal has three protocol
hazards:

- It is not yet a single bounded implementation. The ramp window is still
  "24-48 forecast hours" and the terrain truncation is "low total wavenumber";
  both must be fixed before scoring so the Implementer is not doing a
  coefficient sweep.
- The implementation scope is understated. The current adapter constructs a
  static zero modal `orography`, and the primitive-equation object stores
  orography as a static equation field used by `orography_tendency`. A true
  time-amplitude ramp in the prognostic pressure-gradient path likely needs an
  explicit primitive-equation or step-wrapper change, not only adapter,
  registry, and export edits.
- The proposed "fast-set day-1 RMSE smoke check" should not become a unit test
  or a new implementation-side gate. Keep tests focused on deterministic
  behavior, finite fallbacks, no-op behavior at `r=0`, and registry coverage;
  keep fixed WeatherBench2 guardrails in the Scorer/Orchestrator evaluation
  path.

Retargeting note: the YAML target was updated to the current incumbent
`dino_hsl2_mass_dse_wtg`. A future ready version should also update the body to
name a WTG-preserving side-by-side candidate such as
`dino_hsl2_mass_dse_wtg_orogramp`, preserve the WTG relaxation unchanged, pin a
single ramp formula and duration, pin the spectral truncation/taper, list any
needed `primitive_equations.py` edits explicitly, and keep the MSLP diagnostic
unchanged.

Staged priority: low to moderate. Reconsider only after lower-surface-area
current-incumbent ideas are exhausted or after a Researcher writes the bounded
WTG-targeted version above. Momentum-only or output-only terrain ideas remain
less exposed to the severe prior pressure-gradient/orography guardrail failure.
