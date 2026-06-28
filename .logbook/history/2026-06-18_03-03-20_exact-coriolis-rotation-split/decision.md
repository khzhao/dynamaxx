# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-1.127914598973564`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `+0.016060659619097084`
- Validation candidate primary score: `-1.11604278330304`
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: `+0.014145578761930677`

## Rationale

The candidate cleared the fixed iteration gate with a `+0.016060659619097084`
primary-score delta, exceeding the required `+0.002` threshold. It then cleared
the fixed validation gate with a `+0.014145578761930677` delta, exceeding the
required `+0.001` threshold.

Diagnostics were clean for fast, iteration, validation, and the reused incumbent
artifacts. The early day 1-5 mean RMSE guardrail had no `>2%` violations; the
largest measured early regression was validation `10m_u_component_of_wind` at
`+0.5104589610438858%`. The variable+lead RMSE guardrail had no `>10%`
violations; the largest measured regression was validation `geopotential_500` at
24h with `+6.762772928563493%`.

The change is physically plausible because it isolates the linear Coriolis
rotation from the IMEX tendency used during forecast rollout while preserving
the incumbent digital-filter initialization path. The split rotates nodal winds
exactly for each latitude and then projects back to modal vorticity/divergence.

## Lessons Learned

- Exact treatment of the local Coriolis rotation improves aggregate iteration
  and validation skill without breaching short-lead geopotential guardrails.
- Future proposals near this mechanism should keep watching day-1
  `geopotential_500`, which was the largest remaining variable+lead regression.

## Cleanup Completed

- Candidate code retained or reverted: retained in commit
  `56bda6beec7f67abc2e42cc130ec7295cf29d32a`.
- Research state updated: proposal moved to this history directory; scoring and
  implementation records written locally.
- Leaderboard updated: yes, local `.logbook/leaderboard.json` now points to the
  accepted candidate.
- Git status checked: clean tracked worktree after commit.

## Next Action

Continue the optimization loop with a new Researcher proposal pass and
Evaluator triage against
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split`.
