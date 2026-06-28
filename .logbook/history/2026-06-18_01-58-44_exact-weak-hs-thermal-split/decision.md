# Decision

## Status

Rejected.

## Score Deltas

- Iteration primary score:
  - Candidate: `-1.1439279880915845`
  - Incumbent: `-1.143975258592661`
  - Delta: `+0.000047270501076557`
- Validation primary score:
  - Candidate: not run
  - Incumbent: `-1.1301883620649706`
  - Delta: not applicable

## Gate Rationale

The candidate failed the fixed iteration promotion gate. Its primary-score
delta was positive but far below the required `+0.002` threshold, so validation
was not run.

Diagnostics were clean and both fixed RMSE guardrails passed. The day 1-5 mean
RMSE summaries had no regression above `2%`, and no variable+lead RMSE
regression exceeded `10%`. The largest variable+lead RMSE regression was
`geopotential_500` at 360 hours with `+0.017601691550457336%`.

## Lessons Learned

- Exact positive-time integration of the accepted weak Held-Suarez thermal
  source is numerically clean but effectively neutral at this timestep and
  forcing strength.
- The accepted explicit weak-HS treatment is not a material remaining error
  source under the fixed iteration gate.
- Future source-formulation proposals should probably change a stronger
  physical mechanism than weak-HS source time discretization, while still
  avoiding changes known to damage 2 m temperature skill.
- Scoring confirmed again that raw metric JSON artifacts include persistence
  rows; guardrail calculations must filter by evaluated `model_name`.

## Cleanup

- Leaderboard update: not performed.
- Commit: not performed.
- Validation: skipped by protocol because iteration did not promote.
- Golden: not run.
- Implementation rollback: required for the six candidate source/test files.
