# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.245126054186803`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-0.10115079559414197`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed fast and iteration diagnostics, but it failed all
iteration acceptance requirements. The primary score regressed by
`-0.10115079559414197`, far below the required `+0.002`, so validation was not
run.

Both RMSE guardrails failed. The largest early day 1-5 mean RMSE regression was
`10m_u_component_of_wind` at `+9.833722%`, above the 2% limit. The largest
single variable+lead RMSE regression was `10m_u_component_of_wind` at 24h with
`+16.538051%`, above the 10% limit. `2m_temperature` also failed the early
mean guardrail with `+5.789438%`.

The invariant expectations for mass fields held: `geopotential_500` and MSLP
changed only near roundoff. The rejection is therefore attributed to the
simplified lowest-layer shear diagnostic itself, not to trajectory or mass
field contamination.

## Lessons Learned

- A simple bounded two-layer extrapolation is too crude for the fixed
  near-surface metrics and damages both targeted channels.
- The accepted near-surface residual remains the safer surface diagnostic
  mechanism; further screen-level post-processing needs substantially more
  physical structure before another model-selection trial.
- Output-only changes can pass diagnostics while still causing large RMSE
  regressions, so fast sanity is not a reliable proxy for near-surface skill.

## Cleanup Completed

- Candidate code retained or reverted: reverted the candidate source and test
  changes from the six touched files.
- Research state updated: ready proposal removed after the immutable history
  record was completed.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: tracked worktree clean on branch `kzhao--codex`.

## Next Action

Revert the candidate implementation changes, remove the active ready proposal,
verify tracked worktree cleanliness, then continue the optimization loop with
the remaining staged research queue.
