# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -1.2218428097613614
- Iteration incumbent primary score: -1.2218408656785489
- Iteration delta: -0.0000019440828125105725
- Validation candidate primary score: not_run
- Validation incumbent primary score: -1.2103467803549615
- Validation delta: not_run

## Rationale

The candidate passed fast diagnostics and fixed iteration diagnostics, but the
iteration primary-score delta was slightly negative and below the required
`+0.002` promotion threshold. Validation was therefore not run.

All fixed iteration guardrails passed. The largest early day 1-5 mean RMSE
regression was `5.736504032213701e-8` for mean sea level pressure, and the
largest variable+lead RMSE regression was `1.592198976555658e-5` for 500 hPa
geopotential at 168 hours. This is a clean falsification by lack of measurable
primary-score gain, not a stability issue.

## Lessons Learned

- Passive humidity positivity at diagnostic time is not a meaningful remaining
  error source for the current weak-Held-Suarez incumbent.
- Future humidity proposals should include read-only evidence that humidity
  diagnostic undershoots materially affect evaluated variables before a full
  model-selection run.
- The staged T120 resolution proposal remains the only active research item.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the tracked worktree
- Research state updated: ready proposal removed after rejection; staged T120
  proposal retained
- Leaderboard updated: no, rejected candidates do not update the leaderboard
- Git status checked: tracked status clean after rollback

## Next Action

Start the next optimization iteration from
`dinosaur_dfi_surface_residual_weak_hs` as the incumbent and re-triage the
staged `full-grid-spectral-truncation` proposal before implementation.
