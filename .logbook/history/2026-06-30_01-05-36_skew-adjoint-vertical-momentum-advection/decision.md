# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: -1.7976931348623157e+308
- Fast diagnostics: failed with `nonfinite_forecast` and `nonfinite_metric`
- Iteration candidate primary score: not run
- Iteration incumbent primary score: -0.16500618979404214 from cached leaderboard artifact
- Iteration delta: not available because the fast gate failed
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.16591150807771451 from cached leaderboard artifact
- Validation delta: not available because the fast gate failed

## Rationale

The candidate passed local tests but failed the fixed `fast` evaluation gate with
nonfinite forecasts and nonfinite metric rows. The protocol requires a clean
fast sanity gate before iteration scoring, so candidate `iteration` and
`validation` runs were skipped.

The incumbent was not rerun. The leaderboard artifacts for
`dino_ri2m_ekman_coupled` were verified as readable, finite, diagnostically
clean, and compatible with the fixed data path, target variables, and lead
range. Candidate source edits do not invalidate the accepted incumbent cache
under `roles/PROTOCOL.md`.

This is a terminal rejection rather than a bounded revision. The selected
proposal already included nonfinite skew-tendency fallback, and the
implementation covered that path. Adding damping, clipping, timestep gating, or
growth-based fallback would change the experimental idea and should be proposed
separately if pursued.

## Lessons Learned

- A purely skew-adjoint vertical momentum operator can still destabilize the
  full rollout before the first fixed WeatherBench2 output, even when local
  nonfinite tendency fallback is present.
- Future vertical-advection proposals need a boundedness or damping mechanism
  justified as part of the proposal, not added after seeing fast failure.
- The incumbent cache policy worked as intended: no incumbent rerun was needed
  for a candidate that failed before iteration comparison.

## Cleanup Completed

- Candidate code retained or reverted: reverted by applying the reverse of
  `candidate.diff`.
- Research state updated: selected proposal moved from `ready` to this history
  directory; the alternative Ekman-depth proposal remains in `staging`.
- Leaderboard updated: no. Rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback, with pre-existing
  untracked `gifs/` preserved.

## Next Action

Continue the open-ended loop by asking the Researcher for another small set of
decorrelated proposals or by re-triaging staged ideas if no new proposals are
available.
