# Resumed-Audit Exhaustion Note

## Researcher Review

- Reviewed by: Researcher
- Reviewed at: 2026-06-17T21:09:00Z
- Incumbent model:
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- Incumbent commit: `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`
- Incumbent iteration primary score: `-1.143975258592661`
- Incumbent validation primary score: `-1.1301883620649706`
- Prior stop-condition note:
  `.logbook/research/scrap/exhausted-ideas-2026-06-17-20-37.md`

This resumed audit looked specifically for a narrow model-selection proposal
that might have been missed after the two recent humidity rejections. I did not
find one strong enough to write as a new proposal.

## Queue State

- `.logbook/research/proposals/`: empty
- `.logbook/research/ready/`: empty
- `.logbook/research/staging/`: empty
- `.logbook/research/scrap/`: contains prior scrap and exhaustion artifacts,
  plus this resumed-audit note

No proposal files were moved. No source code, tests, registry entries,
leaderboard records, evaluation outputs, metrics, splits, target variables, or
lead times were changed. No model-selection evaluation or golden protocol was
run.

## Sources Inspected

- `roles/PROTOCOL.md`
- `roles/RESEARCHER.md`
- `roles/templates/proposal.md`
- `.logbook/leaderboard.json`
- `.logbook/research/scrap/exhausted-ideas-2026-06-17-20-37.md`
- Recent decisions:
  - `.logbook/history/2026-06-17_19-31-12_bounded-saturation-adjustment/decision.md`
  - `.logbook/history/2026-06-17_18-02-45_bounded-moist-virtual-temperature-dynamics/decision.md`
  - `.logbook/history/2026-06-17_15-45-30_bounded-log-pressure-init-extrapolation/decision.md`
  - `.logbook/history/2026-06-17_14-44-29_polar-vector-wind-initialization-taper/decision.md`
  - `.logbook/history/2026-06-17_13-35-18_surface-layer-diagnostic-extrapolation/decision.md`
  - `.logbook/history/2026-06-17_12-29-40_passive-humidity-dfi-bypass/decision.md`
- Additional pressure, thermal, damping, and initialization decisions:
  - `.logbook/history/2026-06-16_17-43-05_global-mean-pressure-anchor/decision.md`
  - `.logbook/history/2026-06-17_02-11-52_log-pressure-output-interpolation/decision.md`
  - `.logbook/history/2026-06-17_08-03-52_conservative-pressure-thickness-init-remap/decision.md`
  - `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
  - `.logbook/history/2026-06-17_10-15-26_potential-temperature-logp-initialization/decision.md`
  - `.logbook/history/2026-06-17_04-21-14_layer-mean-thermal-recentering/decision.md`
  - `.logbook/history/2026-06-17_05-33-37_hydrostatic-thickness-initialization/decision.md`
  - `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  - `.logbook/history/2026-06-17_11-26-04_low-level-sparing-thermal-drift-limiter/decision.md`
  - `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  - `.logbook/history/2026-06-16_18-41-23_six-hundred-second-inner-step/decision.md`
  - `.logbook/history/2026-06-16_19-57-46_divergence-selective-gravity-wave-damping/decision.md`
  - `.logbook/history/2026-06-16_20-56-11_vertical-advection-suppression/decision.md`
  - `.logbook/history/2026-06-16_22-11-18_full-grid-spectral-truncation/decision.md`
- Scrap revival context:
  - `.logbook/research/scrap/barotropic-angular-momentum-fixer.md`
  - `.logbook/research/scrap/geopotential-datum-output-correction.md`
  - `.logbook/research/scrap/held-suarez-relaxation-forcing.md`
  - `.logbook/research/scrap/semi-lagrangian-vertical-transport.md`
  - `.logbook/research/scrap/upper-sigma-rayleigh-sponge.md`
- Source context:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`

## Narrow Ideas Considered But Not Written

- DFI mass-field re-anchoring after digital filter initialization. Anchoring the
  zero-wavenumber `log_surface_pressure` mode was already neutral-negative at
  `-0.000000944240674982666`, while a full spatial re-anchor would perturb
  pressure gradients after repeated pressure-coordinate, output-interpolation,
  and conservative-remap failures. This is not strong enough to distinguish
  itself from rejected pressure/mass variants.
- Humidity as a diagnostic-only hydrostatic refinement. The incumbent already
  uses humidity in layer-mean hydrostatic temperature initialization and
  virtual-temperature geopotential diagnostics. Passive humidity DFI bypass was
  near roundoff, active moist virtual-temperature dynamics regressed by
  `-0.055193744700895`, and bounded saturation adjustment regressed by
  `-0.026391567842939834` with early mass, height, and wind guardrail failures.
  A further humidity variant would be a weak duplicate under current evidence.
- A lower-risk version of full-column thermal recentering. The follow-up
  low-level-sparing limiter protected early 10 m wind but lost primary skill,
  while the original full-column version failed the early 10 m wind guardrail.
  Remaining variants would be mask or strength tuning around the same failed
  mechanism.
- A very narrow wind-bias correction. Exact-pole wind regularization moved the
  score by only `+1.444147295082132e-07`; the broader angular-momentum fixer is
  already in scrap because it would rewrite prognostic winds each step without
  diagnostic evidence for barotropic angular-momentum drift.
- A top-only or weak damping fallback. Existing hyperdiffusion, divergence
  damping, shorter stepping, spectral truncation, vertical-advection ablation,
  and top-sponge scrap evidence make another damping or numerics candidate a
  poor use of a fixed iteration cycle without a new measured instability
  diagnostic.
- A surface diagnostic residual extension. The accepted near-surface residual
  remains in the incumbent, while a simple surface-layer extrapolation regressed
  by `-0.10115079559414197` and failed early `2m_temperature` and
  `10m_u_component_of_wind` guardrails. Extending the residual family now would
  be metric-facing tuning rather than a new dycore mechanism.

## Stop Condition Evidence

The active research queues are empty, the latest exhaustion note already has
Evaluator confirmation, and this resumed pass did not uncover a non-duplicate
candidate that survives the recent humidity rejections plus pressure, surface,
wind, thermal, and damping negative evidence. Under `roles/PROTOCOL.md`, the
Researcher stop condition remains: no ready or researchable ideas remain after
a documented search.

The appropriate next action is Evaluator or Orchestrator confirmation of this
resumed-audit stop condition, not another forced proposal.
