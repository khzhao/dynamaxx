# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.2368096372876574
- Iteration incumbent primary score: -0.2197104515448394
- Iteration delta: -0.01709918574281799
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.21940899263836755
- Validation delta: not run

## Rationale

The coupled surface residual-vector candidate failed the fixed iteration
promotion gate. Candidate diagnostics were clean with zero issues, but the
primary score regressed by `-0.01709918574281799` against the cached incumbent,
well below the required `+0.002` promotion threshold. It also failed the early
day 1-5 mean RMSE guardrail: `2m_temperature` regressed by
`2.904957387960501%`, above the fixed `2%` limit. The worst variable+lead RMSE
regression was `2m_temperature` at 216 h with `3.9714099404882055%`, below the
10% per-lead guardrail, but that does not rescue the failed primary and
early-lead gates.

Validation was skipped because iteration did not promote. Golden was not run.
The incumbent iteration metrics were reused from the valid leaderboard cache;
no incumbent rerun was performed.

## Lessons Learned

- Coupling T2m and U10 residual decay through a shared vector harmed the
  incumbent's strongest near-surface residual behavior rather than preserving
  useful boundary-layer regime information.
- The main damage appeared in early `2m_temperature`, while U10, MSLP, and Z500
  stayed nearly neutral. Future surface-residual ideas should explicitly
  protect early T2m before changing residual decay structure.
- The poor fast score was directionally predictive of the fixed iteration
  failure, even though fast remains only a sanity gate.

## Cleanup Completed

- Candidate code retained or reverted: reverted via reverse application of
  `candidate.diff`.
- Research state updated: selected ready proposal removed after being copied to
  this immutable history directory.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean; pre-existing untracked `gifs/`
  directory preserved.

## Next Action

Continue the open-ended optimization loop after cleanup. The staged
`delayed-lowmode-virtual-geopotential-coupling` idea remains available but was
not selected for this iteration.
