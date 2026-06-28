---
schema_version: 1
slug: moisture-convergence-gated-wtg-dse
title: Moisture-Convergence Gated Tropical WTG Mass-DSE Relaxation
status: ready
created_at: 2026-06-26T21:57:45Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
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

# Moisture-Convergence Gated Tropical WTG Mass-DSE Relaxation

## Hypothesis

The accepted tropical WTG mass-DSE relaxation improved the incumbent, but it
still applies a fixed tropical free-tropospheric mask to both convectively active
and dry subsiding columns. WTG balance is most physically tied to tropical
convective adjustment, where diabatic heating, ascent, and gravity-wave
adjustment keep free-tropospheric temperature gradients weak. A bounded,
forecast-state moisture-convergence gate should concentrate the accepted WTG
relaxation in columns with low-level moist convergence while retaining a smaller
background WTG correction elsewhere. This may preserve the incumbent's validated
mass-field gain while reducing over-relaxation in dry subsidence regions.

## Mechanism

Add one opt-in side-by-side candidate derived from
`dino_hsl2_mass_dse_wtg_vdse_ramp`. Keep the incumbent DFI, residual diagnostics,
weak-Held-Suarez forcing, mass-DSE HSL, pressure-ramped vertical-DSE increment,
WTG sigma envelope, WTG low-mode projection, per-step temperature cap, and
layer heat-offset correction unchanged.

Change only the horizontal support weights inside
`_tropical_wtg_mass_dse_relaxation_step_filter` when the forecast state contains
a finite `specific_humidity` tracer:

- compute nodal `aux_state.divergence` and nodal specific humidity from the same
  diagnostic state already used by the WTG filter;
- build a lower-tropospheric smooth sigma envelope, full from sigma 0.75 to
  0.90 and tapered to zero by sigma 0.60 and 0.98;
- form a nonnegative convective proxy from the lower-tropospheric integral of
  `specific_humidity * max(-divergence, 0)` under that envelope;
- restrict the proxy to the accepted tropical latitude envelope and normalize it
  by its tropical area-weighted mean absolute value plus a small finite epsilon;
- map the normalized proxy to a bounded multiplier, for example
  `0.6 + 0.8 * x / (1 + x)`, then renormalize under the accepted tropical
  weights so the area-mean multiplier remains near 1.0;
- multiply the accepted WTG horizontal weights by this multiplier, recompute the
  tropical layer mean and the layer heat-offset denominator using the modulated
  weights, and keep the existing finite-diagnostic fallback.

If humidity is absent, the proxy is nonfinite, or the normalized tropical weight
sum is degenerate, the filter must exactly fall back to the incumbent fixed-mask
WTG behavior. The proposal does not add precipitation, cloud water, learned
parameters, target variables, new inputs, output postprocessing, or evaluation
protocol changes.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`: add the opt-in
    moisture-convergence gate branch and a factory such as
    `moisture_convergence_gated_wtg_dinosaur_dycore_model`.
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`: export the new factory
    if the module exports side-by-side Dinosaur factories there.
  - `src/dynamaxx/dycore/registry.py`: register a side-by-side model name such
    as `dino_hsl2_mass_dse_wtg_vdse_mfcgate`.
  - `tests/dycore/models/dinosaur/`: add synthetic filter tests for humidity
    no-op fallback, finite humidity gating, conservation of unchanged prognostic
    variables other than temperature, layer heat neutrality under modulated
    weights, and registry factory parity against the incumbent except for the
    new selector.
  - `tests/dycore/test_registry.py`: add the new model to registry coverage.
- Registry changes: add only the side-by-side candidate; do not replace the
  incumbent or remove existing entries.
- API changes: no forecast API, target variable, lead-time, split, metric, or
  golden-protocol changes.
- Tests to update: focused unit tests plus the existing Dinosaur non-JIT smoke
  pattern for finite forecasts when humidity is present and
  `use_humidity_in_dynamics=False`.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium and late leads
    if fixed-mask WTG currently removes useful dry-subsidence thermal structure.
  - `10m_u_component_of_wind` in tropical and subtropical belts if a more
    convectively localized thermal adjustment improves low-mode pressure
    gradients without changing the surface wind diagnostic.
- Expected neutral metrics:
  - `2m_temperature` should remain close to the incumbent because the WTG mask
    stays in the free troposphere, the background multiplier is not zero, and
    near-surface residual diagnostics are unchanged.
  - Dry or humidity-free synthetic states should be bitwise identical to the
    incumbent WTG path.
- Possible regressions:
  - The accepted WTG gain may rely on broad tropical damping rather than
    convective localization, especially after the rejected ocean-weighted and
    late-tapered WTG variants showed that weakening the accepted support can
    lose skill.
  - Passive humidity may be phase-shifted relative to active heating in this
    dry-dynamics configuration, causing noisy or misplaced gates.

## Risks

- Numerical stability: moderate. The filter remains capped and heat-neutral,
  but dynamically modulated weights add a new denominator and must preserve the
  existing finite fallback for small or nonfinite tropical proxy sums.
- Compute cost: low to moderate. One additional low-level vertical reduction
  over nodal divergence and humidity is required per WTG filter application.
- Data leakage: low. The gate uses only current forecast-state divergence,
  humidity, fixed grid geometry, and constants; it does not use targets,
  analysis increments, verification data, or lead-specific fitted statistics.
- Physical plausibility: moderate. Moisture-flux convergence is a standard
  convective-environment diagnostic, and WTG theory links tropical convection
  and weak free-tropospheric temperature gradients. The weakness is that this
  dycore carries humidity passively unless humidity dynamics are enabled.
- Rollback complexity: low. The branch is opt-in and should be confined to the
  existing WTG filter and candidate factory.

## Evaluation Plan

- Fast gate: run `uv run pytest`, then
  `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_mfcgate`.
  Reject immediately on nonfinite forecasts, broken registry tests, or failure
  of the humidity-absent incumbent-fallback unit test.
- Iteration gate: run
  `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_mfcgate --workers 4`
  and compare against cached incumbent iteration score `-0.2197104515448394`.
- Validation gate: only if iteration is positive and guardrails are acceptable,
  run
  `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_mfcgate --workers 4`
  against cached incumbent validation score `-0.21940899263836755`.
- Outcome that would falsify the hypothesis: a clean iteration score at or
  below the incumbent, or any broad `2m_temperature`/MSLP guardrail degradation,
  would show that the accepted broad WTG support is empirically better than
  moisture-convergence localization under the fixed evaluation contract.

## Citations

- Sobel, A. H., Nilsson, J., and Polvani, L. M. (2001). The weak temperature
  gradient approximation and balanced tropical moisture waves. Journal of the
  Atmospheric Sciences, 58(23), 3650-3665.
  https://doi.org/10.1175/1520-0469(2001)058%3C3650:TWTGAA%3E2.0.CO;2
- Raymond, D. J., and Zeng, X. (2005). Modelling tropical atmospheric
  convection in the context of the weak temperature gradient approximation.
  Quarterly Journal of the Royal Meteorological Society, 131(608), 1301-1320.
  https://doi.org/10.1256/qj.03.97
- Banacos, P. C., and Schultz, D. M. (2005). The use of moisture flux
  convergence in forecasting convective initiation: Historical and operational
  perspectives. Weather and Forecasting, 20(3), 351-366.
  https://doi.org/10.1175/WAF858.1

## Researcher Notes

This is intentionally only one proposal because the active staging and scrap
queues already cover most nearby WTG, vertical-DSE, surface-residual, pressure,
spectral, humidity, and orographic variants. It is distinct from
`ocean-weighted-tropical-wtg-mass-dse` because the support is dynamic and
state-dependent rather than a static land-sea mask. It is distinct from
`late-tapered-tropical-wtg-relaxation` because it preserves the mean WTG
strength instead of weakening it by lead time. It is distinct from
`zonal-anomaly-tropical-wtg-mass-dse`,
`first-baroclinic-tropical-wtg-mass-dse`,
`time-centered-tropical-wtg-mass-dse`, and
`inline-tendency-tropical-wtg-dse` because it does not change the relaxed
subspace, vertical mode, timing, or equation placement.

Negative evidence is substantial: recent WTG refinements that narrowed or
weakened the accepted operator were clean but negative, and the incumbent WTG
plus pressure-ramped vertical-DSE path is strong. This proposal is only worth
triage if the Evaluator wants one targeted test of whether WTG support should
be redistributed toward convective columns without reducing the tropical-mean
relaxation strength.

## Evaluator Notes

### 2026-06-26T22:01:21Z

Decision: move to `ready`; rank 1 of 1 new proposals and the single ready
recommendation for this pass.

The proposal has real negative evidence around it, but it is the best available
next model-selection experiment after comparing it with active staging. The
accepted WTG operator produced a score-scale gain, while
`ocean-weighted-tropical-wtg-mass-dse`,
`mass-neutral-clipped-wtg-dse`, and
`late-tapered-tropical-wtg-relaxation` were clean but negative. Those failures
argue against simply narrowing, weakening, or reclosing the accepted WTG
support. This proposal is different enough to justify one targeted test because
it preserves the tropical-mean relaxation strength through renormalization,
keeps a nonzero background WTG correction, leaves the pressure-ramped
vertical-DSE path unchanged, and confines the new information to bounded
horizontal support weights inside the existing rollout-only filter.

The scientific claim is sufficiently supported for triage: WTG theory links
tropical free-tropospheric temperature adjustment to convective heating and
large-scale ascent, and moisture-flux convergence is a standard convective
environment diagnostic. The local caveat is important: humidity is passive in
this dry-dynamics configuration, and prior humidity mechanisms were weak or
negative. `moist-static-energy-hsl-transport` was effectively neutral, and
bounded moist virtual-temperature dynamics regressed the fixed score. This
candidate is narrower than those because humidity does not enter pressure,
geopotential, momentum, or the transported thermal invariant; it only modulates
an already accepted WTG mask with finite fallback to incumbent behavior.

The strongest staged alternatives are less attractive for the immediate slot.
`delayed-lowmode-virtual-geopotential-coupling` feeds passive humidity into an
active divergence tendency, which repeats a riskier version of the humidity
dynamics failure mode. `boundary-layer-sheltered-vertical-dse` damps part of a
newly accepted high-signal vertical-DSE mechanism and was already held behind
the now-rejected lower-risk cap-release test. `stagewise-sil3-tendency-filtering`
has broader time-integration blast radius after a near-neutral transform
precision experiment and negative diffusion/split history.
`compensated-vertical-integral-reductions` is numerically legitimate but likely
subthreshold against the `+0.002` iteration promotion gate. Existing staged WTG
variants either weaken the accepted operator, change operator placement at
higher cost, or predate the current vertical-DSE incumbent.

Implementation constraints for Orchestrator/Implementer: keep this strictly
side-by-side; do not change the incumbent registry entry; do not alter fixed
protocols, targets, lead times, or output postprocessing; require exact
incumbent fallback when humidity is absent, nonfinite, or degenerate; and keep
the multiplier constants predeclared rather than tuned against iteration or
validation results. Validation should be skipped unless the fixed iteration
gate promotes cleanly against the cached incumbent.
