# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -1.2621122452124416
- Iteration incumbent primary score: -1.2218408656785489
- Iteration delta: -0.040271379533892704
- Validation candidate primary score: not_run
- Validation incumbent primary score: -1.2103467803549615
- Validation delta: not_run

## Rationale

The candidate passed full pytest, fast diagnostics, and iteration diagnostics,
but failed the fixed iteration promotion gate on primary score and guardrails.
The iteration primary delta was `-0.040271379533892704`, below the required
`+0.002` threshold. Validation was therefore not run.

The degradation was concentrated in `2m_temperature`. Early day 1-5 mean RMSE
regressed by `0.02751304810261005`, exceeding the `0.02` guardrail. Long-lead
variable+lead RMSE also exceeded the `0.10` guardrail at 312, 336, and 360
hours, with a maximum relative regression of `0.12899288988287547` at 360
hours.

## Lessons Learned

- Calendar-aware seasonal displacement of the weak Held-Suarez equilibrium is
  numerically stable but too aggressive for the fixed WeatherBench2 iteration
  split.
- The accepted weak-Held-Suarez gain appears sensitive to preserving the
  incumbent zonally symmetric equilibrium shape; simple seasonal shifting
  worsens 2 m temperature drift.
- Future Held-Suarez-family proposals should not change thermal-equilibrium
  geometry without a stronger bounded mechanism and a cheap pre-iteration
  temperature-drift check.

## Cleanup Completed

- Candidate code retained or reverted: reverted from the tracked worktree
- Research state updated: ready proposal removed after rejection
- Leaderboard updated: no, rejected candidates do not update the leaderboard
- Git status checked: tracked status clean after rollback

## Next Action

Start the next optimization iteration from
`dinosaur_dfi_surface_residual_weak_hs` as the incumbent. Ask Researcher for
new ideas or a documented exhaustion note while keeping
`semi-lagrangian-vertical-transport` staged for fresh triage.
