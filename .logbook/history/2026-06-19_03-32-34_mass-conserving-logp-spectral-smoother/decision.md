# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.8308818797588234`
- Iteration incumbent primary score: `-0.8308832822743712`
- Iteration delta: `+0.0000014025155478103457`
- Validation candidate primary score: not run
- Validation incumbent primary score: not run
- Validation delta: not applicable

## Rationale

The candidate passed unit tests, the fast gate, iteration diagnostics, and both
RMSE guardrails. It did not meet the iteration promotion threshold from
`roles/PROTOCOL.md`: the primary-score delta was
`+0.0000014025155478103457`, below the required `+0.002` by
`0.0019985974844521897`. Validation was therefore not run.

The early day-1-through-day-5 mean RMSE guardrail had no violations. The largest
variable-by-lead RMSE regression was `+0.00748325882069714%` for
`geopotential_500` at day 12, well below the `10%` guardrail. The measured
effect is numerically clean but too small to justify promotion.

The Scorer reused incumbent iteration metrics from `.logbook/leaderboard.json`
after verifying the incumbent model, evaluation fingerprint, readable finite
artifact, and side-by-side candidate registration. The incumbent was still
compared against the candidate; only the incumbent rerun was skipped under the
cache-reuse rule.

## Lessons Learned

- A bounded high-mode `log_surface_pressure` smoother is stable and guardrail
  clean, but it produces an effectively neutral iteration score against the
  current incumbent.
- Pressure-noise control at this strength is not a material remaining error
  source for the fixed WeatherBench2 iteration protocol.
- Future pressure/geopotential proposals should either change a more physically
  consequential part of the prognostic balance or target a clearly distinct
  initialization/operator issue, not another conservative weak smoother.

## Cleanup Completed

- Candidate code retained or reverted: reverted after scoring.
- Research state updated: selected proposal remains frozen in this history
  directory with implementation and scoring records.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration with a fresh Researcher proposal set.
