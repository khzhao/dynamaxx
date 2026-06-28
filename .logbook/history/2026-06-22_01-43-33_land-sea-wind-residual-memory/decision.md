# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.4989518866948269`
- Iteration incumbent primary score: `-0.49843977504709575`
- Iteration delta: `-0.0005121116477311283`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.48771725322193726`
- Validation delta: not run

## Rationale

The candidate failed the fixed iteration promotion gate. The required iteration
primary-score delta is at least `+0.002`; this candidate scored
`-0.0005121116477311283` below the cached incumbent. Candidate iteration
completed with clean diagnostics and passed the fixed RMSE guardrails, but a
clean subthreshold or negative primary delta is not sufficient for validation.

Incumbent iteration metrics were reused from `.logbook/leaderboard.json`; no
incumbent evaluation command was run. Candidate validation and `golden` were
not run.

## Lessons Learned

- Land-sea residual structure was useful for `2m_temperature`, but the analogous
  low-mode 10 m wind residual-memory split did not improve the fixed iteration
  primary score.
- The RMSE guardrail deltas were near numerical noise, so this output-only wind
  memory change has little useful effect under the fixed metric.
- Future wind proposals should avoid small residual-memory variants unless they
  change a clearly measurable diagnostic or target a stronger physical
  mechanism.

## Cleanup Completed

- Candidate code retained or reverted: reverted with the saved candidate diff.
- Research state updated: consumed ready proposal removed after copying into
  this history directory.
- Leaderboard updated: unchanged because the candidate was rejected.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration immediately.
