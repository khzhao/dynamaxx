# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.5150752074995624
- Iteration incumbent primary score: -0.5150627015910243
- Iteration delta: -0.000012505908538074095
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5044433981077879
- Validation delta: not applicable

## Rationale

The candidate completed fixed fast and iteration gates with clean diagnostics, but it failed the primary iteration promotion threshold. The required candidate-minus-incumbent iteration delta is at least `+0.002`; the observed delta was `-0.000012505908538074095` against the cached accepted incumbent.

Guardrails were clean. The worst early day 1-5 mean RMSE regression was `4.811324437525059e-10` for `10m_u_component_of_wind`, and the worst variable-lead RMSE regression was `2.1726286536216773e-09` for `2m_temperature` at 96 hours. Validation was skipped because the iteration promotion gate did not pass.

The incumbent iteration metrics were reused from the valid leaderboard cache. The validation incumbent cache was checked and compatible but not used for candidate comparison because candidate validation was skipped. No incumbent rerun was performed.

## Lessons Learned

- The bounded Helmholtz-projected momentum diffusion filter is numerically stable after the finite and energy guards, but it is effectively neutral and does not improve the fixed iteration score.
- The incumbent scalar modal diffusion appears sufficient for this accepted model at the current order and timescale.
- Future momentum-filter proposals should bring a more targeted mechanism than changing vector projection alone, because this version mostly reduced to numerical-scale differences.

## Cleanup Completed

- Candidate code retained or reverted: reverted after preserving `candidate.diff`.
- Research state updated: selected ready proposal removed from `.logbook/research/ready` after archival in history.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the open-ended optimization loop with a fresh resource and git-state check, then select or generate the next proposal.
