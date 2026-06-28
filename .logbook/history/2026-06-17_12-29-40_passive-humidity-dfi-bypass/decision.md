# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1439754503896644`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-1.9179700339044814e-07`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed full pytest, fast sanity, and fixed iteration diagnostics,
but it did not meet the fixed iteration promotion threshold. The primary score
delta was slightly negative (`-1.9179700339044814e-07`) versus the required
`+0.002`, so validation was not run.

The guardrails were clean. The largest early day 1-5 mean RMSE regression was
`geopotential_500` at `+0.000656%`, far below the 2% limit. The largest single
variable+lead RMSE regression was `geopotential_500` at 24h with `+0.007681%`,
far below the 10% limit. This shows the passive humidity DFI bypass is stable
but not score-relevant for the current incumbent.

## Lessons Learned

- Preserving passive humidity through dry DFI changes the fixed metrics only at
  near-roundoff scale for this incumbent.
- The prior dry-consistent geopotential rejection showed humidity diagnostics
  must remain present, but this experiment shows DFI filtering of that passive
  tracer is not a meaningful remaining error source.
- Future humidity-only proposals should not focus on passive tracer preservation
  unless they include a stronger physical coupling mechanism that still
  preserves dry-dynamics stability and the fixed forecast contract.

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
