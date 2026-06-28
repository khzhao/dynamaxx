# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.21971074781018693`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `-2.9626534753246503e-07`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21940899263836755`
- Validation delta: not run

## Rationale

The candidate passed implementation checks, full tests, the fast sanity gate,
and the iteration diagnostic/guardrail checks, but it did not meet the fixed
iteration promotion threshold. The required primary-score delta is `+0.002`;
the observed delta was `-2.9626534753246503e-07` against the cached leaderboard
incumbent.

RMSE guardrails were clean. The largest early day 1-5 mean RMSE relative
regression was `geopotential_500` at `1.5154990780144199e-06`, below the fixed
`0.02` threshold. The worst variable+lead RMSE relative regression was
`geopotential_500` at 24 h with `4.902731068543002e-06`, below the fixed `0.1`
threshold. Clean guardrails do not override the failed primary promotion gate.

Validation was skipped because iteration did not promote. Golden was not run.
The incumbent iteration artifacts were reused from the valid leaderboard cache;
no incumbent rerun was performed.

## Lessons Learned

- Reordering theta recentering before WTG is stable but effectively neutral and
  slightly negative against the accepted incumbent.
- The accepted final theta-recentering order is not measurably diluting a WTG
  benefit under the fixed iteration metric.
- Future WTG work should deprioritize filter-order changes unless paired with a
  stronger physical mechanism that does not alter the fixed evaluation contract.

## Cleanup Completed

- Candidate code retained or reverted: reverted after this decision record was
  written.
- Research state updated: ready proposal removed after being copied into this
  immutable history directory.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the open-ended optimization loop with a new Researcher/Evaluator pass
using `dino_hsl2_mass_dse_wtg_vdse_ramp` as the incumbent and the cached
leaderboard artifacts as the comparison baseline.
