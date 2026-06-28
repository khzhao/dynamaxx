# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -1.2218391186283701
- Iteration incumbent primary score: -1.2218408656785489
- Iteration delta: 0.0000017470501787464343
- Validation candidate primary score: not_run
- Validation incumbent primary score: -1.2103467803549615
- Validation delta: not_run

## Rationale

The candidate passed fast diagnostics, full pytest, and all fixed iteration
RMSE guardrails, but the iteration primary-score gain was only
`+0.0000017470501787464343`. This is far below the protocol's required
`+0.002` iteration promotion threshold. Validation was therefore not run.

The rejection is due to effect size only. Candidate diagnostics were clean with
zero issues, early day 1-5 mean RMSE guardrails all passed, and the largest
variable+lead RMSE regression was only `0.00006489240410109463` for
`geopotential_500` at 48 hours.

## Lessons Learned

- Splitting weak Held-Suarez forcing out of the DFI equation is numerically
  stable and physically cleaner, but it is nearly indistinguishable from the
  incumbent under the fixed iteration protocol.
- The incumbent's remaining error is unlikely to be materially affected by
  removing weak Held-Suarez from the DFI initialization branch.
- Future initialization changes should avoid small bookkeeping-only splits
  unless they also change a physically meaningful balanced state component.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the tracked worktree
- Research state updated: ready proposal removed after rejection
- Leaderboard updated: no, rejected candidates do not update the leaderboard
- Git status checked: tracked status clean after rollback

## Next Action

Start the next optimization iteration from
`dinosaur_dfi_surface_residual_weak_hs` as the incumbent. Ask Researcher for
new ideas or a documented exhaustion note while keeping
`semi-lagrangian-vertical-transport` staged until Evaluator decides it should
be promoted, revised, or scrapped.
