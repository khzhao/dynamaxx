# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.5150627015910243`
- Iteration incumbent primary score: `-0.532053269893688`
- Iteration delta: `+0.016990568302663656`
- Validation candidate primary score: `-0.5044433981077879`
- Validation incumbent primary score: `-0.5219023378614627`
- Validation delta: `+0.01745893975367474`

## Rationale

The candidate passed all fixed acceptance gates. Unit tests and diff checks passed before scoring. Candidate `fast`, `iteration`, and `validation` all completed with clean diagnostics and no reported issues. The incumbent comparison reused the valid leaderboard cache; no incumbent evaluation or `golden` run was performed.

The iteration primary-score delta exceeded the `+0.002` promotion threshold by `+0.014990568302663656`. The validation primary-score delta exceeded the `+0.001` acceptance threshold by `+0.01645893975367474`. No early day-1-through-day-5 mean RMSE regression exceeded `2%`, and no variable-lead RMSE regression exceeded `10%`. The largest validation RMSE regression was mean sea level pressure at day 4, `+0.6206428681060913%`.

The mechanism remains physically interpretable: the weak Held-Suarez equilibrium is shifted by a bounded, low-wavenumber analysis-state temperature offset, while the default incumbent path is preserved behind a default-false selector.

## Lessons Learned

- A bounded low-order analysis offset to the weak Held-Suarez equilibrium materially improved both iteration and validation scores without triggering fixed RMSE guardrails.
- The cache policy worked as intended: accepted incumbent metrics were reused from `.logbook/leaderboard.json`, avoiding an unnecessary incumbent rerun.
- Future proposals can explore similarly conservative analysis-conditioned equilibrium or relaxation changes, but should watch mean sea level pressure around day 4.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as accepted incumbent source state.
- Research state updated: consumed ready proposal removed after copying into this history directory.
- Leaderboard updated: updated locally to candidate artifacts and accepted commit.
- Git status checked: tracked worktree clean after accepted commit.

## Next Action

Start the next continuous-loop iteration immediately.
