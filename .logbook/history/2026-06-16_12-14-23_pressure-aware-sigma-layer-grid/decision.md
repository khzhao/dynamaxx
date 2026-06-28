# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: -1.4026822509855363
- Fast diagnostics: passed, issue count 0
- Iteration candidate primary score: -1.4240296998737416
- Iteration incumbent primary score: -1.3208025947740873
- Iteration delta: -0.10322710509965427
- Validation candidate primary score: not run
- Validation incumbent primary score: -1.308334010223954
- Validation delta: not run

## Rationale

The candidate passed tests and fixed diagnostics, but the iteration primary score regressed by `-0.10322710509965427`, far below the required `+0.002` promotion threshold. Validation was therefore not run.

RMSE guardrails did not fail for the fixed target variables: early-lead mean RMSE and per-variable/lead RMSE changes were roundoff-scale. The rejection is driven by the aggregate primary score, not by nonfinite output or a conventional target RMSE guardrail breach. This indicates that the pressure-aware vertical grid is not beneficial under the current fixed WeatherBench2 evaluation contract even though it is numerically stable.

## Lessons Learned

- The accepted `dinosaur_dfi` incumbent should keep its equidistant sigma grid; pressure-level midpoint interfaces sharply reduced aggregate skill.
- Guardrail-neutral changes can still fail the fixed primary score, so future scoring analysis should inspect all primary-score components for rejected coordinate experiments.
- Vertical-coordinate changes are higher risk than their small code surface suggests because they alter initialization, DFI, finite differences, and output interpolation together.

## Cleanup Completed

- Candidate code retained or reverted: reverted; no candidate code retained in tracked source/test files.
- Research state updated: removed from `.logbook/research/ready`; immutable copy retained in this history directory.
- Leaderboard updated: no; incumbent remains `dinosaur_dfi`.
- Git status checked: clean tracked worktree after rollback.

## Next Action

Continue the loop by re-triaging the remaining staged ideas against the accepted `dinosaur_dfi` incumbent. Do not run `golden`.
