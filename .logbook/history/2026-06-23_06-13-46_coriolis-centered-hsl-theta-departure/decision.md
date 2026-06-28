# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.3128234541629607`
- Iteration incumbent primary score: `-0.31282890543336245`
- Iteration delta: `+0.0000054512704017462`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.3072374345999185`
- Validation delta: not run

## Rationale

`dino_hsl_corcen` passed unit tests, fast scoring, and iteration diagnostics.
It did not promote because the iteration primary delta was only
`+0.0000054512704017462`, below the required `+0.002` threshold. Validation was
therefore skipped.

The RMSE guardrails passed comfortably. The largest day-1-to-5 mean RMSE
regression was `2m_temperature` at `+0.001225365959976717%`, and the worst
single variable-and-lead regression was `mean_sea_level_pressure` at 24h with
`+0.006187473340578273%`. This indicates the idea was effectively neutral
rather than unstable or physically damaging.

The incumbent `dino_hsl2_theta` comparison used the compatible cached
leaderboard artifacts; no incumbent rerun was performed.

## Lessons Learned

- Diagnostic half-step Coriolis centering of the HSL theta departure wind is
  numerically safe under the fixed gates but does not move the primary score
  enough to justify validation.
- Further variants in this neighborhood need a stronger mechanism than local
  Coriolis time-centering alone.
- The clean guardrails suggest the HSL2 incumbent is not sensitive to this
  diagnostic wind rotation at benchmark scale.

## Cleanup Completed

- Candidate code retained or reverted: reverted with
  `.logbook/history/2026-06-23_06-13-46_coriolis-centered-hsl-theta-departure/candidate.diff`.
- Research state updated: removed
  `.logbook/research/ready/coriolis-centered-hsl-theta-departure.md`; copied
  immutable proposal remains in this history directory.
- Leaderboard updated: no, rejected candidate did not replace the incumbent.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the open-ended optimization loop with a new Researcher/Evaluator
iteration. Future HSL trajectory ideas should be deprioritized unless they
change a stronger physical or numerical coupling than diagnostic Coriolis
centering alone.
