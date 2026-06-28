# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-1.1241936221835356`
- Iteration incumbent primary score: `-1.127914598973564`
- Iteration delta: `+0.003720976790028363`
- Validation candidate primary score: `-1.1127999773519712`
- Validation incumbent primary score: `-1.11604278330304`
- Validation delta: `+0.003242805951068739`

## Rationale

The candidate cleared the fixed iteration promotion gate with a
`+0.003720976790028363` primary-score delta, exceeding the required `+0.002`
threshold. It then cleared the fixed validation acceptance gate with a
`+0.003242805951068739` delta, exceeding the required `+0.001` threshold.

Diagnostics were clean for fast, iteration, validation, and the reused
incumbent artifacts. The early day 1-5 mean RMSE guardrail had no `>2%`
violations; the largest early regression was validation
`mean_sea_level_pressure` at `+0.8699505158908783%`. The variable+lead RMSE
guardrail had no `>10%` violations; the largest regression was iteration
`mean_sea_level_pressure` at 96h with `+2.0735194152026865%`.

The result supports the hypothesis that the accepted exact Coriolis split still
benefited from lower operator-ordering error. The symmetric half/full/half
rollout preserved the unsplit DFI path and all incumbent physics settings while
improving both fixed gates.

## Lessons Learned

- Symmetric ordering of the exact Coriolis source produced a smaller but real
  gain on top of the accepted Lie split.
- Future split-timing proposals should watch short-lead
  `mean_sea_level_pressure`, which was the largest measured regression here but
  remained well inside protocol guardrails.

## Cleanup Completed

- Candidate code retained or reverted: retained in commit
  `30a496b1f2ed8f894511404341c7774288bdb4c8`.
- Research state updated: selected proposal moved from `ready` into this
  history directory; scoring and implementation records written locally.
- Leaderboard updated: yes, local `.logbook/leaderboard.json` now points to the
  accepted candidate.
- Git status checked: clean tracked worktree after commit.

## Next Action

Continue the optimization loop with a new Researcher proposal pass and
Evaluator triage against
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang`.
