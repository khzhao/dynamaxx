# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.52227605019974
- Iteration incumbent primary score: -0.5150627015910243
- Iteration delta: -0.007213348608715697
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5044433981077879
- Validation delta: not applicable

## Rationale

The candidate completed fixed fast and iteration gates with clean diagnostics, but it failed the primary iteration promotion threshold. The required candidate-minus-incumbent iteration delta is at least `+0.002`; the observed delta was `-0.007213348608715697` against the cached accepted incumbent.

Guardrails did not force the rejection. Early day 1-5 mean RMSE regression was `+0.03378362862626507%`, below the 2% guardrail. The worst variable-lead RMSE regression was `10m_u_component_of_wind` at 360 hours with relative regression `+1.939879528357435%`, below the 10% guardrail. Validation was skipped because the iteration promotion gate did not pass.

The incumbent iteration metrics were reused from the valid leaderboard cache. The validation incumbent cache was checked and compatible but not used for candidate comparison because candidate validation was skipped. No incumbent rerun was performed.

## Lessons Learned

- Nudging the lowest sigma temperature toward same-time `2m_temperature` was numerically stable but reduced aggregate iteration skill.
- The accepted surface residual path likely already captures the useful screen-temperature signal, or the prognostic lowest-layer perturbation harms coupled fields enough to dominate small thermal benefits.
- Future near-surface ideas should be cautious about changing prognostic lower-layer temperature unless they preserve wind and pressure coupling more tightly.

## Cleanup Completed

- Candidate code retained or reverted: reverted after preserving `candidate.diff`.
- Research state updated: selected ready proposal removed from `.logbook/research/ready` after archival in history.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the open-ended optimization loop with a fresh resource and git-state check, then select or generate the next proposal.
