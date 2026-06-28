# Exhausted Research Ideas Stop Condition

## Evaluator Review

- Reviewed by: Evaluator
- Reviewed at: 2026-06-17T16:46:29Z
- Incumbent model:
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- Incumbent history:
  `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init`
- Incumbent iteration primary score: `-1.143975258592661`
- Incumbent validation primary score: `-1.1301883620649706`

This note documents the protocol stop condition: no ready or researchable ideas
remain after documented search. It is a research-state note, not a dycore source
change and not a proposal for implementation.

## Active Queue State

The active research directories were inspected:

- `.logbook/research/proposals/`: no proposal files
- `.logbook/research/ready/`: no proposal files
- `.logbook/research/staging/`: no proposal files
- `.logbook/research/scrap/`: only rejected or superseded ideas remain

The Researcher final-search result supplied to this Evaluator pass was: no new
proposals, no active proposals, no ready ideas, no staged ideas, and no
researchable non-duplicate ideas remain. My independent pass found no
contradicting active proposal file or revival candidate.

## Recent History Check

Recent evaluated fallbacks do not justify another immediate implementation:

- `polar-vector-wind-initialization-taper` was stable and guardrail-clean, but
  its iteration delta was only `+1.444147295082132e-07`, numerical-noise scale
  and far below the `+0.002` promotion threshold.
- `bounded-log-pressure-init-extrapolation` was stable and guardrail-clean, but
  regressed primary by `-0.000955044360586`, so the remaining edge-only
  pressure-initialization fallback is not useful.
- `surface-layer-diagnostic-extrapolation` regressed primary by
  `-0.10115079559414197` and failed early `10m_u_component_of_wind` and
  `2m_temperature` guardrails, weakening further near-surface diagnostic
  shortcuts.
- `passive-humidity-dfi-bypass` was effectively neutral
  (`-1.9179700339044814e-07`), so passive-humidity DFI bookkeeping is not a
  material remaining error source.
- `low-level-sparing-thermal-drift-limiter` avoided the earlier wind guardrail
  failure but lost primary (`-0.001517601128549373`), weakening thermal limiter
  follow-ups.
- `potential-temperature-logp-initialization` and
  `conservative-pressure-thickness-init-remap` were clean but negative,
  indicating that additional pressure/thermodynamic initialization remaps need
  stronger evidence before another iteration.
- `dry-consistent-geopotential-diagnostic` failed the short-lead Z500 guardrail,
  and `log-pressure-output-interpolation` had 54 variable-lead RMSE guardrail
  failures, weakening scored-output diagnostic remaps.
- `helmholtz-wind-initialization` severely damaged mass fields, while the polar
  wind taper was too small to matter. Together they leave no credible wind
  initialization middle ground in the current notes.

The latest accepted improvements were narrow same-time initialization changes:
log-pressure sigma initialization, hydrostatic-thickness initialization, and
layer-mean hydrostatic temperature initialization. The documented follow-ups on
that axis have now either failed, been neutral, or been consumed.

## Scrap Review

No scrapped proposal should be promoted or revived under the current evidence:

- `barotropic-angular-momentum-fixer`: still lacks a diagnostic showing that
  resolved axial angular-momentum drift is large, monotonic, and causally linked
  to scored wind error. It rewrites prognostic wind state every positive inner
  step, making it too close to the broad wind/numerics family that has repeatedly
  failed or produced negligible signal.
- `geopotential-datum-output-correction`: remains too directly metric-facing and
  is superseded by cleaner diagnostic attempts that failed or triggered Z500
  guardrail problems. The prior mass residual was too small, terrain/orography
  failed guardrails, dry-consistent geopotential failed short-lead Z500, and
  output interpolation produced many guardrail failures.
- `held-suarez-relaxation-forcing`: this older proposal is obsolete and
  superseded by the already evaluated wind-sparing weak Held-Suarez accepted
  path. Its original Rayleigh-drag component remains a direct risk to the
  sensitive early 10 m wind guardrail.
- `semi-lagrangian-vertical-transport`: remains a broad core-transport rewrite
  with runtime, interpolation, phase, and long-lead stability risk. The closest
  vertical-transport ablation failed fast with nonfinite outputs, and no new
  diagnostic implicates centered vertical transport as the dominant remaining
  error source.
- `upper-sigma-rayleigh-sponge`: remains an under-evidenced damping/numerics
  idea. Prior damping, timestep, truncation, sigma-grid, and vertical-transport
  variants mostly failed to promote or failed guardrails, and no measured
  model-top reflection diagnostic has been added.

## Stop Condition

Under `roles/PROTOCOL.md`, the loop may stop when there are no ready or
researchable ideas remaining after a documented search. That condition is met:
the active queues are empty, the Researcher search found no non-duplicate
researchable ideas, recent ready/staged fallbacks have been scored and rejected,
and the remaining scrap files have no new evidence sufficient for revival.

Do not run `golden`. Do not run further evaluation. Do not modify dycore source.
Future work should resume only if a genuinely new proposal is written, or if a
new diagnostic changes the evidence for one of the scrapped mechanisms.
