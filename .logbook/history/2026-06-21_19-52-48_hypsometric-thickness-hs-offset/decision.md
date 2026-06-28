# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.5150654718773497
- Iteration incumbent primary score: -0.5150627015910243
- Iteration delta: -2.770286325448623e-06
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.5044433981077879 cached, verified
- Validation delta: not computed

## Rationale

The fast gate passed with clean diagnostics, and the candidate iteration run
completed with `failed=False` and zero issues. Incumbent iteration and
validation artifacts were reused from the valid leaderboard cache; no incumbent
evaluation command was run.

The candidate did not meet the fixed iteration promotion threshold. Its
iteration primary score was slightly worse than the cached incumbent by
`-2.770286325448623e-06`, far below the required `+0.002` delta. Guardrails
were clean, with worst early day 1-5 mean RMSE relative regression
`3.4570851671668364e-07` and worst variable-lead relative regression
`1.1408463981766875e-05`, but clean guardrails do not compensate for a failed
primary-score gate. Candidate validation was correctly skipped.

## Lessons Learned

- The hypsometric thickness source is effectively neutral relative to the
  accepted analysis-HS equilibrium offset and does not provide measurable
  iteration skill.
- Nearby proposals should avoid another small source variant for the same
  analysis-HS offset unless the mechanism changes rollout behavior more
  materially.
- The incumbent cache policy worked as intended: cached leaderboard metrics
  were verified and reused, avoiding any baseline rerun.

## Cleanup Completed

- Candidate code retained or reverted: reverted after preserving
  `candidate.diff`.
- Research state updated: selected ready proposal removed from
  `.logbook/research/ready`.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Start the next continuous-loop iteration with a fresh resource, git, logbook,
and incumbent-cache check.
