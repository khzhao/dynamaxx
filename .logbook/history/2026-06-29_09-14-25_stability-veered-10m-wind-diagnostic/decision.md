# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.16517847120559984`
- Iteration incumbent primary score: `-0.16500618979404214`
- Iteration delta: `-0.00017228141155770094`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.16591150807771451`
- Validation delta: not evaluated

## Rationale

The candidate passed local tests, fast evaluation, iteration diagnostics, and RMSE guardrails, but it failed the fixed iteration promotion gate. The iteration score regressed by `-0.00017228141155770094` relative to the cached incumbent and therefore did not meet the required `+0.002` promotion threshold. Validation was correctly skipped.

The signal was localized: the largest day-1-through-day-5 mean RMSE regression was `0.0017816532076095485` for `10m_u_component_of_wind`, and the largest single-lead RMSE regression was `0.006395679979946111` for `10m_u_component_of_wind` at 24 hours. Both guardrails were clean, but the primary-score movement was not competitive.

Incumbent iteration metrics were reused from the leaderboard cache at `outputs/eval/iteration_dino_ri2m_ekman_coupled.json`. No incumbent rerun was performed.

## Lessons Learned

- A bounded output-only wind veering diagnostic is numerically safe but did not improve the fixed score after the accepted Richardson wind and coupled Ekman closure.
- Future 10 m wind ideas should avoid small observational-operator rotations unless they use a stronger independent signal and explicitly protect early-lead zonal wind.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the tracked source/test tree using this history directory's `candidate.diff`.
- Research state updated: selected proposal moved to this history directory; rejected peer proposal remains in scrap.
- Leaderboard updated: no, rejected candidate did not replace the incumbent.
- Git status checked: yes after rollback; tracked worktree clean, with pre-existing untracked `gifs/` preserved.

## Next Action

Start the next continuous optimization iteration from incumbent `dino_ri2m_ekman_coupled`, reusing valid cached incumbent metrics from `.logbook/leaderboard.json`.
