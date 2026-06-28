# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.21288078610169414`
- Iteration incumbent primary score: `-0.21299732605547173`
- Iteration delta: `+0.00011653995377758353`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21274255459898536`
- Validation delta: not run

## Rationale

The candidate passed the full unit suite, fast diagnostics, and iteration
diagnostics. It failed the fixed iteration promotion gate because the primary
score improvement was only `+0.00011653995377758353`, below the required
`+0.002` promotion threshold.

The RMSE guardrails passed and were not the reason for rejection. Early
day-1-through-day-5 mean RMSE relative regressions were all near numerical
noise scale, and the worst single variable-lead RMSE regression was
`+2.497315654025058e-9` relative for `2m_temperature` at 48 h, far below the
fixed `10%` limit.

Validation was skipped because iteration did not promote. Golden was not run.
The incumbent was not rerun; cached leaderboard iteration artifacts from commit
`3992244f20b2a938fdd96f8904f3749f5505670d` were valid and reused.

## Revision Decision

A bounded revision is not requested. The measured signal was positive but about
17 times smaller than the fixed promotion threshold. Increasing the closure
strength enough to plausibly bridge that gap would turn the candidate into
scratchpad amplitude tuning rather than a small implementation repair of the
selected idea.

## Lessons Learned

- A conservative rollout-only Eady-gated heat-flux filter is stable for this
  incumbent but too weak to materially affect the fixed iteration score.
- The mechanism may be worth revisiting only with stronger read-only evidence
  for a specific baroclinic thermal-gradient error, not as a blind amplitude
  retune.
- Future rollout-thermal proposals should include a clearer expected effect
  size or diagnostic proof before consuming long iteration evaluations.

## Cleanup Completed

- Candidate code retained or reverted: reverted after this decision record was
  written.
- Research state updated: selected ready proposal moved into this history
  directory.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the open-ended optimization loop with a fresh resource/git inspection
and Researcher/Evaluator pass. The staged
`ep-flux-zonal-momentum-redistribution` proposal remains staged, not ready,
pending diagnostic evidence.
