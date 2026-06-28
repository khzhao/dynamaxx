# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1233009637594966`
- Iteration incumbent primary score: `-1.1241936221835356`
- Iteration delta: `+0.0008926584240389612`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1127999773519712`
- Validation delta: not applicable

## Rationale

The candidate passed the fast sanity gate with clean diagnostics, then improved
the fixed iteration primary score by `+0.0008926584240389612`. That was below
the required `+0.002` promotion threshold, so validation was not run.

Diagnostics and guardrails were clean. No early day 1-5 mean RMSE regression
exceeded `2%`, and no variable+lead RMSE regression exceeded `10%`. The largest
single RMSE regression was `mean_sea_level_pressure` at 120h with
`+1.394802914666302%`.

The small positive score suggests that matching DFI to the accepted split
Coriolis rollout is physically reasonable but not a material remaining error
source under the fixed iteration gate.

## Lessons Learned

- Signed exact-Coriolis treatment inside DFI was clean and slightly positive,
  but less than half the iteration promotion threshold.
- The current unsplit DFI path is not worth replacing without a stronger
  initialization mechanism.
- Future DFI proposals should avoid spending another iteration on operator
  consistency alone unless paired with a distinct, reviewed mechanism.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the six source/test files.
- Research state updated: selected proposal moved from `ready` into this
  history directory; implementation, scores, and scoring notes written locally.
- Leaderboard updated: no, rejected candidate.
- Git status checked: clean tracked worktree after rollback.

## Next Action

Continue the optimization loop with a new Researcher proposal pass and
Evaluator triage against the unchanged incumbent
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang`.
