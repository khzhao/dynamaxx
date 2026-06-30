# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.16669329268791927
- Iteration incumbent primary score: -0.16500618979404214
- Iteration delta: -0.0016871028938771349
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.16591150807771451 from cached leaderboard artifact
- Validation delta: not available because validation was skipped

## Rationale

The candidate passed local tests, passed the fixed `fast` gate, and completed
the fixed `iteration` gate with clean diagnostics. RMSE guardrail differences
were numerical-noise scale and did not block promotion. The candidate still
failed the primary-score gate: its iteration primary score was worse than the
cached incumbent instead of at least `+0.002` better.

Validation was skipped by protocol because the iteration promotion gate failed.
The incumbent was not rerun. Cached incumbent iteration and validation artifacts
were verified as readable, finite, diagnostically clean, and compatible with the
fixed data path, target variables, lead range, and evaluation code. Candidate
source edits do not invalidate the accepted incumbent cache under
`roles/PROTOCOL.md`.

One scorer-side anomaly was recorded: an initial registration probe used a
nonexistent `list_models` helper and exited 1. The corrected
`dycore_model_names` / `create_dycore_model` check passed, and no files were
modified by the failed probe.

## Lessons Learned

- Ramping the accepted Ekman stress-pumping closure during the first forecast
  day is stable but materially worse on the fixed iteration primary score.
- The incumbent full-strength early Ekman impulse appears preferable to a
  gradual positive-time activation for this metric set.
- Future Ekman timing variants need stronger evidence than generic spinup
  plausibility before spending iteration compute.

## Cleanup Completed

- Candidate code retained or reverted: reverted by applying the reverse of
  `candidate.diff`.
- Research state updated: selected proposal moved from `ready` to this history
  directory; `state-increment-trust-region-filter` remains staged.
- Leaderboard updated: no. Rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback, with pre-existing
  untracked `gifs/` preserved.

## Next Action

Continue the open-ended loop with fresh Researcher proposals or a re-triage of
staged ideas, while preserving fixed evaluation protocols and incumbent cache
reuse.
