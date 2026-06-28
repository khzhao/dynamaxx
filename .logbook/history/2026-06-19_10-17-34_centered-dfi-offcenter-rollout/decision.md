# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5719815909858376`
- Iteration incumbent primary score: `-0.5719873627530224`
- Iteration delta: `+0.000005771767184858945`
- Validation candidate primary score: not run
- Validation incumbent primary score: not run
- Validation delta: not applicable

## Rationale

The candidate passed unit tests, the fast gate, iteration diagnostics, and both
iteration RMSE guardrails. It did not meet the iteration promotion threshold:
the primary-score delta was `+0.000005771767184858945`, below the required
`+0.002`. Validation was therefore not run, and golden was not run.

Guardrail movement was essentially neutral. The largest early day-1-through-day-5
mean RMSE regression was `+0.002344%` for `10m_u_component_of_wind`, and the
largest variable-by-lead RMSE regression was `+0.009600%` for
`geopotential_500` at day 1, both far below their guardrails.

The Scorer reused incumbent iteration metrics from `.logbook/leaderboard.json`
after verifying that the candidate was side-by-side, the incumbent model and
evaluation fingerprint matched the leaderboard, and shared `time_integration.py`
and eval protocol code were unchanged. The incumbent was still compared against
the candidate; only the incumbent rerun was skipped under the cache-reuse rule.

## Lessons Learned

- Keeping DFI centered while retaining off-centered positive-time rollout is
  numerically clean but has no material effect on the fixed iteration score.
- The accepted off-centered incumbent's gains are not sensitive to this DFI
  solver selector at the protocol threshold scale.
- Future off-centering followups should target a stronger physical or numerical
  mechanism than DFI solver routing alone.

## Cleanup Completed

- Candidate code retained or reverted: reverted after scoring.
- Research state updated: selected proposal remains frozen in this history
  directory with implementation and scoring records.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration with a fresh Researcher proposal set.
