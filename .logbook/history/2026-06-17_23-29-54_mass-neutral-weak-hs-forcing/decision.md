# Decision

## Status

Rejected.

## Score Deltas

- Iteration primary score:
  - Candidate: `-1.2018611065751152`
  - Incumbent: `-1.143975258592661`
  - Delta: `-0.05788584798245422`
- Validation primary score:
  - Candidate: not run
  - Incumbent: `-1.1301883620649706`
  - Delta: not applicable

## Gate Rationale

The candidate failed the fixed iteration promotion gate. Its primary-score
delta was below the required `+0.002` threshold, and validation was therefore
not run.

Diagnostics were clean, but the guardrails failed. The day 1-5 mean RMSE for
`2m_temperature` regressed by `5.411372769008427%`, above the allowed `2%`
early-lead threshold. The same variable also exceeded the `10%` variable+lead
RMSE guardrail from lead hours 168 through 360, with the worst regression
`27.361807150182948%` at 360 hours.

## Lessons Learned

- Removing the layerwise global-mean weak Held-Suarez thermal tendency is not a
  viable improvement for the current incumbent.
- The accepted weak Held-Suarez global-mean thermal source appears important
  for near-surface temperature skill, even though the mass-neutral variant
  slightly improved some non-temperature early RMSE summaries.
- Future forcing proposals should avoid removing the accepted global thermal
  mean unless they add a more physically grounded near-surface temperature
  compensation in a separately proposed mechanism.

## Cleanup

- Leaderboard update: not performed.
- Commit: not performed.
- Validation: skipped by protocol because iteration did not promote.
- Golden: not run.
- Implementation rollback: required for the six candidate source/test files.
