# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.31286871436185787`
- Iteration incumbent primary score: `-0.31282890543336245`
- Iteration delta: `-3.9808928495421725e-05`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.3072374345999185`
- Validation delta: not run

## Rationale

`dino_hsl_picard` passed the fast and iteration execution gates with clean
diagnostics, but it failed the fixed iteration promotion gate. The primary
iteration delta versus cached incumbent `dino_hsl2_theta` was slightly
negative, below the required `+0.002` improvement threshold. Validation was
therefore correctly skipped.

RMSE guardrails were clean: early day 1-5 mean RMSE regressions had zero
violations, and the worst variable+lead RMSE regression was
`mean_sea_level_pressure` at `360` hours with relative regression
`0.00010533637568576736`, below the `0.10` guardrail. The candidate was
therefore numerically stable under the fixed gates, but not measurably better
than the incumbent.

Incumbent metrics were reused from the valid leaderboard cache:
`outputs/eval/iteration_dino_hsl2_theta.json` and
`outputs/eval/iteration_dino_hsl2_theta.csv`. The incumbent was not rerun.

## Lessons Learned

- A second Picard correction of the theta departure trajectory is effectively
  neutral to slightly negative after the accepted midpoint HSL theta path.
- The accepted `dino_hsl2_theta` midpoint trajectory appears to capture the
  useful departure-point improvement without needing another fixed-point wind
  remap.
- Future HSL theta proposals should avoid adding more trajectory correction
  cost unless they address a different, documented failure mode.

## Cleanup Completed

- Candidate code retained or reverted: reverted after saving `candidate.diff`.
- Research state updated: ready proposal removed after terminal decision.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the optimization loop with a new Researcher/Evaluator cycle and select
exactly one next ready idea.
