# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.49843977504709575`
- Iteration incumbent primary score: `-0.5150627015910243`
- Iteration delta: `+0.01662292654392855`
- Validation candidate primary score: `-0.48771725322193726`
- Validation incumbent primary score: `-0.5044433981077879`
- Validation delta: `+0.01672614488585067`

## Rationale

The candidate passed all fixed acceptance gates. Full pytest, candidate fast,
candidate iteration, and candidate validation all completed with clean
diagnostics. The incumbent comparison reused valid leaderboard iteration and
validation artifacts; no incumbent evaluation command was run, and `golden` was
not run.

The iteration primary-score delta exceeded the `+0.002` promotion threshold by
`+0.01462292654392855`. The validation primary-score delta exceeded the
`+0.001` acceptance threshold by `+0.01572614488585067`. No early day-1-through-
day-5 mean RMSE regression exceeded `2%`, and no variable-lead RMSE regression
exceeded `10%`. The largest validation variable-lead RMSE regression was
`geopotential_500` at 288 hours, `+0.0018690374539547118%`.

The mechanism is bounded and physically interpretable: it preserves the accepted
analysis-HS incumbent while making only the `2m_temperature` near-surface
residual memory land-sea aware. Land points retain incumbent residual decay,
ocean points keep longer residual memory, coastlines blend continuously, and the
model falls back to incumbent behavior if the static mask is unavailable or not
aligned.

## Lessons Learned

- Land-sea structure in the `2m_temperature` diagnostic was a recoverable error
  source under the fixed WeatherBench2 gates.
- The measured gain was concentrated in `2m_temperature`; pressure,
  geopotential, and 10 m wind changes remained near numerical noise and within
  fixed guardrails.
- The updated cache policy worked as intended: accepted incumbent metrics were
  reused from `.logbook/leaderboard.json`, avoiding an unnecessary incumbent
  rerun.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as accepted
  incumbent source state.
- Research state updated: consumed ready proposal removed after copying into
  this history directory.
- Leaderboard updated: updated locally to candidate artifacts and accepted
  commit.
- Git status checked: tracked worktree clean after accepted commit.

## Next Action

Start the next continuous-loop iteration immediately.
