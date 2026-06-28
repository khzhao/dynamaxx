# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.206563907329551`
- Iteration incumbent primary score: `-0.2616483974683927`
- Iteration delta: `+0.0550844901388417`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.2600180396322455`
- Validation delta: not applicable

## Rationale

The candidate passed the iteration primary-score threshold but failed the fixed
worst variable+lead RMSE guardrail, so it did not promote to validation. The
primary iteration delta was `+0.0550844901388417`, above the required `+0.002`,
and fast and iteration diagnostics were clean. However, mean sea level pressure
at 24 hours regressed from RMSE `380.0773181846907` to `426.628518862156`,
which is a `+12.24782391640764%` regression against the `10%` limit.

The early day 1-5 mean RMSE guardrail passed. The largest early mean regression
was `2m_temperature` at `+1.0189086270942393%`, below the `2%` limit. The
incumbent iteration and validation caches were valid and reused from
`.logbook/leaderboard.json`; no incumbent rerun was needed. Validation and
golden were not run because iteration did not promote.

## Lessons Learned

- DSE vertical thermal transport is a high-signal mechanism for aggregate
  iteration score, but it introduces an unacceptable short-lead MSLP shock.
- Future variants should protect or ramp short-lead pressure adjustment before
  reusing this mechanism; this exact candidate cannot be accepted under the
  fixed guardrails.

## Cleanup Completed

- Candidate code retained or reverted: reverted with the saved candidate diff.
- Research state updated: removed `.logbook/research/ready/vertical-dse-transport-mass-hsl.md`.
- Leaderboard updated: not updated because the candidate was rejected.
- Git status checked: tracked tree clean after rollback; unrelated untracked
  `gifs/` directory preserved.

## Next Action

Continue the optimization loop with the next research/evaluation iteration.
