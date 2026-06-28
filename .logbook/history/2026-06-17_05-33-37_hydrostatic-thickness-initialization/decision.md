# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-1.1486642287781768`
- Iteration incumbent primary score: `-1.2155220438349768`
- Iteration delta: `+0.0668578150568`
- Validation candidate primary score: `-1.1354942896701432`
- Validation incumbent primary score: `-1.202899107828725`
- Validation delta: `+0.06740481815858179`

## Rationale

The candidate passed the fixed fast, iteration, and validation gates without
changing metrics, splits, lead times, target variables, or deterministic
evaluation commands. Fast diagnostics were clean. Iteration primary score
improved by `+0.0668578150568`, above the `+0.002` promotion threshold.
Validation primary score improved by `+0.06740481815858179`, above the `+0.001`
acceptance threshold.

The guardrails also passed. Iteration early day 1-5 mean RMSE improved by
`-2.8776927565342354%`, validation early day 1-5 mean RMSE improved by
`-2.9840245432386937%`, and there were no variable+lead RMSE regressions above
`10%`. The largest accepted regressions were short-lead `2m_temperature`
increases of `+2.5496159901750286%` on iteration and `+2.192158573040194%` on
validation, both below the protocol guardrail.

The implementation is physically plausible and scoped to initialization: it
uses same-time pressure-level geopotential thickness to estimate hydrostatic dry
temperature before the already accepted log-pressure sigma remap, while leaving
the forecast API, tendencies, DFI, weak Held-Suarez relaxation, near-surface
residual correction, and output contract unchanged.

## Lessons Learned

- Same-time hydrostatic balance projection is a strong improvement for this
  incumbent, unlike broader vertical-coordinate or tendency changes that
  previously destabilized or failed guardrails.
- Short-lead `2m_temperature` remains the most sensitive regression channel for
  initialization experiments and should stay prominent in future proposal risk
  sections.
- Score calculations must continue filtering exact evaluated `model_name` rows
  because evaluation JSON files also contain `persistence` rows with duplicate
  channel and lead keys.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `4f4b397d90551cd87e35604fb8431f2c08c79606`.
- Research state updated: consumed ready proposal removed after preserving it
  in this history directory.
- Leaderboard updated: yes, incumbent set to
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init`.
- Git status checked: tracked worktree clean after commit; ignored logbook
  metadata retained locally.

## Next Action

Start the next continuous-loop iteration by inspecting resources and research
state, then asking the Researcher for a small set of new decorrelated proposals.
