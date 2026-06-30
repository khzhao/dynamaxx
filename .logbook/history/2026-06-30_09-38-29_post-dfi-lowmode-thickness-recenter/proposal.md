---
schema_version: 1
slug: post-dfi-lowmode-thickness-recenter
title: Post-DFI Low-Mode Thickness Recenter
status: ready
created_at: 2026-06-30T09:33:49Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
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

# Post-DFI Low-Mode Thickness Recenter

## Hypothesis

The accepted `dino_ri2m_ekman_coupled` incumbent retains the initialization
chain that has historically mattered most: log-pressure interpolation,
hydrostatic layer-mean temperature initialization, DFI, exact Coriolis
splitting, theta-form thermodynamics, and bounded surface diagnostics. The
latest failed ideas show that simple Ekman timing, mass-neutral pumping,
roughness redistribution, and pressure-work heating are not the next obvious
source of gain.

A narrower remaining hypothesis is that DFI can slightly disturb the broad
hydrostatic thickness relationship that the accepted layer-mean initialization
created. A one-time, post-DFI, low-horizontal-mode thermal recenter that restores
only a sign-consistent free-tropospheric thickness residual should reduce early
Z500/MSLP spinup while leaving the accepted positive-time Ekman, WTG,
vertical-DSE, T2m, and 10 m wind mechanisms unchanged.

## Mechanism

Register one side-by-side candidate, for example
`dino_ri2m_postdfi_thick`, derived from `ekman_coupled_dinosaur_dycore_model()`.

For the candidate only:

- build the initial Dinosaur state exactly as the incumbent does, including
  hydrostatic layer-mean temperature initialization;
- run the existing DFI initializer unchanged;
- after DFI returns the initialized state and before positive-time rollout,
  diagnose pressure-level geopotential from the DFI state using the same
  hydrostatic sigma-geopotential and sigma-to-pressure helpers used for output;
- compare DFI-diagnosed low-mode `geopotential_500` and a neighboring
  thickness proxy such as `geopotential_300 - geopotential_700` against the
  analyzed initial pressure-level geopotential fields when those channels are
  present;
- retain only residuals that are horizontally low-mode, sign-consistent between
  Z500 and the 300-700 hPa thickness proxy, and smaller than a fixed physical
  cap;
- convert that common low-mode thickness residual into a vertically smooth,
  area-mean-free temperature increment over the middle sigma layers by the dry
  hypsometric relation;
- cap the equivalent temperature increment tightly, for example no more than
  `0.5 K` per layer, and reject increments that would reduce dry static
  stability below a small positive floor;
- leave vorticity, divergence, `log_surface_pressure`, tracers, `sim_time`,
  DFI equations, positive-time step filters, output residuals, and all fixed
  target variables unchanged;
- fall back exactly to the incumbent post-DFI state if any required analysis
  geopotential channel is absent, pressure bracketing is invalid, diagnostics
  are nonfinite, the residuals are sign-inconsistent, or the corrected state is
  nonfinite.

This is not a DFI low-mode merge: it does not restore raw vorticity,
divergence, pressure, or temperature leaves. It is not a thermal IAU spinup:
there is no positive-time analysis forcing. It is a single initialization-time
hydrostatic thickness recenter with strict no-op conditions.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model key such as `dino_ri2m_postdfi_thick`.
- API changes:
  - None. Forecast inputs, requested outputs, target variables, lead schedule,
    metrics, and fixed protocols remain unchanged.
- Tests to update:
  - Verify exact incumbent behavior when required geopotential channels are
    missing.
  - Verify sign-inconsistent Z500 and layer-thickness residuals no-op.
  - Verify synthetic sign-consistent low-mode thickness residuals produce a
    bounded middle-layer temperature increment and preserve layer area means.
  - Verify static-stability and nonfinite guards fall back to the incumbent
    post-DFI state.
  - Verify candidate factory parity with `dino_ri2m_ekman_coupled` except for
    the new selector and name.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 1-7 if residual
    post-DFI low-mode thickness imbalance remains.
  - Small secondary `10m_u_component_of_wind` gains are possible through cleaner
    balanced pressure evolution, but the mechanism does not target U10.
- Expected neutral metrics:
  - `2m_temperature` should stay close to the incumbent because near-surface
    residual memory, RI2m output, and positive-time surface coupling are
    unchanged.
- Possible regressions:
  - If DFI's thickness adjustment is dynamically useful, undoing even a small
    low-mode component can degrade Z500 or MSLP phase.
  - Analysis geopotential residuals may contain representativeness error rather
    than model imbalance; sign and static-stability guards are essential.

## Risks

- Numerical stability:
  - Low to moderate. The correction changes only initialized temperature, but
    thermal changes feed pressure-gradient balance. Strict finite, cap, sign,
    and static-stability fallbacks are required.
- Compute cost:
  - Low. It adds one initialization diagnostic and spectral mask, not a per-step
    filter.
- Data leakage:
  - Low. It uses only same-time initial analysis channels and the model's own
    DFI lead-zero diagnostic. It must not use future truth, validation errors,
    or leaderboard statistics.
- Physical plausibility:
  - Moderate to high. Hydrostatic thickness-temperature coupling is standard,
    and the proposal explicitly preserves pressure and wind leaves.
- Rollback complexity:
  - Low. Remove one initialization helper/selector, one factory/export, one
    registry key, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_postdfi_thick`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_postdfi_thick --workers 4`.
  - Compare against the cached `dino_ri2m_ekman_coupled` incumbent artifacts
    when valid. Support requires primary delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_postdfi_thick --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` with clean diagnostics and
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show post-DFI low-mode
    thickness recentering is not a material remaining error source. Any early
    Z500, MSLP, or U10 guardrail failure would show the adjustment disrupts
    useful balance.

## Citations

- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
  digital filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
  assimilation using incremental analysis updates. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Holton, J. R. and Hakim, G. J. 2013. An Introduction to Dynamic Meteorology,
  fifth edition. Academic Press.
- Local positive evidence:
  `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted layer-mean hydrostatic initialization with iteration delta
  `+0.004688970185515728` and validation delta `+0.005305927605172567`.
- Local negative evidence:
  `.logbook/research/scrap/low-mode-preserving-dfi-initialization.md` warns
  against raw low-mode DFI state merging; this proposal does not merge raw
  vorticity, divergence, temperature, or pressure leaves.

## Researcher Notes

The recent accepted incumbent is
`.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping`, with cached
iteration primary `-0.16500618979404214` and validation primary
`-0.16591150807771451`. The latest rejected Ekman family members were
subthreshold or worse: wind veering regressed slightly, pressure-work thermal
coupling was only `+0.000917146345733949`, exact mass-neutral pumping was
slightly negative, and spinup ramp regressed by `-0.0016871028938771349`.

This proposal is intentionally orthogonal to those results. It does not change
Ekman coefficient, depth, timing, pumping projection, pressure-work heating, or
surface diagnostics. It also avoids the broad staged
`state-increment-trust-region-filter` and the staged
`hydrostatic-pressure-increment-consistency-filter`: the only corrected leaf is
temperature, the correction occurs once after DFI, and the gate is an initial
free-tropospheric hydrostatic thickness residual.

## Evaluator Notes

### 2026-06-30T09:37:05Z

Decision: move to `ready`; ranked 1 of 2 in this triage batch.

This is the strongest current proposal because it is narrow, initialization-only,
and materially different from both recent Ekman follow-ups and prior failed DFI
merge experiments. The mechanism does not preserve raw low-mode vorticity,
divergence, temperature, or pressure as in the scrapped
`low-mode-preserving-dfi-initialization`; it diagnoses a same-time
hydrostatic-thickness residual after the incumbent DFI state is built, then
applies only a small, capped, area-mean-free middle-layer temperature correction
when Z500 and 300-700 hPa thickness residuals agree in sign. That makes it a
bounded hydrostatic initialization correction rather than a broad DFI routing or
state-merge experiment.

Local evidence is mixed but favorable enough for one implementation slot. The
accepted hydrostatic layer-mean temperature initialization produced clean
iteration and validation gains, so layer/thickness initialization remains a
credible source of score movement. By contrast, the latest Ekman-adjacent
variants are mostly negative or subthreshold, and the staged positive-time
pressure-height filter still needs read-only diagnostics. This proposal tests a
different error source with lower rollout risk: one post-DFI temperature update,
no positive-time forcing, no output residual, and exact no-op fallbacks when the
required initial geopotential channels or consistency checks fail.

The main risk is that DFI's low-mode thermal adjustment may be dynamically
useful; undoing even a sign-consistent piece could worsen early Z500/MSLP. The
implementation should therefore predeclare the spectral cutoff, thickness
levels, temperature cap, static-stability floor, and no-op thresholds before any
evaluation. It should not be tuned after fast results, and it should use the
cached `dino_ri2m_ekman_coupled` incumbent metrics as the comparison baseline.
