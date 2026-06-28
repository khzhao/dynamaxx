# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: `-0.5580695796244858`
- Iteration candidate primary score: `-0.5721268800247525`
- Iteration incumbent primary score: `-0.5719847137456165`
- Iteration delta: `-0.00014216627913599122`
- Validation candidate primary score: not run
- Validation incumbent primary score: not run
- Validation delta: not run

## Rationale

The candidate passed the fast gate and produced clean iteration diagnostics, but
it failed the iteration promotion threshold. The required primary-score delta is
`+0.002`; the measured delta was `-0.00014216627913599122` against a freshly
rerun current-source incumbent.

The fixed RMSE guardrails passed. No early day 1-5 mean RMSE regression exceeded
`2%`, and no variable+lead RMSE regression exceeded `10%`. The largest reported
variable+lead regression was `10m_u_component_of_wind` day 15 at
`+0.07849195911340257%`. Validation was not run because iteration did not
promote. Golden was not run.

The Scorer correctly rejected incumbent cache reuse because the implementation
modified shared incumbent source in `adapter.py` and uncommitted registry code.
The leaderboard incumbent iteration artifacts were snapshotted before rerun.
Because this candidate is rejected, the accepted leaderboard artifacts are
restored from that snapshot and the leaderboard is not updated.

## Lessons Learned

- Applying the accepted theta layer-mean recentering inside DFI was clean but
  slightly worse on the fixed iteration primary score.
- The measured effect was not a stability problem; the RMSE movements were
  small and well within guardrails.
- Shared adapter changes should continue to invalidate incumbent cache reuse
  unless immutable pre-change incumbent metrics are available.

## Cleanup Completed

- Candidate code retained or reverted: reverted.
- Research state updated: implemented proposal retained in immutable history.
- Leaderboard updated: no.
- Incumbent leaderboard artifacts restored: yes, from `cache_snapshots`.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop with a new Researcher pass.
