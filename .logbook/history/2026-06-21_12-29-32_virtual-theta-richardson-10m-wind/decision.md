# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.5158726264914787
- Iteration incumbent primary score: -0.5150627015910243
- Iteration delta: -0.0008099249004543951
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5044433981077879
- Validation delta: not applicable

## Rationale

The candidate completed fixed fast and iteration gates with clean diagnostics, but it failed the primary iteration promotion threshold. The required candidate-minus-incumbent iteration delta is at least `+0.002`; the observed delta was `-0.0008099249004543951` against the cached accepted incumbent.

Guardrails did not force the rejection. Early day 1-5 mean RMSE regression passed for every fixed target variable. The worst variable-lead RMSE regression was `10m_u_component_of_wind` at day 8 with relative regression `0.004712142560269195`, below the 10% threshold. Validation was skipped because the iteration promotion gate did not pass.

The incumbent metrics were reused from the leaderboard cache. The cache was valid under the updated protocol, and no incumbent rerun was performed.

## Lessons Learned

- Adding bounded humidity dependence to the existing Richardson 10 m wind diagnostic slightly regressed the wind target and did not improve the aggregate primary score.
- Diagnostic-only virtual-temperature changes are unlikely to rescue this incumbent unless paired with a mechanism that improves non-wind variables or materially lowers 10 m wind RMSE.
- The updated cache policy worked as intended: candidate source edits did not invalidate the accepted incumbent cache.

## Cleanup Completed

- Candidate code retained or reverted: reverted after preserving `candidate.diff`.
- Research state updated: selected ready proposal removed from `.logbook/research/ready` after archival in history.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the open-ended optimization loop with a fresh resource and git-state check, then select or generate the next proposal.
