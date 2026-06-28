# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.21972592802933302`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `-0.000015476484493626153`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21940899263836755` available from cache, not used for comparison
- Validation delta: not run

## Rationale

The candidate was numerically clean but failed the fixed iteration promotion
gate. Its iteration primary score was slightly worse than the cached incumbent,
with a delta of `-1.5476484493626153e-05`, below the required `+0.002`.

Diagnostics were clean with zero issues. RMSE guardrails also passed: the worst
early day 1-5 mean RMSE regression was `2m_temperature` at
`+1.2602968186530021e-05`, and the worst variable+lead RMSE regression was
`2m_temperature` at `240h` with `+2.948277864775715e-05`, both far below the
fixed thresholds.

Validation was skipped because iteration did not promote. Golden was not run.
The incumbent iteration metrics were reused from the valid leaderboard cache;
no incumbent rerun was performed.

## Lessons Learned

- Switching the candidate to the high-precision `FastSphericalHarmonics`
  transform path is stable, but it does not improve the current WeatherBench2
  iteration score.
- The measured effect is very small and negative, so the remaining error is not
  usefully addressed by this transform-core precision change.
- This candidate is substantially slower to evaluate than recent physics-local
  candidates, so future spectral-transform-core ideas should be backed by a
  stronger implementation-specific mechanism before spending a full iteration
  run.

## Cleanup Completed

- Candidate code retained or reverted: reverted via reverse application of
  `candidate.diff`.
- Research state updated: selected ready proposal removed after being copied to
  this immutable history directory.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean; pre-existing untracked `gifs/`
  directory preserved.

## Next Action

After cleanup, continue the open-ended optimization loop. The staged
`stagewise-sil3-tendency-filtering` proposal remains available but should be
weighed against its broader time-integration risk and prior diffusion
experiment history.
