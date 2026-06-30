# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.1650176080797289
- Iteration incumbent primary score: -0.16500618979404214
- Iteration delta: -0.000011418285686765062
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.16591150807771451 from cached leaderboard artifact
- Validation delta: not available because validation was skipped

## Rationale

The candidate passed `uv run pytest`, passed the fixed `fast` gate, and completed
the fixed `iteration` gate with clean diagnostics and no RMSE guardrail failures.
It still failed promotion because the iteration primary score was slightly worse
than the cached incumbent instead of at least `+0.002` better.

Validation was skipped by protocol because the iteration promotion gate failed.
The incumbent was not rerun. Cached incumbent iteration and validation artifacts
were verified as readable, finite, diagnostically clean, and compatible with the
fixed data path, target variables, lead range, and evaluation code. Candidate
source edits do not invalidate the accepted incumbent cache under
`roles/PROTOCOL.md`.

## Lessons Learned

- Exact surface-mass neutrality in the accepted Ekman pumping increment is
  stable, but it is effectively neutral at WeatherBench2 iteration scale and
  does not materially improve the incumbent.
- The accepted log-area-neutral Ekman pumping projection is not an obvious
  leading error source after the large coupled-Ekman gain.
- Future Ekman variants need to change a forecast-relevant mechanism more
  strongly than an invariant correction that leaves metric rows near roundoff.

## Cleanup Completed

- Candidate code retained or reverted: reverted by applying the reverse of
  `candidate.diff`.
- Research state updated: selected proposal moved from `ready` to this history
  directory; `damped-courant-limited-vertical-momentum-transport` remains staged.
- Leaderboard updated: no. Rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback, with pre-existing
  untracked `gifs/` preserved.

## Next Action

Continue the open-ended loop with fresh Researcher proposals or a re-triage of
staged ideas, while preserving fixed evaluation protocols and incumbent cache
reuse.
