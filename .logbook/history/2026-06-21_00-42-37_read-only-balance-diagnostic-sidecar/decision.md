# Decision Record

## Decision

`needs_revision`

## Score Summary

- Iteration candidate primary score: not run
- Iteration incumbent primary score: -0.5150627015910243
- Iteration delta: not applicable
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5044433981077879
- Validation delta: not applicable

## Rationale

The proposal is infrastructure-only and does not create a dycore candidate that
can beat the incumbent under the fixed WeatherBench2 gates. After the repository
reset and caching-policy clarification, retaining non-score source changes
would violate the user invariant that the latest commit is always the best
scored incumbent. No source implementation was retained, no fixed evaluation
protocol was changed, no incumbent run was performed, and no leaderboard update
was made.

## Lessons Learned

- Keep evaluation-support or diagnostic sidecars separate from model-selection
  commits unless an explicit infrastructure commit policy exists.
- Do not let infrastructure-ready ideas block continuous model-selection
  iterations.

## Cleanup Completed

- Candidate code retained or reverted: no candidate code was retained.
- Research state updated: proposal moved back to staging by Evaluator.
- Leaderboard updated: no.
- Git status checked: tracked worktree clean before the next model-selection iteration.

## Next Action

Continue the continuous loop with the selected model candidate
`smooth-analysis-hs-spectral-taper`.
