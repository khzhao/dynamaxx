# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.21968357037076797
- Iteration incumbent primary score: -0.2197104515448394
- Iteration delta: +0.000026881174071430314
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.21940899263836755
- Validation delta: not run

## Rationale

The candidate was numerically clean but did not meet the fixed iteration
promotion threshold. Its iteration primary score improved by only
`+0.000026881174071430314` against the cached incumbent, below the required
`+0.002` delta needed to run validation. Candidate diagnostics were clean with
zero issues, the early day 1-5 mean RMSE guardrail passed for all channels, and
the worst variable+lead RMSE regression was only `geopotential_500` at 24 h
with `+0.0006775690481942966%`, well below the 10% limit.

Validation was skipped because iteration did not promote. Golden was not run.
The incumbent iteration metrics were reused from the valid leaderboard cache;
no incumbent rerun was performed.

## Lessons Learned

- Mass-centering the layer-mass DSE HSL scalar is safe and slightly positive,
  but the measured effect is effectively neutral relative to the current
  incumbent and far below the fixed promotion threshold.
- The failure mode is insufficient aggregate primary-score movement, not
  diagnostics, nonfinite behavior, or RMSE guardrail regression.
- Future mass-DSE consistency ideas need a stronger mechanism than changing the
  scalar reference alone, or should be treated as diagnostic evidence rather
  than a likely accepted candidate.

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
`compensated-vertical-integral-reductions` and
`delayed-lowmode-virtual-geopotential-coupling` ideas remain available but were
not selected for this iteration.
