# Decision

## Status

Rejected.

## Score Deltas

- Iteration primary score:
  - Candidate: `-1.1463108571625462`
  - Incumbent: `-1.143975258592661`
  - Delta: `-0.002335598569885189`
- Validation primary score:
  - Candidate: not run
  - Incumbent: `-1.1301883620649706`
  - Delta: not applicable

## Gate Rationale

The candidate failed the fixed iteration promotion gate. Its primary-score
delta was below the required `+0.002` threshold, so validation was not run.

Diagnostics were clean and both fixed RMSE guardrails passed. The day 1-5 mean
RMSE summaries had no regression above `2%`, and no variable+lead RMSE
regression exceeded `10%`. The decision is therefore driven by the negative
primary-score delta rather than a stability or diagnostic failure.

## Lessons Learned

- Preserving raw pre-DFI vorticity while keeping DFI-filtered divergence,
  thermal, mass, and tracer leaves did not recover enough wind skill to improve
  the fixed iteration primary score.
- The accepted full DFI state remains preferable to this approximate
  vorticity-preserving merge.
- Future DFI follow-ups should avoid partial state merges unless they include a
  stronger balance argument or target a clearly measured residual not captured
  by this clean negative result.
- Scoring noted that raw metric JSON artifacts include persistence rows; future
  guardrail calculations must filter by evaluated `model_name`.

## Cleanup

- Leaderboard update: not performed.
- Commit: not performed.
- Validation: skipped by protocol because iteration did not promote.
- Golden: not run.
- Implementation rollback: required for the six candidate source/test files.
