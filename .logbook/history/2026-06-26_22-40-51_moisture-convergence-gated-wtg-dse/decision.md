# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.21974636083207516`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `-3.590928723576359e-05`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21940899263836755`
- Validation delta: not run

## Rationale

The candidate passed the fast sanity gate and had clean diagnostics, but it did
not meet the fixed iteration promotion threshold. The required iteration primary
delta is `+0.002`; the observed delta was `-3.590928723576359e-05` against the
cached leaderboard incumbent.

Iteration RMSE guardrails were clean. The worst early day 1-5 mean RMSE
relative regression was `6.082983483621549e-10`, below the `0.02` guardrail.
The worst variable+lead RMSE relative regression was `3.170936417645094e-09`,
below the `0.1` guardrail. These guardrails do not override the failed primary
promotion gate.

Validation was skipped because the candidate did not promote on iteration.
Golden was not run because it is locked out for iterative model selection.

## Lessons Learned

- A bounded moisture-convergence modulation of WTG horizontal support produced
  nearly neutral RMSE guardrail changes but did not improve the aggregate
  iteration primary score.
- Preserving tropical-mean WTG support was not sufficient to improve on the
  pressure-ramped vertical DSE WTG incumbent.
- The cache policy worked as intended: the accepted incumbent artifacts were
  compatible and complete, so the incumbent was not rerun.

## Cleanup Completed

- Candidate code retained or reverted: reverted with reverse application of
  `candidate.diff`.
- Research state updated: ready proposal removed from
  `.logbook/research/ready`.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: yes; tracked source and test changes were removed after
  rollback.

## Next Action

Continue the open-ended optimization loop with a new Researcher proposal pass.
