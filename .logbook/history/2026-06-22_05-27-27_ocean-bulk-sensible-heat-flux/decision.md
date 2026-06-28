# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.42701187536092744`
- Iteration incumbent primary score: `-0.49843977504709575`
- Iteration delta: `+0.0714278996861683`
- Validation candidate primary score: `-0.417391902036791`
- Validation incumbent primary score: `-0.48771725322193726`
- Validation delta: `+0.07032535118514627`

## Rationale

The candidate passed all model-selection gates against the cached leaderboard
incumbent artifacts. Incumbent iteration and validation metrics were reused from
the accepted baseline cache; no incumbent evaluation was rerun.

Fast diagnostics were clean. Iteration exceeded the `+0.002` promotion threshold
by a wide margin, and validation exceeded the `+0.001` acceptance threshold.
Diagnostics were clean for fast, iteration, and validation. Early day 1-5 mean
RMSE regressions stayed below the 2% guardrail for every target variable. The
worst variable-lead RMSE regressions were `+0.003001933955484315` on iteration
and `+0.002187786775164069` on validation, both for
`10m_u_component_of_wind` at 72 hours and both below the 10% guardrail.

The fixed iteration and validation CLI commands completed all forecast chunks
and metric aggregation but failed while writing official top-level metric files
because the candidate model name exceeded the filesystem filename-component
limit. Metrics were recovered with the repository's existing fixed runner
aggregation functions from completed chunk artifacts, without changing metrics,
splits, lead times, target variables, or data. Short reusable copies were stored
under `outputs/eval/` for leaderboard cache use.

## Lessons Learned

- Ocean-only bulk sensible heat exchange is a high-leverage physical addition on
  top of the accepted land-sea surface temperature residual candidate.
- Future long model names can exceed the top-level eval artifact filename
  limit, even when chunked fixed evaluations complete successfully.
- Scorer cache reuse worked as intended: the incumbent comparison came from
  valid leaderboard artifacts, not from a redundant incumbent run.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `329dd5758204b7e77f1abb258b1dab9ee5d9b2c8`.
- Research state updated: selected ready proposal removed after acceptance.
- Leaderboard updated: yes, to the accepted candidate and short metric artifact
  paths.
- Git status checked: tracked worktree clean after commit.

## Next Action

Start the next continuous-loop iteration immediately.
