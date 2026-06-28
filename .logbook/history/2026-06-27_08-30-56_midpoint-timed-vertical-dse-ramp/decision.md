# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.2196613024621508`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `+0.000049149082688604295`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21940899263836755` cached, not used
- Validation delta: not applicable

## Rationale

The candidate passed unit, lint, full pytest, fast, and iteration diagnostics.
Its largest variable-lead RMSE regression was only `+0.0000658702179304283`
relative at mean sea level pressure 48h, and early day-1 to day-5 regressions
were well below guardrail limits.

However, the fixed acceptance protocol requires iteration primary score to
improve by at least `+0.002` before validation. The measured iteration delta was
only `+0.000049149082688604295`, so the candidate did not promote. Validation
was skipped to preserve validation discipline.

## Lessons Learned

- Start-of-step versus midpoint sampling of the accepted vertical-DSE ramp is
  almost neutral under the current iteration split.
- Future vertical-DSE ideas should target a stronger physical mechanism than
  scalar ramp clock centering.

## Cleanup Completed

- Candidate code retained or reverted: reverted with `git apply -R` from
  `candidate.diff`.
- Research state updated: proposal moved from `ready` into this history
  directory; alternate WTG-envelope proposal remains staged.
- Leaderboard updated: no. Rejected candidates do not update leaderboard.
- Git status checked: tracked source/test tree clean after revert; pre-existing
  untracked `gifs/` preserved.

## Next Action

Revert this candidate implementation, verify tracked source/test tree is clean
apart from preserved `gifs/`, report the iteration result, and start the next
iteration.
