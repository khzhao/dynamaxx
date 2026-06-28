# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.2203902442291438`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `-0.0006797926843044033`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21940899263836755` cached, not used
- Validation delta: not applicable

## Rationale

The candidate passed unit, lint, full pytest, fast, and iteration diagnostics,
but the fixed protocol requires a positive iteration promotion of at least
`+0.002`. The candidate instead regressed by `-0.0006797926843044033`.
Validation was skipped to preserve validation discipline.

Guardrails did not force a separate rejection: the worst variable-lead RMSE
regression was `+0.0027943003920317165` relative for `10m_u_component_of_wind`
at 264h, and early day-1 to day-5 relative regressions were below protocol
limits. The primary-score regression is sufficient for rejection.

## Lessons Learned

- The accepted WTG latitude envelope appears to need its subtropical taper for
  the current pressure-ramped vertical-DSE incumbent.
- A narrow equatorial-only WTG support improves early Z500 slightly but damages
  wind and MSLP enough to lose primary skill.

## Cleanup Completed

- Candidate code retained or reverted: reverted with `git apply -R` from
  `candidate.diff`.
- Research state updated: proposal moved from `ready` into this history
  directory.
- Leaderboard updated: no. Rejected candidates do not update leaderboard.
- Git status checked: tracked source/test tree clean after revert; pre-existing
  untracked `gifs/` preserved.

## Next Action

Revert this candidate implementation, verify tracked source/test tree is clean
apart from preserved `gifs/`, report the iteration result, and start the next
iteration.
