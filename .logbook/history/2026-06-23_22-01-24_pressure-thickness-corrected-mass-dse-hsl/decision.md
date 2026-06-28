# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.2678206586319622`
- Iteration incumbent primary score: `-0.2616483974683927`
- Iteration delta: `-0.006172261163569502`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.2600180396322455`
- Validation delta: not applicable

## Rationale

The candidate failed the fixed iteration promotion threshold. It needed an
iteration delta of at least `+0.002` against the cached incumbent
`dino_hsl2_mass_dse`, but measured `-0.006172261163569502`. Candidate fast and
iteration diagnostics were clean, and the incumbent iteration cache was valid
and reused from `.logbook/leaderboard.json`; no incumbent rerun was needed.

The fixed RMSE guardrails did not fail. The worst early day 1-5 mean RMSE
regression was mean sea level pressure at `0.4935870834249615%`, below the
`2%` limit. The worst variable+lead RMSE regression was mean sea level pressure
at 360 hours with `1.4280541410196068%`, below the `10%` limit. The rejection
is therefore based on broad primary-score degradation, not a diagnostics or
guardrail failure.

Validation and golden were not run because iteration did not promote.

## Lessons Learned

- The pressure-thickness product-rule correction disrupted the accepted
  mass-DSE balance under the fixed iteration metric.
- Future scoring checks should continue filtering eval records by `model_name`
  before guardrail comparison because metric JSON files include persistence
  rows alongside evaluated-model rows.

## Cleanup Completed

- Candidate code retained or reverted: reverted with the saved candidate diff.
- Research state updated: removed `.logbook/research/ready/pressure-thickness-corrected-mass-dse-hsl.md`.
- Leaderboard updated: not updated because the candidate was rejected.
- Git status checked: tracked tree clean after rollback.

## Next Action

Continue the optimization loop with the next research/evaluation iteration.
