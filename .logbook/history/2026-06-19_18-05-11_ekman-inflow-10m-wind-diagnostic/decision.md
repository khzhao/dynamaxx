# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.5706118440326521`
- Iteration incumbent primary score: `-0.5719865269927361`
- Iteration delta: `+0.0013746829600840282`
- Validation candidate primary score: not run
- Validation incumbent primary score: not run
- Validation delta: not run

## Rationale

The candidate passed the fast gate and completed iteration with clean
diagnostics. The iteration RMSE guardrails also passed: no day 1-5 target
variable mean RMSE regression exceeded `2%`, and no variable+lead RMSE
regression exceeded `10%`.

The fixed promotion gate requires iteration primary-score improvement of at
least `+0.002`. The measured iteration delta was
`+0.0013746829600840282`, so the candidate did not qualify for validation.
Validation and golden were not run.

Incumbent metrics were recomputed rather than reused because this side-by-side
candidate modified shared Dinosaur adapter and registry source used by the
incumbent factory. The recomputed incumbent iteration score was used for the
decision; the accepted leaderboard artifact files were restored after scoring.

## Lessons Learned

- The bounded Ekman inflow diagnostic is numerically stable, but its primary
  improvement is below the fixed iteration threshold.
- The useful movement was concentrated in `10m_u_component_of_wind`; mass-field
  changes were effectively neutral and well inside guardrails.
- Side-by-side registry candidates still invalidate incumbent cache reuse when
  they edit shared source used by the incumbent.

## Cleanup Completed

- Candidate code retained or reverted: reverted all candidate source and test
  edits.
- Research state updated: selected proposal is preserved in this immutable
  history directory and no leaderboard update was made.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: tracked worktree clean after rollback.
- Evaluation artifacts: candidate fast and iteration outputs remain under
  `outputs/eval/`; accepted incumbent iteration and validation artifacts were
  restored from snapshots.

## Next Action

Start the next continuous-loop iteration with a fresh Researcher/Evaluator
cycle and exactly one new ready idea.
