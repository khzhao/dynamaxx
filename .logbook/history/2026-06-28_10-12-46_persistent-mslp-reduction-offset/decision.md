# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.21299743637019536`
- Iteration incumbent primary score: `-0.21299732605547173`
- Iteration delta: `-1.1031472363365324e-7`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21274255459898536`
- Validation delta: not run

## Rationale

The candidate passed focused tests, full pytest, compile/lint checks, fast eval, and iteration diagnostics. It failed the fixed iteration promotion gate because the primary-score delta was slightly negative and far below the required `+0.002`.

Guardrails were clean and not the reason for rejection. The largest variable-lead relative RMSE regression was `5.696330249715942e-7` for `10m_u_component_of_wind` at 288 h, far below the `10%` limit. The early day-1-through-day-5 mean RMSE relative changes were all numerical-noise scale.

Validation was skipped because iteration did not promote. The incumbent was not rerun; cached leaderboard artifacts from commit `3992244f20b2a938fdd96f8904f3749f5505670d` were valid and reused.

## Lessons Learned

- A persistent multiplicative MSLP reduction factor is stable but effectively neutral for the current RI2m incumbent.
- Future MSLP diagnostic proposals should not assume the initial MSLP/surface-pressure ratio is a material fixed-score bottleneck.
- More formula-heavy MSLP diagnostics should be ranked carefully because the simplest direct test did not move the metric.

## Cleanup Completed

- Candidate code retained or reverted: reverted after this history record was written.
- Research state updated: ready proposal moved into this history directory.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the open-ended optimization loop with a new resource/git inspection and Researcher/Evaluator pass.
