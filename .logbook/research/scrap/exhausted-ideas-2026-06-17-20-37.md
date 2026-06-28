# Exhausted Research Ideas Stop Condition

## Researcher Review

- Reviewed by: Researcher
- Reviewed at: 2026-06-17T20:37:39Z
- Incumbent model:
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- Incumbent commit: `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`
- Incumbent iteration primary score: `-1.143975258592661`
- Incumbent validation primary score: `-1.1301883620649706`
- Leaderboard path: `.logbook/leaderboard.json`

This note documents the Researcher stop condition rather than a proposal. I did
not find a genuinely new, researchable, side-by-side dycore idea that is both
decorrelated from prior failures and strong enough to justify consuming another
fixed iteration/validation cycle.

## Active Queue State

The active research queues were inspected before writing this note:

- `.logbook/research/proposals/`: empty
- `.logbook/research/ready/`: empty
- `.logbook/research/staging/`: empty
- `.logbook/research/scrap/`: contains only rejected, obsolete, or exhaustion
  artifacts

No proposal files were moved. No source code, tests, registry entries, metrics,
evaluation protocols, target variables, splits, or lead times were changed.

## Incumbent And Code Context

The incumbent already includes the accepted chain of finite output support,
digital filter initialization, near-surface residual diagnostics, weak
wind-sparing Held-Suarez thermal relaxation, log-pressure initialization,
hydrostatic thickness initialization, and hydrostatic layer-mean temperature
initialization. Source inspection of
`src/dynamaxx/dycore/models/dinosaur/adapter.py`,
`src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`, and
`src/dynamaxx/dycore/registry.py` confirmed that plausible small changes would
mostly fall into families that have already been evaluated:

- initialization remaps for pressure, temperature, wind, and hydrostatic balance;
- output-only diagnostic residuals or pressure/geopotential remaps;
- weak forcing, damping, sponge, diffusion, step-size, and vertical-transport
  changes;
- humidity feedback, passive humidity bookkeeping, or saturation adjustment.

The incumbent iteration CSV still shows long-lead cold 2 m temperature bias,
positive MSLP bias, and poor 10 m zonal-wind skill, but recent history indicates
that the obvious mechanisms for attacking those drifts are either too broad,
too metric-facing, too weak, or harmful to early RMSE guardrails.

## Recent Negative Evidence

The requested recent decisions were treated as direct negative evidence:

- `bounded-saturation-adjustment` was rejected with iteration delta
  `-0.026391567842939834` and early day 1-5 RMSE guardrail failures for MSLP,
  Z500, and 10 m zonal wind. This blocks another minimal irreversible moist
  heating proposal.
- `bounded-moist-virtual-temperature-dynamics` was rejected with iteration delta
  `-0.055193744700895`. This blocks more humidity variants that simply activate
  moisture in dry dynamics.
- `bounded-log-pressure-init-extrapolation` was clean but negative, with
  iteration delta `-0.000955044360586`. This weakens remaining pressure-edge
  initialization variants.
- `polar-vector-wind-initialization-taper` was clean but only
  `+1.444147295082132e-07`, numerical-noise scale. This blocks another narrow
  pole-only wind cleanup.
- `surface-layer-diagnostic-extrapolation` regressed by
  `-0.10115079559414197` and failed early 2 m temperature and 10 m wind
  guardrails. This blocks simple screen-level extrapolation variants.
- `passive-humidity-dfi-bypass` was effectively neutral. This blocks passive
  humidity bookkeeping as a meaningful remaining source.

Earlier decisions also remove the most tempting fallback families:

- broad damping/numerics variants, including hyperdiffusion, divergence damping,
  shorter inner step, full-grid spectral truncation, vertical-advection
  suppression, semi-Lagrangian vertical transport, and top sponge ideas;
- terrain/orography and mass/geopotential diagnostic corrections, which either
  failed guardrails or were too metric-facing;
- thermal recentering follow-ups, where the full-column signal failed the early
  10 m wind guardrail and the low-level-sparing revision lost primary skill;
- wind-control variants, where Helmholtz initialization was severely harmful,
  the polar taper was too small, and the angular-momentum fixer was already
  scrapped as too broad without a diagnostic proving the drift mechanism.

## Ideas Considered And Not Written

- A stronger or longer-lived near-surface residual was not written because it
  would be direct metric-facing tuning of an already accepted output correction,
  and the latest surface-layer diagnostic extrapolation failed badly.
- Another weak-Held-Suarez, Rayleigh, sponge, or diffusion proposal was not
  written because the accepted weak-HS path is already in the incumbent and
  multiple damping-style follow-ups were negative or scrapped.
- Another pressure or hydrostatic initialization proposal was not written
  because accepted log-pressure and layer-mean hydrostatic initialization have
  already consumed the useful signal, while pressure-edge clipping,
  conservative pressure-thickness remapping, potential-temperature remapping,
  and output interpolation were negative or guardrail-failing.
- Another humidity proposal was not written because both active moist density
  feedback and irreversible saturation heating recently degraded iteration
  skill, and passive humidity preservation was neutral.
- A balanced thermal-recentering revision was not written because the obvious
  protection mechanisms either repeat the failed low-level-sparing idea or add
  metric-facing 10 m wind post-processing.

## Stop Condition

Under `roles/PROTOCOL.md`, the loop may stop when no ready or researchable ideas
remain after a documented search. That condition is met for the Researcher pass:
the active queues are empty, the incumbent code and registry were inspected, the
recent rejected decisions were incorporated as negative evidence, and the
remaining plausible mechanisms are duplicates, near-duplicates, or lower-quality
variants of already rejected or scrapped ideas.

The appropriate next action is Evaluator or Orchestrator confirmation of this
stop condition, not another forced proposal. Future research should resume only
if a new diagnostic changes the evidence for a scrapped family or a genuinely
new mechanism appears that preserves the fixed deterministic forecast API and
evaluation protocols.

## Evaluator Confirmation

- Reviewed by: Evaluator
- Reviewed at: 2026-06-17T20:39:22Z
- Incumbent model:
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- Incumbent iteration primary score: `-1.143975258592661`
- Incumbent validation primary score: `-1.1301883620649706`

I independently reviewed the active research queues, the requested recent
decision records, the latest leaderboard entry, the registered incumbent model,
the named scrap proposals, and the prior exhaustion note. I agree with the
Researcher conclusion: no proposal should be revived, promoted, or rewritten as
a ready/staged model-selection candidate under the current evidence.

### Queue State

- `.logbook/research/proposals/`: empty
- `.logbook/research/ready/`: empty
- `.logbook/research/staging/`: empty
- `.logbook/research/scrap/`: contains only rejected, superseded, or exhaustion
  artifacts

### Scrap Revival Review

- `barotropic-angular-momentum-fixer`: keep in `scrap`. The file itself
  required a diagnostic showing large, monotonic axial-angular-momentum drift
  causally linked to scored wind error before revival. No such new evidence is
  present, and the latest wind-control history remains negative or
  numerical-noise scale.
- `geopotential-datum-output-correction`: keep in `scrap`. It remains a direct
  scored-output correction and is weakened by terrain/orography, mass-residual,
  log-pressure output interpolation, dry-consistent geopotential, and
  conservative pressure remap failures or sub-threshold results.
- `held-suarez-relaxation-forcing`: keep in `scrap`. This older Rayleigh-drag
  version was superseded by the accepted wind-sparing weak-Held-Suarez path;
  reviving the obsolete drag component would duplicate a consumed family while
  reintroducing early 10 m wind guardrail risk.
- `semi-lagrangian-vertical-transport`: keep in `scrap`. It is still a broad
  core-transport rewrite with runtime, diffusion, phase, and long-lead
  stability risk. No new diagnostic identifies centered vertical transport as
  the dominant remaining error source after the latest failures.
- `upper-sigma-rayleigh-sponge`: keep in `scrap`. It remains an under-evidenced
  damping/numerics variant, and no measured upper-layer reflection or imbalance
  diagnostic has appeared to overcome the prior negative damping, timestep,
  truncation, sigma-grid, and vertical-transport history.
- Prior exhaustion note
  `.logbook/research/scrap/exhausted-ideas-2026-06-17.md`: still consistent
  with the current pass. The later humidity candidates add further negative
  evidence rather than a revival path.

### Stop Condition

Under `roles/PROTOCOL.md`, the applicable stop condition is exactly: "no ready
or researchable ideas remain after a documented search." That condition is met:
all active proposal states are empty, the remaining scrap files were reviewed
for revival evidence, recent scored fallbacks do not change the prior
decisions, and no concrete research state update is warranted.

Do not run `golden`, do not run additional model-selection evaluation, and do
not modify source code, tests, registry, leaderboard, evaluation outputs, or
fixed protocols for this confirmation.
